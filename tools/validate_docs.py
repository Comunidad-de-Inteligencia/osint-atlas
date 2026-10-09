from __future__ import annotations
import re,sys,urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def prose(text):
    lines=[]; fence=None
    for line in text.splitlines():
        stripped=line.lstrip()
        match=re.match(r"(^\x60{3,}|^~{3,})",stripped)
        if match:
            char=match[1][0]
            if fence is None: fence=char
            elif fence==char: fence=None
            lines.append("")
        elif fence is None: lines.append(line)
    return "\n".join(lines)


def headings(text):
    return [(len(m[1]),m[2]) for line in prose(text).splitlines() if (m:=re.match(r"^(#{1,6})\s+(.+?)\s*#*$",line))]


def anchors(text):
    seen={}; result=set()
    for _,title in headings(text):
        slug=re.sub(r"[^\w\- ]","",title.lower()).replace(" ","-")
        index=seen.get(slug,0); seen[slug]=index+1
        result.add(slug if index==0 else f"{slug}-{index}")
    result.update(re.findall(r'<(?:a|h[1-6])[^>]+id=["\']([^"\']+)',text))
    return result


def validate_document(path,root=ROOT):
    text=path.read_text(encoding="utf-8-sig"); content=prose(text); errors=[]
    hs=headings(text)
    if not hs or hs[0][0]!=1 or sum(level==1 for level,_ in hs)!=1:
        errors.append("se requiere un único H1 inicial")
    for (previous,_),(current,_) in zip(hs,hs[1:]):
        if current>previous+1: errors.append(f"salto H{previous} a H{current}")
    for alt,_ in re.findall(r"!\[([^]]*)\]\(([^)]+)\)",content):
        if not alt.strip(): errors.append("imagen sin texto alternativo")
    for label,target in re.findall(r"(?<!!)\[([^]]*)\]\(([^)]+)\)",content):
        if not label.strip(): errors.append("enlace sin descripción")
        target=target.strip("<>")
        parsed=urllib.parse.urlsplit(target)
        if parsed.scheme in ("http","https","mailto"):continue
        local=(path.parent/urllib.parse.unquote(parsed.path)).resolve() if parsed.path else path
        if not local.is_relative_to(root): errors.append("enlace fuera del repositorio"); continue
        if not local.exists(): errors.append(f"enlace interno roto: {target}");continue
        if parsed.fragment and local.suffix==".md":
            if urllib.parse.unquote(parsed.fragment) not in anchors(local.read_text(encoding="utf-8-sig")):
                errors.append(f"ancla inexistente: {target}")
    return errors


def main():
    files=[*ROOT.glob("*.md"),*(ROOT/"docs").rglob("*.md")]
    files=[p for p in files if p.name!="AGENTS.md"]
    errors=[f"{p.relative_to(ROOT)}: {error}" for p in files for error in validate_document(p)]
    sys.path.insert(0, str(ROOT / "tools"))
    from check_translations import pending
    errors.extend(pending(ROOT))
    for error in errors:print("ERROR: "+error,file=sys.stderr)
    if not errors: print(f"OK: estructura y enlaces de {len(files)} documentos; no es una certificación de accesibilidad")
    return bool(errors)
if __name__=="__main__":raise SystemExit(main())
