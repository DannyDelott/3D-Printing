#!/usr/bin/env python3
"""Reorient the saved Bambu project sideways, preserving settings and Z scale."""
from project_paths import artifact_path, artifact_url, publish_html
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import xml.etree.ElementTree as ET
import json
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
SOURCE=artifact_path('stile-template-left-dovetail-v2-before-arrangement.3mf')
TARGET=artifact_path('stile-template-left-dovetail-v2-bambu.3mf')
NS={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
ET.register_namespace('',NS['m'])
ET.register_namespace('p','http://schemas.microsoft.com/3dmanufacturing/production/2015/06')
ET.register_namespace('BambuStudio','http://schemas.bambulab.com/package/2021')
with ZipFile(SOURCE) as z:
    files={n:z.read(n) for n in z.namelist()}
root=ET.fromstring(files['3D/3dmodel.model'])
settings=ET.fromstring(files['Metadata/model_settings.config'])
report=[]
for i,item in enumerate(root.findall('m:build/m:item',NS)):
    original=np.array([float(n) for n in item.attrib['transform'].split()])
    # Both parts were vertical, unrotated in XY. Rotate 90 degrees about Z.
    assert np.allclose(original[:8],[1,0,0,0,1,0,0,0])
    transform=[0,1,0,-1,0,0,0,0,original[8],128,88+i*70,original[11]]
    item.set('transform',' '.join(f'{v:.9g}' for v in transform))
    obj=root.find(f"m:resources/m:object[@id='{item.attrib['objectid']}']/m:components/m:component",NS)
    mesh_xml=ET.fromstring(files[obj.attrib['{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}path'].lstrip('/')])
    vertices=np.array([[float(v.attrib[k]) for k in ['x','y','z']] for v in mesh_xml.findall('.//m:vertex',NS)])
    xyz=vertices@np.array(transform[:9]).reshape(3,3)+transform[9:]
    low,high=xyz.min(axis=0),xyz.max(axis=0)
    assert low[0]>1 and high[0]<255 and low[1]>50 and high[1]<210
    assert abs(low[2])<1e-5
    report.append({'object':item.attrib['objectid'],'bounds_mm':[low.tolist(),high.tolist()],'rotation_degrees':90})
    for assembly in settings.findall('assemble/assemble_item'):
        if assembly.get('object_id')==item.attrib['objectid'] and assembly.get('instance_id')=='0':assembly.set('transform',item.attrib['transform'])
assert report[1]['bounds_mm'][0][1]-report[0]['bounds_mm'][1][1]>12
files['3D/3dmodel.model']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
files['Metadata/model_settings.config']=ET.tostring(settings,encoding='utf-8',xml_declaration=True)
with ZipFile(TARGET,'w',ZIP_DEFLATED) as z:
    for n,content in files.items():z.writestr(n,content)
result={'source':SOURCE.name,'file':TARGET.name,'preserved':'Original mesh geometry, Z scale, filament, printer and process settings','parts':report,'front_clearance_mm':min(p['bounds_mm'][0][1] for p in report),'status':'Placement checked; slice in Bambu to refresh preview.'}
(artifact_path('validation-stile-arrangement.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
