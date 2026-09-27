#!/usr/bin/env python3
"""Current rail datasheet: five short-side hexagons and the approved V9 joint."""
import json
import numpy as np
import trimesh
from project_paths import ROOT,artifact_path,publish_html
r=json.loads(artifact_path('validation-rail-v10.json').read_text())
scene=trimesh.load(artifact_path('rail-template-native-dovetail-v10.3mf'));g=scene.to_geometry()
v=np.concatenate([g.triangles-g.bounds.mean(axis=0),np.repeat(g.face_normals[:,None,:],3,axis=1)],axis=2)
data={'file':'rail-template-native-dovetail-v10','vertices':v.reshape(-1).round(6).tolist(),'view_bounds_mm':g.extents.tolist()}
paths=[]
for mesh in scene.geometry.values():
 for loop in mesh.section([0,0,1],[0,0,6.35]).discrete:paths.append('M'+' L'.join(f'{x:.4f},{-y:.4f}' for x,y in loop[:,:2])+'Z')
source=(ROOT/'source/comparison.html.in').read_text();viewer=source[source.index('function startPreview()'):source.index('</script>')]
e=r['slice'];estimate=f"{e['seconds']//3600}h {(e['seconds']%3600)//60}m · {e['grams']:.1f} g"
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Rail V10 · five short-side hexagons</title><style>body{max-width:1020px;margin:40px auto;padding:0 24px;background:#faf8f3;color:#243e36;font:16px system-ui;line-height:1.55}a{color:#305b4d}.button{display:inline-block;padding:12px 18px;background:#243e36;color:white;border-radius:8px;text-decoration:none}canvas{width:100%;height:340px;touch-action:none;border:1px solid #ddd4c6;border-radius:10px}svg{width:100%;height:auto}button{padding:8px 12px}table{width:100%;border-collapse:collapse}td{padding:10px;border-bottom:1px solid #ddd4c6}td:last-child{text-align:right}</style>
<p><a href="curve-comparison.html">← Cabinet door templates</a></p><h1>Rail V10 · five short-side hexagons</h1><p>One additional matching opening on the short side. The exact approved V9 dovetail and elliptical routing edge are retained.</p><p><a class="button" href="rail-template-native-dovetail-v10-sliced.3mf" download>Download arranged rail 3MF</a></p><p>ESTIMATE · P1S · two pieces · ½″ thick.</p>
<canvas id="print-canvas" tabindex="0" aria-label="Interactive assembled V10 rail"></canvas><p id="print-error" hidden></p><p><button id="view-reset">Reset 3D</button> <button id="view-top">Top view</button> <button id="zoom-in">+</button> <button id="zoom-out">−</button> · Drag to orbit · scroll to zoom</p>
<svg viewBox="-10 -165 430 196" aria-label="Rail schematic with five openings on short side, eight on tall side, 403.225 mm width"><path d="PATHS" fill="#dfc79f" stroke="#887559" stroke-width=".4" fill-rule="evenodd"/><path d="M0 5 V13 H403.225 V5" fill="none" stroke="#53615b" stroke-width=".5"/><text x="127" y="25" font-size="7" fill="#243e36">403.225 mm · 3″ / 6″ rail ends</text></svg>
<table><tr><td>Hexagons</td><td>5 short side + 8 tall side = 13</td></tr><tr><td>Hole size across flats</td><td>25.20 mm</td></tr><tr><td>Minimum webs / perimeter rim</td><td>10.00 / 13.40 mm</td></tr><tr><td>Solid center band</td><td>3½″ · 88.90 mm</td></tr><tr><td>Joint width / depth clearance</td><td>0.20 / 0.10 mm</td></tr><tr><td>Joint fit</td><td>Approved V9 coupon; mating geometry unchanged</td></tr></table>
<p>The five short-side holes are redistributed into a staggered pattern to maintain the web thickness. Tall-side holes, routing profile, and mating surfaces are unchanged. Full-template strength remains untested. Rotate the assembled rail 180° in plane for the upper rail.</p>
<p>Cabinet mounting: hinge strip on the right; approximately 1¼″ diameter round knob centered on the left stile. Curve orientation and template dimensions are unchanged; no knob drill hole is included.</p>
<p><a href="rail-template-native-dovetail-v10-bambu.3mf" download>Editable Bambu project</a> · <a href="rail-template-native-dovetail-v10.step" download>STEP</a> · <a href="rail-template-native-dovetail-v10.stl" download>STL</a> · <a href="stile-dovetail-v10.html">Stile V10 · test coupon first</a> · <a href="validation-rail-v10.json">Validation</a></p>
<script>let activePrint=DATA,previewRenderer=null;VIEWER</script></html>'''
publish_html(artifact_path('rail-v10.html'),html.replace('ESTIMATE',estimate).replace('PATHS',' '.join(paths)).replace('DATA',json.dumps(data,separators=(',',':'))).replace('VIEWER',viewer))
print('Published rail V10 datasheet')
