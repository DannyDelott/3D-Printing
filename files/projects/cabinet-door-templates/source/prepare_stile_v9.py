#!/usr/bin/env python3
"""Transfer the physically approved rail V9 joint to the existing stile outline.

Copy the exact rounded STEP joint locally, extend the two masks with stock beyond
that region, then intersect the stile. No mating plane or radius is recalculated.
"""
import hashlib,json
from zipfile import ZipFile
import cadquery as cq
import numpy as np
import trimesh
from shapely.geometry import Polygon,LineString
from project_paths import artifact_path
from round_native_dovetail import CENTER_Y,THICKNESS,export_mesh
from prepare_native_dovetail import write_project

NAME='stile-template-left-dovetail-v9'

def box(x0,x1,y0,y1):
    return cq.Workplane().box(x1-x0,y1-y0,THICKNESS,centered=(False,False,False)).val().translate((x0,y0,0))

def main():
    report=json.loads(artifact_path('validation-stiles.json').read_text())
    width=report['stile_width_inches']*25.4
    length=report['bounding_length_inches']*25.4
    split=length/2
    source=cq.importers.importStep(str(artifact_path('stile-template-left-half-inch.step'))).val()
    horizontal=source.rotate((0,0,0),(0,0,1),-90)
    # The unsplit STEP is normalized to x/y=0; rotate then move width into +Y.
    horizontal=horizontal.translate((0,width,0))
    shift=(201.6125-split,CENTER_Y-width/2,0)
    stock=horizontal.translate(shift)
    y0,y1=CENTER_Y-width/2,CENTER_Y+width/2
    # All fillets lie between x=194 and209; these boundaries are in solid stock.
    joint_window=box(190,212,y0,y1)
    parts={};geometry={};proof={}
    for label,rail_label in [('tongue','right-tongue'),('socket','left-socket')]:
        path=artifact_path(f'rail-native-v9-{rail_label}.step')
        rail=cq.importers.importStep(str(path)).val()
        local=rail.intersect(joint_window).clean()
        extension=box(212,600,y0,y1) if label=='tongue' else box(-100,190,y0,y1)
        mask=local.fuse(extension).clean()
        part=stock.intersect(mask).clean()
        assert part.isValid() and len(part.Solids())==1
        # Symmetric CAD difference proves every local mating surface is identical.
        clipped=part.intersect(joint_window)
        difference=clipped.cut(local).Volume()+local.cut(clipped).Volume()
        assert difference<1e-5,difference
        assert part.cut(stock).Volume()<1e-5
        proof[label]={'source_rail_step_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'local_joint_difference_mm3':difference}
        parts[label]=part.translate(tuple(-n for n in shift))
        geometry[label]=export_mesh(parts[label],f'{NAME}-{label}')
    overlap=parts['tongue'].intersect(parts['socket']).Volume();assert overlap<1e-6
    gaps=[]
    for z in [.5,6.35,12.2]:
        sections={}
        for label,g in geometry.items():
            loops=g.section([0,0,1],[0,0,z]).discrete
            p=Polygon(max(loops,key=len)[:,:2])
            sections[label]=p.intersection(LineString([(split,-1),(split,width+1)]))
        male=np.array(sections['tongue'].coords)[:,1]
        ears=sorted(sections['socket'].geoms,key=lambda l:l.bounds[1])
        pair=[male.min()-ears[0].bounds[3],ears[1].bounds[1]-male.max()]
        assert np.allclose(pair,[.1,.1],atol=1e-5)
        gaps.append({'height_mm':z,'side_clearances_mm':pair})
    assembled=trimesh.Scene()
    for label,g in geometry.items():assembled.add_geometry(g,geom_name=label,node_name=label)
    artifact_path(f'{NAME}.3mf').write_bytes(assembled.export(file_type='3mf'))
    assembled.to_geometry().export(artifact_path(f'{NAME}.stl'))
    cq.exporters.export(cq.Compound.makeCompound(list(parts.values())),str(artifact_path(f'{NAME}.step')))
    assert np.allclose(assembled.extents,[length,width,THICKNESS],atol=1e-5)
    for g in geometry.values():g.apply_translation(-g.bounds.mean(axis=0))
    with ZipFile(artifact_path('rail-template-native-dovetail-v9-bambu.3mf')) as z:files={n:z.read(n) for n in z.namelist()}
    placement=write_project(files,geometry,[(128,90),(128,166)],artifact_path(f'{NAME}-bambu.3mf'),'V9 stile - approved 0.20 mm dovetail')
    # The widest socket lies on its bottom plane; include its retained depth gap.
    rail_report=json.loads(artifact_path('validation-native-dovetail-v9.json').read_text())
    socket_tip=201.6125-6.35
    lower_tip=rail_report['lower_base_y_mm']+(socket_tip-(201.6125+6.35))*rail_report['flank_slope']-.1
    side_wall=lower_tip-y0
    assert side_wall>0
    result={'revision':9,'joint':'Exact approved V9 rail joint, transferred without scaling','thickness_mm':THICKNESS,'width_clearance_mm':.2,'depth_clearance_mm':.1,'external_radius_mm':.3,'internal_radius_mm':.2,'taper_degrees':2,'dimensions_mm':[length,width,THICKNESS],'split_mm':split,'measured_clearance':gaps,'joint_identity':proof,'assembled_overlap_mm3':overlap,'minimum_nominal_socket_side_wall_mm':side_wall,'parts':placement,'physical_status':'V9 coupon fit approved by user; full stile strength untested','note':'The 57.15 mm stile leaves approximately %.2f mm of material beside the widest socket. The fit coupon is wider; its approval does not establish full stile strength.'%side_wall,'rotation_reuse':'Rotate the assembled template 180 degrees in plane for the opposite stile.'}
    artifact_path('validation-stile-dovetail-v9.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
