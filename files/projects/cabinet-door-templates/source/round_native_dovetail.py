#!/usr/bin/env python3
"""V7: radius the V6 native dovetail, retaining its tapered mating planes.

Bambu's triangle export is not suitable for exact CAD fillets. Reconstruct the
five native cut planes against the original V3 STEP, then fillet only the ten
joint edges on each half. The V6 tongue vertices define the flank intercept and
slope; nominal dimensions remove single-precision export noise (<0.00003 mm).
"""
from project_paths import artifact_path, artifact_url, publish_html, DESIGNS
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import math
import cadquery as cq
import numpy as np
import trimesh
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from prepare_native_dovetail import write_project, mesh
import manifold3d as mf

ROOT=Path(__file__).resolve().parents[1]
R_OUTER,R_INNER=0.3,0.2
DEPTH_CLEARANCE=0.1
THICKNESS=12.7
X_BASE=201.6125+12.7/2
X_TIP=201.6125-12.7/2+DEPTH_CLEARANCE
V6=artifact_path('rail-template-native-dovetail-v6-bambu.3mf')
original=cq.importers.importStep(str(artifact_path('rail-template-elliptical-honeycomb-v3.step'))).val()
original=original.intersect(cq.Workplane().box(500,300,THICKNESS,centered=(False,False,False)).val()).clean()
native=trimesh.load(V6)
tongue=list(native.geometry.values())[0].copy()
tongue.apply_translation([403.225-tongue.bounds[1,0],-tongue.bounds[0,1],-tongue.bounds[0,2]])
# Recover bottom endpoints directly from the previously tested V6 tongue.
points=tongue.vertices
base=points[(abs(points[:,0]-X_BASE)<.0001)&(points[:,2]<.0001)&(points[:,1]>15)&(points[:,1]<75)]
tip=points[(abs(points[:,0]-X_TIP)<.0001)&(points[:,2]<.0001)]
LOWER_BASE=float(base[:,1].min())
CENTER_Y=float((tip[:,1].min()+tip[:,1].max())/2)
SLOPE=float((LOWER_BASE-tip[:,1].min())/(base[:,0].mean()-tip[:,0].mean()))
TAPER=math.tan(math.radians(2))


def mask(socket, width_clearance=0.1, flank_inset=0., x_limits=(-10,420)):
    def wire(z):
        x_tip=X_TIP-(DEPTH_CLEARANCE if socket else 0)
        def lower(x):
            return LOWER_BASE+flank_inset+TAPER*z+(x-X_BASE)*SLOPE-(width_clearance/2 if socket else 0)
        xy=[(X_BASE,-10),(X_BASE,lower(X_BASE)),(x_tip,lower(x_tip)),
            (x_tip,2*CENTER_Y-lower(x_tip)),(X_BASE,2*CENTER_Y-lower(X_BASE)),(X_BASE,200)]
        far=x_limits[0] if socket else x_limits[1]
        xy.extend([(far,200),(far,-10)])
        # Build analytic plane faces, avoiding a loft's unnecessary B-splines.
        if sum(xy[i][0]*xy[(i+1)%len(xy)][1]-xy[(i+1)%len(xy)][0]*xy[i][1] for i in range(len(xy)))<0:xy.reverse()
        return [cq.Vector(x,y,z) for x,y in xy]
    bottom,top=wire(-1),wire(THICKNESS+1)
    def face(points):return cq.Face.makeFromWires(cq.Wire.makePolygon(points,close=True))
    faces=[face(bottom[::-1]),face(top)]
    for i in range(len(bottom)):
        j=(i+1)%len(bottom)
        faces.append(face([bottom[i],bottom[j],top[j],top[i]]))
    result=cq.Solid.makeSolid(cq.Shell.makeShell(faces))
    assert result.isValid()
    return result


def round_joint(shape, y_limits=(14,75), internal_x=None):
    operation=BRepFilletAPI_MakeFillet(shape.wrapped)
    edges=[]
    for edge in shape.Edges():
        box=edge.BoundingBox()
        if not (194<box.xmin and box.xmax<209 and y_limits[0]<box.ymin and box.ymax<y_limits[1]):continue
        faces=[f for f in shape.Faces() if any(e.isSame(edge) for e in f.Edges())]
        assert len(faces)==2
        # At a concave junction the other face lies on the positive normal side.
        internal=faces[0].normalAt().dot(faces[1].Center()-edge.Center())>0.001
        if internal_x is not None:
            # The narrow stile has distant curved faces; classify the known
            # concave upright corners by their mating-plane intersection.
            internal=box.zlen>THICKNESS-.01 and abs(edge.Center().x-internal_x)<.001
        radius=R_INNER if internal else R_OUTER
        operation.Add(radius,edge.wrapped)
        edges.append({'radius_mm':radius,'type':'internal' if internal else 'external',
                      'original_length_mm':edge.Length(),'midpoint_mm':edge.Center().toTuple()})
    assert len(edges)==10
    assert sum(e['type']=='internal' for e in edges)==2
    operation.Build()
    assert operation.IsDone()
    result=cq.Shape.cast(operation.Shape())
    assert result.isValid() and len(result.Solids())==1
    return result,edges


def solid(geometry):
    result=mf.Manifold(mf.Mesh64(np.asarray(geometry.vertices,dtype=np.float64),np.asarray(geometry.faces,dtype=np.uint64)))
    assert result.status()==mf.Error.NoError
    return result


