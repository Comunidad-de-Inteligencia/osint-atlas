from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from osint_atlas.catalog import load_catalog,catalog_version,generated_timestamp,load_yaml
from osint_atlas.maintenance import classify,targets,collect,read_state,advance,dashboard


def main():
    p=argparse.ArgumentParser(description="Comprueba exclusivamente documentación aprobada; no edita fichas")
    p.add_argument("--scope",choices=["critical","all"],default="all")
    p.add_argument("--timeout",type=float,default=10); p.add_argument("--delay",type=float,default=1)
    p.add_argument("--workers",type=int,default=4); p.add_argument("--state",type=Path,default=ROOT/".cache/maintenance-state/state.json")
    p.add_argument("--output",type=Path,default=ROOT/"reports/link-health.json")
    args=p.parse_args()
    catalog=load_catalog(); state=read_state(args.state)
    results=collect(targets(catalog,args.scope),state["checks"],args.timeout,args.delay,args.workers)
    process="daily" if args.scope=="critical" else "weekly"
    resolutions=load_yaml(ROOT/"data/resolutions.yaml")["resolutions"]
    state=advance(state,results,process,catalog_version(),resolutions=resolutions)
    actionable=[i for i in state["incidents"].values() if not i.get("resolved")]
    report={"generated_at":generated_timestamp(),"process":process,"action_required":bool(actionable),"actionable":actionable,"results":results,"state":state}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (args.output.parent/"state.json").write_text(json.dumps(state,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    (args.output.parent/"README.md").write_text(dashboard(state),encoding="utf-8")
    print(f"Comprobaciones: {len(results)}; incidencias pendientes: {len(actionable)}")
    return 0

if __name__=="__main__": raise SystemExit(main())
