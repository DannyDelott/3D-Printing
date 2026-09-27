#!/usr/bin/env python3
"""One plate comparing two clearances, with matching preview and downloads."""
import hashlib,json
import numpy as np
import trimesh
from project_paths import ROOT,artifact_path,artifact_url,publish_html
from build_library import STYLE
STEM='stile-dovetail-v11-comparison'

def coupon_payload():
    report=json.loads(artifact_path('validation-stile-v11.json').read_text())
    path=artifact_path(STEM+'-bambu.3mf');g=trimesh.load(path).to_geometry()
    assert g.is_watertight and len(g.split())==4
    v=np.concatenate([g.triangles-g.bounds.mean(axis=0),np.repeat(g.face_normals[:,None,:],3,axis=1)],axis=2)
    outlines=[((loop[:,:2]-g.bounds[0,:2])/25.4).round(6).tolist() for loop in g.section([0,0,1],[0,0,6.35]).discrete]
    assert len(outlines)==4
    estimate=report['test_slice']
    return {'file':STEM,'vertices':v.reshape(-1).round(6).tolist(),'view_bounds_mm':g.extents.tolist(),'bounds_mm':g.extents.tolist(),'outlines_inches':outlines,'holes_inches':[],'horizontal':False,'kind':'coupon','revision':'V11','title':'Stile fit coupons','description':'Two labeled sockets · 0.15 and 0.10 mm total clearance','status':'Physical test pending · V10 at 0.20 mm was too loose','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'downloads':{'3mf':artifact_url(STEM+'-sliced.3mf'),'stl':artifact_url(STEM+'.stl'),'step':artifact_url(STEM+'.step')},'fields':[['Total clearances','0.15 mm / 0.10 mm'],['Per side','0.075 mm / 0.050 mm'],['Stile width','57.15 mm · 2¼″'],['Thickness','12.70 mm · ½″'],['Socket arms','About 10 mm'],['Tail length / socket depth','12.60 / 12.70 mm'],['Taper','2°'],['Print estimate',f"{round(estimate['seconds']/60)} min · {estimate['grams']:.1f} g"]],'note':'One plate, four pieces. Sockets are engraved .15 and .10; both tails are identical to the V10 coupon. Try .15 first, then .10 if needed. Keep both printed top faces up and slide together along the thickness. Choose a fit that holds under its own weight without bowing the arms. Full stile and rail files are unchanged; the tighter fit has not yet been applied to the full stile.'}

def build():
    data=coupon_payload();report=json.loads(artifact_path('validation-stile-v11.json').read_text());e=report['test_slice']
    source=(ROOT/'source/comparison.html.in').read_text();viewer=source[source.index('function startPreview()'):source.index('</script>')]
    rows=''.join(f'<tr><td>{k}</td><td>{v}</td></tr>' for k,v in data['fields'])
    g=trimesh.load(artifact_path(STEM+'-bambu.3mf')).to_geometry();paths=[]
    for loop in g.section([0,0,1],[0,0,6.35]).discrete:
        paths.append('M'+' L'.join(f'{x:.4f},{256-y:.4f}' for x,y in loop[:,:2])+'Z')
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Stile V11 · tighter fit coupons</title><style>STYLE .button{display:inline-block;padding:12px 18px;background:#243e36;color:white;border-radius:8px;text-decoration:none}svg{max-height:380px}canvas{height:360px}</style>
<p><a href="curve-comparison.html#stile-coupon">← Cabinet door templates</a></p><h1>Stile V11 · tighter fit coupons</h1><p>Compare 0.15 mm and 0.10 mm total width clearance using the same tail and reinforced socket arms as V10.</p><p class="status">The V10 coupon at 0.20 mm separated under gravity. These two tighter fits are awaiting your print test. Full stile and rail files remain unchanged.</p>
<p><a class="button" href="stile-dovetail-v11-comparison-sliced.3mf" download>Download both coupons · one plate</a> · ESTIMATE</p>
<canvas id="print-canvas" tabindex="0" aria-label="Four coupon pieces arranged on one P1S plate"></canvas><p id="print-error" hidden></p><p><button id="view-reset">Reset 3D</button> <button id="view-top">Top view</button> <button id="zoom-in">+</button> <button id="zoom-out">−</button> · Drag to orbit · scroll to zoom</p>
<svg viewBox="65 45 135 180" role="img" aria-label="Upper pair 0.10 mm, lower pair 0.15 mm. Coupon width 57.15 mm and assembled length 36 mm."><path d="PATHS" fill="#dfc79f" stroke="#887559" stroke-width=".3" fill-rule="evenodd"/><g font-size="4" fill="#243e36"><text x="94" y="55">.10 · 0.050 mm per side</text><text x="94" y="132">.15 · 0.075 mm per side</text><text x="93" y="201">Socket</text><text x="136" y="201">Identical tail</text><text x="83" y="213">Each assembled coupon: 36 × 57.15 × 12.70 mm</text></g></svg>
<table>ROWS</table><p>Try the socket marked <strong>.15</strong> first. If it still falls apart, try <strong>.10</strong>. Both unmarked tails have identical geometry. Hold the top faces facing the same way and slide together along the thickness. A useful fit holds under its own weight and seats with firm hand pressure without bowing the arms.</p>
<p>Only the socket width allowance changed. Tail length, 0.10 mm tip clearance, 2° taper, 0.30 / 0.20 mm corner radii, stock thickness, and print settings are retained. The socket labels are recessed 0.40 mm into the backbone, away from the mating surfaces and arms.</p>
<p>Print flat at 100% using the saved P1S PLA settings: 0.20 mm layers, five walls, 15% infill. The four-piece plate has been sliced and reimported with Bambu. Physical fit and retention still need testing.</p>
<p><a href="stile-dovetail-v11-015-bambu.3mf" download>Only 0.15 mm pair · Bambu project</a> · <a href="stile-dovetail-v11-010-bambu.3mf" download>Only 0.10 mm pair · Bambu project</a></p><p><a href="stile-dovetail-v11-comparison-bambu.3mf" download>Editable combined project</a> · <a href="stile-dovetail-v11-comparison.step" download>STEP</a> · <a href="stile-dovetail-v11-comparison.stl" download>STL</a> · <a href="validation-stile-v11.json">Validation</a></p>
<script>let activePrint=DATA,previewRenderer=null;VIEWER</script></html>'''
    for a,b in [('STYLE',STYLE),('ESTIMATE',f"{round(e['seconds']/60)} min · {e['grams']:.1f} g"),('PATHS',' '.join(paths)),('ROWS',rows),('DATA',json.dumps(data,separators=(',',':'))),('VIEWER',viewer)]:html=html.replace(a,b)
    publish_html(artifact_path('stile-dovetail-v11.html'),html)
    print('Published labeled V11 coupon comparison')
if __name__=='__main__':build()
