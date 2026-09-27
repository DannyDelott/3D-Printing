#!/usr/bin/env python3
"""Split the exact left V1 stile; retain the rail's sliding dovetail dimensions."""
from project_paths import artifact_path, artifact_url, publish_html
import json
import math
import numpy as np
import trimesh
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Cut
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.STEPControl import STEPControl_Reader
from OCP.IFSelect import IFSelect_RetDone
from OCP.gp import gp_Trsf, gp_Vec, gp_Ax1, gp_Pnt, gp_Dir
from generate_template import ROOT, export
from generate_dovetail import prism, offset_polygon, volume, HEAD, NECK, DEPTH, CLEARANCE, THICKNESS

NAME='stile-template-left-dovetail-v2'

def main():
    report=json.loads((artifact_path('validation-stiles.json')).read_text())
    length=report['bounding_length_inches']*25.4
    width=report['stile_width_inches']*25.4
    split=(length-DEPTH)/2
    reader=STEPControl_Reader()
    assert reader.ReadFile(str(artifact_path('stile-template-left-v1.step')))==IFSelect_RetDone
    reader.TransferRoots();original=reader.OneShape()
    transform=gp_Trsf();transform.SetTranslation(gp_Vec(0,-report['left_assembly_y_inches'][0]*25.4,0))
    original=BRepBuilderAPI_Transform(original,transform,True).Shape()
    transform.SetRotation(gp_Ax1(gp_Pnt(0,0,0),gp_Dir(0,0,1)),-math.pi/2)
    original=BRepBuilderAPI_Transform(original,transform,True).Shape()
    transform.SetTranslation(gp_Vec(0,width,0))
    original=BRepBuilderAPI_Transform(original,transform,True).Shape()
    cy=width/2
    boundary=[(-10,-10),(split,-10),(split,cy-NECK/2),(split+DEPTH,cy-HEAD/2),(split+DEPTH,cy+HEAD/2),(split,cy+NECK/2),(split,width+10),(-10,width+10)]
    parts=[BRepAlgoAPI_Common(original,prism(boundary)).Shape(),BRepAlgoAPI_Cut(original,prism(offset_polygon(boundary,CLEARANCE))).Shape()]
    assert volume(BRepAlgoAPI_Common(*parts).Shape())<1e-5
    assert all(volume(BRepAlgoAPI_Cut(part,original).Shape())<1e-5 for part in parts)
    removed=volume(original)-sum(volume(p) for p in parts)
    assert 0<removed<1000
    assert split-CLEARANCE>length/2-44.45 and split+DEPTH+CLEARANCE<length/2+44.45
    info={};meshes=[]
    for label,part in zip(['tongue','socket'],parts):
        info[label]=export(part,f'{NAME}-{label}')
        assert max(info[label]['size_mm'][:2])<256
        meshes.append(trimesh.load(artifact_path(f'{NAME}-{label}.stl'),force='mesh'))
    assembled=[m.copy() for m in meshes];assembled[1].apply_translation([split+CLEARANCE,0,0])
    scene=trimesh.Scene()
    for label,mesh in zip(['Stile - dovetail tongue','Stile - dovetail socket'],assembled):scene.add_geometry(mesh,node_name=label,geom_name=label)
    (artifact_path(f'{NAME}.3mf')).write_bytes(scene.export(file_type='3mf'))
    loaded=trimesh.load(artifact_path(f'{NAME}.3mf'))
    assert len(loaded.geometry)==2 and np.allclose(loaded.extents,[length,width,THICKNESS],atol=1e-4)
    # Independent objects, flat and side by side near the middle of the P1S plate.
    arranged=trimesh.Scene()
    for i,mesh in enumerate(meshes):
        m=mesh.copy();m.apply_transform(trimesh.transformations.rotation_matrix(math.pi,[0,0,1]));m.apply_translation(-m.bounds[0]);m.apply_translation([(256-m.extents[0])/2,88+i*70-m.extents[1]/2,0])
        assert np.all(m.bounds[0]>=-1e-5) and np.all(m.bounds[1]<=[256,256,256])
        arranged.add_geometry(m,geom_name=['Stile tongue','Stile socket'][i])
    (artifact_path(f'{NAME}-plate.3mf')).write_bytes(arranged.export(file_type='3mf'))
    result={'revision':NAME,'source':'stile-template-left-v1.step','split_from_short_end_mm':split,'midpoint_shift_mm':length/2-split,'head_width_mm':HEAD,'neck_width_mm':NECK,'engagement_mm':DEPTH,'normal_clearance_mm':CLEARANCE,'solid_band_mm':88.9,'parts':info,'removed_clearance_volume_mm3':removed,'status':'Valid CAD, watertight halves, two independent objects; physical fit untested.'}
    (artifact_path('validation-stile-dovetail-v2.json')).write_text(json.dumps(result,indent=2)+'\n')
    displayed=[m.copy() for m in assembled];displayed[1].apply_translation([12,0,0]);combined=trimesh.util.concatenate(displayed)
    vertices=np.concatenate([combined.triangles-combined.bounds.mean(axis=0),np.repeat(combined.face_normals[:,None,:],3,axis=1)],axis=2)
    data={'file':NAME,'vertices':vertices.reshape(-1).round(6).tolist(),'view_bounds_mm':combined.extents.tolist()}
    source=(ROOT/'source/comparison.html.in').read_text();viewer=source[source.index('function startPreview()'):source.index('</script>')]
    paths=[]
    for mesh,color in zip(assembled,['#cba778','#789b94']):
        triangles=mesh.triangles[mesh.face_normals[:,2]>.99,:,:2]
        d=' '.join('M'+' L'.join(f'{x:.3f},{-y:.3f}' for x,y in tri)+' Z' for tri in triangles)
        paths.append(f'<path d="{d}" fill="{color}"/>')
    template=(ROOT/'source/stile-dovetail.html.in').read_text()
    html=template.replace('NAME',NAME).replace('PATHS',''.join(paths)).replace('SPLIT',f'{split:.3f}').replace('LENGTH',f'{length:.3f}').replace('PARTSIZE',f"{info['tongue']['size_mm'][0]:.3f} / {info['socket']['size_mm'][0]:.3f}").replace('DATA',json.dumps(data,separators=(',',':'))).replace('VIEWER',viewer)
    publish_html(artifact_path('stile-dovetail-v2.html'), html)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
