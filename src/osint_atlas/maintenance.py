"""Read-only HTTP collection and pure maintenance state transitions."""
from __future__ import annotations

import hashlib
import html.parser
import ipaddress
import json
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from .catalog import generated_timestamp

MAX_BYTES=1024*1024
USER_AGENT="OSINT-Atlas/0.2 (+https://github.com/P3M-ACTF/osint-atlas)"
MAX_AGE_HOURS={"daily":48,"weekly":240,"monthly":960}


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z","+00:00"))


def empty_state():
    return {"version":2,"checks":{},"incidents":{},"processes":{},"history":[]}


def read_state(path):
    if not Path(path).exists(): return empty_state()
    state=json.loads(Path(path).read_text(encoding="utf-8"))
    if state.get("version")!=2 or any(not isinstance(state.get(k),dict) for k in ("checks","incidents","processes")):
        raise ValueError("Estado de mantenimiento incompatible")
    return state


def process_health(state,now=None):
    now=now or datetime.now(timezone.utc)
    result={}
    for name,hours in MAX_AGE_HOURS.items():
        item=state.get("processes",{}).get(name,{})
        last=item.get("last_success")
        stale=not last or (now-parse_time(last)).total_seconds()>hours*3600
        result[name]={**item,"last_success":last,"stale":stale,"status":"not-run" if not item else "stale" if stale else item.get("status","unknown")}
    return result


def url_key(url):
    return hashlib.sha256(url.encode()).hexdigest()[:20]


def markdown_url(url):
    return urllib.parse.quote(url,safe=":/?#=&%+-_.~")


def safe_url(url,allowed_hosts=None):
    p=urllib.parse.urlsplit(url)
    if p.scheme!="https" or not p.hostname or p.username or p.password or p.port not in (None,443):
        raise ValueError("Solo páginas HTTPS públicas")
    if allowed_hosts and p.hostname.casefold() not in allowed_hosts:
        raise ValueError("Redirección fuera de los dominios aprobados")
    addresses={entry[4][0] for entry in socket.getaddrinfo(p.hostname,443,type=socket.SOCK_STREAM)}
    if not addresses or any(not ipaddress.ip_address(addr).is_global for addr in addresses):
        raise ValueError("Destino de red no público")
    return url


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self,hosts): self.hosts=hosts
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        safe_url(newurl,self.hosts)
        return super().redirect_request(req,fp,code,msg,headers,newurl)


