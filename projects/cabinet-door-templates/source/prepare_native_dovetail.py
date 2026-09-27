#!/usr/bin/env python3
"""Validate the actual Bambu cut and extract its full-thickness fit sample.

The joint geometry comes from the archived Bambu native-cut project. This script
only joins touching exported shells (10 nm overlap at a coplanar seam), clips a
sample, and packages the meshes with the same printer/process/filament settings.
"""
from project_paths import artifact_path, artifact_url, publish_html
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
import manifold3d as mf
from shapely.geometry import Polygon, LineString

ROOT = Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--revision',type=int,default=5,choices=[5,6])
REV=parser.parse_args().revision
TOLERANCE={5:0.03,6:0.1}[REV]
SOURCE = artifact_path(f'native-v{REV}-source/native-cut-project.3mf')
NS = {'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
PROD = 'http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
ET.register_namespace('',NS['m'])
ET.register_namespace('p',PROD)
ET.register_namespace('BambuStudio','http://schemas.bambulab.com/package/2021')


def solid(mesh):
    value = mf.Manifold(mf.Mesh(np.asarray(mesh.vertices,dtype=np.float32),np.asarray(mesh.faces,dtype=np.uint32)))
    assert value.status() == mf.Error.NoError
    return value


def mesh(value):
    exported=value.simplify(0.00001).to_mesh64()
    result=trimesh.Trimesh(exported.vert_properties[:,:3],exported.tri_verts)
    assert result.is_watertight and result.is_winding_consistent
    assert len(result.split()) == 1
    return result


def write_project(files, meshes, positions, target, prefix):
    contents=dict(files)
    doc=ET.fromstring(contents['3D/3dmodel.model'])
    config=ET.fromstring(contents['Metadata/model_settings.config'])
    assert len(meshes)==len(positions)
    if len(meshes)!=len(doc.findall('m:build/m:item',NS)):
        # Reuse the saved process settings for a multi-coupon plate.
        from copy import deepcopy
        from uuid import uuid4
        resources=doc.find('m:resources',NS);build=doc.find('m:build',NS)
        template=deepcopy(resources.find('m:object',NS))
        component=template.find('m:components/m:component',NS)
        object_xml=ET.fromstring(contents[component.get('{'+PROD+'}path').lstrip('/')])
        metadata=deepcopy(config.find('object'))
        resources.clear();build.clear()
        for obj in config.findall('object'):config.remove(obj)
        plate=config.find('plate');assembly=config.find('assemble');assembly.clear()
        for instance in plate.findall('model_instance'):plate.remove(instance)
        for name in list(contents):
            if name.startswith('3D/Objects/'):del contents[name]
        rel_ns='http://schemas.openxmlformats.org/package/2006/relationships'
        relations=ET.Element('{'+rel_ns+'}Relationships')
        for i in range(len(meshes)):
            mesh_id,root_id=str(2*i+1),str(2*i+2)
            path=f'/3D/Objects/object_{i+1}.model'
            obj=deepcopy(template);obj.set('id',root_id);obj.set('{'+PROD+'}UUID',str(uuid4()))
            part=obj.find('m:components/m:component',NS)
            part.set('objectid',mesh_id);part.set('{'+PROD+'}path',path);part.set('{'+PROD+'}UUID',f'{i+1:04d}0000-b206-40ff-9872-83e8017abed1')
            resources.append(obj)
            mesh_doc=deepcopy(object_xml);mesh_doc.find('.//m:object',NS).set('id',mesh_id)
            contents[path.lstrip('/')]=ET.tostring(mesh_doc,encoding='utf-8',xml_declaration=True)
            ET.SubElement(build,'{'+NS['m']+'}item',{'objectid':root_id,'printable':'1','{'+PROD+'}UUID':f'{int(root_id):08d}-b1ec-4553-aec9-835e5b724bb4'})
            entry=deepcopy(metadata);entry.set('id',root_id);entry.find('part').set('id',mesh_id);entry.find('part').set('uuid',str(uuid4()));config.append(entry)
            instance=ET.SubElement(plate,'model_instance')
            for key,value in [('object_id',root_id),('instance_id','0'),('identify_id',str(20000+i))]:ET.SubElement(instance,'metadata',{'key':key,'value':value})
            ET.SubElement(assembly,'assemble_item',{'object_id':root_id,'instance_id':'0','offset':'0 0 0'})
            ET.SubElement(relations,'{'+rel_ns+'}Relationship',{'Target':path,'Id':f'rel-{i+1}','Type':'http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel'})
        ET.register_namespace('',rel_ns)
        contents['3D/_rels/3dmodel.model.rels']=ET.tostring(relations,encoding='utf-8',xml_declaration=True)
        ET.register_namespace('',NS['m'])
    report=[]
    for item, (label, geometry), (x,y) in zip(doc.findall('m:build/m:item',NS),meshes.items(),positions):
        object_id=item.get('objectid')
        component=doc.find(f"m:resources/m:object[@id='{object_id}']/m:components/m:component",NS)
        path=component.get('{'+PROD+'}path').lstrip('/')
        obj=ET.fromstring(contents[path])
        elem=obj.find('.//m:mesh',NS)
        elem.clear()
        vertices=ET.SubElement(elem,'{'+NS['m']+'}vertices')
        for point in geometry.vertices:
            ET.SubElement(vertices,'{'+NS['m']+'}vertex',dict(zip(['x','y','z'],[f'{v:.9g}' for v in point])))
        triangles=ET.SubElement(elem,'{'+NS['m']+'}triangles')
        for face in geometry.faces:
            ET.SubElement(triangles,'{'+NS['m']+'}triangle',dict(zip(['v1','v2','v3'],map(str,face))))
        contents[path]=ET.tostring(obj,encoding='utf-8',xml_declaration=True)
        translation=np.array([x,y,-geometry.bounds[0,2]])
        item.set('transform','1 0 0 0 1 0 0 0 1 '+' '.join(f'{v:.9g}' for v in translation))
        item.set('printable','1')
        bounds=geometry.bounds+translation
        assert np.all(bounds[0]>=-1e-4) and np.all(bounds[1]<=[256,256,256])
        metadata=config.find(f"object[@id='{object_id}']")
        for field in metadata.findall('.//metadata'):
            if field.get('key')=='name':field.set('value',prefix+' - '+label)
            if field.get('face_count') is not None:field.set('face_count',str(len(geometry.faces)))
        for stat in metadata.findall('.//mesh_stat'):stat.set('face_count',str(len(geometry.faces)))
        for assembly in config.findall('assemble/assemble_item'):
            if assembly.get('object_id')==object_id and assembly.get('instance_id')=='0':assembly.set('transform',item.get('transform'))
        report.append({'name':label,'bounds_mm':bounds.tolist(),'volume_mm3':geometry.volume,'watertight':True,'bodies':1})
    contents['3D/3dmodel.model']=ET.tostring(doc,encoding='utf-8',xml_declaration=True)
    contents['Metadata/model_settings.config']=ET.tostring(config,encoding='utf-8',xml_declaration=True)
    # Native cut provenance remains in SOURCE; derived samples are ordinary objects.
    contents.pop('Metadata/cut_information.xml',None)
    with ZipFile(target,'w',ZIP_DEFLATED) as z:
        for name,data in contents.items():
            if name.endswith('.png') or name=='Metadata/slice_info.config':continue
            z.writestr(name,data)
    with ZipFile(target) as z:assert z.testzip() is None
    imported=trimesh.load(target)
    assert len(imported.geometry)==len(meshes)
    assert all(g.is_watertight for g in imported.geometry.values())
    return report


def main():
    raw=trimesh.load(SOURCE)
    originals=list(raw.geometry.values())
    a,b=map(solid,originals)
    components=a.decompose()
    assert len(components)==2
    components.sort(key=lambda x:x.volume())
    tongue_bounds=np.array(components[0].bounding_box()).reshape(2,3)
    center_y=float(tongue_bounds[:,1].mean()-originals[0].bounds[0,1])
    # Bambu's native cut exports a tongue touching its backing at an unjoined
    # coplanar face. A 0.00001 mm overlap resolves the mesh seam, far below STL
    # and printer resolution. It is not a change to the designed fit allowance.
    a=components[1]+components[0].translate([0.00001,0,0])
    b=mf.Manifold.batch_boolean(b.decompose(),mf.OpType.Add)
    assert len(a.decompose())==len(b.decompose())==1
    full={'Right tongue':mesh(a),'Left socket':mesh(b)}
    # Reconstruct assembled coordinates from unchanged outside edges, not the
    # automatically arranged plate transforms.
    full['Right tongue'].apply_translation([403.225-full['Right tongue'].bounds[1,0],
                                          -full['Right tongue'].bounds[0,1],-full['Right tongue'].bounds[0,2]])
    full['Left socket'].apply_translation(-full['Left socket'].bounds[0])
    assembled={name:solid(g) for name,g in full.items()}
    measured=[]
    for z in [0.2,9.525,18.85]:
        sections={}
        for name,g in full.items():
            section=g.section(plane_origin=[0,0,z],plane_normal=[0,0,1])
            poly=Polygon(max(section.discrete,key=len)[:,:2])
            sections[name]=poly.intersection(LineString([(201.6125,0),(201.6125,100)]))
        tongue=np.array(sections['Right tongue'].coords)[:,1]
        ears=sorted(sections['Left socket'].geoms,key=lambda line:line.bounds[1])
        gaps=[float(tongue.min()-ears[0].bounds[3]),float(ears[1].bounds[1]-tongue.max())]
        assert abs(sum(gaps)-TOLERANCE)<0.0001
        measured.append({'height_mm':z,'side_gaps_mm':gaps,'total_width_clearance_mm':sum(gaps)})
    overlap=(assembled['Right tongue']^assembled['Left socket']).volume()
    # Single-precision export introduces micrometre-scale seam rounding.
    assert overlap<0.02
    box=mf.Manifold.cube([20.7,61,20]).translate([201.6125-10.35,center_y-30.5,-0.1])
    coupon={name:mesh(value^box) for name,value in assembled.items()}
    for name,g in coupon.items():
        assert abs(g.extents[2]-19.05)<0.0001
        # Every sample is clipped directly from its matching full-size native mesh.
        assert (solid(g)-assembled[name]).volume()<0.001
    for geometry in list(full.values())+list(coupon.values()):geometry.apply_translation(-geometry.bounds.mean(axis=0))
    with ZipFile(SOURCE) as z:files={n:z.read(n) for n in z.namelist()}
    full_path=artifact_path(f'rail-template-native-dovetail-v{REV}-bambu.3mf')
    test_path=artifact_path(f'rail-native-dovetail-v{REV}-fit-test.3mf')
    full_report=write_project(files,full,[(128,174),(128,50.7)],full_path,f'V{REV} native dovetail - fit test required')
    test_report=write_project(files,coupon,[(145,128),(110,128)],test_path,f'FIT TEST V{REV}')
    for name,g in full.items():g.export(artifact_path(f'rail-native-v{REV}-{name.lower().replace(" ","-")}.stl'))
    for name,g in coupon.items():g.export(artifact_path(f'rail-native-v{REV}-test-{name.lower().replace(" ","-")}.stl'))
    report={'source':str(SOURCE.relative_to(ROOT)),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'method':'Bambu Studio 2.8.2.60 native Cut / Dovetail, exported in the GUI',
        'settings':{'rotation_degrees':[90,0,90],'depth_mm':12.7,'width_mm':38.1,'flap_angle_degrees':60,'groove_angle_degrees':2,
                    'width_tolerance_mm':TOLERANCE,'depth_tolerance_mm':TOLERANCE},
        'measured_fit_clearance':measured,'joint_center_y_mm':center_y,'numerical_shell_join_overlap_mm':0.00001,'assembled_overlap_mm3':overlap,
        'full':full_report,'test':test_report,'fit_status':'UNCONFIRMED - print the extracted joint test before either full half',
        'existing_v4_compatibility':'Not compatible: the native dovetail changes shape and reverses which half contains the tongue.'}
    (artifact_path(f'validation-native-dovetail-v{REV}.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
