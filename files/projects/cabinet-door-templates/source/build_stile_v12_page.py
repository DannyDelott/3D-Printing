#!/usr/bin/env python3
"""Publish low-cost V12 sockets alongside the main component previews."""
import hashlib,json
import numpy as np
import trimesh
from project_paths import ROOT,artifact_path,artifact_url,publish_html
from build_library import STYLE
STEM='stile-dovetail-v12-sockets'

def coupon_payload():
    report=json.loads(artifact_path('validation-stile-v12.json').read_text())
    path=artifact_path(STEM+'-bambu.3mf');g=trimesh.load(path).to_geometry()
    assert g.is_watertight and len(g.split())==2 and abs(g.extents[2]-12.7)<1e-5
    v=np.concatenate([g.triangles-g.bounds.mean(axis=0),np.repeat(g.face_normals[:,None,:],3,axis=1)],axis=2)
    outlines=[((loop[:,:2]-g.bounds[0,:2])/25.4).round(6).tolist() for loop in g.section([0,0,1],[0,0,6.35]).discrete]
    assert len(outlines)==2
    estimate=report['sockets_slice']
    return {'file':STEM,'vertices':v.reshape(-1).round(6).tolist(),'view_bounds_mm':g.extents.tolist(),'bounds_mm':g.extents.tolist(),'outlines_inches':outlines,'holes_inches':[],'horizontal':False,'kind':'coupon','revision':'V12','title':'Stile fit sockets','description':'Two labeled sockets · 0.05 and 0.00 mm total clearance','status':'0.05 mm coupon passed · full V13 fit failed','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'downloads':{'3mf':artifact_url(STEM+'-sliced.3mf'),'stl':artifact_url(STEM+'.stl'),'step':artifact_url(STEM+'.step')},'fields':[['Total clearances','0.05 mm / 0.00 mm'],['Per side','0.025 mm / 0.000 mm'],['Reuse tail','Intact V10 / V11 stile coupon tail'],['Thickness','12.70 mm · ½″'],['Socket arms','About 10 mm'],['Tail length / socket depth','12.60 / 12.70 mm'],['Taper','2°'],['Print estimate',f"{round(estimate['seconds']/60)} min · {estimate['grams']:.1f} g"]],'note':'The user confirmed that the .05 socket worked great. Full V13 was subsequently reported too tight with bowed socket arms; hold further full-stile prints pending correction. The .00 socket remains an unselected historical alternative.'}

def build():
    data=coupon_payload();source=(ROOT/'source/comparison.html.in').read_text();viewer=source[source.index('function startPreview()'):source.index('</script>')]
    rows=''.join(f'<tr><td>{k}</td><td>{v}</td></tr>' for k,v in data['fields'])
    g=trimesh.load(artifact_path(STEM+'-bambu.3mf')).to_geometry();paths=[]
    for loop in g.section([0,0,1],[0,0,6.35]).discrete:paths.append('M'+' L'.join(f'{x:.4f},{256-y:.4f}' for x,y in loop[:,:2])+'Z')
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Stile V12 · retention fit test</title><style>STYLE .button{display:inline-block;padding:12px 18px;background:#243e36;color:white;border-radius:8px;text-decoration:none}canvas{height:350px}svg{max-height:320px}</style>
<p><a href="curve-comparison.html#stile-coupon">← Main component preview</a></p><h1>Stile V12 · retention fit test</h1><p>The V11 sockets both slid back out through the thickness. These sockets test 0.05 mm and 0.00 mm total width clearance with the same V10/V11 tail, rounded corners, reinforced arms and 2° taper.</p>
<p class="status">The .05 coupon passed; the full V13 print was subsequently reported too tight with bowed socket arms. <a href="stile-dovetail-v13.html">Full stile V13 now uses this fit.</a> These comparison sockets remain available for reference.</p><p><a class="button" href="stile-dovetail-v12-sockets-sliced.3mf" download>Download two labeled sockets</a></p>
<canvas id="print-canvas" tabindex="0" aria-label="Two labeled stile test sockets"></canvas><p id="print-error" hidden></p><p><button id="view-reset">Reset 3D</button> <button id="view-top">Top view</button> <button id="zoom-in">+</button> <button id="zoom-out">−</button> · Drag to orbit · scroll to zoom</p>
<svg viewBox="95 50 75 155" role="img" aria-label="Upper socket 0.00 mm; lower socket 0.05 mm. Each mates with a 36 by 57.15 by 12.70 mm assembled coupon."><path d="PATHS" fill="#dfc79f" stroke="#887559" stroke-width=".25" fill-rule="evenodd"/><g font-size="3" fill="#243e36"><text x="114" y="55">.00 · zero nominal gap</text><text x="114" y="131">.05 · 0.025 mm per side</text><text x="99" y="201">Assembled test: 36 × 57.15 × 12.70 mm</text></g></svg>
<table>ROWS</table><p>NOTE</p><p>The width allowance is the only fit change. Depth clearance remains 0.10 mm, external/internal radii remain 0.30/0.20 mm, and the saved P1S PLA settings remain 0.20 mm layers, five walls and 15% infill. Labels are engraved away from mating surfaces.</p>
<p>If neither socket retains an easy sliding fit, a positive retaining feature is the next design change; these samples do not mechanically lock.</p>
<p><a href="stile-dovetail-v12-comparison-sliced.3mf" download>Need fresh tails? Complete four-piece comparison plate</a></p><p><a href="stile-dovetail-v12-005-bambu.3mf" download>Only .05 pair</a> · <a href="stile-dovetail-v12-000-bambu.3mf" download>Only .00 pair</a> · <a href="stile-dovetail-v12-sockets.step" download>STEP</a> · <a href="validation-stile-v12.json">Validation</a></p>
<script>let activePrint=DATA,previewRenderer=null;VIEWER</script></html>'''
    for a,b in [('STYLE',STYLE),('PATHS',' '.join(paths)),('ROWS',rows),('NOTE',data['note']),('DATA',json.dumps(data,separators=(',',':'))),('VIEWER',viewer)]:html=html.replace(a,b)
    publish_html(artifact_path('stile-dovetail-v12.html'),html)
    print('Published V12 sockets:',data['fields'][-1])
if __name__=='__main__':build()