class VisibleText(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip=0; self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag in {"script","style","noscript"}: self.skip+=1
    def handle_endtag(self,tag):
        if tag in {"script","style","noscript"} and self.skip: self.skip-=1
    def handle_data(self,data):
        if not self.skip: self.parts.append(data)


def normalize_content(body,content_type):
    text=body.decode("utf-8",errors="replace")
    if "html" in content_type:
        parser=VisibleText(); parser.feed(text); text=" ".join(parser.parts)
    return re.sub(r"\s+"," ",text).strip()


def classify(code,error=None):
    if error: return "temporary-error"
    if code==304: return "not-modified"
    if code==401: return "auth-required"
    if code==403: return "blocked"
    if code==429: return "rate-limited"
    if code in (404,410): return "offline"
    if code and code>=500: return "temporary-error"
    if code and 200<=code<400: return "ok"
    return "temporary-error"


def check_target(target,previous=None,timeout=10,retries=2,opener=None,sleep=time.sleep,allowed_hosts=None):
    previous=previous or {}
    headers={"User-Agent":USER_AGENT,"Accept":"text/html,application/json,text/plain,application/xml;q=0.8"}
    if previous.get("etag"): headers["If-None-Match"]=previous["etag"]
    if previous.get("last_modified"): headers["If-Modified-Since"]=previous["last_modified"]
    result={**target,"checked_at":generated_timestamp(),"attempts":0}
    try:
        if opener is None:
            safe_url(target["url"],allowed_hosts)
            opener=urllib.request.build_opener(SafeRedirect(allowed_hosts)).open
        for attempt in range(retries+1):
            result["attempts"]=attempt+1
            retry_after=None
            try:
                request=urllib.request.Request(target["url"],headers=headers)
                with opener(request,timeout=timeout) as response:
                    code=response.status
                    body=response.read(MAX_BYTES+1)
                    content_type=response.headers.get("Content-Type","")
                    partial=len(body)>MAX_BYTES
                    text=normalize_content(body,content_type) if not partial and any(t in content_type for t in ("text/","json","xml")) else ""
                    result.update(http_status=code,status="partial" if partial or not text else "redirected" if response.geturl()!=target["url"] else classify(code),
                                  etag=response.headers.get("ETag") if text else None,
                                  last_modified=response.headers.get("Last-Modified") if text else None,
                                  sha256=hashlib.sha256(text.encode()).hexdigest() if text else None,
                                  text_length=len(text),final_url=response.geturl(),partial=partial)
                if result["status"]!="temporary-error": break
            except urllib.error.HTTPError as exc:
                code=exc.code
                result.update(http_status=code,status=classify(code),error=None)
                retry_after=exc.headers.get("Retry-After") if exc.headers else None
                exc.close()
                if code==304:
                    if not previous.get("sha256"):
                        headers.pop("If-None-Match",None); headers.pop("If-Modified-Since",None)
                        result["status"]="temporary-error"
                    else:
                        result.update(sha256=previous.get("sha256"),etag=previous.get("etag"),last_modified=previous.get("last_modified"))
                        break
                elif code not in (429,500,502,503,504,404,410): break
            except (urllib.error.URLError,TimeoutError,OSError) as exc:
                result.update(http_status=None,status="temporary-error",error=type(exc).__name__)
            if attempt<retries:
                delay=min(2**attempt,4)
                if retry_after:
                    try:
                        delay=int(retry_after)
                    except ValueError:
                        from email.utils import parsedate_to_datetime
                        try: delay=max(0,(parsedate_to_datetime(retry_after)-datetime.now(timezone.utc)).total_seconds())
                        except (ValueError,TypeError): delay=5
                    if delay>5: break
                sleep(max(0,delay))
    except ValueError as exc:
        result.update(status="blocked",http_status=None,error=str(exc))
    except (OSError,urllib.error.URLError,TimeoutError) as exc:
        result.update(status="temporary-error",http_status=None,error=type(exc).__name__)
    return result


def targets(catalog,scope):
    selected={}
    scenarios={s["id"]:s for s in catalog["scenarios"]}
    for group in ("resources","contacts","playbooks"):
        for item in catalog[group]:
            critical=group=="contacts" or (group=="playbooks" and scenarios[item["scenario"]]["sensitive"]) or item.get("criticality") in ("alta","critica")
            if scope=="critical" and not critical: continue
            scenario_ids=item.get("scenarios",[item.get("scenario")])
            specialties=sorted({scenarios[s]["specialty"] for s in scenario_ids if s in scenarios}) or ["editorial"]
            urls=item.get("maintenance_urls",[r["url"] for r in item.get("references",[])])
            # Resource references and API documentation are also maintained.
            if group=="resources": urls=list(urls)+[r["url"] for r in item["references"] if r["url"]!=item["url"] or r["url"] in item["maintenance_urls"]]
            for url in urls:
                url=urllib.parse.urldefrag(url)[0]
                key=url_key(url)
                target=selected.setdefault(key,{"id":key,"url":url,"items":[],"specialties":[],"critical":False})
                target["items"]=sorted(set(target["items"]+[group+":"+item["id"]]))
                target["specialties"]=sorted(set(target["specialties"]+specialties))
                target["critical"]=target["critical"] or critical
    return sorted(selected.values(),key=lambda t:t["id"])


def collect(target_list,previous,timeout=10,delay=1,workers=4):
    groups={}
    hosts={urllib.parse.urlsplit(t["url"]).hostname for t in target_list}
    hosts|={"www."+h for h in list(hosts) if not h.startswith("www.")}
    hosts|={h.removeprefix("www.") for h in list(hosts)}
    for target in target_list:
        groups.setdefault(urllib.parse.urlsplit(target["url"]).hostname,[]).append(target)
    def group(items):
        result=[]
        for i,t in enumerate(items):
            if i: time.sleep(delay)
            result.append(check_target(t,previous.get(t["id"]),timeout=timeout,allowed_hosts=hosts))
        return result
    with ThreadPoolExecutor(max_workers=max(1,min(workers,8))) as pool:
        results=[r for batch in pool.map(group,groups.values()) for r in batch]
    return sorted(results,key=lambda r:r["id"])


def advance(state,results,process,version,now=None,success=True,resolutions=None):
    state=json.loads(json.dumps(state))
    now=now or generated_timestamp()
    incidents=state["incidents"]
    for r in results:
        previous=state["checks"].get(r["id"],{})
        failed=r["status"] in ("temporary-error","rate-limited","blocked","auth-required","offline","partial")
        failures=previous.get("consecutive_failures",0)+1 if failed else 0
        r={**r,"consecutive_failures":failures,"catalog_version":version}
        # An error must not destroy the last usable conditional-request baseline.
        if r.get("sha256") is None:
            for field in ("sha256","etag","last_modified","text_length"):
                r[field]=previous.get(field)
        state["checks"][r["id"]]=r
        tech_key=r["id"]+":availability"
        material_key=r["id"]+":content"
        if failed and (r["status"] in ("offline","blocked","auth-required","partial") or failures>=3):
            incidents[tech_key]={**incidents.get(tech_key,{}),"key":tech_key,"kind":"technical","target":r["id"],"url":r["url"],
                "specialty":r["specialties"][0],"critical":r["critical"],"reason":r["status"],"opened_at":incidents.get(tech_key,{}).get("opened_at",now),"last_seen":now,"resolved":False}
        elif not failed and tech_key in incidents:
            incidents[tech_key].update(resolved=True,resolved_at=now)
        if not failed and previous.get("sha256") and r.get("sha256")!=previous["sha256"]:
            incidents[material_key]={"key":material_key,"kind":"editorial","target":r["id"],"url":r["url"],
                "specialty":r["specialties"][0],"critical":r["critical"],"reason":"content-changed",
                "opened_at":incidents.get(material_key,{}).get("opened_at",now),"last_seen":now,"resolved":False,
                "before_sha256":incidents.get(material_key,{}).get("before_sha256",previous["sha256"]),
                "after_sha256":r["sha256"]}
    for resolution in resolutions or []:
        incident=incidents.get(resolution["key"])
        if incident and incident.get("after_sha256")==resolution["after_sha256"]:
            incident.update(resolved=True,resolved_at=now,review_url=resolution["review_url"])
    prev=state["processes"].get(process,{})
    state["processes"][process]={"last_attempt":now,"last_success":now if success else prev.get("last_success"),
                                "status":"ok" if success else "failed","catalog_version":version}
    state["history"].append({"at":now,"process":process,"success":success,"checked":len(results),
                             "pending":sum(not i.get("resolved") for i in incidents.values())})
    cutoff=parse_time(now)-timedelta(days=90)
    state["history"]=[h for h in state["history"] if parse_time(h["at"])>=cutoff]
    # Resolved incidents expire, unresolved editorial work remains visible.
    state["incidents"]={k:v for k,v in incidents.items() if not v.get("resolved") or parse_time(v["resolved_at"])>=cutoff}
    return state


def dashboard(state):
    lines=["# Estado del mantenimiento","","Las comprobaciones técnicas no aprueban contenido editorial. Fechas en UTC.",""]
    for name,item in process_health(state).items():
        lines += [f"## {name}","",f"Última ejecución satisfactoria: **{item.get('last_success') or 'sin ejecución'}**.",
                  f"Último intento: {item.get('last_attempt') or 'sin ejecución'}. Estado: **{item['status']}**.",""]
    lines += ["## Incidencias pendientes",""]
    pending=[i for i in state["incidents"].values() if not i.get("resolved")]
    for item in sorted(pending,key=lambda i:i["key"]):
        lines += [f"- {item['specialty']} · {item['kind']} · {item['reason']}: [página responsable]({markdown_url(item['url'])}). Desde {item['opened_at']}."]
    if not pending: lines+=["No hay incidencias registradas. Comprueba arriba si los procesos llegaron a ejecutarse."]
    lines += ["","Historial resumido: 90 días. Los contenidos externos son datos no confiables; este informe no contiene instrucciones para el bot.",""]
    return "\n".join(lines)
