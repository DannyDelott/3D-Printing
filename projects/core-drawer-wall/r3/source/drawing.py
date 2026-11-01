"""R2 mounting detail, with dimensioned profiles directly from the part CAD."""
from model import *
s=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 590"><style>text{font:14px system-ui;fill:#34483d}.h{font-weight:650}.small{font-size:12px}</style>']
def text(x,y,t,cl='',a='start'):s.append(f'<text x="{x}" y="{y}" text-anchor="{a}" class="{cl}">{t}</text>')
def path(poly,x,y,k,fill):
 d=' '.join('M'+' L'.join(f'{x+k*a:.2f},{y-k*b:.2f}' for a,b in pts)+'Z' for pts in poly.to_polygons());s.append(f'<path d="{d}" fill="{fill}" fill-rule="evenodd" stroke="#41584a" stroke-width="1"/>')
def line(x,y,X,Y):s.append(f'<path d="M{x} {y}L{X} {Y}" fill="none" stroke="#59715d"/>')
def rect(x,y,w,h,c):s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c}" stroke="#596e5e"/>')
text(20,23,'MOUNTED UPPER JUNCTION · FACE VIEWS','h')
a,b=90,210;k=2.8
path(junction(False,'front').slice(-lip+.04),a,b,k,'#d5d8c8')
path(junction(False,'rear').slice(-lip+1.25),350,b,k,'#d5d8c8')
text(a,244,'Front · two tie slots','','middle');text(350,244,'Rear · screw eye + two tie slots','','middle')
line(355,129,449,92);text(447,83,'Ø4.8 mm eye');text(447,105,'#8 pan-head screw','small')
line(338,149,467,174);text(457,198,'Recess on plywood side','small')
line(20,266,620,266);text(20,300,'SIDE SECTION · THROUGH THE MOUNT','h')
# Horizontal axis is core length; screw and tie paths are projected together.
X=110;K=4.7;FR=X-lip*K;RR=X+(L+lip)*K
rect(FR,359,lip*K,100,'#c3cbb8');rect(RR-4.2*K,359,4.2*K,100,'#c3cbb8')
rect(RR,325,19.05*K,142,'#e2d1b7')
text(X+K*L/2,340,'60 mm nominal core','','middle')
line(X,346,X+L*K,346);line(X,341,X,350);line(X+L*K,341,X+L*K,350)
# Screw passes through rear plate, perpendicular to the ply.
rect(RR-4.2*K-3,376,3,13,'#6f7970');rect(RR-4.2*K,380,19.05*K,4,'#6f7970')
text(508,385,'¾″ plywood','h');text(508,406,'~15 mm screw','small');text(508,424,'penetration','small')
s.append(f'<path d="M{FR-3} 422 Q{FR-7} 422 {FR-7} 426 V431 Q{FR-7} 435 {FR-3} 435 H{RR-2} V422 Z" fill="none" stroke="#626760" stroke-width="3"/>')
text(181,479,'2.5 × 200 mm tie through the gap');line(245,461,245,435)
line(20,501,620,501);text(20,532,'Jaw slot 3.6 mm  ·  core pitch 90.4 mm  ·  vertical rise 78.3 mm')
text(20,557,'Fit the screw before installing the front connector. The shelf supports the drawer wall.','small')
(P/'section.svg').write_text(''.join(s)+'</svg>')
