"""Three independent, pull-out gap pockets. Coordinates match the R3.4 supports."""
import numpy as np
def make(r,M,edge,ff):
 ex=r.extr; B=r.box; C=r.circle
 def roof(cx,z,bridge=2):
  poly=r.poly([(-60,-45),(60,-45),(60,z-60+bridge),(bridge,z),(-bridge,z),(-60,z-60+bridge)])
  return ex(poly,-200,200).transform([[1,0,0,cx],[0,0,1,0],[0,1,0,0]])
 def hollow_grip(cx,cy,width,height,depth,wall):
  def piece(e):
   rings=[]
   for w,dy,hw,hh in [(-.06,0,width/2,height/2),(depth*.35,1.2,width/2,height/2),(depth+e,1.2,width*.33,.65)]:
    rect=r.rnd(cx-hw-e,cy+dy-hh-e,cx+hw+e,cy+dy+hh+e,min(hh+e-.03,2.8+e))
    points=np.asarray(rect.to_polygons()[0]);rings.append(np.column_stack([points,np.full(len(points),ff+w)]))
   return M.hull_points(np.concatenate(rings))
  neg=piece(0);pos=piece(wall)^ex(B(cx-30,cy-22,cx+30,cy+22),ff,ff+depth+wall+.2)
  return pos,neg
 # The outside wall follows the bank edge. Trim its two inside corners
 # against the top and bottom cardboard so the pocket fills the half-gap.
 lo=43.6;hi=114.2
 left=-43.35;right=-6.8;cx=(left+right)/2
 clearance=r.CS()
 for x,y in [(0,0),(0,2*r.rise),(r.half,r.rise)]:
  clearance+=C(r.OD/2+1.75,x,y)
 side_section=r.rnd(left,lo,right,hi,2.1)-clearance
 side_window=side_section.offset(.4,circular_segments=48)
 side_fascia=side_section.offset(1.05,circular_segments=48)
 side_outer=ex(side_section,ff+.25,56)^roof(cx,56)
 inner=(r.rnd(left+1.4,lo+1.5,right-1.4,hi+8,1.8)-clearance.offset(1.4))
 side_void=ex(inner,ff+1.6,56)^roof(cx,54.4)
 grip,neg=hollow_grip(cx,hi-9.5,14,8.2,6.,1.35)
 side_lid=side_outer^ex(B(-55,hi-1.2,0,hi+.2),ff,-r.lip)
 side_void-=side_lid
 side_stop=ex(side_fascia,-r.lip-1.2,-r.lip)
 side_bin=(side_outer+ex(side_fascia,ff,ff+2.4)+side_stop-side_void+grip)-neg
 side_space=(side_outer^side_void)-grip
 def side_frame(back):
  base=edge(back)
  # Front and rear bearing shelves, with 0.15 mm below the nominal slide.
  rail=r.poly([(-43.7,lo-.15),(-7.5,lo-.15),(-4.3,46.8),(-3.0,46.8),(-3.0,44.5),(-7.1,lo-2.25),(-43.7,lo-2.25)])
  rail-=C(r.ro+.08,0,0)
  # The back shelf projects far enough to support the 56 mm long bin.
  shelf=ex(rail,-r.lip,8.0 if back else 5.0)
  return (base+shelf)-ex(side_window,-2.5,10)
 # Triangular bins occupy the interstice, without touching any spool bore.
 ctr=[(0,0),(-r.half,r.rise),(r.half,r.rise)];zone=r.poly(ctr)
 cavity_outline=zone;face_limit=zone;seats=r.CS();prongs=r.CS()
 for x,y in ctr:
  cavity_outline-=C(44.75,x,y); face_limit-=C(43.9,x,y)
  seats+=C(40.,x,y)
  prongs+=C(r.ri,x,y)-C(40.,x,y);prongs+=C(r.ro+.95,x,y)-C(r.ro,x,y)
 form=cavity_outline.offset(-1.25).offset(1.25,circular_segments=32)
 tri_sec=form^B(-25,38.5,25,58.4)
 tri_window=tri_sec.offset(.4,circular_segments=32)
 tri_face=tri_sec.offset(1.15,circular_segments=32)^face_limit
 tri_outer=ex(tri_sec,ff+.25,56)^roof(0,56,2.5)
 inner=form.offset(-1.22,circular_segments=32)^B(-26,39.75,26,70)
 tri_void=ex(inner,ff+1.6,56)^roof(0,54.4,2.5)
 grip2,neg2=hollow_grip(0,51.1,10.6,4.2,4.3,1.25)
 tri_lid=tri_outer^ex(B(-25,57.15,25,58.5),ff,-r.lip)
 tri_void-=tri_lid
 tri_stop=ex(tri_face,-r.lip-1.2,-r.lip)
 tri_bin=(tri_outer+ex(tri_face,ff,ff+2.4)+tri_stop-tri_void+grip2)-neg2
 tri_space=(tri_void^tri_outer)-grip2
 def tri_frame(back):
  skin=zone-seats
  cy=63.7
  base=ex(skin,-r.lip,0)+ex(prongs^zone,0,3.)
  if not back:base-=ex(tri_window,-2.5,9)
  return base
 return dict(side_frame=side_frame,side_bin=side_bin,side_space=side_space,side_sweep=side_section,tri_frame=tri_frame,tri_bin=tri_bin,tri_space=tri_space,tri_sweep=tri_sec)
