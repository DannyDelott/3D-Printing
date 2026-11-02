"""Spacer shapes in installed XY; depth grows from each rim toward the other."""
def build(r):
 ex=r.extr;circle=r.circle;box=r.box;pitch=r.pitch;rise=r.rise
 def bands(zone,centers):
  aperture=r.CS();seats=r.CS();outer=r.CS();prongs=r.CS();shoulder=r.CS()
  for x,y in centers:
   hole=circle(40.,x,y);s=circle(r.ro,x,y)
   aperture+=hole;seats+=s
   outer+=circle(r.ro+1.0,x,y)-s
   prongs+=circle(r.ri,x,y)-hole
   shoulder+=circle(r.ro+1.,x,y)-hole
  return zone-aperture,zone-seats,zone^(outer+prongs),zone^shoulder
 def edge(rear):
  centers=[(0,0),(r.half,rise),(0,2*rise)]
  zone=r.poly([(-r.half,0),(0,0),(r.half,rise),(0,rise*2),(-r.half,rise*2)])
  skin,free,prongs,seat=bands(zone,centers)
  # The front closes the half-gap. The back is a frame. Vertical ribs carry
  # compression between curved rim seats, independently of the flat front skin.
  # Short local jaws where load actually enters the rims. A central rib
  # and two diagonal webs connect the three pads; no second full fascia.
  zones=box(-22,0,12,49)+box(-22,2*rise-49,12,2*rise)+box(-7,rise-10.17,8,rise+10.17)
  seat=seat^zones;prongs=prongs^zones
  def strut(x,y,X,Y,w):
   dx,dy=X-x,Y-y;length=(dx*dx+dy*dy)**.5;vx=-dy*w/(2*length);vy=dx*w/(2*length)
   return r.poly([(x+vx,y+vy),(X+vx,Y+vy),(X-vx,Y-vy),(x-vx,y-vy)])
  posts=box(-4.9,39,-2.5,2*rise-39)+strut(-3.7,41,3,rise,1.6)+strut(3,rise,-3.7,2*rise-41,1.6)
  x=-3.7;y=rise
  rail=r.rnd(x-2.0,y-2.9,4,y+2.9,1);truss=free^(posts+rail)
  panel=skin
  for cx,cy in centers:panel-=circle(42.,cx,cy)
  mat=ex((seat+truss) if rear else (panel+seat),-r.lip,-.8)
  mat+=ex(seat,-.8,0)+ex(prongs,0,2.8)+ex(truss,-.8,2.4)
  # Inward ribs underneath the outer upper bin support its floor.
  mat+=r.guide().translate((0,rise,0))
  return max(mat.simplify(.001).decompose(),key=lambda m:m.volume())
 return edge
