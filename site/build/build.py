"""Build the static library from the catalog and existing project artifacts."""
import hashlib
import json
import posixpath
import shutil
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

import filament

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / 'site'
OUT = ROOT / '_site'
FORMATS = {'.3mf', '.stl', '.step', '.brep', '.fcstd'}
PUBLISHED = FORMATS | {'.html', '.png', '.jpg', '.jpeg', '.webp', '.svg', '.json', '.md', '.py', '.txt', '.css', '.js', '.in'}
EXCLUDED = {'archive', '.venv', '__pycache__', 'work', 'node_modules'}
ICONS = {
    'arrow': 'M5 12h14m-6-6 6 6-6 6',
    'left': 'M19 12H5m6-6-6 6 6 6',
    'search': 'M21 21l-5-5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0',
    'download': 'M12 3v12m-5-5 5 5 5-5M4 17v4h16v-4',
    'external': 'M14 3h7v7M21 3 10 14M10 3H3v18h18v-7',
}


def icon(name):
    return f'<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="{ICONS[name]}"/></svg>'


def href(page, target):
    return quote(posixpath.relpath(target, posixpath.dirname(page) or '.'), safe='/')


def artifact(path):
    return path if path.startswith('assets/') else 'files/' + path


def versioned_asset(page, path):
    version = hashlib.sha256((SITE / path).read_bytes()).hexdigest()[:12]
    return href(page, path) + "?v=" + version


def frame(page, title, body, description):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title><meta name="description" content="{escape(description, quote=True)}">
<link rel="stylesheet" href="{versioned_asset(page, 'style.css')}">
<script type="module" src="{versioned_asset(page, 'client.js')}"></script></head><body>
<a class="skip" href="#main">Skip to content</a><div class="shell">
<main id="main">{body}</main>
</div></body></html>'''


def index(projects):
    page = 'index.html'
    filters = ''.join(f'<button type="button" data-category="{escape(c)}" aria-pressed="{str(i == 0).lower()}">{escape(c)}</button>' for i, c in enumerate(['All projects'] + sorted({p['category'] for p in projects})))
    rows = ''
    for p in projects:
        text = escape(' '.join([p['title'], p['description'], p['category'], p['revision']]).lower(), quote=True)
        rows += f'''<a href="{href(page, 'projects/' + p['slug'] + '/index.html')}" class="project-row" data-category="{escape(p['category'])}" data-search="{text}">
<img src="{href(page, p['preview'])}" alt="" loading="lazy" width="90" height="70"><h2>{escape(p['title'])}</h2>
<span class="row-category">{escape(p['category'])}</span>{icon('arrow')}</a>'''
    body = f'''<section class="index-intro"><h1>Projects</h1><div class="directory-meta"><p>{len(projects)} projects</p><a href="https://github.com/DannyDelott/3D-Printing" target="_blank" rel="noreferrer">GitHub {icon('external')}</a></div></section>
<div class="toolbar" id="filters" hidden><div class="filters" aria-label="Project categories">{filters}</div><label class="search">{icon('search')}<input id="search" type="search" aria-label="Search projects" placeholder="Find a project…"></label></div>
<div class="table-head" aria-hidden="true"><span>Model</span><span>Project</span><span class="row-category">Category</span><span></span></div>
<div id="results">{rows}</div><p id="empty" class="empty" hidden>No projects match. Try another name or category. <button id="clear-search" class="secondary">Clear filters</button></p>

