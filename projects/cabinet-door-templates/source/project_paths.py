"""Resolve design-owned artifacts and publish links relative to their datasheet.

Add a revision and its artifacts to designs/<design>/design.json. Generators use
stable artifact names; the manifest owns their location and compatibility.
"""
from pathlib import Path
from html import escape, unescape
import json
import os
import re
from urllib.parse import urlsplit, unquote, quote

ROOT=Path(__file__).resolve().parents[1]
CATALOG=json.loads((ROOT/'designs/catalog.json').read_text())
DESIGNS=[json.loads((ROOT/'designs'/name/'design.json').read_text()) for name in CATALOG['designs']]
ARTIFACTS={name:ROOT/path for name,path in CATALOG['artifacts'].items()}
for design in DESIGNS:
    for revision in design['revisions']:
        base=ROOT/'designs'/design['id']/revision['path']
        for name,path in revision['artifacts'].items():
            if name in ARTIFACTS:
                raise ValueError(f'Duplicate artifact identifier: {name}')
            ARTIFACTS[name]=base/path


def artifact_path(name):
    """Get a declared input/output; unregistered artifacts fail before writing."""
    name=str(name)
    if name in CATALOG['legacy_urls']:
        return ROOT/CATALOG['legacy_urls'][name]
    return ARTIFACTS[name]


def artifact_url(name, page=None):
    destination=ROOT/'index.html' if page is None else Path(page)
    return Path(os.path.relpath(artifact_path(name),destination.parent)).as_posix()


def publish_html(destination, html):
    """Relocate known local links in generated HTML; preserve external URLs."""
    destination=Path(destination)
    def link(match):
        raw=unescape(match.group(2));url=urlsplit(raw)
        if url.scheme or url.netloc or not url.path or '${' in raw:
            return match.group(0)
        name=unquote(url.path)
        if name in CATALOG['legacy_urls'] or name in ARTIFACTS:
            path=artifact_url(name,destination)
        elif (ROOT/name).exists():
            path=Path(os.path.relpath(ROOT/name,destination.parent)).as_posix()
        else:
            return match.group(0)
        suffix=('?'+url.query if url.query else '')+('#'+url.fragment if url.fragment else '')
        return match.group(1)+escape(quote(path,safe='/')+suffix,quote=True)+match.group(3)
    html=re.sub(r'((?:href|src)=["\'])([^"\']+)(["\'])',link,html)
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(html)
