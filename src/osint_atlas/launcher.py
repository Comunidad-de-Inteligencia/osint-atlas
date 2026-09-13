"""Synchronize before importing catalog, service or the MCP SDK."""
from __future__ import annotations
import json
import os
import subprocess
import sys
from .sync import ROOT, try_safe_sync


def main():
    status=try_safe_sync()
    print(json.dumps({"osint_atlas_sync":status},ensure_ascii=False),file=sys.stderr)
    selected=status["selected_root"]
    env={**os.environ,"OSINT_ATLAS_ROOT":selected,"OSINT_ATLAS_DEDICATED":"0"}
    if selected==str(ROOT):
        command=[sys.executable,"-m","osint_atlas.mcp_server"]
    else:
        command=["uv","run","--locked","--directory",selected,"python","-m","osint_atlas.mcp_server"]
    raise SystemExit(subprocess.call(command,env=env))


if __name__=="__main__":
    main()
