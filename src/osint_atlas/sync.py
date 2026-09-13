from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(os.environ.get("OSINT_ATLAS_ROOT",Path(__file__).resolve().parents[2])).resolve()
APPROVED_REMOTES={"https://github.com/P3M-ACTF/osint-atlas.git","https://github.com/P3M-ACTF/osint-atlas","git@github.com:P3M-ACTF/osint-atlas.git"}


def _git(*args,timeout=20,root=None):
    return subprocess.run(["git","-C",str(root or ROOT),*args],capture_output=True,text=True,timeout=timeout,check=False)


def source_age_days():
    try:
        result=_git("log","-1","--format=%ct",timeout=3)
        if result.returncode: return None
        return max(0,round((datetime.now(timezone.utc).timestamp()-int(result.stdout.strip()))/86400,2))
    except (OSError,ValueError,subprocess.TimeoutExpired):
        return None


def try_safe_sync():
    base={"repository":str(ROOT),"source_age_days":source_age_days(),"selected_root":str(ROOT)}
    if os.environ.get("OSINT_ATLAS_DEDICATED")!="1":
        return {**base,"status":"local-only","detail":"Sincronización desactivada: requiere copia dedicada explícita."}
    state_path=ROOT/".cache/last-good.json"
    try:
        previous=json.loads(state_path.read_text(encoding="utf-8"))
        previous_path=Path(previous["selected_root"]).resolve()
        if previous_path.is_relative_to(ROOT/".cache/snapshots") and previous_path.is_dir():
            base.update(selected_root=str(previous_path))
    except (OSError,ValueError,KeyError):
        pass
    try:
        dirty=_git("status","--porcelain")
        if dirty.returncode or dirty.stdout.strip():
            return {**base,"status":"skipped-dirty","detail":"Cambios locales: se conserva la copia disponible."}
        remote=_git("remote","get-url","origin")
        if remote.returncode or remote.stdout.strip() not in APPROVED_REMOTES:
            return {**base,"status":"unapproved-remote","detail":"Se requiere el remoto autorizado de OSINT Atlas."}
        fetched=_git("fetch","--quiet","origin","main")
        if fetched.returncode:
            return {**base,"status":"sync-failed","detail":"No se pudo actualizar; se usa la última copia disponible."}
        if _git("merge-base","--is-ancestor","HEAD","origin/main").returncode:
            return {**base,"status":"needs-review","detail":"Historia divergente: no se mezcla el contenido."}
        sha=_git("rev-parse","origin/main").stdout.strip()
        if not sha or len(sha)!=40:
            raise ValueError("Revisión remota inválida")
        candidate=ROOT/".cache/snapshots"/sha
        candidate.parent.mkdir(parents=True,exist_ok=True)
        if not candidate.exists():
            created=_git("worktree","add","--detach",str(candidate),sha)
            if created.returncode: raise OSError("No se pudo preparar la copia")
        # A fresh environment and process validate code, lock and data together.
        env={**os.environ,"OSINT_ATLAS_ROOT":str(candidate),"OSINT_ATLAS_DEDICATED":"0"}
        checked=subprocess.run(["uv","run","--locked","--directory",str(candidate),"python","tools/build_catalog.py","--check"],
                               capture_output=True,text=True,timeout=60,env=env)
        if checked.returncode: raise ValueError("Actualización incompatible o dependencias no disponibles")
        state={**base,"status":"updated","selected_root":str(candidate),"commit":sha,
               "last_success":datetime.now(timezone.utc).isoformat(),"detail":"Instantánea validada antes de iniciar el servidor."}
        temp=state_path.with_suffix(".tmp")
        temp.write_text(json.dumps(state,ensure_ascii=False),encoding="utf-8")
        os.replace(temp,state_path)
        return state
    except (OSError,ValueError,subprocess.TimeoutExpired):
        return {**base,"status":"sync-failed","detail":"Fallo de Git, red, validación o tiempo máximo; se conserva la última copia válida."}
