"""Example stack elevation and installed anchor cross section from the CAD."""
from model import *
def svg(head):
 return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {head}"><style>text{{font:14px system-ui,sans-serif;fill:#2d4435}}.small{{font-size:12px}}.head{{font-weight:650}}</style>']
def txt(s,x,y,t,cl='',a='start'):s.append(f'<text x="{x}" y="{y}" class="{cl}" text-anchor="{a}">{t}</text>')
def circ(s,x,y,rad,color):s.append(f'<circle cx="{x}" cy="{y}" r="{rad}" fill="{color}" stroke="#859481" stroke-width=".8"/>')
def line(s,x,y,X,Y,col='#647462',w=1):s.append(f'<path d="M{x} {y}L{X} {Y}" fill="none" stroke="{col}" stroke-width="{w}"/>')
def rect(s,x,y,w,h,c):s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c}"/>')
def path(s,cs,x,y,k,fill):
 d=' '.join('M'+' L'.join(f'{x+k*a:.2f},{y-k*b:.2f}' for a,b in poly)+'Z' for poly in cs.to_polygons());s.append(f'<path d="{d}" fill="{fill}" fill-rule="evenodd" stroke="#546653" stroke-width=".8"/>')
def main():
 s=svg('610 465');k=.59;xc=291;yb=387
 for row in range(8):
  n=9-row;y=yb-row*r.rise*k
  txt(s,13,y+4,str(row+1),'small')
  for j in range(n):
   x=xc+(j-(n-1)/2)*r.pitch*k
   circ(s,x,y,44*k,'#d2b696');circ(s,x,y,43.4*k,'#d3ddd1')
   if row==3 and j in [0,n-1]:
    Y=y+(r.rise-(r.rise/3+2.9))*k
    circ(s,x,Y,4.4,'#bd7142')
   if row==7:
    rect(s,x-4,y-61.8*k,8,10,'#a9bda8');circ(s,x,y-56.5*k,4.3,'#285b46')
 line(s,49,yb+44.8*k,534,yb+44.8*k,'#354b3a',3)
 txt(s,292,438,'813.6 mm / 32.03 in across the outside feet','','middle')
 X=549;line(s,X,yb+44.8*k,X,yb-(7*r.rise+61.8)*k);line(s,X-5,yb+44.8*k,X+5,yb+44.8*k);line(s,X-5,yb-(7*r.rise+61.8)*k,X+5,yb-(7*r.rise+61.8)*k)
 txt(s,543,207,'654.6','small');txt(s,543,224,'mm','small')
 circ(s,55,456,4,'#bd7142');txt(s,65,460,'Row 4: middle screw','small');circ(s,293,456,4,'#285b46');txt(s,304,460,'Row 8: top screw above rim','small')
 (P/'layout.svg').write_text(''.join(s)+'</svg>')
 s=svg('640 355');txt(s,20,24,'MIDDLE SCREW FACE','head');txt(s,331,24,'TOP CLIP · SIDE SECTION','head')
 k=2.75;path(s,mid(True).slice(-1.15),115,185,k,'#c4cfba')
 line(s,118,185-k*(r.rise/3+2.9),199,72);txt(s,202,68,'Ø4.8 wood screw','small')
 line(s,115,185-k*(r.rise/3-3.7),199,143);txt(s,197,160,'M3 through-bolt','small')
 x=341;K=3.25
 def side(w0,v0,w1,v1,c):rect(s,x+K*w0,224-K*(v1-28),(w1-w0)*K,(v1-v0)*K,c)
 side(0,41.5,60,44,'#c4a27c');side(-1.4,39.8,0,52.6,'#98ad98');side(60,39.8,61.4,61.8,'#98ad98');side(61.4,25,80.45,66,'#e1d4c1')
 side(-8.6,47.1,61.4,49.9,'#545e59');side(-5.3,45.3,-1.4,51.7,'#545e59');side(56.4,55.1,75.45,57.9,'#545e59');side(56.1,53.6,57.2,59.4,'#545e59')
 line(s,385,112,409,155);txt(s,331,106,'M3 × 70','small');txt(s,446,78,'#8 × ¾″','small');line(s,495,81,530,130)
 txt(s,331,247,'Front nut       60 mm core       Plywood','small');txt(s,20,290,'Mid pair replaces a three-way joint. Top pair captures one exposed core.');txt(s,20,318,'Full disk Ø86.8 mm • 1.9 mm radial overlap • 3.6 mm between neighboring faces.','small')
 (P/'mount.svg').write_text(''.join(s)+'</svg>')
if __name__=='__main__':main()
