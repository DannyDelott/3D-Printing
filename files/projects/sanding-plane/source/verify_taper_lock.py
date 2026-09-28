"""Validate taper trial exports, actual slice evidence and served downloads."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,urllib.request
import numpy as np
import trimesh
PROJECT=Path(__file__).resolve().parents[1]
PREFIX='profile-jig-taper-lock-coupon'

def main():
    report={'archives':{},'assembled_collisions_mm3':{}}
    paths=sorted((PROJECT/'models').glob(PREFIX+'-*.3mf'))
    assert len(paths)==8
    for path in paths:
        with ZipFile(path) as z:assert z.testzip() is None
        scene=trimesh.load(path)
        count=2 if path.stem.endswith('print-plate') else 3 if path.stem.endswith('preview') else 1
        assert len(scene.geometry)==count,path
        for mesh in scene.geometry.values():
            assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1,path
        stl=path.with_suffix('.stl')
        if stl.exists():
            mesh=trimesh.load_mesh(stl)
            assert np.allclose(mesh.bounds,scene.bounds,atol=.001),path
            assert len(mesh.split())==count,path
        for f in (path,stl):
            if f.exists():assert urllib.request.urlopen('http://127.0.0.1:8741/models/'+f.name).read()==f.read_bytes()
        report['archives'][path.name]=dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bodies=count)
    scene=trimesh.load(PROJECT/'models'/f'{PREFIX}-preview.3mf')
    meshes=list(scene.geometry.items())
    for i,(name,a) in enumerate(meshes):
        for name2,b in meshes[i+1:]:
            intersection=trimesh.boolean.intersection([a,b],engine='manifold')
            volume=abs(float(intersection.volume)) if len(intersection.faces) else 0
            assert volume<.1,(name,name2,volume)
            report['assembled_collisions_mm3'][f'{name}:{name2}']=volume
    folder=PROJECT/'print-checks'/f'{PREFIX}-print-plate'
    check=json.loads((folder/'verification.json').read_text())
    assert check['model_sha256']==report['archives'][f'{PREFIX}-print-plate.3mf']['sha256']
    assert check['warnings']==[] and check['supports_disabled'] and check['support_toolpaths']==0
    result=json.loads((folder/'result.json').read_text())['sliced_plates'][0]
    assert len(result['objects'])==2
    report['print_check']=check
    report['estimate']=dict(grams=result['filaments'][0]['total_used_g'],seconds=result['total_predication'])
    report['physical_validation']='Tapered coupon physically tested by Danny with no shifting reported. Full-size loading and long-term wear remain untested.'
    (PROJECT/'validation-taper-lock-exports.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Verified eight taper trial 3MFs, connected watertight parts, assembly clearance, two-part support-free slice and served downloads.')

if __name__=='__main__':main()