'''
    return frame(page, '3D printing projects', body, '3D printing projects, dimensions, print notes, and downloadable files.')


def file_link(page, name, path):
    original = SITE / path if path.startswith('assets/') else ROOT / path
    size = original.stat().st_size
    units = f'{size / 1_000_000:.1f} MB' if size >= 1_000_000 else f'{max(1, round(size / 1000))} KB'
    return f'<a href="{href(page, artifact(path))}" download><span class="format">{escape(original.suffix[1:].upper())}</span><span class="dl-name">{escape(name)}</span><span class="file-size">{units}</span>{icon("download")}</a>'


def project_views(project):
    views = project.get('views', [])
    if not views:
        return [project]
    return [project | view | {'viewPath': '' if index == 0 else view['id'], 'activeView': view['id'], 'assemblyMode': view.get('assemblyMode')} for index, view in enumerate(views)]


def project_path(project):
    suffix = project.get('viewPath', '')
    return f'projects/{project["slug"]}/' + (suffix + '/' if suffix else '') + 'index.html'


def component_navigation(project, page):
    views = project.get('views', [])
    if not views:
        return ''
    groups = dict.fromkeys(view['group'] for view in views)
    result = '<div class="component-picker" aria-label="Components and fit coupons">'
    for group in groups:
        links = ''
        for variant in project_views(project):
            if variant['group'] != group:
                continue
            current = ' aria-current="page"' if variant['activeView'] == project['activeView'] else ''
            assembly_link = ' data-assembly-link' if variant.get('assemblyMode') else ''
            links += f'<a href="{href(page, project_path(variant))}"{current}{assembly_link}>{escape(variant["label"])}</a>'
        result += f'<section><h2>{escape(group)}</h2><nav aria-label="{escape(group)} models">{links}</nav></section>'
    return result + '</div>'


def assembly_selector(project, page):
    mode = project.get('assemblyMode')
    if not mode:
        return ''
    options = []
    for shoe in project['assemblyShoes']:
        view = next(v for v in project_views(project) if v['activeView'] == shoe['id'])
        preview = shoe[mode]
        options.append(f'<option value="{escape(shoe["id"], quote=True)}" data-model="{href(page, artifact(preview["model"]))}" data-poster="{href(page, preview["preview"])}" data-details="{href(page, project_path(view))}">{escape(shoe["label"])}</option>')
    return f'''<div class="assembly-controls" hidden><label for="assembly-shoe">Preview shoe</label>
<select id="assembly-shoe" aria-controls="model-viewer">{''.join(options)}</select>
<a id="shoe-details">Shoe details &amp; downloads {icon('arrow')}</a></div>'''


def project_page(p, published):
    page = project_path(p)
    downloads = ''.join(file_link(page, name, path) for name, path in p['downloads'])
    dimensions = ''.join(f'<tr><th scope="row">{escape(key)}</th><td>{escape(value)}</td></tr>' for key, value in p['dimensions'])
    estimate_rows, estimate_notes = filament.render(p, json.loads((SITE / 'filament-estimates.json').read_text()), ROOT)
    attribution = f'<div class="notes"><p>{escape(p["license"])}</p></div>' if p.get('license') else ''
    related = ''.join(f'<li><a href="{escape(url, quote=True)}" target="_blank" rel="noreferrer">{escape(label)} {icon("external")}</a></li>' for label, url in p.get('related', []))
    selected_paths = {path for view in project_views(p) for _, path in view['downloads']}
    extras = [path for path in published if path.startswith(p['root'] + '/') and Path(path).suffix.lower() in FORMATS and path not in selected_paths]
    extra_links = ''.join(file_link(page, str(Path(path).relative_to(p['root'])), path) for path in extras)
    datasheets = [path for path in published if path.startswith(p['root'] + '/') and Path(path).name == 'datasheet.html']
    sheet_links = ''.join(f'<li><a href="{href(page, artifact(path))}">{escape(str(Path(path).parent.relative_to(p["root"])))}</a></li>' for path in datasheets)
    archive = ''
    if extras or datasheets:
        archive = f'''<section class="file-archive" id="files"><h2>Project files & revisions</h2>
{f'<details><summary>Original datasheets <span>{len(datasheets)}</span></summary><ul class="sheet-list">{sheet_links}</ul></details>' if datasheets else ''}
{f'<details><summary>Additional model files <span>{len(extras)}</span></summary><div class="download-list">{extra_links}</div></details>' if extras else ''}</section>'''
    legacy = f'<a href="{href(page, artifact(p["datasheet"]))}">Original design library {icon("external")}</a>' if p.get('datasheet') else ''
    body = f'''<a class="back" href="{href(page, 'index.html')}">{icon('left')} All projects</a>
