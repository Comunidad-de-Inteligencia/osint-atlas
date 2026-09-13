import base64,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"src"))
from osint_atlas.maintenance import empty_state
def main():
    path=ROOT/".cache/maintenance-state/state.json"
    r=subprocess.run(["gh","api","repos/P3M-ACTF/osint-atlas/contents/state.json?ref=maintenance-state"],capture_output=True,text=True,encoding="utf-8",timeout=30)
    if r.returncode:
        if "404" not in r.stderr: raise RuntimeError("No se pudo recuperar el estado anterior; no se reinicia")
        state=empty_state()
    else: state=json.loads(base64.b64decode(json.loads(r.stdout)["content"]))
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(state,ensure_ascii=False),encoding="utf-8")
if __name__=="__main__":main()
