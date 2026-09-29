"""Render the printable coupon datasheet from its geometry and slicer reports."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def write():
 r=json.loads((ROOT/'validation-storage-detent-r1.json').read_text())
 slice_report=ROOT/'print-checks/storage-detent-r1-coupon/result.json'
 if not slice_report.exists():slice_report=ROOT/'work/storage-detent-r1-coupon/result.json'
 result=json.loads(slice_report.read_text())['sliced_plates'][0]
 grams=sum(x['total_used_g'] for x in result['filaments']);minutes=round(result['total_predication']/60)
 dest=ROOT/'storage-detent';dest.mkdir(exist_ok=True)
 svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 970 280" role="img" aria-label="64 by 32 mm coupon, 1.6 mm leaf and R3.5 rounded detent">
 <style>text{{font:14px system-ui;fill:#304431}}.dim{{fill:none;stroke:#5f775e}}.small{{font-size:12px}}</style>
 <text x="55" y="25">Back face · this side on the print bed</text>
 <rect x="55" y="50" width="256" height="128" fill="#a2b99a" stroke="#4e6c4a"/>
 <rect x="71" y="84" width="236" height="60" fill="white" stroke="#4e6c4a"/>
 <rect x="63" y="90" width="160" height="48" rx="3" fill="#a2b99a" stroke="#4e6c4a"/>
 <circle cx="207" cy="114" r="14" class="dim" stroke-dasharray="3 3"/>
 <path d="M55 202H311 M55 196v12 M311 196v12 M30 50V178 M24 50h12 M24 178h12" class="dim"/>
 <text x="153" y="222">64 mm / 2.52 in</text><text transform="translate(20 161) rotate(-90)">32 mm / 1.26 in</text>
 <path d="M71 155H207 M71 150v10 M207 150v10" class="dim"/><text x="108" y="172" class="small">34 mm root to ball</text>
 <text x="425" y="25">Side section · detent seated in the shoe</text>
 <path d="M425 55H465V96H729V80H465V55" fill="#a2b99a" stroke="#4e6c4a"/>
 <circle cx="701" cy="125" r="35" fill="#a2b99a" stroke="#4e6c4a"/>
 <path d="M600 134H661L691 164H711L741 134H865V194H600Z" fill="#ddcda8" stroke="#8e7e5a"/>
 <path d="M756 80h20 M756 96h20 M766 80V96" class="dim"/><text x="788" y="92">{r['spring']['leaf_thickness_mm']:.1f} mm leaf</text>
 <path d="M697 160V164" class="dim"/><text x="617" y="222">Rounded R{r['spring']['ball_radius_mm']:.1f} mm · 90° pocket</text>
 <text x="425" y="253" class="small">{r['spring']['rail_travel_mm']:.1f} mm nominal lift over the rail · spring force requires a physical test</text>
 </svg>'''
 (dest/'section.svg').write_text(svg)
 html=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Shoe storage detent · R1 coupon</title>
 <style>*{{box-sizing:border-box}}body{{font:15px/1.5 system-ui;color:#2b3c2d;margin:30px auto;padding:0 24px;max-width:1180px}}h1{{font-size:30px;letter-spacing:-.7px;margin:0 0 6px}}h2{{font-size:18px;margin-top:24px}}p{{margin-top:8px}}.intro{{color:#526650}}.layout{{display:grid;grid-template-columns:1.2fr 1fr;gap:30px}}canvas{{width:100%;height:390px;background:#eff3e9;border:1px solid #dce3d6;border-radius:6px}}button,a.download{{font:inherit;display:inline-block;padding:10px 14px;border:1px solid #becdb8;border-radius:5px;background:white;color:inherit;text-decoration:none;cursor:pointer}}a.download{{background:#365b39;color:white;border-color:#365b39}}table{{width:100%;border-collapse:collapse}}td,th{{padding:8px 0;border-bottom:1px solid #dce3d6;text-align:left;vertical-align:top}}th{{font-weight:500;width:47%}}.small{{font-size:13px;color:#5a6b55}}img{{width:100%}}li{{margin-bottom:8px}}@media(max-width:760px){{.layout{{display:block}}body{{padding:0 16px}}canvas{{height:330px}}}}</style>
 <h1>Shoe storage detent coupon</h1><p class="intro">R1 · One printed part. Test the snap-in feel using a shoe you already have.</p>
 <div class="layout"><section><canvas aria-label="Interactive coupon in print orientation"></canvas><button id="reset">Reset view</button><p class="small">Drag to orbit · scroll to zoom. The open rail channel faces up in this print orientation.</p>
 <h2>Fit test</h2><ol><li>Print in PLA using the saved orientation. Let it cool, then remove any strings from the rail and the spring window.</li><li>Slide the coupon onto the rear end of a full-size shoe—the end nearest its tapered locking pocket. Continue until the ball seats in that pocket.</li><li>Hold the coupon and pull the shoe along the rail to release it. Repeat about ten times, checking for whitening, cracking or a change in grip.</li><li>Over a padded surface, point the opening downward to check whether the shoe stays in place. Note both retention and how much pull releases it.</li></ol></section>
 <section><a class="download" href="../print-checks/storage-detent-r1-coupon/storage-detent-r1-coupon-configured.3mf">Download 3MF · P1S / PLA</a><p class="small"><a href="../models/storage-detent-r1-coupon.3mf">Geometry 3MF</a> · <a href="../models/storage-detent-r1-coupon.stl">STL</a> · <a href="../models/storage-detent-r1-coupon.step">STEP</a></p>
 <table><tr><th>Overall size</th><td>64 × 32 × 10.10 mm<br>2.52 × 1.26 × 0.40 in</td></tr><tr><th>Print estimate</th><td>{grams:.1f} g · {minutes} min</td></tr><tr><th>Spring leaf</th><td>34 mm root to ball<br>12 mm wide × 1.60 mm thick</td></tr><tr><th>Rounded detent</th><td>R3.50 mm</td></tr><tr><th>Nominal spring travel</th><td>{r['spring']['rail_travel_mm']:.2f} mm over the rail</td></tr><tr><th>Pocket</th><td>8 mm mouth · 2 mm floor<br>3 mm deep · 90° included angle</td></tr><tr><th>Rail clearance</th><td>0.35 mm per side</td></tr><tr><th>Settings</th><td>PLA · 0.20 mm · 5 walls<br>15% infill · supports off</td></tr></table>
 <p>Print flat back and leaf down, with the channel upward. The leaf begins on the bed and bends away from the shoe when the ball travels over the rail.</p><p class="small">Both existing full-size profiles clear the fixed coupon in CAD. Bambu slicing passed without warnings. Pull force, fatigue and retention are untested. This version deliberately uses the tapered pocket as well as the rail; it is not a rail-only connection.</p><p class="small">If it binds before reaching the pocket, stop and report the rail fit separately from the snap force. Stop if the leaf cracks or takes a permanent bend.</p></section></div>
 <h2>Dimensions and seating</h2><img src="section.svg" alt="Coupon plan and section through the detent and tapered pocket">
 <script type="module">import {{createModelView}} from '../../../../viewer.js';const view=await createModelView(document.querySelector('canvas'),'../models/storage-detent-r1-coupon.stl');document.querySelector('#reset').onclick=()=>view.fit();</script></html>'''
 (dest/'datasheet.html').write_text(html)

if __name__=='__main__':write()
