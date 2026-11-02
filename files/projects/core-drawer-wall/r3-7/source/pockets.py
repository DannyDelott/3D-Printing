"""Three independent, pull-out gap pockets. Coordinates match the R3.4 supports."""
import numpy as np
def make(r,M,edge,ff):
 ex=r.extr; B=r.box; C=r.circle
 def brow(top):
  # The front cover grows back at 45 degrees from the face as the bin
  # prints upright. It ends at the rim and leaves the rest open from above.
  section=r.poly([(ff,top+.3),(ff,top-16.6),(-r.lip,top-1.35),(-r.lip,top+.3)])
  return ex(section,-90,90).transform([[0,0,1,0],[0,1,0,0],[1,0,0,0]])
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
 side_fascia=side_section.offset(1.05,circular_segments=48)^B(-50,lo,0,hi+3)
 side_outer=ex(side_section,ff+.25,59.6)
 inner=(r.rnd(left+1.4,lo+1.5,right-1.4,hi+8,1.8)-clearance.offset(1.4))
 side_void=ex(inner,ff+1.6,58.0)-brow(hi)
 grip,neg=hollow_grip(cx,hi-9.5,14,8.2,6.,1.35)
 side_stop=ex(side_fascia,-r.lip-1.2,-r.lip)
 side_bin=(side_outer+ex(side_fascia,ff,ff+2.4)+side_stop-side_void+grip)-neg
 side_space=(side_outer^side_void)-grip
 def side_frame(back):
  base=edge(back)
  # Front and rear bearing shelves, with 0.15 mm below the nominal slide.
  rail=r.poly([(-43.7,lo-.15),(-7.5,lo-.15),(-4.3,46.8),(-3.0,46.8),(-3.0,44.5),(-7.1,lo-2.25),(-43.7,lo-2.25)])
  rail-=C(r.ro+.08,0,0)
  # The back shelf projects far enough to support the rear end of the bin.
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
 tri_sec=form^B(-25,44.85,25,61.4)
 tri_window=tri_sec.offset(.4,circular_segments=32)
 tri_face=tri_sec.offset(1.15,circular_segments=32)^face_limit^B(-25,44.85,25,64)
 tri_outer=ex(tri_sec,ff+.25,59.6)
 inner=form.offset(-1.22,circular_segments=32)^B(-26,46.05,26,70)
 tri_void=ex(inner,ff+1.6,58.0)-brow(61.4)
 grip2,neg2=hollow_grip(0,51.1,10.6,4.2,4.3,1.25)
 tri_stop=ex(tri_face,-r.lip-1.2,-r.lip)
 tri_bin=(tri_outer+ex(tri_face,ff,ff+2.4)+tri_stop-tri_void+grip2)-neg2
 tri_space=(tri_void^tri_outer)-grip2
 def tri_frame(back):
  skin=zone-seats
  base=ex(skin,-r.lip,0)+ex(prongs^zone,0,3.)
  base-=ex(tri_window,0 if back else -2.5,9)
  return base
 return dict(side_frame=side_frame,side_bin=side_bin,side_space=side_space,side_sweep=side_section,tri_frame=tri_frame,tri_bin=tri_bin,tri_space=tri_space,tri_sweep=tri_sec)
