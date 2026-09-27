#!/usr/bin/env python3
"""Publish the reinforced stile and its exact full-width coupon together."""
import json
import numpy as np
import trimesh
from project_paths import ROOT,artifact_path,publish_html
from build_library import STYLE
FULL='stile-template-left-dovetail-v10';TEST='stile-dovetail-v10-fit-test'
r=json.loads(artifact_path('validation-stile-dovetail-v10.json').read_text())
models={}
for key,stem in [('coupon',TEST),('full',FULL)]:
    g=trimesh.load(artifact_path(stem+'.3mf')).to_geometry()
    v=np.concatenate([g.triangles-g.bounds.mean(axis=0),np.repeat(g.face_normals[:,None,:],3,axis=1)],axis=2)
    models[key]={'file':stem,'vertices':v.reshape(-1).round(6).tolist(),'view_bounds_mm':g.extents.tolist()}
coupon=trimesh.load(artifact_path(TEST+'.3mf')).to_geometry()
paths=[]
for loop in coupon.section([0,0,1],[0,0,6.35]).discrete:
    xy=loop[:,:2]-coupon.bounds[0,:2]
    paths.append('M'+' L'.join(f'{x:.5f},{y:.5f}' for x,y in xy)+'Z')
source=(ROOT/'source/comparison.html.in').read_text();viewer=source[source.index('function startPreview()'):source.index('</script>')]
def estimate(key):
    e=r[key+'_slice'];return f"{round(e['seconds']/60)} min · {e['grams']:.1f} g"
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Stile V10 · reinforced socket arms</title><style>STYLE svg{max-height:400px}.button{display:inline-block;padding:10px 16px;background:#243e36;color:white;border-radius:7px;text-decoration:none}button[aria-pressed=true]{background:#dce5db}.small{font-size:14px}</style>
<p><a href="curve-comparison.html#stile-coupon">← Cabinet door templates</a></p><h1>Stile V10 · reinforced socket arms</h1><p>The narrower dovetail leaves about 10 mm beside the socket while keeping the stile’s routing profile and 0.20 mm total clearance.</p>
<p class="status">V10 fit is too loose: the user reports it falls apart under gravity. <a href="stile-dovetail-v11.html">Print the new V11 comparison coupons at 0.15 and 0.10 mm.</a> This full stile still has 0.20 mm clearance.</p>
<p><button id="show-coupon" aria-pressed="true">Full-width coupon</button> <button id="show-full" aria-pressed="false">Full stile</button></p>
<canvas id="print-canvas" tabindex="0" aria-label="Interactive assembled stile coupon"></canvas><p id="print-error" hidden></p><p><button id="view-reset">Reset 3D</button> <button id="view-top">Top view</button> <button id="zoom-in">+</button> <button id="zoom-out">−</button> · Drag to orbit · scroll to zoom</p>
<p><a id="model-download" class="button" href="stile-dovetail-v10-fit-test-sliced.3mf" download>Download stile coupon 3MF</a> <span id="estimate">TEST_ESTIMATE</span></p><p id="model-description">Assembled view; download contains two separated pieces arranged flat for the P1S. The coupon is cut directly from the full stile, at its actual 57.15 mm width.</p>
<svg viewBox="-22 -8 100 82" role="img" aria-label="36 mm long coupon, 57.15 mm stile width, nominal 37 mm socket and 10.075 mm side arms"><g transform="translate(0 57.15) scale(1 -1)"><path d="PATHS" fill="#dfc79f" stroke="#887559" stroke-width=".2" fill-rule="evenodd"/></g><g fill="none" stroke="#53615b" stroke-width=".25"><path d="M-2 0 H-7 V57.15 H-2 M0 60 V65 H36 V60 M39 0 H43 V10.075 H39 M39 10.075 H48 V47.075 H39"/></g><g fill="#243e36" font-size="3.3"><text transform="translate(-10 43) rotate(-90)">57.15 mm stile width</text><text x="7" y="70">36 mm coupon</text><text x="46" y="6">10.075 mm arm</text><text x="51" y="29">37 mm socket</text><text x="46" y="53">Nominal dimensions</text></g></svg>
<table><tr><td>Side arms</td><td>10.075 mm nominal · 9.93 mm at rounded lip</td></tr><tr><td>Previous V9 side arms</td><td>About 1.81 mm</td></tr><tr><td>Socket width</td><td>37 mm nominal before edge rounding</td></tr><tr><td>Total width / depth clearance</td><td>0.20 mm / 0.10 mm</td></tr><tr><td>Thickness / taper</td><td>12.70 mm / 2°</td></tr><tr><td>External / internal radii</td><td>0.30 mm / 0.20 mm</td></tr><tr><td>Full assembled envelope</td><td>486.751 × 57.15 × 12.70 mm</td></tr><tr><td>Coupon envelope</td><td>36 × 57.15 × 12.70 mm</td></tr></table>
<p>Keep both printed top faces facing the same way and slide the joint together along its thickness. Check that the arms remain straight during assembly and gentle handling. Rotate the assembled full template 180° in its plane to make the opposite stile. V10 stile halves are not interchangeable with V9 or the rail halves.</p>
<p>Print flat at 100%. The saved P1S PLA projects use a 0.20 mm layer height, five walls and 15% infill. Both final 3MF files were sliced and reimported with Bambu; digital checks do not establish physical strength. Rail V10 is unchanged.</p>
<p><a href="stile-template-left-dovetail-v10-sliced.3mf" download>Full stile 3MF · FULL_ESTIMATE</a> · <a href="stile-template-left-dovetail-v10-bambu.3mf" download>Editable Bambu project</a> · <a href="stile-template-left-dovetail-v10.step" download>Full STEP</a> · <a href="stile-dovetail-v10-fit-test.step" download>Coupon STEP</a> · <a href="validation-stile-dovetail-v10.json">Validation report</a></p>
<script>const models=MODELS;let activePrint=models.coupon,previewRenderer=null;VIEWER
const buttons={coupon:document.querySelector('#show-coupon'),full:document.querySelector('#show-full')};
const links=LINKS;
for(const [key,button] of Object.entries(buttons))button.addEventListener('click',()=>{activePrint=models[key];previewRenderer?.setModel();for(const [k,b] of Object.entries(buttons))b.setAttribute('aria-pressed',String(k===key));const a=document.querySelector('#model-download');a.href=links[key];a.textContent=key==='coupon'?'Download stile coupon 3MF':'Download full stile 3MF';document.querySelector('#estimate').textContent=key==='coupon'?'TEST_ESTIMATE':'FULL_ESTIMATE';document.querySelector('#print-canvas').setAttribute('aria-label','Interactive assembled '+(key==='coupon'?'stile coupon':'full stile'));});
</script></html>'''
from project_paths import artifact_url
page=artifact_path('stile-dovetail-v10.html')
links={key:artifact_url(stem+'-sliced.3mf',page) for key,stem in [('coupon',TEST),('full',FULL)]}
for a,b in [('STYLE',STYLE),('PATHS',' '.join(paths)),('MODELS',json.dumps(models,separators=(',',':'))),('LINKS',json.dumps(links)),('VIEWER',viewer),('TEST_ESTIMATE',estimate('test')),('FULL_ESTIMATE',estimate('full'))]:html=html.replace(a,b)
publish_html(page,html)
print('Published stile V10 and full-width coupon datasheet')
