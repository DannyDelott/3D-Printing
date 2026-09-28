"""Reopen revision D exports and tie print evidence/downloads to their hashes."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,urllib.request
import numpy as np
import trimesh
PROJECT=Path(__file__).resolve().parents[1]
PREFIX='profile-jig-profile-up'

def main():
    report={'archives':{},'print_checks':{},'assembled_collisions_mm3':{}}
    for path in sorted((PROJECT/'models').glob(PREFIX+'-*.3mf')):
        with ZipFile(path) as archive:assert archive.testzip() is None
        scene=trimesh.load(path)
        assert len(scene.geometry)==(3 if path.stem.endswith(('preview','print-plate')) else 1),path
        for mesh in scene.geometry.values():assert mesh.is_watertight and mesh.is_winding_consistent,path
        stl=path.with_suffix('.stl')
        if stl.exists():
            mesh=trimesh.load_mesh(stl);assert np.allclose(mesh.bounds,scene.bounds,atol=.001),path
            assert len(mesh.split())==(3 if path.stem.endswith('print-plate') else 1)
        report['archives'][path.name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bodies':len(scene.geometry)}
    for kind in ('full','coupon'):
        scene=trimesh.load(PROJECT/'models'/f'{PREFIX}-{kind}-preview.3mf')
        meshes=list(scene.geometry.items())
        for i,(name,a) in enumerate(meshes):
            for name2,b in meshes[i+1:]:
                overlap=trimesh.boolean.intersection([a,b],engine='manifold')
                volume=abs(float(overlap.volume)) if len(overlap.faces) else 0
                report['assembled_collisions_mm3'][f'{kind}:{name}:{name2}']=volume
                assert volume<.1,report['assembled_collisions_mm3']
    for suffix,supports in [('coupon-shoe',False),('coupon-print-plate',False),('full-shoe',False),('full-knob',False),('full-body',True)]:
        stem=f'{PREFIX}-{suffix}';folder=PROJECT/'print-checks'/(stem+('-supports' if supports else ''))
        check=json.loads((folder/'verification.json').read_text())
        assert check['model_sha256']==report['archives'][stem+'.3mf']['sha256']
        assert check['warnings']==[] and check['supports_disabled']==(not supports)
        assert check['support_toolpaths']>0 if supports else check['support_toolpaths']==0
        report['print_checks'][suffix]=check
        for ext in ('stl','3mf'):
            path=PROJECT/'models'/f'{stem}.{ext}'
            assert urllib.request.urlopen(f'http://127.0.0.1:8741/models/{path.name}').read()==path.read_bytes()
    report['physical_validation']='Tapered coupon physically tested with no shifting reported. Full sander uses the same seat; full-size loading and long-term wear remain untested.'
    (PROJECT/'validation-profile-up-exports.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Verified',len(report['archives']),'3MFs, 5 sliced layouts, mesh collisions and live STL/3MF downloads.')

if __name__=='__main__':main()
