#!/usr/bin/env python3
"""Publish and slice the rail/stile set using the approved V9 mating geometry."""
import json,subprocess,tempfile
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import cadquery as cq
import numpy as np
import trimesh
from project_paths import ROOT,artifact_path,publish_html
from slice_rounded_dovetail import retain_precision
from check_bambu_import import check_import


def main():
    # Package the unchanged rail halves in assembly coordinates for CAD downloads.
    rail=trimesh.Scene();shapes=[]
    for part in ['right-tongue','left-socket']:
        rail.add_geometry(trimesh.load(artifact_path(f'rail-native-v9-{part}.stl')),geom_name=part,node_name=part)
        shapes.append(cq.importers.importStep(str(artifact_path(f'rail-native-v9-{part}.step'))).val())
    artifact_path('rail-template-native-dovetail-v9.3mf').write_bytes(rail.export(file_type='3mf'))
    rail.to_geometry().export(artifact_path('rail-template-native-dovetail-v9.stl'))
    cq.exporters.export(cq.Compound.makeCompound(shapes),str(artifact_path('rail-template-native-dovetail-v9.step')))
    name='stile-template-left-dovetail-v9';report=json.loads(artifact_path('validation-stile-dovetail-v9.json').read_text())
    with tempfile.TemporaryDirectory(prefix='stile-v9-slice-') as tmp:
        with artifact_path('validation-stile-v9-slice.txt').open('w') as log:
            subprocess.run(['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio','--slice','0','--arrange','0','--orient','0','--export-3mf',f'{name}-sliced.3mf','--outputdir',tmp,str(artifact_path(f'{name}-bambu.3mf'))],cwd=tmp,stdout=log,stderr=subprocess.STDOUT,check=True)
        output=Path(tmp)/f'{name}-sliced.3mf'
        report['slicer_mesh_precision']=retain_precision(artifact_path(f'{name}-bambu.3mf'),output)
        artifact_path(f'{name}-sliced.3mf').write_bytes(output.read_bytes())
    with ZipFile(artifact_path(f'{name}-sliced.3mf')) as z:
        info=ET.fromstring(z.read('Metadata/slice_info.config'))
        vals={e.get('key'):e.get('value') for e in info.findall('plate/metadata')}
        assert vals['outside']=='false' and vals['support_used']=='false'
        assert len(info.findall('plate/object'))==2
        report['slice']={'seconds':int(vals['prediction']),'grams':float(vals['weight']),'outside':False,'supports':False}
    report['assembly_import']=check_import(artifact_path(f'{name}.3mf'))
    artifact_path('validation-stile-dovetail-v9.json').write_text(json.dumps(report,indent=2)+'\n')
    geometry=trimesh.load(artifact_path(f'{name}.3mf')).to_geometry()
    vertices=np.concatenate([geometry.triangles-geometry.bounds.mean(axis=0),np.repeat(geometry.face_normals[:,None,:],3,axis=1)],axis=2)
    data={'file':name,'vertices':vertices.reshape(-1).round(6).tolist(),'view_bounds_mm':geometry.extents.tolist()}
    source=(ROOT/'source/comparison.html.in').read_text();viewer=source[source.index('function startPreview()'):source.index('</script>')]
    paths=[]
    for g in trimesh.load(artifact_path(f'{name}.3mf')).geometry.values():
        for loop in g.section([0,0,1],[0,0,6.35]).discrete:
            paths.append('M'+' L'.join(f'{x:.4f},{-y:.4f}' for x,y in loop[:,:2])+' Z')
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Stile · approved V9 dovetail</title><style>body{max-width:1020px;margin:40px auto;padding:0 24px;background:#faf8f3;color:#243e36;font:16px system-ui;line-height:1.55}a{color:#305b4d}.button{display:inline-block;background:#243e36;color:white;padding:12px 18px;border-radius:8px;text-decoration:none}canvas{width:100%;height:320px;touch-action:none;border:1px solid #ddd4c6;border-radius:10px}button{padding:8px 14px}table{width:100%;border-collapse:collapse}td{padding:10px;border-bottom:1px solid #ddd4c6}td:last-child{text-align:right}svg{width:100%;height:auto}.status{padding:18px;background:#e7eee8;border-radius:8px}</style>
<p><a href="curve-comparison.html">← Cabinet door templates</a></p><h1>Stile · V9 dovetail</h1><p class="status">V9 coupon fit approved. The stile uses the identical rounded rail joint at 0.20 mm total width clearance. Full stile strength is untested.</p>
<p><a class="button" href="stile-template-left-dovetail-v9-sliced.3mf" download>Download arranged stile 3MF</a></p><p>PRINTINFO · P1S · 0.2 mm layers · 5 walls · 15% infill. Two pieces lie flat, clear of the front purge line.</p>
<canvas id="print-canvas" aria-label="Interactive assembled stile template" tabindex="0"></canvas><p id="print-error" hidden></p><p><button id="view-reset">Reset 3D</button> <button id="view-top">Top view</button> <button id="zoom-in">+</button> <button id="zoom-out">−</button> · Drag to orbit · scroll to zoom</p>
<svg viewBox="-8 -67 505 105" role="img" aria-label="486.751 mm long, 57.15 mm wide stile; dovetail centered at 243.375 mm"><path d="PATHS" fill="#dfc79f" fill-rule="evenodd" stroke="#887559" stroke-width=".35"/><path d="M0 5 V13 H486.751 V5" fill="none" stroke="#53615b" stroke-width=".5"/><g font-size="6" font-family="system-ui" fill="#243e36"><text x="183" y="24">486.751 × 57.150 × 12.700 mm</text><text x="177" y="34">Joint center: 243.375 mm</text></g></svg>
<table><tr><td>Total width clearance / per side</td><td>0.20 / 0.10 mm</td></tr><tr><td>Depth clearance / taper</td><td>0.10 mm / 2°</td></tr><tr><td>External / internal radii</td><td>R0.30 / R0.20 mm</td></tr><tr><td>Nominal material beside widest socket</td><td>1.81 mm</td></tr><tr><td>Proof of transferred joint</td><td>Zero CAD difference from rail V9</td></tr></table>
<p>The socket has only about 1.81 mm of material beside its widest point because the stile is narrower than the fit coupon. The successful coupon confirms joint fit; it does not verify the full stile’s resistance to bending or routing loads.</p>
<p>Assemble with both printed top faces facing the same way. Rotate the assembled template 180° in its plane to make the opposite stile. One stile template and one rail template produce all four frame members.</p>
<p><a href="stile-template-left-dovetail-v9-bambu.3mf" download>Editable Bambu project</a> · <a href="stile-template-left-dovetail-v9.step" download>Assembled STEP</a> · <a href="stile-template-left-dovetail-v9.stl" download>Assembled STL</a> · <a href="validation-stile-dovetail-v9.json">Validation</a></p>
<script>let activePrint=DATA,previewRenderer=null;VIEWER</script></html>'''
    estimate=report['slice'];time=f"{estimate['seconds']//3600}h {(estimate['seconds']%3600)//60}m · {estimate['grams']:.1f} g"
    html=html.replace('PRINTINFO',time).replace('PATHS',' '.join(paths)).replace('DATA',json.dumps(data,separators=(',',':'))).replace('VIEWER',viewer)
    publish_html(artifact_path('stile-dovetail-v9.html'),html)
    print('Published approved V9 rail/stile set:',report['slice'])

if __name__=='__main__':main()
