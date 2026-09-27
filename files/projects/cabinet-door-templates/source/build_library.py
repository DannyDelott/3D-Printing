#!/usr/bin/env python3
"""Publish design/revision navigation from the manifests; do not regenerate CAD."""
from html import escape
import json
import os
from pathlib import Path
from project_paths import ROOT, DESIGNS, artifact_path, publish_html

STYLE="""body{max-width:1050px;margin:40px auto;padding:0 24px;background:#faf8f3;color:#243e36;font:16px 'Avenir Next',sans-serif;line-height:1.6}h1,h2{font-family:Georgia,serif;font-weight:normal}a{color:#236b60}li{margin:8px 0}canvas{width:100%;height:300px;touch-action:none;border:1px solid #d9d9ce}button{padding:8px 14px;border:1px solid #9ca99d;background:transparent;color:#243e36;border-radius:4px}code{overflow-wrap:anywhere}.status{padding:15px 20px;background:#e7eee8}small{color:#53615b}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:12px;border-bottom:1px solid #d9d9ce}svg{width:100%;max-height:200px}"""

def base(design,revision):return ROOT/'designs'/design['id']/revision['path']
def relative(target,page):return Path(os.path.relpath(target,page.parent)).as_posix()
def groups(revision):
    result={}
    for name,location in revision['artifacts'].items():
        if location=='datasheet.html':continue
        result.setdefault(location.split('/')[0],[]).append((name,location))
    return result


def library_markup():
    html=['<section id="design-library" style="border-top:1px solid #d9d9ce;margin-top:32px;padding-top:24px"><h2>Design library</h2><p>Each revision keeps its models, fit tests, sources, and validation together. Physical approval is separate from digital checks.</p>']
    for design in DESIGNS:
        html.append(f'<details><summary>{escape(design["title"])} · {len(design["revisions"])} revisions</summary>')
        for part in ['rails','stiles']:
            revisions=[r for r in design['revisions'] if r['part']==part]
            if not revisions:continue
            html.append(f'<h3>{part.title()}</h3><ul>')
            for rev in revisions:
                url=(base(design,rev)/rev['datasheet']).relative_to(ROOT).as_posix()
                html.append(f'<li><a href="{url}">{escape(rev["title"])}</a><span class="small">{escape(rev["status"])}</span></li>')
            html.append('</ul>')
        html.append('</details>')
    return ''.join(html+['</section>'])


def generic_sheet(design,rev):
    page=base(design,rev)/'datasheet.html'
    title=f'{design["title"]} · {rev["title"]}'
    content=[f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)}</title><style>{STYLE}</style><p><a href="{relative(ROOT/"index.html",page)}">← Cabinet door templates</a></p><h1>{escape(title)}</h1><p class="status">{escape(rev["status"])}</p>']
    # Every preview uses the exact downloadable file displayed alongside it.
    candidates=[(n,p) for n,p in rev['artifacts'].items() if p.startswith('models/') and n.endswith('.3mf') and '-sliced' not in n]
    if candidates:
        import numpy as np
        import trimesh
        name,location=candidates[0]
        mesh=trimesh.load(artifact_path(name),force='mesh',process=True)
        triangles=mesh.triangles-mesh.bounds.mean(axis=0)
        normals=np.repeat(mesh.face_normals[:,None,:],3,axis=1)
        bounds=mesh.extents.copy()
        if bounds[1]>bounds[0]:
            rotation=np.array([[0,1,0],[-1,0,0],[0,0,1]])
            triangles=triangles@rotation.T;normals=normals@rotation.T;bounds=bounds[[1,0,2]]
        data={'file':name,'vertices':np.concatenate([triangles,normals],axis=2).reshape(-1).round(6).tolist(),'view_bounds_mm':bounds.tolist()}
        dims=' × '.join(f'{n:.3f}' for n in mesh.extents)
        content.append(f'<p><a href="{location}" download>Download displayed 3MF</a> · <small>{escape(name)}</small></p><p>File bounding dimensions: {dims} mm.</p><canvas id="print-canvas" tabindex="0" aria-label="Interactive model preview"></canvas><p id="print-error" hidden></p><p><button id="view-reset">Reset 3D</button> <button id="view-top">Top view</button> <button id="zoom-in">+</button> <button id="zoom-out">−</button></p>')
        # Same WebGL viewer used by the comparison and existing bespoke sheets.
        source=(ROOT/'source/comparison.html.in').read_text()
        viewer=source[source.index('function startPreview()'):source.index('</script>')]
        content.append('<script>let activePrint='+json.dumps(data,separators=(',',':'))+',previewRenderer=null;'+viewer+'</script>')
    for group,files in groups(rev).items():
        content.append(f'<h2>{escape(group.replace("-"," ").title())}</h2><ul>')
        content.extend(f'<li><a href="{escape(path)}">{escape(name)}</a></li>' for name,path in files)
        content.append('</ul>')
    content.append('<p>Digital validation does not establish physical fit or routing strength. Refer to the revision notes and fit-test results.</p></html>')
    # Links above are already relative to this revision.
    page.write_text(''.join(content))


