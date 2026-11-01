"""Front view and wall-tie section from the same millimetre CAD as the plates."""
import model as c
s=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 650 475"><style>text{font:15px system-ui;fill:#344638}.h{font-weight:650}.sm{font-size:13px}</style>']
def cs(shape,x,y,k,fill):
 d=' '.join('M'+' L'.join(f'{x+k*a:.1f},{y-k*b:.1f}' for a,b in poly)+'Z' for poly in shape.to_polygons())
 s.append(f'<path d="{d}" fill="{fill}" fill-rule="evenodd" stroke="#4e6252" stroke-width=".9"/>')
def label(x,y,t,cl='sm',anchor='start'):s.append(f'<text x="{x}" y="{y}" class="{cl}" text-anchor="{anchor}">{t}</text>')
def line(x,y,X,Y,dash=''):s.append(f'<path d="M{x} {y}L{X} {Y}" stroke="#637463" fill="none" stroke-dasharray="{dash}"/>')
def rect(x,y,w,h,f):s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{f}" stroke="#516150"/>')
label(28,25,'FRONT · LOWER PAIR','h');label(365,25,'SIDE · WALL ATTACHMENT','h')
k=1.45;y=151;x0=100
for i in [0,1]:
 x=x0+k*c.pitch*i;cs(c.disk(c.OD/2)-c.disk(c.ID/2),x,y,k,'#dcc2a4');cs(c.foot.slice(-.8),x,y,k,'#c0cbb7');cs(c.face,x,y,k,'#8fa99b')
cs(c.clip.slice(-.8),x0+k*c.half,y,k,'#abbca7')
line(x0,58,x0+k*c.pitch,58);line(x0,53,x0,64);line(x0+k*c.pitch,53,x0+k*c.pitch,64);label(x0+k*c.half,51,'90.4 pitch','','middle')
label(30,248,'50 mm flat foot','');line(110,233,102,219);label(166,248,'11.7 mm seam clip','');line(200,230,167,159)
# Side section through the upper tube at the tie. Tab back surface is on ply.
x=378;k=2.7; y=181
def X(w):return x+k*w
def Y(v):return y-k*(v-30)
def profile(w,v,W,V,fill):rect(X(w),Y(V),k*(W-w),k*(V-v),fill)
profile(0,c.ID/2,c.L,c.OD/2,'#cfaa81');profile(c.L+c.lip+4.8,20,c.L+c.lip+4.8+19.05,68,'#e8d8c0')
profile(c.L+c.lip,34,c.L+c.lip+4.8,67,'#b3c2ac')
profile(-c.lip,39.4,0,46.8,'#b3c2ac');profile(0,44.5,6,46.8,'#b3c2ac');profile(0,39.4,6,40.9,'#b3c2ac')
for lo,hi in [(37.4,40.1),(46,48.7)]:profile(c.L+c.lip,lo,c.L+c.lip+4.8,hi,'#fafaf6')
profile(c.L+c.lip+3.2,37.4,c.L+c.lip+4.8,48.7,'#fafaf6')
s.append(f'<path d="M{X(-2.2)} {Y(38.6)}Q{X(-3)} {Y(38.6)} {X(-3)} {Y(40)}V{Y(46)}Q{X(-3)} {Y(47.5)} {X(-1)} {Y(47.5)}H{X(c.L+c.lip+4)}V{Y(38.6)}Z" fill="none" stroke="#4c5048" stroke-width="2.8"/>')
line(X(c.L+c.lip-2),Y(58),X(c.L+c.lip+16),Y(58));label(365,62,'Ø4.8 screw eye','');line(448,65,X(c.L+c.lip),Y(58));label(365,218,'Tie wraps front guard + rear tab','');label(365,239,'Cardboard carries the drawer.','sm')
line(25,272,625,272);label(28,308,'STAGGERED WALL','h')
k=.73
for a,b in [(0,0),(c.pitch,0),(2*c.pitch,0),(c.half,c.pitch*3**.5/2),(3*c.half,c.pitch*3**.5/2)]:
 cs(c.disk(c.OD/2)-c.disk(c.ID/2),80+k*a,426-k*b,k,'#ceb08e')
label(299,351,'Upper rows nest between two cores.','');label(299,380,'78.3 mm rise per row · 45.2 mm offset','');label(299,409,'Join each new seam at the front and rear.','')
(c.P/'section.svg').write_text(''.join(s)+'</svg>')
