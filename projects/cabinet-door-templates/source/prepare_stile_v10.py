#!/usr/bin/env python3
"""Narrow the stile dovetail without scaling depth, taper, radii or clearance."""
import json,hashlib,subprocess,tempfile
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import cadquery as cq
import numpy as np
import trimesh
from shapely.geometry import Polygon,LineString
from project_paths import artifact_path
from round_native_dovetail import mask,round_joint,export_mesh,CENTER_Y,LOWER_BASE,X_BASE,X_TIP,SLOPE,THICKNESS,DEPTH_CLEARANCE
from prepare_native_dovetail import write_project
from slice_rounded_dovetail import retain_precision

FULL='stile-template-left-dovetail-v10'
TEST='stile-dovetail-v10-fit-test'
WIDTH=57.15
SOCKET_WIDTH=37.
CLEARANCE=.2
COUPON_LENGTH=36.


def box(x0,x1,y0=0,y1=WIDTH):
    return cq.Workplane().box(x1-x0,y1-y0,THICKNESS,centered=(False,False,False)).val().translate((x0,y0,0))


def package(parts,stem):
    meshes={label:export_mesh(part,f'{stem}-{label}') for label,part in parts.items()}
    scene=trimesh.Scene()
    for label,g in meshes.items():scene.add_geometry(g,geom_name=label,node_name=label)
    artifact_path(stem+'.3mf').write_bytes(scene.export(file_type='3mf'))
    scene.to_geometry().export(artifact_path(stem+'.stl'))
    cq.exporters.export(cq.Compound.makeCompound(list(parts.values())),str(artifact_path(stem+'.step')))
    return meshes


