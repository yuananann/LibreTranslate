"""Run before release: python -m campus.build_source_manifest.

Audit this list before publishing. New private files must never be included.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
# Only original source files recorded in the release manifest plus the campus extension.
def main():
    manifest=ROOT/'campus'/'source-manifest.json'
    if not manifest.exists(): raise SystemExit('Use the supplied release manifest as the audited baseline.')
    names=set(json.loads(manifest.read_text(encoding='utf-8')))
    for p in (ROOT/'campus').rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.json','.html','.css','.js','.md'}:
            names.add(p.relative_to(ROOT).as_posix())
    manifest.write_text(json.dumps(sorted(names),ensure_ascii=False,indent=2),encoding='utf-8')
    print('Review all paths before publishing:',len(names))

if __name__=='__main__': main()