def build():
    for design in DESIGNS:
        directory=ROOT/'designs'/design['id']
        lines=[f'# {design["title"]}', '', '[Interactive comparison](../../index.html) · [Design manifest](design.json)', '']
        if design['id']=='elliptical':
            lines += ['Rails and stiles share the elliptical door profile. Current templates use 12.70 mm thickness. Rail V10 retains the approved broad V9 dovetail. Stile V13 applies the user-approved V12 .05 coupon fit to the full template: 0.05 mm total width clearance, the same tail, 36.85 mm nominal socket and 10.15 mm side arms (10.01 mm at the rounded lip). V10 at 0.20 mm and V11 at 0.15/0.10 mm were loose. The V12 .05 coupon passed; the full V13 print was subsequently reported too tight with bowed socket arms. Hold further full-stile prints pending correction. The zero-clearance alternative was not selected. One assembled rail and one assembled stile template can each rotate 180 degrees in plane for the opposite frame member. V7 cracked and bowed during the fit test. V8 at 0.40 mm was too loose. The V9 coupon at 0.20 mm total clearance passed the user’s physical fit test. Stile V9 had approximately 1.81 mm beside its socket; the user reported those arms flexing. Full template strength remains untested.', '']
        for part in ['rails','stiles']:
            revisions=[r for r in design['revisions'] if r['part']==part]
            if not revisions:continue
            lines += [f'## {part.title()}','', '| Revision | Status |','| --- | --- |']
            for rev in revisions:
                dest=base(design,rev);dest.mkdir(parents=True,exist_ok=True)
                lines.append(f'| [{rev["title"]}]({rev["path"]}/README.md) | {rev["status"]} |')
                notes=[f'# {design["title"]} · {rev["title"]}', '',rev['status']+'.','', '[Interactive datasheet](datasheet.html) · [Design manifest](../../../design.json) · [All designs](../../../../../index.html)', '']
                if rev.get('template_thickness_mm'):
                    notes += [f'Nominal CAD template thickness: **{rev["template_thickness_mm"]} mm**. Slicer variants may retain different historical settings; see the datasheet and validation.', '']
                for group,files in groups(rev).items():
                    notes += [f'## {group.replace("-"," ").title()}','']
                    notes += [f'- [{name}]({path})' for name,path in files]
                    notes.append('')
                notes += ['Shared generators remain in the project’s [source directory](../../../../../source/README.md). Earlier decisions are preserved in [project history](../../../../../archive/project-history.md).', '']
                (dest/'README.md').write_text('\n'.join(notes))
                if rev.get('generated_datasheet'):generic_sheet(design,rev)
            lines.append('')
        (directory/'README.md').write_text('\n'.join(lines))
    print(f'Published navigation for {len(DESIGNS)} designs and {sum(len(d["revisions"]) for d in DESIGNS)} revisions')

if __name__=='__main__':build()
