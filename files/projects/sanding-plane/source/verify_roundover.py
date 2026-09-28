"""Verify the R2 exported working faces, print geometry and slice provenance."""
import hashlib
import json
import math
from pathlib import Path
from zipfile import ZipFile

import cadquery as cq
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'roundover-1-8-r2'


def main():
    source=json.loads((ROOT/f'validation-{PREFIX}.json').read_text())
    report={}
    for kind in ('shoe','coupon'):
        stem=f'{PREFIX}-{kind}'
        length=source['parts'][kind]['dimensions_mm'][1]
        for name,expected in source['parts'][kind]['files'].items():
            assert hashlib.sha256((ROOT/'models'/name).read_bytes()).hexdigest()==expected,name
        solid=cq.importers.importStep(str(ROOT/'models'/f'{stem}.step')).val()
        assert solid.isValid() and len(solid.Solids())==1
        working=[f for f in solid.Faces() if f.geomType()=='CYLINDER'
                 and abs(f._geomAdaptor().Cylinder().Radius()-3.475)<1e-6]
        assert len(working)==1
        assert abs(working[0].Area()-3.475*math.pi/2*length)<1e-4
        shoulders=[f for f in solid.Faces() if f.geomType()=='PLANE'
                   and abs(f.Area()-2.5*length)<1e-4]
        assert len(shoulders)==2
        angles=[math.degrees(math.acos(abs(f.normalAt().z))) for f in shoulders]
        assert all(abs(a-42)<1e-6 for a in angles),angles
        mesh=trimesh.load_mesh(ROOT/'models'/f'{stem}.stl',process=True)
        assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1
        folder=ROOT/'print-checks'/stem
        configured=folder/f'{stem}-configured.3mf'
        with ZipFile(configured) as archive:assert archive.testzip() is None
        imported=trimesh.load(configured,force='mesh')
        assert imported.is_watertight and len(imported.split())==1
        assert np.allclose(imported.extents,mesh.extents,atol=1e-4)
        assert abs(imported.volume-mesh.volume)<.05
        assert np.all(imported.bounds[0]>=-1e-5) and np.all(imported.bounds[1,:2]<=256)
        evidence=json.loads((folder/'verification.json').read_text())
        assert evidence['supports_disabled'] and not evidence['support_toolpaths'] and not evidence['warnings']
        assert evidence['model_sha256']==hashlib.sha256((ROOT/'models'/f'{stem}.3mf').read_bytes()).hexdigest()
        report[kind]=dict(step_valid=True,arc_radius_mm=3.475,arc_degrees=90,
                         shoulder_length_mm=2.5,shoulder_angles_degrees=angles,
                         dimensions_mm=mesh.extents.tolist(),watertight=True,bed_bounds_valid=True,
                         configured_sha256=hashlib.sha256(configured.read_bytes()).hexdigest(),
                         slice_matches_geometry=True,supports=False,warnings=[])
    (ROOT/f'validation-{PREFIX}-exports.json').write_text(json.dumps(report,indent=2)+'\n')
    print('R2 STEP contact faces, STL/3MF geometry, plate bounds and slice provenance passed.')


if __name__=='__main__':main()
