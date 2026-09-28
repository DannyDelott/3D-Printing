"""Write the R1 drawing and HTML from the generated model's recorded dimensions."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def write(report):
    dest = ROOT/'roundover-1-8'
    dest.mkdir(exist_ok=True)
    r = report['printed_radius_mm']
    paper = report['assumed_paper_thickness_mm']
    nominal = report['nominal_radius_mm']
    w,length,height = report['parts']['shoe']['dimensions_mm']
    a=r/math.sqrt(2)
    surface=lambda x:14+r-math.sqrt(r*r-x*x) if abs(x)<=a else 14+r-r/math.sqrt(2)+abs(x)-a
    pts=[(-12,0),(12,0),(9,5),(w/2,5+w/2-9),(w/2,surface(w/2))]
    pts += [(a-2*a*i/80,surface(a-2*a*i/80)) for i in range(81)]
    pts += [(-w/2,surface(-w/2)),(-w/2,5+w/2-9),(-9,5)]
    polygon=' '.join(f'{155+x*6:.3f},{258-z*6:.3f}' for x,z in pts)
    arc=[]
    for i in range(81):
        theta=-math.pi/4+i*math.pi/160
        arc.append((r*math.sin(theta),r-r*math.cos(theta)))
    path=' '.join(('M' if i==0 else 'L')+f'{455+x*24:.2f},{145-z*24:.2f}' for i,(x,z) in enumerate(arc))
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
    <path d="{path}" fill="none" stroke="#4e6054" stroke-width="4"/>
    <path d="M{455-a*24:.2f} {145-(r-r/math.sqrt(2))*24:.2f}l-42 -42 M{455+a*24:.2f} {145-(r-r/math.sqrt(2))*24:.2f}l42 -42" class="dim"/>
    <path d="M455 148V174" class="dim"/>
    <text x="455" y="194" text-anchor="middle">Printed concave R{r:.3f} mm</text>
    <text x="455" y="216" text-anchor="middle">Workpiece R{nominal:.3f} mm · 1/8 in</text>
    <text x="455" y="238" text-anchor="middle">{paper:.2f} mm abrasive allowance</text>
    <text x="455" y="260" text-anchor="middle">90° arc · tangent 45° guides</text>
    <text x="330" y="311" text-anchor="middle">Full length {length:g} mm / {length/25.4:.2f} in · Coupon 70 mm / 2.76 in</text></svg>'''
    (dest/'section.svg').write_text(svg)
    html=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>1/8-inch roundover shoe · R1</title>
    <style>*{{box-sizing:border-box}}body{{font:15px/1.5 system-ui;color:#243529;margin:32px auto;padding:0 24px;max-width:1100px}}h1{{font-size:29px;margin-bottom:8px}}h2{{font-size:18px}}p{{max-width:78ch}}.layout{{display:grid;grid-template-columns:1.3fr 1fr;gap:30px}}canvas{{width:100%;height:310px;background:#f4f6ef}}button,.download{{border:1px solid #bec8bc;background:white;padding:8px 13px;color:inherit;text-decoration:none;display:inline-block;border-radius:5px}}.download{{background:#294d37;color:white;margin-bottom:12px}}table{{width:100%;border-collapse:collapse}}td,th{{border-bottom:1px solid #d9dfd5;padding:7px;text-align:left}}th{{font-weight:500}}img{{width:100%}}small{{color:#53634e}}@media(max-width:760px){{.layout{{display:block}}body{{margin:20px auto}}}}</style></head><body>
    <h1>1/8-inch roundover shoe</h1><p>R1 · An interchangeable shoe for sanding a routed outside corner with the existing tapered-lock sanding plane.</p>
    <div class="layout"><section><canvas id="model" aria-label="Interactive shoe preview"></canvas><button id="reset">Reset view</button><p><small>Drag to orbit · Scroll to zoom</small></p><img src="section.svg" alt="Dimensioned cross-section and radius detail"></section><section>
    <a class="download" href="../print-checks/roundover-1-8-r1-shoe/roundover-1-8-r1-shoe-configured.3mf">Download 3MF · Full shoe</a>
    <table><tr><th>Full shoe</th><td>{length:g} × {w:.2f} × {height:.2f} mm<br>{length/25.4:.2f} × {w/25.4:.2f} × {height/25.4:.2f} in</td></tr><tr><th>Coupon length</th><td>70 mm · 2.76 in</td></tr><tr><th>Workpiece radius</th><td>{nominal:.3f} mm · 1/8 in</td></tr><tr><th>Printed groove radius</th><td>{r:.3f} mm</td></tr><tr><th>Assumed abrasive thickness</th><td>{paper:.2f} mm, including adhesive</td></tr><tr><th>Connection</th><td>Existing dovetail and 90° tapered seat</td></tr><tr><th>Material / layers</th><td>PLA · 0.20 mm · 5 walls · 15% infill</td></tr></table>
    <h2>Print and fit</h2><p>Print rail-cap-down with the groove upward, without supports. Line the arc and both tangent faces with one thin strip of sandpaper; seat it fully into the groove. Hold the plane at 45° to the two board faces and move along the edge.</p><p>Print the coupon first. It uses the same cross-section and fits the existing 70 mm coupon carrier and tapered knob. The full shoe uses the existing 186 mm carrier and tapered knob.</p>
    <p><a href="../print-checks/roundover-1-8-r1-coupon/roundover-1-8-r1-coupon-configured.3mf">Download 3MF · Fit coupon</a> · <a href="../models/roundover-1-8-r1-shoe.step">Editable STEP</a></p>
    <p><small>Fit against routed wood has not been physically tested. The 0.30 mm abrasive allowance is an assumption; measure your paper before judging fit. Intended for a plain quarter-round without a bead or shoulder.</small></p>
    <p><a href="https://www.amazon.com/dp/B0C5DVBNLS">Matching bit: TOTOWOOD 1/8-inch roundover</a></p></section></div>
    <script type="module">import {{createModelView}} from '../../../../viewer.js';const v=await createModelView(document.querySelector('canvas'),'../models/roundover-1-8-r1-shoe.stl');document.querySelector('#reset').onclick=()=>v.fit();</script></body></html>'''
    (dest/'datasheet.html').write_text(html)

if __name__=='__main__':
    write(json.loads((ROOT/'validation-roundover-1-8-r1.json').read_text()))
