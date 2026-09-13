from __future__ import annotations
import argparse,hashlib,html.parser,json,re,sys,time,urllib.error,urllib.parse,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from osint_atlas.catalog import load_catalog,load_yaml,catalog_version,generated_timestamp
from osint_atlas.maintenance import read_state,advance,dashboard,safe_url,SafeRedirect,MAX_BYTES,USER_AGENT,url_key,classify


class Links(html.parser.HTMLParser):
    def __init__(self): super().__init__(); self.urls=set()
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            href=dict(attrs).get("href")
            if href:self.urls.add(href)


def canonical_url(url):
    p=urllib.parse.urlsplit(url)
    query=urllib.parse.urlencode([(k,v) for k,v in urllib.parse.parse_qsl(p.query) if not k.lower().startswith(("utm_","fbclid","gclid"))])
    return urllib.parse.urlunsplit((p.scheme,p.netloc,p.path.rstrip("/") or "/",query,""))


def select_candidates(source,body,known,limit=20):
    if source.get("format","html")=="markdown":
        links=set(re.findall(r"(?<!!)\[[^\]\n]+\]\((https://[^\s)]+)\)",body))
    else:
        parser=Links(); parser.feed(body); links=parser.urls
    selected={}
    for href in links:
        url=canonical_url(urllib.parse.urljoin(source["url"],href))
        p=urllib.parse.urlsplit(url)
        if p.scheme!="https" or not p.hostname or p.username or p.password or url in known: continue
        if any(pattern in p.path.lower() for pattern in source["exclude_patterns"]): continue
        if not any(pattern in p.path.lower() for pattern in source["include_patterns"]): continue
        key="candidate:"+url_key(url)
        selected[key]={"key":key,"kind":"editorial","reason":"candidate","url":url,"catalog":source["id"],
                       "source_url":source.get("provenance_url",source["url"]),"territory":source["territory"],"specialty":source.get("specialty","public-data"),
                       "license_note":source["license_note"],"critical":False,"opened_at":generated_timestamp(),"resolved":False}
    return sorted(selected.values(),key=lambda c:c["url"])[:limit]


def fetch_catalog(source,opener,hosts,timeout=15,sleep=time.sleep):
    safe_url(source["url"],hosts)
    for attempt in range(2):
        try:
            request=urllib.request.Request(source["url"],headers={"User-Agent":USER_AGENT})
            with opener(request,timeout=timeout) as response:
                body=response.read(MAX_BYTES+1)
                if len(body)>MAX_BYTES: raise ValueError("Documento supera el límite")
            return body.decode("utf-8",errors="replace")
        except OSError as exc:
            delay=2
            if isinstance(exc,urllib.error.HTTPError):
                if exc.code not in (429,500,502,503,504): raise
                retry_after=exc.headers.get("Retry-After") if exc.headers else None
                if retry_after:
                    try: delay=max(0,int(retry_after))
                    except ValueError: raise exc  # Defer a dated retry to a later run.
                    if delay>5: raise
            if attempt: raise
            sleep(delay)


def record_discovery(state,sources,candidates,errors):
    observations=state.setdefault("discovery",{})
    failures={e["key"]:e for e in errors}
    for item in candidates:
        previous=state["incidents"].get(item["key"],{})
        state["incidents"][item["key"]]={**item,"opened_at":previous.get("opened_at",item["opened_at"])}
    for source in sources:
        key="discovery:"+source["id"]
        error=failures.get(key)
        previous=observations.get(key,{})
        count=previous.get("consecutive_failures",0)+1 if error else 0
        observations[key]={"consecutive_failures":count,"last_attempt":generated_timestamp(),"status":error["status"] if error else "ok"}
        if error and (error["status"] not in ("temporary-error","rate-limited") or count>=3):
            before=state["incidents"].get(key,{})
            state["incidents"][key]={**error,"opened_at":before.get("opened_at",error["opened_at"])}
        elif not error and key in state["incidents"]:
            state["incidents"][key].update(resolved=True,resolved_at=generated_timestamp())
    return state


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,default=ROOT/"reports/discovery-candidates.json")
    p.add_argument("--state",type=Path,default=ROOT/".cache/maintenance-state/state.json")
    p.add_argument("--limit-per-catalog",type=int,default=20)
    args=p.parse_args()
    known={canonical_url(r["url"]) for r in load_catalog()["resources"]}
    sources=load_yaml(ROOT/"data/discovery.yaml")["approved_catalogs"]
    hosts={urllib.parse.urlsplit(s["url"]).hostname for s in sources}
    opener=urllib.request.build_opener(SafeRedirect(hosts)).open
    candidates={}; errors=[]
    for source in sources:
        try:
            body=fetch_catalog(source,opener,hosts)
            for c in select_candidates(source,body,known,args.limit_per_catalog): candidates[c["key"]]=c
        except (OSError,ValueError) as exc:
            errors.append({"key":"discovery:"+source["id"],"kind":"technical","reason":"discovery-failed","url":source["url"],
                           "specialty":source.get("specialty","public-data"),"critical":False,"opened_at":generated_timestamp(),"resolved":False,"error":type(exc).__name__,
                           "status":classify(exc.code) if isinstance(exc,urllib.error.HTTPError) else "partial" if isinstance(exc,ValueError) else "temporary-error"})
    state=record_discovery(read_state(args.state),sources,list(candidates.values()),errors)
    state=advance(state,[],"monthly",catalog_version(),success=not errors)
    pending=[i for i in state["incidents"].values() if not i.get("resolved")]
    report={"generated_at":generated_timestamp(),"action_required":bool(pending),"candidates":list(candidates.values()),
            "errors":errors,"actionable":pending,"state":state}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (args.output.parent/"state.json").write_text(json.dumps(state,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    (args.output.parent/"README.md").write_text(dashboard(state),encoding="utf-8")
    print(f"Candidatos: {len(candidates)}; errores: {len(errors)}")
    return 1 if errors else 0
if __name__=="__main__": raise SystemExit(main())
