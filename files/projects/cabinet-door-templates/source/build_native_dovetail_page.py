#!/usr/bin/env python3
"""Publish a datasheet from the native joint files and actual Bambu estimates."""
from project_paths import artifact_path, artifact_url, publish_html
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import json
import argparse
import numpy as np
import trimesh
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--revision',type=int,default=5,choices=[5,6,7,8,9])
REV=parser.parse_args().revision
report=json.loads((artifact_path(f'validation-native-dovetail-v{REV}.json')).read_text())
for label,file in [('test',f'rail-native-dovetail-v{REV}-fit-test-sliced.3mf'),('full',f'rail-template-native-dovetail-v{REV}-sliced.3mf')]:
 with ZipFile(artifact_path(file)) as z:
  assert z.testzip() is None
  info=ET.fromstring(z.read('Metadata/slice_info.config'))
  vals={x.get('key'):x.get('value') for x in info.findall('plate/metadata')}
  report[label+'_slice']={'seconds':int(vals['prediction']),'grams':float(vals['weight']),'outside':vals['outside'],'support_used':vals['support_used'],'file':file}
  assert vals['outside']=='false' and vals['support_used']=='false'
  assert len(info.findall('plate/object'))==2
(artifact_path(f'validation-native-dovetail-v{REV}.json')).write_text(json.dumps(report,indent=2)+'\n')
full=trimesh.load(artifact_path(f'rail-template-native-dovetail-v{REV}-bambu.3mf'))
a,b=[g.copy() for g in full.geometry.values()]
a.apply_translation([403.225-a.bounds[1,0],-a.bounds[0,1],-a.bounds[0,2]])
b.apply_translation(-b.bounds[0])
paths=[]
for g,color in [(a,'#648b81'),(b,'#cba778')]:
 ts=g.triangles[g.face_normals[:,2]>.99,:,:2]
 path=' '.join('M'+' L'.join(f'{x:.3f},{-y:.3f}' for x,y in tri)+'Z' for tri in ts)
 paths.append(f'<path d="{path}" fill="{color}"/>')
