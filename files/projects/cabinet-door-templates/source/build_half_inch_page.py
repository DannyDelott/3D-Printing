#!/usr/bin/env python3
"""Index current half-inch models; the comparison page previews these same files."""
from project_paths import artifact_path, artifact_url, publish_html
from pathlib import Path
import json
from zipfile import ZipFile
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
report=json.loads((artifact_path('validation-half-inch-templates.json')).read_text())
labels=['Elliptical honeycomb rail','Left stile','Right stile','Solid elliptical rail','Continuous sweep rail','Original circles rail']
rows=[]
for (name,item),label in zip(report['models'].items(),labels):
 dims=' × '.join(f'{v:.2f}' for v in item['size_mm'])
 links=' · '.join(f'<a href="models/{name}.{ext}" download>{ext.upper()}</a>' for ext in ['3mf','stl','step'])
 rows.append(f'<tr><td>{label}</td><td>{dims} mm</td><td>{links}</td></tr>')
with ZipFile(artifact_path('stile-template-left-dovetail-v13-sliced.3mf')) as z:
 info=ET.fromstring(z.read('Metadata/slice_info.config'))
 vals={x.get('key'):x.get('value') for x in info.findall('plate/metadata')}
 assert vals['outside']=='false' and vals['support_used']=='false'
 seconds=int(vals['prediction']);grams=float(vals['weight'])
report['split_stile_slice']={'seconds':seconds,'grams':grams,'outside':False,'supports':False}
(artifact_path('validation-half-inch-templates.json')).write_text(json.dumps(report,indent=2)+'\n')
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Cabinet templates · ½ inch</title><style>body{max-width:1020px;margin:40px auto;padding:0 24px;background:#faf8f3;color:#243e36;font:16px system-ui;line-height:1.6}h1{font-size:32px}a{color:#305b4d}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:12px 8px;border-bottom:1px solid #ddd4c6}.status{padding:20px;border:1px solid #b69d70;border-radius:10px;background:#f1e9d8}.button{display:inline-block;padding:10px 16px;background:#243e36;color:white;border-radius:7px;text-decoration:none;margin:4px 0}</style>
<h1>Cabinet templates · ½″ stock</h1><p>Current templates and the rounded rail fit coupon use 12.70 mm stock. Cabinet profiles, openings, and in-plane dimensions are unchanged.</p>
<div class="status"><strong>Approved V9 dovetail · rail</strong><p>0.30 mm external radii · 0.20 mm internal radii · 0.20 mm total width clearance · 2° taper. The coupon is cut directly from the full model at the same 12.70 mm thickness.</p><a class="button" href="rail-native-dovetail-v9-fit-test-sliced.3mf" download>Download rounded rail fit test</a><p><a href="rail-v10.html">Current rail: 13 hexagons and approved V9 joint</a> · <a href="rail-template-native-dovetail-v10-sliced.3mf" download>Download full rail · approved joint</a></p></div>
<p><a href="curve-comparison.html">Interactive rail and stile previews</a></p>
<h2>Complete template geometry</h2><p>These are the complete, unsplit outlines. Their long dimension exceeds a P1S plate; use the split projects below or make a cut in Bambu Studio.</p><table><tr><th>Template</th><th>Dimensions</th><th>Downloads</th></tr>ROWS</table>
<h2>Split stile V13 · approved 0.05 mm joint</h2><p>Your V12 .05 coupon fit is now applied to the full stile. Total width clearance is 0.05 mm (0.025 mm per side), with the same tail, 0.10 mm depth clearance, 2° taper and rounded edges. Socket arms are 10.15 mm nominal and about 10.01 mm at the rounded lip. Rotate the assembled stile 180° in its plane for the opposite side.</p><a class="button" href="stile-template-left-dovetail-v13-sliced.3mf" download>Download split stile · STILETIME · STILEGRAMS g</a><p><a href="stile-dovetail-v13.html">Interactive stile preview and dimensions</a> · <a href="stile-template-left-dovetail-v13-bambu.3mf" download>Editable Bambu project</a></p>
<p><small>Use the current half-inch files together. Earlier V4–V8 rail files remain available as historical revisions and are not the current print recommendation.</small></p></html>'''
html=html.replace('ROWS',''.join(rows)).replace('STILETIME',f'{seconds//3600}h {(seconds%3600)//60}m').replace('STILEGRAMS',f'{grams:.2f}')
publish_html(artifact_path('half-inch-templates.html'), html)
print('Generated half-inch template index')
