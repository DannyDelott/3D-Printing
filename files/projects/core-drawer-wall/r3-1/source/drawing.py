from model import *
s=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 790 365"><style>text{font:15px system-ui;fill:#324c3f}.h{font-size:19px;font-weight:650}.s{font-size:13px}</style>']
def shape(cs,x,y,k,fill,stroke='#4d6152',width=1):
 d=' '.join('M'+' L'.join(f'{x+k*a:.2f},{y-k*b:.2f}' for a,b in pts)+'Z' for pts in cs.to_polygons())
 s.append(f'<path d="{d}" fill="{fill}" fill-rule="evenodd" stroke="{stroke}" stroke-width="{width}"/>')
def text(x,y,label,cl='',anchor='middle'):s.append(f'<text x="{x}" y="{y}" class="{cl}" text-anchor="{anchor}">{label}</text>')
def line(x,y,X,Y):s.append(f'<path d="M{x} {y}L{X} {Y}" stroke="#4e6856" fill="none"/>')
text(190,30,'Inside the R3 drawer','h');text(590,30,'Round-front option','h')
for x in [190,590]:shape(r.circle(r.OD/2)-r.circle(r.ID/2),x,172,2.6,'#d5b797')
ideal=r.circle(r.R-r.wall)^box(-50,r.floor+r.thick,50,r.top)
shape(ideal,190,172,2.6,'#d49c67');shape(r.cavity,190,172,2.6,'#acbfb0')
line(181,93,106,66);text(95,60,'Upper flats: 0.5 mL','s')
line(124,235,64,257);text(62,279,'Lower flats','s')
# Front facing diagram: solid shield covers the top and sides.
shape(face,590,172,2.6,'#a8bcac');shape(box(-14,25.5,14,30.5),590,172,2.6,'#859d8d')
line(590,267,635,286);text(661,302,'6 mm lower gap','s')
text(190,316,'6.7 mL total in the shaded corners.','s')
text(590,324,'Circular upper edge overlaps the bore by 1.9 mm.','s')
text(395,355,'83 mm nominal bore · same R3 base, upper junctions and wall mount','s')
(P/'section.svg').write_text(''.join(s)+'</svg>')
