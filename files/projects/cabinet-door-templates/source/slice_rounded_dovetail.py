#!/usr/bin/env python3
"""Slice a rounded dovetail revision with the saved P1S settings, retaining precise source mesh vertices.

Bambu serializes vertices as floats and can collapse tiny triangles at fillet
poles. Keep the original mesh data in the sliced package after verifying matching
transforms, topology and sub-micron coordinate differences. G-code is untouched.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
from project_paths import artifact_path
from check_bambu_import import check_import

NS={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}


def retain_precision(source, sliced):
    with ZipFile(source) as z:original={n:z.read(n) for n in z.namelist()}
    with ZipFile(sliced) as z:contents={n:z.read(n) for n in z.namelist()}
    # Plate and component transforms must be identical before replacing meshes.
    src=ET.fromstring(original['3D/3dmodel.model']);dst=ET.fromstring(contents['3D/3dmodel.model'])
    for query in ['m:build/m:item','.//m:component']:
        assert [e.attrib for e in src.findall(query,NS)]==[e.attrib for e in dst.findall(query,NS)]
    max_error=0.
    for name,raw in original.items():
        if not name.startswith('3D/Objects/') or not name.endswith('.model'):continue
        before=ET.fromstring(raw);after=ET.fromstring(contents[name])
        assert [e.attrib for e in before.findall('.//m:triangle',NS)]==[e.attrib for e in after.findall('.//m:triangle',NS)]
        points=lambda doc:np.array([[float(e.get(k)) for k in ['x','y','z']] for e in doc.findall('.//m:vertex',NS)])
        error=float(np.abs(points(before)-points(after)).max());assert error<1e-4
        max_error=max(max_error,error)
        # Restore only the mesh, retaining Bambu's object metadata and IDs.
        for a,b in zip(before.findall('.//m:object',NS),after.findall('.//m:object',NS)):
            assert a.get('id')==b.get('id')
            mesh=a.find('m:mesh',NS)
            if mesh is not None:b.remove(b.find('m:mesh',NS));b.append(mesh)
        # Bambu requires unprefixed core tags and the declared production prefix.
        # Default ns0/ns1 serialization also leaves requiredextensions="p" unbound.
        ET.register_namespace('',NS['m'])
        ET.register_namespace('p','http://schemas.microsoft.com/3dmanufacturing/production/2015/06')
        contents[name]=ET.tostring(after,encoding='utf-8',xml_declaration=True)
    gcode={n:hashlib.sha256(raw).hexdigest() for n,raw in contents.items() if n.endswith('.gcode')}
    assert gcode
    with ZipFile(sliced,'w',ZIP_DEFLATED) as z:
        for name,raw in contents.items():z.writestr(name,raw)
    with ZipFile(sliced) as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(n)).hexdigest()==h for n,h in gcode.items())
    mesh=trimesh.load(sliced).to_geometry();baseline=trimesh.load(source).to_geometry()
    body_count=len(trimesh.load(source).geometry)
    assert mesh.is_watertight and len(mesh.split())==body_count
    assert np.allclose(mesh.bounds,baseline.bounds,atol=1e-8)
    assert abs(mesh.volume-baseline.volume)<1e-6
    return {'maximum_restored_coordinate_delta_mm':max_error,'watertight_bodies':body_count,'gcode_sha256':gcode,'bambu_final_import':check_import(sliced)}


def main(revision=8):
    report_path=artifact_path(f'validation-native-dovetail-v{revision}.json')
    report=json.loads(report_path.read_text())
    report['slicer_mesh_precision']={}
    for label,src,dest in [('test',f'rail-native-dovetail-v{revision}-fit-test.3mf',f'rail-native-dovetail-v{revision}-fit-test-sliced.3mf'),('full',f'rail-template-native-dovetail-v{revision}-bambu.3mf',f'rail-template-native-dovetail-v{revision}-sliced.3mf')]:
        with tempfile.TemporaryDirectory(prefix=f'cabinet-v{revision}-slice-') as tmp:
            with artifact_path(f'validation-native-v{revision}-{label}-slice.txt').open('w') as log:
                subprocess.run(['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio','--slice','0','--arrange','0','--orient','0','--export-3mf',dest,'--outputdir',tmp,str(artifact_path(src))],cwd=tmp,stdout=log,stderr=subprocess.STDOUT,check=True)
            output=Path(tmp)/dest
            report['slicer_mesh_precision'][label]=retain_precision(artifact_path(src),output)
            artifact_path(dest).write_bytes(output.read_bytes())
        print(f'Sliced and verified {label}',flush=True)
    report_path.write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--revision',type=int,choices=[8,9],default=8)
    main(parser.parse_args().revision)
