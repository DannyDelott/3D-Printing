"""Write the R3 drawing and HTML from the generated model's recorded dimensions."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def write(report):
    dest = ROOT/'roundover-1-8'
    dest.mkdir(exist_ok=True)
    r = report['printed_radius_mm']
    paper = report['assumed_paper_thickness_mm']
    cushion = report['nominal_cushion_thickness_mm']
    nominal = report['nominal_radius_mm']
    w,length,height = report['parts']['shoe']['dimensions_mm']
    a=r/math.sqrt(2)
    shoulder=report['contact']['shoulder_length_mm']
    flare=report['contact']['flare_per_side_degrees']
    angle=math.radians(45-flare)
    b=a+shoulder*math.cos(angle)
    end_z=14+r-a+shoulder*math.sin(angle)
    surface=lambda x:14+r-math.sqrt(r*r-x*x)
    pts=[(-12,0),(12,0),(9,5),(w/2,5+w/2-9),(w/2,15),(b,end_z)]
    pts += [(a-2*a*i/80,surface(a-2*a*i/80)) for i in range(81)]
    pts += [(-b,end_z),(-w/2,15),(-w/2,5+w/2-9),(-9,5)]
    polygon=' '.join(f'{155+x*6:.3f},{258-z*6:.3f}' for x,z in pts)
    arc=[]
    for i in range(81):
        theta=-math.pi/4+i*math.pi/160
        arc.append((r*math.sin(theta),r-r*math.cos(theta)))
    path=' '.join(('M' if i==0 else 'L')+f'{455+x*18:.2f},{145-z*18:.2f}' for i,(x,z) in enumerate(arc))
    lining=[]
    for radius in (r, r-cushion):
        points=[(455+radius*math.sin(t)*18,145-(r-radius*math.cos(t))*18) for t in [-math.pi/4+i*math.pi/160 for i in range(81)]]
        lining.append(points)
    pad_polygon=' '.join(f'{x:.2f},{y:.2f}' for x,y in lining[0]+list(reversed(lining[1])))
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 320" role="img" aria-label="Dimensioned shoe cross-section and quarter-round detail">
    <style>text{{font:13px system-ui;fill:#27382d}} .dim{{fill:none;stroke:#4e6054;stroke-width:1}} .small{{font-size:11px}}</style>
    <text x="60" y="25">End view · print orientation</text>
    <polygon points="{polygon}" fill="#a9b79e" stroke="#4e6054" stroke-width="1.5"/>
    <path class="dim" d="M59.75 58H250.25 M59.75 53V64 M250.25 53V64"/>
    <text x="155" y="48" text-anchor="middle">{w:.2f} mm · {w/25.4:.2f} in</text>
    <path class="dim" d="M280 258V{258-height*6:.2f} M275 258H285 M275 {258-height*6:.2f}H285"/>
    <text x="295" y="225" transform="rotate(-90 295 225)">{height:.2f} mm · {height/25.4:.2f} in</text>
    <text x="155" y="285" text-anchor="middle">Rail cap on print bed</text>
    <text x="360" y="25">Contact profile · enlarged</text>
    <polygon points="{pad_polygon}" fill="#e6c78f" stroke="#9b763e" stroke-width="1"/><path d="{path}" fill="none" stroke="#4e6054" stroke-width="4"/>
    <path d="M{455-a*18:.2f} {145-(r-r/math.sqrt(2))*18:.2f}L{455-b*18:.2f} {145-(end_z-14)*18:.2f} M{455+a*18:.2f} {145-(r-r/math.sqrt(2))*18:.2f}L{455+b*18:.2f} {145-(end_z-14)*18:.2f}" class="dim"/>
    <path d="M455 148V174" class="dim"/>
    <text x="455" y="194" text-anchor="middle">Printed concave R{r:.3f} mm</text>
    <text x="455" y="216" text-anchor="middle">Workpiece R{nominal:.3f} mm · 1/8 in</text>
    <text x="455" y="238" text-anchor="middle">{cushion:.3f} mm cushion + {paper:.2f} mm paper / adhesive</text>
    <text x="455" y="260" text-anchor="middle">{shoulder:g} mm shoulders · {flare:g}° outward flare each</text>
    <text x="330" y="311" text-anchor="middle">Full length {length:g} mm / {length/25.4:.2f} in · Coupon 70 mm / 2.76 in</text></svg>'''
    (dest/'section.svg').write_text(svg)
    html=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>1/8-inch roundover shoe · R3</title>
    <style>*{{box-sizing:border-box}}body{{font:15px/1.5 system-ui;color:#243529;margin:32px auto;padding:0 24px;max-width:1100px}}h1{{font-size:29px;margin-bottom:8px}}h2{{font-size:18px}}p{{max-width:78ch}}.layout{{display:grid;grid-template-columns:1.3fr 1fr;gap:30px}}canvas{{width:100%;height:310px;background:#f4f6ef}}button,.download{{border:1px solid #bec8bc;background:white;padding:8px 13px;color:inherit;text-decoration:none;display:inline-block;border-radius:5px}}.download{{background:#294d37;color:white;margin-bottom:12px}}table{{width:100%;border-collapse:collapse}}td,th{{border-bottom:1px solid #d9dfd5;padding:7px;text-align:left}}th{{font-weight:500}}img{{width:100%}}small{{color:#53634e}}@media(max-width:760px){{.layout{{display:block}}body{{margin:20px auto}}}}</style></head><body>
    <h1>1/8-inch roundover shoe</h1><p>R3 · A centered roundover shoe for a 1/8-inch POWERTEC cushion and sanding at 45°.</p>
    <div class="layout"><section><canvas id="model" aria-label="Interactive shoe preview"></canvas><button id="reset">Reset view</button><p><small>Drag to orbit · Scroll to zoom</small></p><img src="section.svg" alt="Dimensioned cross-section and radius detail"></section><section>
    <a class="download" href="../print-checks/roundover-1-8-r3-shoe/roundover-1-8-r3-shoe-configured.3mf">Download 3MF · Full shoe</a>
    <table><tr><th>Full shoe</th><td>{length:g} × {w:.2f} × {height:.2f} mm<br>{length/25.4:.2f} × {w/25.4:.2f} × {height/25.4:.2f} in</td></tr><tr><th>Coupon length</th><td>70 mm · 2.76 in</td></tr><tr><th>Workpiece radius</th><td>{nominal:.3f} mm · 1/8 in</td></tr><tr><th>Printed groove radius</th><td>{r:.3f} mm</td></tr><tr><th>Cushion thickness</th><td>{cushion:.3f} mm · 1/8 in nominal</td></tr><tr><th>Assumed abrasive thickness</th><td>{paper:.2f} mm, including adhesive</td></tr><tr><th>Shoulders</th><td>{shoulder:g} mm long · {flare:g}° outward flare per side</td></tr><tr><th>Connection</th><td>Existing dovetail and 90° tapered seat</td></tr><tr><th>Material / layers</th><td>PLA · 0.20 mm · 5 walls · 15% infill</td></tr></table>
    <h2>Print and fit</h2><p>Print rail-cap-down with the groove upward, without supports. Fit one layer of POWERTEC 71014 mat into the curved seat. Start with an approximately 8 mm wide cushion strip and trim its installed edges at the ends of the curve. Apply approximately 5 mm wide sandpaper over the cushion; do not stretch it across the opening. Leave both short shoulders bare; the material beyond them is cut back to clear the board faces. Hold the plane at 45° to the two board faces and move along the edge.</p><p>Print the coupon first. It uses the same cross-section and fits the existing 70 mm coupon carrier and tapered knob. The full shoe uses the existing 186 mm carrier and tapered knob.</p>
    <p><a href="../print-checks/roundover-1-8-r3-coupon/roundover-1-8-r3-coupon-configured.3mf">Download 3MF · Fit coupon</a> · <a href="../models/roundover-1-8-r3-shoe.step">Editable STEP</a></p>
    <p><small>Fit against routed wood has not been physically tested. The groove allows the full 3.175 mm nominal cushion thickness plus 0.30 mm for paper and all adhesive layers. Cushion compression is unmeasured: test on routed scrap under light sanding pressure before printing the full shoe. Trim the pad or abrasive if either touches the adjoining flats. Intended for a plain quarter-round without a bead or shoulder.</small></p>
    <p><a href="https://www.amazon.com/dp/B00NFB81ZC">Cushion: POWERTEC 71014 · 1/8 in</a></p><p><a href="https://www.amazon.com/dp/B0C5DVBNLS">Matching bit: TOTOWOOD 1/8-inch roundover</a></p></section></div>
    <script type="module">import {{createModelView}} from '../../../../viewer.js';const v=await createModelView(document.querySelector('canvas'),'../models/roundover-1-8-r3-shoe.stl');document.querySelector('#reset').onclick=()=>v.fit();</script></body></html>'''
    (dest/'datasheet.html').write_text(html)

if __name__=='__main__':
    write(json.loads((ROOT/'validation-roundover-1-8-r3.json').read_text()))
