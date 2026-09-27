#!/usr/bin/env python3
"""Add a fifth matching short-side hexagon, preserving the approved V9 joint."""
import json,math,hashlib,subprocess,tempfile
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import cadquery as cq
import numpy as np
import trimesh
from shapely.geometry import Polygon
from project_paths import artifact_path
from round_native_dovetail import export_mesh,THICKNESS
from prepare_native_dovetail import write_project
from slice_rounded_dovetail import retain_precision

FLATS=25.2

def prism(points):
    return cq.Workplane('XY').polyline(points).close().extrude(THICKNESS).val()

def box(x0,x1):
    return cq.Workplane().box(x1-x0,200,THICKNESS,centered=(False,False,False)).val().translate((x0,0,0))

def main():
    # Keep the first center and a 28 mm horizontal / 22 mm vertical stagger.
    radius=FLATS/math.sqrt(3);first=10+32/math.sqrt(3)
    left=[(first+28*i,26+22*(i%2)) for i in range(5)]
    pitch=35.2;xp=pitch*math.sqrt(3)/2
    right=[(first+col*xp,26+row*pitch+(col%2)*pitch/2) for col in range(8,12) for row in range(2)]
    centers=left+right
    holes=[[(x+radius*math.cos(k*math.pi/3),y+radius*math.sin(k*math.pi/3)) for k in range(6)] for x,y in centers]
    outline=cq.importers.importStep(str(artifact_path('rail-template-elliptical-solid-half-inch.step'))).val()
    new=outline
    for points in holes:new=new.cut(prism(points))
    new=new.clean();assert new.isValid() and len(new.Solids())==1
    # Measured CAD distance from every opening to the original routing perimeter.
    face=max([f for f in outline.Faces() if abs(f.Center().z)<1e-5],key=lambda f:f.Area())
    rim=min(cq.Wire.makePolygon([cq.Vector(x,y,0) for x,y in points],close=True).distance(face.outerWire()) for points in holes)
    polygons=list(map(Polygon,holes))
    web=min(a.distance(b) for i,a in enumerate(polygons) for b in polygons[i+1:])
    assert rim>=10-1e-6 and web>=10-1e-6,(rim,web)
    assert max(x for pts in holes[:5] for x,y in pts)<157.1625
    assert min(x for pts in holes[5:] for x,y in pts)>246.0625
    unsplit=export_mesh(new,'rail-template-elliptical-honeycomb-v10')
    artifact_path('rail-template-elliptical-honeycomb-v10.3mf').write_bytes(unsplit.export(file_type='3mf'))
    shapes={};meshes={};proof={}
    for label,part in [('Right tongue','right-tongue'),('Left socket','left-socket')]:
        old_path=artifact_path(f'rail-native-v9-{part}.step');old=cq.importers.importStep(str(old_path)).val()
        if part=='right-tongue':shape=old
        else:
            mask=old.intersect(box(190,212)).fuse(box(-1,190)).clean()
            shape=new.intersect(mask).clean()
        assert shape.isValid() and len(shape.Solids())==1
        local=box(185,220);a=shape.intersect(local);b=old.intersect(local)
        delta=a.cut(b).Volume()+b.cut(a).Volume();assert delta<1e-5
        proof[part]={'joint_difference_from_v9_mm3':delta,'source_sha256':hashlib.sha256(old_path.read_bytes()).hexdigest()}
        shapes[label]=shape;meshes[label]=export_mesh(shape,f'rail-native-v10-{part}')
    assert shapes['Right tongue'].intersect(shapes['Left socket']).Volume()<1e-6
    scene=trimesh.Scene()
    for label,g in meshes.items():scene.add_geometry(g,geom_name=label,node_name=label)
    artifact_path('rail-template-native-dovetail-v10.3mf').write_bytes(scene.export(file_type='3mf'))
    scene.to_geometry().export(artifact_path('rail-template-native-dovetail-v10.stl'))
    cq.exporters.export(cq.Compound.makeCompound(list(shapes.values())),str(artifact_path('rail-template-native-dovetail-v10.step')))
    for g in meshes.values():g.apply_translation(-g.bounds.mean(axis=0))
    with ZipFile(artifact_path('rail-template-native-dovetail-v9-bambu.3mf')) as z:files={n:z.read(n) for n in z.namelist()}
    placement=write_project(files,meshes,[(128,174),(128,50.7)],artifact_path('rail-template-native-dovetail-v10-bambu.3mf'),'V10 rail - approved V9 joint - 13 hexagons')
    with tempfile.TemporaryDirectory(prefix='rail-v10-slice-') as tmp:
        output=Path(tmp)/'rail-template-native-dovetail-v10-sliced.3mf'
        with artifact_path('validation-rail-v10-slice.txt').open('w') as log:
            subprocess.run(['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio','--slice','0','--arrange','0','--orient','0','--export-3mf',output.name,'--outputdir',tmp,str(artifact_path('rail-template-native-dovetail-v10-bambu.3mf'))],cwd=tmp,stdout=log,stderr=subprocess.STDOUT,check=True)
        precision=retain_precision(artifact_path('rail-template-native-dovetail-v10-bambu.3mf'),output)
        artifact_path(output.name).write_bytes(output.read_bytes())
    with ZipFile(artifact_path('rail-template-native-dovetail-v10-sliced.3mf')) as z:
        xml=ET.fromstring(z.read('Metadata/slice_info.config'));v={e.get('key'):e.get('value') for e in xml.findall('plate/metadata')}
        assert v['outside']=='false' and v['support_used']=='false'
    report={'revision':10,'hole_count':13,'short_side_holes':5,'tall_side_holes':8,'hole_across_flats_mm':FLATS,'hole_centers_mm':centers,'minimum_web_mm':web,'minimum_perimeter_rim_mm':rim,'solid_band_x_mm':[157.1625,246.0625],'split_x_mm':201.6125,'thickness_mm':12.7,'mesh':{'size_mm':unsplit.extents.tolist()},'approved_joint_revision':9,'width_clearance_mm':.2,'joint_identity':proof,'parts':placement,'slice':{'seconds':int(v['prediction']),'grams':float(v['weight']),'outside':False,'supports':False},'slicer_mesh_precision':precision,'physical_status':'Unchanged V9 joint fit approved from coupon; revised full rail untested'}
    artifact_path('validation-rail-v10.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['hole_count','minimum_web_mm','minimum_perimeter_rim_mm','joint_identity','slice']},indent=2))

if __name__=='__main__':main()