<div class="detail-heading"><h1>{escape(p['title'])}</h1></div>
{component_navigation(p, page)}<div class="detail-layout"><div>{assembly_selector(p, page)}<div class="viewer" data-viewer="{versioned_asset(page, 'viewer.js')}" data-model="{href(page, artifact(p['previewModel']))}">
<img id="model-poster" src="{href(page, p['preview'])}" alt="{escape(p['title'])} model preview">
<canvas id="model-viewer" hidden tabindex="0" aria-label="Interactive model. Drag to orbit; arrow keys to pan; plus and minus to zoom."></canvas></div>
<div class="viewer-caption"><span id="viewer-status" role="status"></span><div class="viewer-controls"><button id="retry-model" hidden>Retry 3D preview</button><button id="top-view" hidden>Top</button><button id="zoom-in" hidden aria-label="Zoom in">+</button><button id="zoom-out" hidden aria-label="Zoom out">−</button><button id="reset-view" hidden>Reset view</button></div></div>
<section class="notes" id="description"><h2>About this print</h2><p>{escape(p['description'])}</p>{f'<ul>{related}</ul>' if related else ''}</section>
<div class="detail-footer">{legacy}<a href="{href(page, artifact(p['readme']))}">Original project notes {icon('external')}</a></div>
</div><aside class="detail-info"><section id="dimensions"><h2>Specifications</h2><table class="specs"><tbody>{dimensions}{estimate_rows}</tbody></table>{estimate_notes}</section>
<section id="downloads"><h2>Downloads</h2><div class="download-list">{downloads}</div>
</section>
{attribution}</aside></div>
{archive}'''
    title = p['title'] + (f' · {p["group"]} · {p["label"]}' if p.get('activeView') else '')
    return frame(page, title, body, p['description'])


def inventory(projects):
    files = {'NOTICE.md'}
    for root in sorted({p['root'] for p in projects}):
        for path in (ROOT / root).rglob('*'):
            if not path.is_file() or any(part in EXCLUDED for part in path.relative_to(ROOT).parts):
                continue
            if path.suffix.lower() not in PUBLISHED or '.gcode.' in path.name:
                continue
            # The two older standalone projects also hold scratch builds outside output/.
            relative = path.relative_to(ROOT / root)
            if root.startswith('closet-') and len(relative.parts) > 1 and relative.parts[0] not in {'output', 'source'}:
                continue
            files.add(path.relative_to(ROOT).as_posix())
    return sorted(files)


def validate_catalog(projects):
    seen = set()
    for p in projects:
        slug = p['slug']
        if slug in seen or not slug or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in slug):
            raise ValueError(f'Invalid or duplicate project slug: {slug}')
        seen.add(slug)
        view_ids = [view['id'] for view in p.get('views', [])]
        if len(view_ids) != len(set(view_ids)) or any(not name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in name) for name in view_ids):
            raise ValueError(f'{slug}: invalid or duplicate model view id')
        for item in project_views(p):
            paths = [p['preview'], item['root'], item['readme'], item['preview'], item['previewModel'], *item['source'], *(path for _, path in item['downloads'])]
            if item.get('assemblyMode'):
                shoes = p.get('assemblyShoes', [])
                ids = [shoe['id'] for shoe in shoes]
                if not ids or len(ids) != len(set(ids)) or not set(ids).issubset(view_ids):
                    raise ValueError(f'{slug}: assembly shoes must reference distinct component views')
                for shoe in shoes:
                    preview = shoe[item['assemblyMode']]
                    paths.extend([shoe['source'], preview['model'], preview['preview']])
            if item.get('datasheet'):
                paths.append(item['datasheet'])
            for path in paths:
                base = SITE if path.startswith('assets/') else ROOT
                resolved = (base / path).resolve()
                if not resolved.is_relative_to(base.resolve()) or not resolved.exists():
                    raise ValueError(f'{slug}: missing or unsafe path {path}')



class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ('href', 'src', 'data-model', 'data-poster', 'data-details'):
            if key in attrs:
                self.paths.append(attrs[key])


def check_links():
    errors = []
    for page in OUT.rglob('*.html'):
        parser = Links()
        parser.feed(page.read_text())
        for value in parser.paths:
            url = urlsplit(value)
            if url.scheme or url.netloc or not url.path:
                continue
            target = (page.parent / unquote(url.path)).resolve()
            if not target.is_relative_to(OUT.resolve()) or not target.exists():
                errors.append(f'{page.relative_to(OUT)} -> {value}')
    if errors:
        raise ValueError('Broken site links:\n' + '\n'.join(errors))


def build():
    projects = json.loads((SITE / 'catalog.json').read_text())
    validate_catalog(projects)
    published = inventory(projects)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(SITE / 'assets', OUT / 'assets')
    for filename in ('style.css', 'client.js', 'viewer.js', 'favicon.svg'):
        shutil.copy2(SITE / filename, OUT / filename)
    for path in published:
        target = OUT / 'files' / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / path, target)
    (OUT / 'index.html').write_text(index(projects))
    for p in projects:
        for view in project_views(p):
            target = OUT / project_path(view)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(project_page(view, published))
    (OUT / '.nojekyll').touch()
    (OUT / 'publication.json').write_text(json.dumps({'projects': len(projects), 'files': published}, indent=2) + '\n')
    check_links()
    print(f'Built {len(projects)} projects, {sum(len(project_views(p)) for p in projects)} model pages, and {len(published)} project artifacts. All local HTML links resolve.')


if __name__ == '__main__':
    build()
