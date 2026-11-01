"""One-piece dust-shield drawer; unchanged R3 mount and straight travel."""
from pathlib import Path
import importlib.util,numpy as np,json,math
from manifold3d import Manifold as M
from shapely.geometry import Polygon
P=Path(__file__).resolve().parents[1];out=P/'models'
spec=importlib.util.spec_from_file_location('r3',P.parent/'r3/source/model.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
CS=r.CS;extr=r.extr;box=r.box;poly=r.poly
# The front needs to cover the bore, not trace the internal guide flats.
# At the two low corners only, extend the 45-degree tangent from the circle
# to the flat bed. The top and sides are circular. Every outer-front layer
# above the tangent is supported by the solid layer immediately below.
radius=43.4; t=-radius/math.sqrt(2); tangent=lambda y:radius*math.sqrt(2)+y
face=(r.circle(radius)^box(-50,t,50,50))+poly([(-tangent(r.floor),r.floor),(tangent(r.floor),r.floor),(tangent(t),t),(-tangent(t),t)])
# Keep the interior open above the rim while rounding floor/side transitions.
ci=r.notch(r.circle(r.R-r.wall)^box(-50,r.floor+r.thick,50,55),36.5-r.wall)
for sign in [-1,1]:ci=ci ^ r.halfplane(sign/math.sqrt(2),1/math.sqrt(2),r.upper-r.wall)
ci=ci.offset(-2.5).offset(2.5,circular_segments=96)
front=-r.lip; back=r.L-1-r.wall; blend=2.4; eps=.0002
def tidy(shape):
    pts=shape.to_polygons()[0]
    return r.poly(list(Polygon(pts).simplify(.012).exterior.coords)[:-1])
ci=tidy(ci)
def blend_cloud(at,dir):
    clouds=[]
    for i in range(11):
        a=i*math.pi/20; w=blend*(1-math.cos(a)); off=blend*(1-math.sin(a))
        ring=tidy(ci.offset(-off,circular_segments=48)) if i<10 else ci
        poly=np.array(ring.to_polygons()[0])
        clouds.append(np.column_stack([poly,np.full(len(poly),at+dir*w)]))
    return clouds
# Convex entire cavity: one hull avoids coplanar seams between loft segments.
cut=M.hull_points(np.concatenate(blend_cloud(front,1)+blend_cloud(back,-1)))
body=extr(r.section,front,r.L-1)-cut
# Smooth pull: the upper surface slopes back into the face (no horizontal
# ledge). Lower surface grows at 45 degrees; a 5.7 mm nose is reachable.
f=front-2.4
profile=poly([(20.0,f+.15),(32.6,f+.15),(27.7,f-5.7),(25.8,f-5.7)])
pull=extr(profile,-16,16).transform([[0,0,1,0],[1,0,0,0],[0,1,0,0]])
taper=r.rnd(-16,f-5.7,16,f+.3,2)
pull=pull ^ extr(taper,18,35).transform([[1,0,0,0],[0,0,1,0],[0,1,0,0]])
drawer=body+extr(face,f,front)+pull
cavity=(cut ^ extr(r.section,front,back)).volume()/1000
def main():
    out.mkdir(exist_ok=True);parts=r.plate([('Dust-shield drawer',r.world(drawer))]);m=parts[0][1]
    m.export(out/'dust-shield-r3-1.stl')
    # Use the same standard writer as R3, with a local revision filename.
    r.OUT=out;r.write3('dust-shield',parts);(out/'dust-shield-r3.3mf').rename(out/'dust-shield-r3-1.3mf')
    # All features forward of the mounting plane extract away from the wall.
    # Body sweep uses exactly the existing R3 bearing envelope.
    sweep=extr(r.section,-r.L-12,r.L)
    for b in [True,False]:
        for mode in ['plain','front','rear']:
            j=r.junction(b,mode)
            for x,y in (r.centers[:2] if b else r.centers):
                for a in [j,r.rear(j)]:
                    assert abs((sweep.translate((x,y,0))^a).volume())<1e-5
                    assert abs((drawer.translate((x,y,0))^a).volume())<1e-5
    # Front shield cannot touch an adjacent shield, including on the diagonal.
    for a in range(0,360,60):
        shift=(r.pitch*math.cos(math.radians(a)),r.pitch*math.sin(math.radians(a)),0)
        assert abs((drawer ^ drawer.translate(shift)).volume())<1e-5
    checks=dict(cavity_ml=round(cavity,2),reference_ml=242.29,clear_mouth_mm=43.8,front_bounds=m.extents.round(2).tolist(),upper_bore_overlap_mm=radius-r.ID/2,lower_bore_gap_mm=r.ID/2+r.floor,inside_corner_radius_mm=2.4)
    (P/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    cells=[];groups=[]
    def add(shape,x,z,color):
        ob=r.mesh(r.world(shape.translate((x,z,0))));cells.append(ob);groups.append([len(ob.faces),color])
    for i,(x,z) in enumerate([(-r.pitch,0),(0,0),(r.pitch,0),(-r.half,r.rise),(r.half,r.rise)]):
        add(r.core,x,z,2);add(drawer.translate((0,0,-29 if i==4 else 0)),x,z,3)
    for seam,sh in [(-r.pitch-r.half,r.junction(True,edge=1)),(-r.half,r.junction(True)),(r.half,r.junction(True)),(r.pitch+r.half,r.junction(True,edge=-1))]:
        add(sh,seam,0,0); add(r.rear(sh),seam,0,0)
    for x in [-r.half,r.half]:
        add(r.junction(False,'front'),x,0,0);add(r.rear(r.junction(False,'rear')),x,0,1);add(r.cable(False),x,0,4)
    r.trimesh.util.concatenate(cells).export(out/'wall-example-r3-1.stl');(P/'preview-groups.json').write_text(json.dumps(groups)+'\n')
if __name__=='__main__':main()
