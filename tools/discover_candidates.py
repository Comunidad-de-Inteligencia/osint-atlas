from __future__ import annotations
import argparse,hashlib,html.parser,json,re,sys,urllib.parse,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from osint_atlas.catalog import load_catalog,load_yaml,catalog_version,generated_timestamp
from osint_atlas.maintenance import read_state,advance,dashboard,safe_url,SafeRedirect,MAX_BYTES,USER_AGENT,url_key


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
            safe_url(source["url"],hosts)
            request=urllib.request.Request(source["url"],headers={"User-Agent":USER_AGENT})
            with opener(request,timeout=15) as response:
                body=response.read(MAX_BYTES+1)
                if len(body)>MAX_BYTES: raise ValueError("Documento supera el límite")
            for c in select_candidates(source,body.decode("utf-8",errors="replace"),known,args.limit_per_catalog): candidates[c["key"]]=c
        except (OSError,ValueError) as exc:
            errors.append({"key":"discovery:"+source["id"],"kind":"technical","reason":"discovery-failed","url":source["url"],
                           "specialty":"public-data","critical":False,"opened_at":generated_timestamp(),"resolved":False,"error":type(exc).__name__})
    state=read_state(args.state)
    for item in [*candidates.values(),*errors]:
        previous=state["incidents"].get(item["key"],{})
        state["incidents"][item["key"]]={**item,"opened_at":previous.get("opened_at",item["opened_at"])}
    failed={e["key"] for e in errors}
    for source in sources:
        key="discovery:"+source["id"]
        if key not in failed and key in state["incidents"]:
            state["incidents"][key].update(resolved=True,resolved_at=generated_timestamp())
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
