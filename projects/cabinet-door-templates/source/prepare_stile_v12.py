#!/usr/bin/env python3
"""Two labeled, tighter sockets around the exact V10 coupon tongue."""
import json,hashlib,subprocess,tempfile
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import cadquery as cq
import numpy as np
import trimesh
from shapely.geometry import Polygon,LineString
from project_paths import artifact_path
from prepare_stile_v10 import package,box,WIDTH,THICKNESS,COUPON_LENGTH
from round_native_dovetail import mask,round_joint,CENTER_Y,X_TIP,DEPTH_CLEARANCE
from prepare_native_dovetail import write_project
from slice_rounded_dovetail import retain_precision
from check_bambu_import import check_import

STEM='stile-dovetail-v12-comparison'

def main():
    protected=[artifact_path(n) for n in ['rail-template-native-dovetail-v10-sliced.3mf','stile-template-left-dovetail-v10-sliced.3mf','stile-dovetail-v10-fit-test-sliced.3mf']]
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    old=json.loads(artifact_path('validation-stile-dovetail-v10.json').read_text())
    split=old['split_mm'];shift=(201.6125-split,CENTER_Y-WIDTH/2,0)
    # Keep this intercept fixed: recalculating it for each clearance would change the tail.
    inset=old['flank_inset_mm']
    tongue=cq.importers.importStep(str(artifact_path('stile-dovetail-v10-fit-test-tongue.step'))).val()
    old_socket=cq.importers.importStep(str(artifact_path('stile-dovetail-v10-fit-test-socket.step'))).val()
    stock=box(split-COUPON_LENGTH/2,split+COUPON_LENGTH/2).translate(shift)
    with ZipFile(artifact_path('stile-dovetail-v10-fit-test-bambu.3mf')) as z:files={n:z.read(n) for n in z.namelist()}
    all_meshes={};all_shapes=[];report={'revision':12,'scope':'Fit coupons only; full stile and rail files unchanged','width_clearances_mm':[.05,.00],'thickness_mm':THICKNESS,'depth_clearance_mm':DEPTH_CLEARANCE,'taper_degrees':2,'external_radius_mm':.3,'internal_radius_mm':.2,'coupon_assembled_dimensions_mm':[36,WIDTH,THICKNESS],'pairs':[],'physical_status':'V11 0.15 and 0.10 mm slide back out through thickness. V12 friction-fit retention remains untested'}
    for clearance,tag,y in [(.05,'005',90),(.00,'000',166)]:
        cut=stock.intersect(mask(True,clearance,inset,(-100,600))).clean()
        rounded,edges=round_joint(cut,y_limits=(CENTER_Y-20,CENTER_Y+20),internal_x=X_TIP-DEPTH_CLEARANCE)
        socket=rounded.translate(tuple(-n for n in shift))
        # Engrave the socket backbone, away from its arms and mating surfaces.
        lettering=cq.Workplane('XY').text(f'.{tag[1:]}',4,.5,font='Arial',combine=True).val().rotate((0,0,0),(0,0,1),90).translate((split-14,WIDTH/2,THICKNESS-.4))
        assert socket.intersect(lettering).Volume()>0
        socket=socket.cut(lettering).clean()
        assert socket.isValid() and len(socket.Solids())==1
        parts={'tongue':tongue,'socket':socket};stem=f'stile-dovetail-v12-{tag}'
        meshes=package(parts,stem)
        samples=[]
        for z in [.5,6.35,12.2]:
            polys={k:Polygon(max(g.section([0,0,1],[0,0,z]).discrete,key=len)[:,:2]) for k,g in meshes.items()}
            for x in [split-5,split,split+5]:
                line=LineString([(x,-1),(x,WIDTH+1)])
                male=polys['tongue'].intersection(line);arms=sorted(polys['socket'].intersection(line).geoms,key=lambda p:p.bounds[1])
                gaps=[male.bounds[1]-arms[0].bounds[3],arms[1].bounds[1]-male.bounds[3]]
                assert np.allclose(gaps,[clearance/2]*2,atol=1e-5)
                samples.append({'z_mm':z,'x_mm':x,'side_clearances_mm':gaps})
        assert socket.intersect(tongue).Volume()<1e-6
        # Outside the joint and the engraved label, the coupon stays identical.
        label_zone=box(split-18,split-10);joint_zone=box(split-7,split+7)
        a=socket.cut(label_zone).cut(joint_zone);b=old_socket.cut(label_zone).cut(joint_zone)
        assert a.cut(b).Volume()+b.cut(a).Volume()<1e-6
        assert tongue.cut(parts['tongue']).Volume()==0
        for part,g in meshes.items():
            g.apply_translation(-g.bounds.mean(axis=0))
            label=f'{clearance:.2f} mm - {part}'
            all_meshes[label]=g.copy()
            x=145 if part=='tongue' else 105
            # Combined STEP/STL share the arranged print coordinates.
            all_shapes.append(parts[part].translate(tuple(np.array([x,y,THICKNESS/2])-np.array(parts[part].BoundingBox().center.toTuple()))))
        positions=[(145,y),(105,y)]
        write_project(files,meshes,positions,artifact_path(stem+'-bambu.3mf'),f'Stile V12 {clearance:.2f} mm')
        imported=check_import(artifact_path(stem+'-bambu.3mf'))
        report['pairs'].append({'clearance_mm':clearance,'socket_engraving':f'.{tag[1:]}','plate_center_y_mm':y,'maximum_nominal_socket_width_mm':37-(.2-clearance),'minimum_nominal_arm_mm':10.075+(.2-clearance)/2,'measurements':samples,'engraving_depth_mm':.4,'bambu_import':imported,'filleted_edges':edges})
        print('Verified coupon:',clearance,flush=True)
    positions=[(145,90),(105,90),(145,166),(105,166)]
    report['placement']=write_project(files,all_meshes,positions,artifact_path(STEM+'-bambu.3mf'),'Stile V12 comparison')
    scene=trimesh.load(artifact_path(STEM+'-bambu.3mf'))
    artifact_path(STEM+'.3mf').write_bytes(scene.export(file_type='3mf'))
    scene.to_geometry().export(artifact_path(STEM+'.stl'))
    cq.exporters.export(cq.Compound.makeCompound(all_shapes),str(artifact_path(STEM+'.step')))
    with tempfile.TemporaryDirectory(prefix='stile-v12-') as tmp:
        output=Path(tmp)/(STEM+'-sliced.3mf')
        with artifact_path('validation-stile-v12-slice.txt').open('w') as log:
            subprocess.run(['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio','--slice','0','--arrange','0','--orient','0','--export-3mf',output.name,'--outputdir',tmp,str(artifact_path(STEM+'-bambu.3mf'))],cwd=tmp,stdout=log,stderr=subprocess.STDOUT,check=True)
        report['precision']=retain_precision(artifact_path(STEM+'-bambu.3mf'),output)
        artifact_path(output.name).write_bytes(output.read_bytes())
    with ZipFile(artifact_path(STEM+'-sliced.3mf')) as z:
        info=ET.fromstring(z.read('Metadata/slice_info.config'));v={e.get('key'):e.get('value') for e in info.findall('plate/metadata')}
        assert v['outside']=='false' and v['support_used']=='false' and len(info.findall('plate/object'))==4
        report['test_slice']={'seconds':int(v['prediction']),'grams':float(v['weight']),'outside':False,'supports':False}
    socket_meshes={k:g for k,g in all_meshes.items() if k.endswith('socket')}
    socket_stem='stile-dovetail-v12-sockets'
    report['socket_placement']=write_project(files,socket_meshes,[(128,90),(128,166)],artifact_path(socket_stem+'-bambu.3mf'),'Stile V12 sockets - reuse V11 tail')
    socket_scene=trimesh.load(artifact_path(socket_stem+'-bambu.3mf'))
    artifact_path(socket_stem+'.3mf').write_bytes(socket_scene.export(file_type='3mf'))
    socket_scene.to_geometry().export(artifact_path(socket_stem+'.stl'))
    cq.exporters.export(cq.Compound.makeCompound([s.translate((23,0,0)) for s in all_shapes[1::2]]),str(artifact_path(socket_stem+'.step')))
    check_import(artifact_path(socket_stem+'-bambu.3mf'))
    with tempfile.TemporaryDirectory(prefix='stile-v12-sockets-') as tmp:
        output=Path(tmp)/(socket_stem+'-sliced.3mf')
        with artifact_path('validation-stile-v12-sockets-slice.txt').open('w') as log:
            subprocess.run(['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio','--slice','0','--arrange','0','--orient','0','--export-3mf',output.name,'--outputdir',tmp,str(artifact_path(socket_stem+'-bambu.3mf'))],cwd=tmp,stdout=log,stderr=subprocess.STDOUT,check=True)
        retain_precision(artifact_path(socket_stem+'-bambu.3mf'),output)
        artifact_path(output.name).write_bytes(output.read_bytes())
    with ZipFile(artifact_path(socket_stem+'-sliced.3mf')) as z:
        info=ET.fromstring(z.read('Metadata/slice_info.config'));v={e.get('key'):e.get('value') for e in info.findall('plate/metadata')}
        assert v['outside']=='false' and v['support_used']=='false' and len(info.findall('plate/object'))==2
        report['sockets_slice']={'seconds':int(v['prediction']),'grams':float(v['weight']),'outside':False,'supports':False}
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p)] for p in protected)
    report['preserved_artifacts']=hashes
    artifact_path('validation-stile-v12.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Finished',report['test_slice'])

if __name__=='__main__':main()