a.apply_translation([12,0,0])
combined=trimesh.util.concatenate([a,b]);center=combined.bounds.mean(axis=0)
verts=np.concatenate((combined.triangles-center,np.repeat(combined.face_normals[:,None,:],3,axis=1)),axis=2)
data={'print':{'vertices':verts.reshape(-1).round(5).tolist(),'bounds_mm':combined.extents.tolist()}}
source=(ROOT/'source/comparison.html.in').read_text();viewer=source[source.index('function startPreview()'):source.index('</script>')]
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Rail dovetail V5 · fit test first</title>
<style>body{max-width:1020px;margin:40px auto;padding:0 24px;background:#faf8f3;color:#243e36;font:16px system-ui}h1{font-size:32px;margin-bottom:12px}p,li{line-height:1.55}.status{padding:20px;border:1px solid #b69d70;border-radius:10px;background:#f1e9d8}.button,button{display:inline-block;padding:10px 16px;margin:4px 4px 4px 0;border-radius:7px;border:1px solid #648b81;background:transparent;color:#243e36;text-decoration:none;cursor:pointer}.primary{background:#243e36;color:white}canvas{width:100%;height:340px;touch-action:none;border:1px solid #ddd4c6;border-radius:10px}svg{width:100%;height:280px}table{border-collapse:collapse;width:100%;margin:24px 0}td{padding:10px;border-bottom:1px solid #ddd4c6}td:last-child{text-align:right}small{color:#53615b}a{color:#305b4d}</style>
<h1>Rail dovetail V5</h1><p>The original curved rail, cut with Bambu Studio’s native dovetail tool. Width and depth tolerance are now 0.03 mm, with a 2° groove taper.</p>
<div class="status"><strong>Ready for the small fit test. Full-size fit is not yet confirmed.</strong><p>The test is extracted from the same joint as the full model, at the full 19.05 mm thickness. Both use the saved P1S / PLA settings, 0.2 mm layers, 5 walls and 15% infill.</p><a class="button primary" href="models/rail-native-dovetail-v5-fit-test-sliced.3mf" download>Download fit test · TESTTIME · TESTGRAMS g</a></div>
<p>After cooling, keep both printed top faces facing the same way and slide the tongue into the socket through the thickness. It should seat flush, resist rocking, and require deliberate hand pressure to slide apart. If it is loose, jams, or leaves a step, report that result before printing the full model.</p>
<canvas id="print-canvas" tabindex="0" aria-label="Interactive preview of the V5 rail: drag to orbit, scroll to zoom"></canvas><p id="print-error" hidden></p><p><button id="view-reset">Reset</button><button id="view-top">Top</button><button id="zoom-in">+</button><button id="zoom-out">−</button><small>Drag to orbit · scroll to zoom · 12 mm separation for clarity</small></p>
<svg viewBox="-10 -175 435 220" aria-label="Assembled rail schematic"><g>PATHS</g><g fill="#243e36" font-size="8" font-family="system-ui"><text x="139" y="26">403.225 mm overall</text><text x="3" y="-84">76.2 mm</text><text x="343" y="-162">152.4 mm</text><text x="147" y="41">19.05 mm thickness</text></g><path d="M0 7 V16 H403.225 V7" fill="none" stroke="#53615b" stroke-width=".6"/></svg>
<table><tr><td>Native groove depth / width</td><td>12.7 / 38.1 mm</td></tr><tr><td>Width tolerance / depth tolerance</td><td>0.03 / 0.03 mm</td></tr><tr><td>Flap angle / groove taper</td><td>60° / 2°</td></tr><tr><td>Test pair, assembled envelope</td><td>20.7 × 61 × 19.05 mm</td></tr><tr><td>Full plate estimate, current settings</td><td>FULLTIME · FULLGRAMS g</td></tr><tr><td>Digital validation</td><td>Two watertight bodies · successful slices · no supports</td></tr><tr><td>Physical fit</td><td>Awaiting test print</td></tr></table>
<p><strong>V5 is incompatible with the old V4 halves.</strong> The native cut changes the joint shape and places the tongue on the right half. Both V5 halves would need printing after the test passes.</p>
<p><a class="button" href="models/rail-template-native-dovetail-v5-sliced.3mf" download>Full model · after fit test passes</a><a class="button" href="models/native-v5-source/native-cut-project.3mf" download>Native Bambu source</a></p>
<p><small>The test checks the local fit, not the full template’s stiffness or retention under routing loads. Original outline and openings are retained. The exported touching shells were joined with a 0.00001 mm numerical adjustment. <a href="validation-native-dovetail-v5.json">Validation details</a></small></p>
<script>const data=DATA;data.print.view_bounds_mm=data.print.bounds_mm;let activePrint=data.print,previewRenderer=null;VIEWER</script></html>'''
html=html.replace('v5',f'v{REV}').replace('V5',f'V{REV}')
if REV>=6:
 html=html.replace('0.03','0.10').replace('Width and depth tolerance are now 0.10 mm, with a 2° groove taper.','Measured width clearance is 0.10 mm total (0.05 mm per side). Depth clearance is 0.10 mm, with a 2° groove taper.').replace('Width tolerance / depth tolerance','Total width clearance / depth clearance')
 html=html.replace('Both V6 halves would need printing after the test passes.','Both V6 halves would need printing after the test passes. Do not mix V5 and V6 halves.')
if REV>=7:
 html=html.replace('The original curved rail, cut with Bambu Studio’s native dovetail tool.', 'The curved rail with its tested V6 dovetail planes retained and sharp joint edges rounded in CAD.')
 html=html.replace('19.05','12.70')
 html=html.replace('<table>','<table><tr><td>External joint edges / internal corners</td><td>R 0.30 / R 0.20 mm</td></tr><tr><td>Template and coupon thickness</td><td>½″ · 12.70 mm</td></tr>')
 html=html.replace('It should seat flush, resist rocking, and require deliberate hand pressure to slide apart.', 'It should seat flush and resist rocking. The new entry radii should ease assembly; stop if it binds rather than forcing it.')
 html=html.replace(f'models/native-v{REV}-source/native-cut-project.3mf', f'rail-template-native-dovetail-v{REV}-bambu.3mf').replace('Native Bambu source','Editable Bambu project')
 html=html.replace('The exported touching shells were joined with a 0.00001 mm numerical adjustment.', 'Twenty joint edges were filleted in exact CAD: sixteen external edges at R0.30 and four internal corners at R0.20. The original V3 outline and openings were retained. The V6 test was reported almost perfect but broke during insertion; the rounded, thinner V7 needs a new fit check.')
 html=html.replace('<canvas id="print-canvas"',f'<p><a href="rail-native-v{REV}-right-tongue.step" download>Right half STEP</a> · <a href="rail-native-v{REV}-left-socket.step" download>Left half STEP</a></p><canvas id="print-canvas"')
 html=html.replace('<script>const data=', '<p><a href="curve-comparison.html#coupon">View this coupon alongside the main components</a></p><p>Other current ½″ templates: <a href="half-inch-templates.html">rail and stile downloads</a>.</p><script>const data=')
if REV>=8:
 html=html.replace('with its tested V6 dovetail planes retained and sharp joint edges rounded in CAD.', 'with the V7 pin retained and its rounded socket widened for an easier fit.')
 html=html.replace('0.10 mm total (0.05 mm per side)', f"{report['settings']['width_tolerance_mm']:.2f} mm total ({report['settings']['width_tolerance_mm']/2:.2f} mm per side)").replace('0.10 / 0.10 mm', f"{report['settings']['width_tolerance_mm']:.2f} / {report['settings']['depth_tolerance_mm']:.2f} mm")
 html=html.replace('The V6 test was reported almost perfect but broke during insertion; the rounded, thinner V7 needs a new fit check.', 'The V7 coupon was tight and cracked and bowed the pin. V8 retains the pin, radii, taper and depth clearance; only socket width changes. Physical fit awaits a new print test.')
 html=html.replace('The new entry radii should ease assembly;', 'The wider socket provides more clearance;')
 # Stable artifact identifiers are resolved relative to this revision by publish_html.
 html=html.replace('href="models/', 'href="')
if REV==9:
 html=html.replace('its rounded socket widened for an easier fit.', 'its rounded socket adjusted to 0.20 mm total width clearance.')
 html=html.replace('The V7 coupon was tight and cracked and bowed the pin. V8 retains the pin, radii, taper and depth clearance; only socket width changes. Physical fit awaits a new print test.', 'V7 at 0.10 mm was too tight and damaged the pin; V8 at 0.40 mm was too loose. V9 uses 0.20 mm total width clearance (0.10 mm per side), retaining the pin, radii, taper and depth clearance. Physical fit awaits a new print test.')
 html=html.replace('The wider socket provides more clearance;', 'The socket now has 0.10 mm clearance per side;')
if report.get('physical_fit_approval',{}).get('coupon_fit')=='approved':
 html=html.replace('Ready for the small fit test. Full-size fit is not yet confirmed.', 'V9 coupon fit approved for the rail. Stile V10 uses a narrower joint with its own coupon.')
 html=html.replace('Physical fit awaits a new print test.', 'The user reports V9 fits great; its joint fit is approved.')
 html=html.replace('Awaiting test print','Coupon fit approved by user').replace('Full model · after fit test passes','Download full rail · approved joint')
 html=html.replace('Both V9 halves would need printing after the test passes.', 'Print both V9 halves for the full rail.')
 html=html.replace('before printing the full model.', 'when checking an assembled template.')
 html=html.replace('Rail dovetail V9 · fit test first', 'Rail dovetail V9 · coupon fit approved')
 html=html.replace('<h1>Rail dovetail V9</h1>', '<h1>Rail dovetail V9</h1><p><a class="button primary" href="rail-template-native-dovetail-v9-sliced.3mf" download>Download arranged rail 3MF</a> · <a href="stile-dovetail-v10.html">Stile V10 · new coupon test required</a></p>')
def duration(seconds):
 h,m=divmod(round(seconds/60),60)
 return f'{h}h {m}m' if h else f'{m} min'
html=html.replace('PATHS',''.join(paths)).replace('DATA',json.dumps(data,separators=(',',':'))).replace('VIEWER',viewer)
for label,prefix in [('test','TEST'),('full','FULL')]:
 html=html.replace(prefix+'TIME',duration(report[label+'_slice']['seconds'])).replace(prefix+'GRAMS',f"{report[label+'_slice']['grams']:.1f}")
publish_html(artifact_path(f'dovetail-v{REV}.html'), html)
if REV>=6:
 for version in range(4,REV):
  old=artifact_path(f'dovetail-v{version}.html');text=old.read_text()
  if f'V{REV} fit test' not in text:
   text=text.replace('<h1>',f'<div class="status" style="padding:20px;border:2px solid #a04a32"><strong>Superseded. Use the V{REV} fit test with {report['settings']['width_tolerance_mm']:.2f} mm total width clearance.</strong><p><a href="dovetail-v{REV}.html">Open V{REV} fit test and corrected model</a></p></div><h1>',1)
   publish_html(old, text)
print(f'Generated dovetail-v{REV}.html')
