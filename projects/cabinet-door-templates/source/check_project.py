#!/usr/bin/env python3
"""Check navigation, declared artifacts, Python syntax and preserved model bytes."""
import ast
import hashlib
from html.parser import HTMLParser
import json
import re
from urllib.parse import urlsplit, unquote
from zipfile import ZipFile
from project_paths import ROOT, ARTIFACTS, DESIGNS

errors=[];links=0
class Links(HTMLParser):
    def __init__(self):super().__init__();self.urls=[]
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key in ('href','src') and value:self.urls.append(value)

def check_url(page,url):
    global links
    parsed=urlsplit(url)
    if parsed.scheme or parsed.netloc or not parsed.path:return
    if '${' in url:return
    path=(ROOT if parsed.path.startswith('/') else page.parent)/unquote(parsed.path).lstrip('/')
    links+=1
    if not path.exists():errors.append(f'Broken link: {page.relative_to(ROOT)} -> {url}')

for name,path in ARTIFACTS.items():
    if not path.is_file():errors.append(f'Missing artifact: {name} -> {path.relative_to(ROOT)}')
for p in ROOT.rglob('*.html'):
    parser=Links();text=p.read_text();parser.feed(text)
    for url in parser.urls:check_url(p,url)
    # The comparison's dynamic links are carried in the preview payload.
    if p.name=='index.html':
        match=re.search(r'const data\s*=\s*',text)
        data,_=json.JSONDecoder().raw_decode(text[match.end():])
        for design in data['designs'].values():
            for part in design['parts'].values():
                for url in part['downloads'].values():check_url(p,url)
for p in ROOT.rglob('*.md'):
    for url in re.findall(r'\]\(([^)]+)\)',p.read_text()):check_url(p,url)
for p in (ROOT/'source').glob('*.py'):
    tree=ast.parse(p.read_text(),filename=str(p))
    for node in ast.walk(tree):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='artifact_path' and node.args and isinstance(node.args[0],ast.Constant):
            name=node.args[0].value
            if isinstance(name,str) and name not in ARTIFACTS:errors.append(f'Unregistered generator artifact: {p.name}: {name}')
record=json.loads((ROOT/'archive/migration.json').read_text());preserved=0
for old,new in record['moves'].items():
    path=ROOT/new
    if not path.exists():errors.append(f'Moved file missing: {new}');continue
    if path.suffix.lower() in ('.3mf','.stl','.step','.png','.gcode'):
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest!=record['original_sha256'][old]:errors.append(f'Artifact bytes changed: {new}')
        preserved+=1
        if path.suffix=='.3mf':
            with ZipFile(path) as z:
                if z.testzip():errors.append(f'Invalid 3MF archive: {new}')
for design in DESIGNS:
    by_part={part:{r['id'] for r in design['revisions'] if r['part']==part} for part in ['rails','stiles']}
    for key,revision in design['selection'].items():
        part='rails' if key in ['unsplit_rail','split_rail_candidate'] else 'stiles' if key in ['unsplit_stiles','split_stiles'] else None
        if part and revision not in by_part[part]:errors.append(f'Unknown selected revision: {design["id"]}/{part}/{revision}')
if errors:
    raise SystemExit('\n'.join(errors))
print(f'PASS: {len(DESIGNS)} designs; {len(ARTIFACTS)} declared artifacts; {links} local links; {preserved} model/image/G-code files unchanged; Python syntax and 3MF archives valid.')
