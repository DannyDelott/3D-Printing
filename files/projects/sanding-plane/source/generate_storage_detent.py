"""R1 storage detent coupon: slide onto an existing full-size tapered-pocket shoe.

Run with the repository CAD Python. Coordinates match existing shoe STEP files,
except Y is shifted +65 so the countersink is at Y=0. The flexure is a test,
not a validated spring: only fixed geometry and a deflected geometric proxy are checked.
"""
from pathlib import Path
import hashlib,json,math
import cadquery as cq
import trimesh
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
STEM='storage-detent-r1-coupon'
RADIUS=3.5
CENTER_Z=5.5
BEAM_THICKNESS=1.6

def box(x,y,z,w,d,h):
 return cq.Workplane('XY').box(w,d,h,centered=False).translate((x,y,z))

def main():
 # Open profile side. Rail clearance 0.35 mm per side; cap clearance 0.40 mm.
 block=box(-16,-38,-.1,32,64,10.1)
 points=[(-9.35,-2),(9.35,-2),(9.35,-.4),(12.35,4.6),(12.35,5),(-12.35,5),(-12.35,4.6),(-9.35,-.4)]
 cutter=cq.Workplane('XZ').polyline(points).close().extrude(33,both=True).translate((0,-6,0))
 fixed=block.cut(cutter)
 # Window isolates the spring on its sides and tip; rear root stays attached.
 fixed=fixed.cut(box(-7.5,-34,4.8,15,59,7))
 leaf=box(-6,-36,8.4,12,40,BEAM_THICKNESS)
 # Rounded root transitions on the two external beam edges.
 leaf=leaf.edges('|Z').fillet(.8)
 ball=cq.Workplane('XY').sphere(RADIUS).val().translate((0,0,CENTER_Z))
 # Two side flats lie outside the cone contact circle.
 ball=ball.intersect(box(-3,-5,0,6,10,12).val())
 # Rotate sphere seam away from root surfaces if future OCC versions need it.
 spring=leaf.union(ball,tol=.0001).val()
 body=fixed.union(spring,tol=.0001).clean().val()
 assert body.isValid() and len(body.Solids())==1
 # Seat geometry: cone radius r=z-0.6. Tangent sphere centre at 0.6+R*sqrt(2).
 preload=.6+RADIUS*math.sqrt(2)-CENTER_Z
 travel=4.6-(CENTER_Z-RADIUS)
 assert 0<preload<.1
 fixed=fixed.val()
 report={'revision':'R1','purpose':'One-slot snap-in storage retention test using an existing full-size shoe.',
  'dimensions_mm':[64,32,10.1], 'material':'PLA',
  'interface':{'rail_cap_width_mm':24,'rail_root_width_mm':18,'rail_height_mm':5,'side_clearance_mm':.35,'cap_clearance_mm':.4,
   'pocket_mouth_diameter_mm':8,'pocket_floor_diameter_mm':2,'pocket_depth_mm':3,'pocket_included_angle_deg':90,
   'compatibility':'Common dovetail plus the current 8 mm tapered pocket; rail-only shoes do not snap into this detent.'},
  'spring':{'leaf_width_mm':12,'leaf_thickness_mm':BEAM_THICKNESS,'root_to_ball_mm':34,'ball_radius_mm':RADIUS,
   'ball_side_flat_x_mm':3,'nominal_seated_preload_mm':round(preload,4),'rail_travel_mm':travel,
   'floor_gap_seated_mm':round(CENTER_Z+preload-RADIUS-1.6,4)},'checks':{},'sources':{}}
 seated=spring.translate((0,0,preload+.001))
 retracted=spring.translate((0,0,travel+.05))
 # No rigid feature touches either profile. Spring translation is a clearance
 # proxy, not an elastic/force/fatigue simulation.
 for label,stem in [('fingernail','profile-jig-profile-up-full-shoe'),('roundover','roundover-1-8-r3-shoe')]:
  path=ROOT/'models'/f'{stem}.step';shoe=cq.importers.importStep(str(path)).val().translate((0,65,0))
  assert shoe.intersect(fixed).Volume()<1e-5
  assert shoe.intersect(seated).Volume()<1e-4
  assert shoe.intersect(spring).Volume()>1e-5
  volumes=[]
  for y in [-70,-56,-42,-28,-14,-7,-3,0,3,7,14,28,42,56,70]:
   moved=shoe.translate((0,y,0));v=moved.intersect(fixed).Volume();assert v<1e-5,(label,y,v)
   assert moved.intersect(retracted).Volume()<1e-4,(label,y)
   volumes.append(v)
  report['checks'][label]={'fixed_parts_clear_during_sliding':True,'translated_spring_clears_rail':True,'translated_seated_ball_clears_pocket':True}
  report['sources'][label]={'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 # Print the continuous back and spring face on the bed, channel upward.
 # The whole leaf starts on the bed and its length stays in the XY print plane.
 printed=body.rotate((0,0,0),(1,0,0),180)
 b=printed.BoundingBox();printed=printed.translate((-b.xmin,-b.ymin,-b.zmin))
 dest=ROOT/'models';dest.mkdir(exist_ok=True)
 cq.exporters.export(body,str(dest/f'{STEM}.step'))
 cq.exporters.export(printed,str(dest/f'{STEM}.stl'),tolerance=.025,angularTolerance=.1)
 mesh=trimesh.load_mesh(dest/f'{STEM}.stl',process=True)
 # OCC sphere poles can tessellate into zero-area triangles after STL float rounding.
 mesh.update_faces(mesh.nondegenerate_faces())
 mesh.update_faces(mesh.unique_faces())
 mesh.remove_unreferenced_vertices()
 mesh.export(dest/f'{STEM}.stl')
 assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1
 (dest/f'{STEM}.3mf').write_bytes(trimesh.Scene({STEM:mesh}).export(file_type='3mf'))
 loaded=trimesh.load(dest/f'{STEM}.3mf',force='mesh')
 assert loaded.is_watertight and np.allclose(loaded.bounds,mesh.bounds) and len(loaded.split())==1
 report['print_dimensions_mm']=mesh.extents.round(4).tolist()
 report['checks']['watertight_single_body']=True
 report['physical_status']='Unprinted. Retention, release force, flex fatigue and bridge finish unverified.'
 report['files']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [dest/f'{STEM}.{ext}' for ext in ['step','stl','3mf']]}
 (ROOT/'validation-storage-detent-r1.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2),flush=True)
 # Separate preview geometry retains use orientation for the local concept page.
 work=ROOT/'work/shoe-storage-concept';work.mkdir(parents=True,exist_ok=True)
 cq.exporters.export(body,str(work/'detent-coupon-r1.stl'),tolerance=.025,angularTolerance=.1)
 for label,stem in [('fingernail','profile-jig-profile-up-full-shoe'),('roundover','roundover-1-8-r3-shoe')]:
  s=cq.importers.importStep(str(dest/f'{stem}.step')).val().translate((0,65,0))
  cq.exporters.export(s,str(work/f'{label}-detent-r1.stl'),tolerance=.04,angularTolerance=.15)

if __name__=='__main__':main()
