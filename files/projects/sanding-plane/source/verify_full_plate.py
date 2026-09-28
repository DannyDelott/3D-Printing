"""Check full-plate provenance, Bambu object overrides and generated supports."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,re,urllib.request
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
P=Path(__file__).resolve().parents[1]
S='profile-jig-final-print-plate'

def main():
    report=json.loads((P/'validation-final-plate.json').read_text())
    for item in report['source_models'].values():
        assert hashlib.sha256((P/'models'/item['file']).read_bytes()).hexdigest()==item['sha256']
    meshpath=P/'models'/f'{S}.3mf';scene=trimesh.load(meshpath)
    assert len(scene.geometry)==3
    for mesh in scene.geometry.values():
        assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1
        assert abs(mesh.bounds[0,2])<1e-5
    stl=trimesh.load_mesh(meshpath.with_suffix('.stl'))
    assert len(stl.split())==3 and np.allclose(stl.bounds,scene.bounds,atol=.001)
    folder=P/'print-checks'/(S+'-supports')
    check=json.loads((folder/'verification.json').read_text())
    assert check['warnings']==[] and check['support_parts']==['Carrier']
    assert check['model_sha256']==hashlib.sha256(meshpath.read_bytes()).hexdigest()
    configured=folder/f'{S}-configured.3mf'
    with ZipFile(configured) as z:
        assert z.testzip() is None
        cfg=ET.fromstring(z.read('Metadata/model_settings.config'))
        settings=json.loads(z.read('Metadata/project_settings.config'))
        support={}
        for obj in cfg.findall('object'):
            values={v.get('key'):v.get('value') for v in obj.findall('metadata')}
            support[values['name']]=values['enable_support']
        assert support=={'Carrier':'1','Shoe':'0','Knob':'0'},support
        assert settings['print_sequence']=='by layer'
        raw=ET.fromstring(z.read('3D/3dmodel.model'));ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
        assert len(raw.findall('m:build/m:item',ns))==3
    result=json.loads((folder/'result.json').read_text())['sliced_plates'][0]
    assert len(result['objects'])==3 and not result['warning_message']
    bounds={o['name']:o['bbox'] for o in result['objects']}
    for b in bounds.values():
        assert b['z']==0 and b['x']>0 and b['y']>0
        assert b['x']+b['width']<256 and b['y']+b['depth']<256
    # Confirm actual extruding support moves stay within the carrier's column.
    xy={};feature='';support_points=[]
    for line in (folder/'plate_1.gcode').read_text().splitlines():
        if line.startswith('; FEATURE: '):feature=line.removeprefix('; FEATURE: ')
        if not line.startswith(('G0 ','G1 ')):continue
        fields={k:float(v) for k,v in re.findall(r'\b([XYE])(-?\d+(?:\.\d+)?)',line.split(';')[0])}
        for k in ('X','Y'):
            if k in fields:xy[k]=fields[k]
        if feature.startswith('Support') and fields.get('E',0)>0 and ('X' in fields or 'Y' in fields):
            support_points.append([xy['X'],xy['Y']])
    assert support_points
    points=np.array(support_points);carrier=bounds['Carrier']
    assert points[:,0].min()>carrier['x']-5
    assert points[:,0].max()<carrier['x']+carrier['width']+5
    assert points[:,0].max()<bounds['Shoe']['x']
    assert points[:,1].min()>0 and points[:,1].max()<256
    for f in (meshpath,meshpath.with_suffix('.stl'),configured):
        assert urllib.request.urlopen('http://127.0.0.1:8741/'+f.relative_to(P).as_posix()).read()==f.read_bytes()
    report.update(grams=result['filaments'][0]['total_used_g'],seconds=result['total_predication'],
        configured_sha256=hashlib.sha256(configured.read_bytes()).hexdigest(),warnings=[],
        verified_support_overrides=support,support_extrusion_bounds_mm=[points.min(axis=0).tolist(),points.max(axis=0).tolist()],
        separate_print_objects=3)
    (P/'validation-final-plate.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('grams','seconds','support_extrusion_bounds_mm','verified_support_overrides')},indent=2))

if __name__=='__main__':main()