def export_mesh(shape,stem):
    cq.exporters.export(shape,str(artifact_path(f'{stem}.step')))
    vertices,faces=shape.tessellate(.003,.08)
    result=trimesh.Trimesh([v.toTuple() for v in vertices],faces)
    # OCC includes collapsed triangles at analytic fillet poles. Remove only
    # zero-area facets; keep double precision through mesh and 3MF packaging.
    result.update_faces(result.nondegenerate_faces(height=1e-9))
    result.update_faces(result.unique_faces())
    result.remove_unreferenced_vertices()
    (artifact_path(f'{stem}.stl')).write_text(trimesh.exchange.stl.export_stl_ascii(result))
    assert result.is_watertight and result.is_winding_consistent and len(result.split())==1
    return result


def main(revision=7, width_clearance=0.1):
    shapes={};full={};edge_report={};clean={}
    for name,socket in [('Right tongue',False),('Left socket',True)]:
        clean[name]=original.intersect(mask(socket, width_clearance)).clean()
        assert clean[name].isValid()
        shapes[name],edge_report[name]=round_joint(clean[name])
        full[name]=export_mesh(shapes[name],f'rail-native-v{revision}-'+name.lower().replace(' ','-'))
    pin_change=None
    if revision>=8:
        previous=cq.importers.importStep(str(artifact_path('rail-native-v7-right-tongue.step'))).val()
        pin_change=shapes['Right tongue'].cut(previous).Volume()+previous.cut(shapes['Right tongue']).Volume()
        assert pin_change<1e-6, pin_change
    overlap=shapes['Right tongue'].intersect(shapes['Left socket']).Volume()
    assert overlap<1e-7
    # Measure the requested width clearance on the actual exported mating planes.
    measured=[]
    from shapely.geometry import Polygon,LineString
    for z in [.5,THICKNESS/2,THICKNESS-.5]:
        sections={}
        for name,g in full.items():
            section=g.section(plane_origin=[0,0,z],plane_normal=[0,0,1])
            polygon=Polygon(max(section.discrete,key=len)[:,:2])
            sections[name]=polygon.intersection(LineString([(201.6125,0),(201.6125,100)]))
        male=np.array(sections['Right tongue'].coords)[:,1]
        ears=sorted(sections['Left socket'].geoms,key=lambda x:x.bounds[1])
        gaps=[float(male.min()-ears[0].bounds[3]),float(ears[1].bounds[1]-male.max())]
        assert all(abs(g-width_clearance/2)<.0001 for g in gaps)
        measured.append({'z_mm':z,'gaps_mm':gaps})
    testbox=mf.Manifold.cube([20.7,61,20]).translate([201.6125-10.35,CENTER_Y-30.5,-.1])
    test={name:mesh(solid(g)^testbox) for name,g in full.items()}
    for name,g in test.items():
        assert abs(g.extents[2]-THICKNESS)<.0001
        assert (solid(g)-solid(full[name])).volume()<.001
        (artifact_path(f'rail-native-v{revision}-test-'+name.lower().replace(' ','-')+'.stl')).write_text(trimesh.exchange.stl.export_stl_ascii(g))
    for g in list(full.values())+list(test.values()):g.apply_translation(-g.bounds.mean(axis=0))
    with ZipFile(V6) as z:files={n:z.read(n) for n in z.namelist()}
    full_report=write_project(files,full,[(128,174),(128,50.7)],artifact_path(f'rail-template-native-dovetail-v{revision}-bambu.3mf'),f'V{revision} R0.3 external R0.2 internal')
    test_report=write_project(files,test,[(145,128),(110,128)],artifact_path(f'rail-native-dovetail-v{revision}-fit-test.3mf'),f'FIT TEST V{revision} rounded joint, {width_clearance:.2f} mm width clearance')
    if revision>=8:
        coupon_scene=trimesh.load(artifact_path(f'rail-native-dovetail-v{revision}-fit-test.3mf'))
        coupon_scene.to_geometry().export(artifact_path(f'rail-native-dovetail-v{revision}-fit-test.stl'))
    report={'revision':revision,'method':'V6 Bambu-native mating planes reconstructed against V3 STEP, then exact CAD edge fillets',
        'source_v6_sha256':hashlib.sha256(V6.read_bytes()).hexdigest(),
        'settings':{'external_radius_mm':R_OUTER,'internal_radius_mm':R_INNER,'width_tolerance_mm':width_clearance,'depth_tolerance_mm':DEPTH_CLEARANCE,'groove_angle_degrees':2,'thickness_mm':THICKNESS},
        'joint_center_y_mm':CENTER_Y,'lower_base_y_mm':LOWER_BASE,'flank_slope':SLOPE,
        'filleted_edges':edge_report,'measured_fit_clearance':measured,'assembled_cad_overlap_mm3':overlap,
        'full':full_report,'test':test_report,'fit_status':('V7 coupon was tight and cracked and bowed the pin. V8 widens only the socket; physical fit remains unconfirmed.' if revision==8 else 'V6 was almost perfect but broke during insertion. V7 rounded fit remains physically unconfirmed.'),
        'pin_change_from_v7_mm3':pin_change,'source':{7:'source/round_native_dovetail.py',8:'source/widen_native_dovetail.py',9:'source/tune_native_dovetail.py'}[revision]}
    if revision==9:
        report['fit_status']='V7 at 0.10 mm was too tight and damaged the pin; V8 at 0.40 mm was too loose. V9 uses 0.20 mm total width clearance; physical fit unconfirmed.'
    approval=next(d for d in DESIGNS if d['id']=='elliptical')['selection'].get('approved_joint',{})
    if approval.get('revision')==f'v{revision}':
        report['physical_fit_approval']=approval
        report['fit_status']='Coupon fit approved by user: '+approval['user_feedback']
    (artifact_path(f'validation-native-dovetail-v{revision}.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'edges_per_half':10,'external_radius':R_OUTER,'internal_radius':R_INNER,'overlap_mm3':overlap,'clearance':measured},indent=2))

if __name__=='__main__':main()
