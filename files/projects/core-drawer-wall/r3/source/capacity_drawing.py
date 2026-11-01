"""R2 and R3 interior profiles at the same scale, derived directly from CAD."""
from model import *
s=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 310"><style>text{font:15px system-ui;fill:#34483d}.h{font-weight:650}.s{font-size:13px}</style>']
def path(poly,x,y,k,fill,stroke='#4e6659'):
 d=' '.join('M'+' L'.join(f'{x+k*a:.2f},{y-k*b:.2f}' for a,b in pts)+'Z' for pts in poly.to_polygons());s.append(f'<path d="{d}" fill="{fill}" fill-rule="evenodd" stroke="{stroke}" stroke-width="1"/>')
def text(x,y,label,cl='s'):s.append(f'<text x="{x}" y="{y}" text-anchor="middle" class="{cl}">{label}</text>')
old=notch(circle(38.5-1.6)^box(-50,-29.5+2,50,14),36.5-1.6)
for x,intake,rev,cap in [(155,old,'R2 · 164 mL','50% of core volume'),(470,cavity,'R3 · 242 mL','75% of core volume')]:
 path(circle(OD/2)-circle(ID/2),x,150,2.35,'#c5aa89');path(intake,x,150,2.35,'#b5cbbb');text(x,28,rev,'h');text(x,281,cap)
 if x==470:
  path(old,x,150,2.35,'#dce6db','#8ca398')
text(320,307,'Same 83 mm bore and 60 mm core length. Darker green shows storage gained in R3.')
(P/'capacity.svg').write_text(''.join(s)+'</svg>')