def main():
    # Preserve all rail output bytes and historical stile files.
    protected=[artifact_path(n) for n in ['rail-template-native-dovetail-v10-bambu.3mf','rail-template-native-dovetail-v10-sliced.3mf','stile-template-left-dovetail-v9-sliced.3mf']]
    original_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    old_report=json.loads(artifact_path('validation-stiles.json').read_text())
    length=old_report['bounding_length_inches']*25.4;split=length/2
    source=cq.importers.importStep(str(artifact_path('stile-template-left-half-inch.step'))).val()
    original=source.rotate((0,0,0),(0,0,1),-90).translate((0,WIDTH,0))
    shift=(201.6125-split,CENTER_Y-WIDTH/2,0)
    stock=original.translate(shift)
    # Socket maximum width is specified at the bottom, including depth clearance.
    original_socket_lower=LOWER_BASE+(X_TIP-DEPTH_CLEARANCE-X_BASE)*SLOPE-CLEARANCE/2
    inset=CENTER_Y-SOCKET_WIDTH/2-original_socket_lower
    parts={};edge_report={}
    for label,socket in [('tongue',False),('socket',True)]:
        cut=stock.intersect(mask(socket,CLEARANCE,inset,(-100,600))).clean()
        rounded,edges=round_joint(cut,y_limits=(CENTER_Y-20,CENTER_Y+20),internal_x=X_TIP-DEPTH_CLEARANCE if socket else X_BASE)
        parts[label]=rounded.translate(tuple(-n for n in shift));edge_report[label]=edges
        assert parts[label].isValid() and len(parts[label].Solids())==1
    overlap=parts['tongue'].intersect(parts['socket']).Volume();assert overlap<1e-6
    meshes=package(parts,FULL)
    combined=trimesh.util.concatenate(list(meshes.values()))
    assert np.allclose(combined.extents,[length,WIDTH,THICKNESS],atol=1e-5)
    measurements=[]
    for z in [.5,6.35,12.2]:
        polygons={label:Polygon(max(g.section([0,0,1],[0,0,z]).discrete,key=len)[:,:2]) for label,g in meshes.items()}
        for x in [split-5,split,split+5]:
            line=LineString([(x,-1),(x,WIDTH+1)])
            male=polygons['tongue'].intersection(line);arms=sorted(polygons['socket'].intersection(line).geoms,key=lambda p:p.bounds[1])
            gaps=[male.bounds[1]-arms[0].bounds[3],arms[1].bounds[1]-male.bounds[3]]
            assert np.allclose(gaps,[.1,.1],atol=1e-5)
            measurements.append({'height_mm':z,'x_mm':x,'side_clearances_mm':gaps})
    vertices=meshes['socket'].vertices
    inner=vertices[(vertices[:,0]>split-6.351)&(vertices[:,0]<split+6.351)&(vertices[:,1]>1)&(vertices[:,1]<WIDTH-1)]
    measured_wall=min(inner[:,1].min(),WIDTH-inner[:,1].max())
    assert measured_wall>=9.9  # Nominal 10.075 mm; rounded entry lip removes ~0.14 mm.
    zone=box(split-20,split+20);joined=parts['tongue'].fuse(parts['socket'])
    missing=original.cut(zone).cut(joined).Volume();extra=joined.cut(original).Volume()
    assert missing<1e-5 and extra<1e-5
    coupon_box=box(split-COUPON_LENGTH/2,split+COUPON_LENGTH/2)
    coupon={label:p.intersect(coupon_box).clean() for label,p in parts.items()}
    for label,p in coupon.items():assert p.cut(parts[label]).Volume()<1e-6
    test_meshes=package(coupon,TEST)
    assert np.allclose(trimesh.util.concatenate(list(test_meshes.values())).extents,[COUPON_LENGTH,WIDTH,THICKNESS],atol=1e-5)
    with ZipFile(artifact_path('rail-template-native-dovetail-v9-bambu.3mf')) as z:files={n:z.read(n) for n in z.namelist()}
    report={'revision':10,'settings':{'width_tolerance_mm':CLEARANCE,'depth_tolerance_mm':DEPTH_CLEARANCE,'thickness_mm':THICKNESS,'external_radius_mm':.3,'internal_radius_mm':.2,'groove_angle_degrees':2},'maximum_nominal_socket_width_mm':SOCKET_WIDTH,'minimum_nominal_socket_side_wall_mm':(WIDTH-SOCKET_WIDTH)/2,'minimum_measured_socket_side_wall_mm':float(measured_wall),'previous_side_wall_mm':1.8077915818360175,'flank_inset_mm':inset,'split_mm':split,'dimensions_mm':[length,WIDTH,THICKNESS],'coupon_dimensions_mm':[COUPON_LENGTH,WIDTH,THICKNESS],'measured_clearance':measurements,'filleted_edges':edge_report,'assembled_overlap_mm3':overlap,'outline_preservation':{'missing_outside_joint_mm3':missing,'extra_outside_outline_mm3':extra},'coupon_extraction':'Exact intersections of full-size halves; full 57.15 mm stile width','physical_status':'New narrower stile joint: physical fit and arm stiffness unconfirmed','compatibility':'Do not mix with stile V9 or rail V9/V10 joint halves.'}
    for label,stem,items,positions in [('full',FULL,meshes,[(128,90),(128,166)]),('test',TEST,test_meshes,[(145,128),(105,128)])]:
        for g in items.values():g.apply_translation(-g.bounds.mean(axis=0))
        report[label]=write_project(files,items,positions,artifact_path(stem+'-bambu.3mf'),'Stile V10 '+label+' - narrower joint - test required')
        with tempfile.TemporaryDirectory(prefix='stile-v10-') as tmp:
            output=Path(tmp)/(stem+'-sliced.3mf')
            with artifact_path(f'validation-stile-v10-{label}-slice.txt').open('w') as log:
                subprocess.run(['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio','--slice','0','--arrange','0','--orient','0','--export-3mf',output.name,'--outputdir',tmp,str(artifact_path(stem+'-bambu.3mf'))],cwd=tmp,stdout=log,stderr=subprocess.STDOUT,check=True)
            report[label+'_precision']=retain_precision(artifact_path(stem+'-bambu.3mf'),output)
            artifact_path(output.name).write_bytes(output.read_bytes())
        with ZipFile(artifact_path(stem+'-sliced.3mf')) as z:
            info=ET.fromstring(z.read('Metadata/slice_info.config'));v={e.get('key'):e.get('value') for e in info.findall('plate/metadata')}
            assert v['outside']=='false' and v['support_used']=='false' and len(info.findall('plate/object'))==2
            report[label+'_slice']={'seconds':int(v['prediction']),'grams':float(v['weight']),'outside':False,'supports':False}
        print('Sliced and Bambu-import verified:',label,flush=True)
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==original_hashes[str(p)] for p in protected)
    report['unchanged_prior_artifacts']=original_hashes
    artifact_path('validation-stile-dovetail-v10.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['maximum_nominal_socket_width_mm','minimum_measured_socket_side_wall_mm','test_slice','full_slice']},indent=2))

if __name__=='__main__':main()
