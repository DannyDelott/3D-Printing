"""Build a native Bambu project from the oriented meshes and slice supports-off.

Uses the locally installed Bambu Studio and the recorded P1S/PLA profile.
Does not contact or start a printer. Outputs stay outside the model catalog.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import copy
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET

import trimesh

PROJECT = Path(__file__).resolve().parents[1]
CORE = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
PROD = 'http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
REL = 'http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel'
ET.register_namespace('', CORE)
ET.register_namespace('p', PROD)


def package(stem, supports=False, support_parts=None):
    source = PROJECT / 'models' / f'{stem}.3mf'
    out = PROJECT / 'print-checks' / (stem + ('-supports' if supports else ''))
    out.mkdir(parents=True, exist_ok=True)
    scene = trimesh.load(source)
    offset = [128-(scene.bounds[0,i]+scene.bounds[1,i])/2 for i in (0,1)]
    transform = f'1 0 0 0 1 0 0 0 1 {offset[0]} {offset[1]} 0'
    root = ET.Element(f'{{{CORE}}}model', unit='millimeter')
    ET.SubElement(root,f'{{{CORE}}}metadata',name='Application').text='BambuStudio-02.08.02.60'
    ET.SubElement(root,f'{{{CORE}}}metadata',name='BambuStudio:3mfVersion').text='1'
    resources = ET.SubElement(root,f'{{{CORE}}}resources')
    build = ET.SubElement(root,f'{{{CORE}}}build')
    config = ET.Element('config')
    plate = ET.SubElement(config,'plate')
    ET.SubElement(plate,'metadata',key='plater_id',value='1')
    ET.SubElement(plate,'metadata',key='locked',value='false')
    entries = {}
    relationships = []
    with ZipFile(source) as z:
        raw = ET.fromstring(z.read('3D/3dmodel.model'))
    # The generator bakes layout translations into mesh vertices.
    for item in raw.find(f'{{{CORE}}}build'):
        assert item.get('transform','1 0 0 0 1 0 0 0 1 0 0 0').split() in (
            '1 0 0 0 1 0 0 0 1 0 0 0'.split(),
            '1.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0'.split())
    for index,mesh_obj in enumerate(raw.findall(f'{{{CORE}}}resources/{{{CORE}}}object')):
        mesh_id,object_id = str(index*2+1),str(index*2+2)
        mesh_obj = copy.deepcopy(mesh_obj)
        mesh_obj.set('id',mesh_id)
        for attr in ('pid','pindex'):
            mesh_obj.attrib.pop(attr,None)
        path = f'/3D/Objects/object_{object_id}.model'
        child = ET.Element(f'{{{CORE}}}model',unit='millimeter')
        ET.SubElement(child,f'{{{CORE}}}resources').append(mesh_obj)
        entries[path[1:]] = ET.tostring(child)
        obj = ET.SubElement(resources,f'{{{CORE}}}object',id=object_id,type='model')
        components = ET.SubElement(obj,f'{{{CORE}}}components')
        ET.SubElement(components,f'{{{CORE}}}component',{
            f'{{{PROD}}}path':path,'objectid':mesh_id,'transform':'1 0 0 0 1 0 0 0 1 0 0 0'})
        ET.SubElement(build,f'{{{CORE}}}item',objectid=object_id,transform=transform,printable='1')
        settings_obj = ET.SubElement(config,'object',id=object_id)
        name = mesh_obj.get('name',stem)
        ET.SubElement(settings_obj,'metadata',key='name',value=name)
        ET.SubElement(settings_obj,'metadata',key='extruder',value='1')
        if support_parts is not None:
            assert supports, 'Per-object supports require support generation enabled'
            ET.SubElement(settings_obj,'metadata',key='enable_support',value=str(int(name in support_parts)))
        part = ET.SubElement(settings_obj,'part',id=mesh_id,subtype='normal_part')
        ET.SubElement(part,'metadata',key='name',value=name)
        instance = ET.SubElement(plate,'model_instance')
        for key,value in [('object_id',object_id),('instance_id','0'),('identify_id',str(index+1))]:
            ET.SubElement(instance,'metadata',key=key,value=value)
        relationships.append(f'<Relationship Target="{path}" Id="rel-{index+1}" Type="{REL}"/>')
    settings = json.loads((PROJECT/'print-checks/p1s-pla-settings.json').read_text())
    assert settings['enable_support']=='0'
    if supports:
        settings['enable_support']='1'
        settings['support_type']='normal(auto)'
        settings['support_on_build_plate_only']='0'
    entries.update({
        '3D/3dmodel.model':ET.tostring(root),
        'Metadata/model_settings.config':ET.tostring(config),
        'Metadata/project_settings.config':json.dumps(settings),
        '[Content_Types].xml':'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>',
        '_rels/.rels':f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="{REL}"/></Relationships>',
        '3D/_rels/3dmodel.model.rels':'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join(relationships)+'</Relationships>',
    })
    project = out / f'{stem}-configured.3mf'
    with ZipFile(project,'w',ZIP_DEFLATED) as z:
        for name,data in entries.items():z.writestr(name,data)
    with (out/'slice.log').open('w') as log:
        subprocess.run(['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio',
            '--orient','0','--arrange','0','--slice','0','--export-3mf',f'{stem}-sliced.3mf',
            '--outputdir',str(out),str(project)],stdout=log,stderr=subprocess.STDOUT,check=True)
    result = json.loads((out/'result.json').read_text())
    assert result['return_code']==0
    code = (out/'plate_1.gcode').read_text()
    assert f'; enable_support = {int(supports)}' in code
    if not supports: assert '; FEATURE: Support' not in code
    evidence = dict(model_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        supports_disabled=not supports,support_toolpaths=code.count('; FEATURE: Support'),
        warnings=[p['warning_message'] for p in result['sliced_plates'] if p['warning_message']],
        physical_print='Not performed. PLA fit, bridge finish, retention and durability remain unverified.')
    if support_parts is not None:evidence['support_parts']=sorted(support_parts)
    (out/'verification.json').write_text(json.dumps(evidence,indent=2)+'\n')
    assert not evidence['warnings'], evidence['warnings']
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    package(sys.argv[1] if len(sys.argv)>1 else 'profile-jig-tote-mount-test-print-plate', supports='--supports' in sys.argv)
