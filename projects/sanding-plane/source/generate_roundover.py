"""R1: 1/8-inch outside-roundover shoe; reuse the proven profile-up lock.

Run with the repository CAD Python. Only the two new shoes are exported.
Assembly +Z faces the handles; print orientation places the rail cap down.
The 90-degree concave arc is tangent to two 45-degree guide faces. Radius
includes the assumed total sandpaper/adhesive thickness, measured normally.
"""
import hashlib
import json
import math
from pathlib import Path
from zipfile import ZipFile

import cadquery as cq
import numpy as np
import trimesh
import generate_profile_up as d

RADIUS = 25.4 / 8
PAPER = 0.30
TOOL_RADIUS = RADIUS + PAPER
WIDTH = 31.75
PREFIX = 'roundover-1-8-r1'
ROOT = d.g.PROJECT


def blank(length, thickness):
    r = TOOL_RADIUS
    a = r / math.sqrt(2)
    z = -thickness - r + r / math.sqrt(2)
    edge_z = z - (WIDTH / 2 - a)
    # Exact circular edge in STEP, with tangent straight guides on both sides.
    return (cq.Workplane('XZ').moveTo(-WIDTH/2, 0).lineTo(WIDTH/2, 0)
            .lineTo(WIDTH/2, edge_z).lineTo(a, z)
            .threePointArc((0, -thickness), (-a, z))
            .lineTo(-WIDTH/2, edge_z).close().extrude(length/2, both=True)
            .val().wrapped)


def main():
    originals = list((ROOT/'models').glob('profile-jig-*'))
    original_hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in originals if p.is_file()}
    report = dict(revision='R1', bit_url='https://www.amazon.com/dp/B0C5DVBNLS',
                  nominal_radius_mm=RADIUS, assumed_paper_thickness_mm=PAPER,
                  printed_radius_mm=TOOL_RADIUS, arc_degrees=90,
                  status='CAD and slicer validation only; routed-workpiece fit untested.', parts={})
    for coupon in (False, True):
        label = 'coupon' if coupon else 'shoe'
        stem = f'{PREFIX}-{label}'
        print('Building '+stem, flush=True)
        p,y,_ = d.parts(coupon=coupon,tapered=True,profile_blank=blank)
        checks = d.validate(p,y)
        checks.update(d.validate_taper(p,y))
        original_path = ROOT/'models'/('profile-jig-taper-lock-coupon-shoe.step' if coupon
                                      else 'profile-jig-profile-up-full-shoe.step')
        old = cq.importers.importStep(str(original_path)).val()
        # Compare the complete retained lock/rail above the shoulder plane.
        region = cq.Shape.cast(d.g.block(-30,-110,-d.PRELOAD_TRAVEL,60,220,15))
        new_rail = cq.Shape.cast(p['shoe']).intersect(region)
        old_rail = old.intersect(region)
        difference = new_rail.cut(old_rail).Volume()+old_rail.cut(new_rail).Volume()
        assert difference < 1e-5, difference
        checks['rail_and_pocket_difference_mm3'] = difference
        solid = cq.Shape.cast(p['shoe'])
        # The full cylindrical face must retain the precise compensated radius.
        radii = [f._geomAdaptor().Cylinder().Radius() for f in solid.Faces()
                 if f.geomType() == 'CYLINDER']
        assert any(abs(r-TOOL_RADIUS)<1e-7 for r in radii), radii
        shape = d.orientation('shoe',p['shoe'],coupon)
        mesh = d.c.cad_mesh(shape)
        mesh.apply_translation(-mesh.bounds[0])
        assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1
        assert np.all(mesh.extents[:2]<250)
        stl=ROOT/'models'/f'{stem}.stl'
        mesh.export(stl)
        mf=stl.with_suffix('.3mf')
        mf.write_bytes(trimesh.Scene({stem: mesh}).export(file_type='3mf'))
        d.g.write_step(p['shoe'],stl.with_suffix('.step'))
        with ZipFile(mf) as archive: assert archive.testzip() is None
        loaded=trimesh.load(mf,force='mesh')
        assert loaded.is_watertight and np.allclose(mesh.bounds,loaded.bounds,atol=1e-5)
        assert abs(loaded.volume-mesh.volume)<.02
        checks['watertight'] = True
        checks['single_solid'] = True
        report['parts'][label] = dict(dimensions_mm=mesh.extents.round(4).tolist(),
                                    volume_mm3=mesh.volume,checks=checks,
                                    files={f.name:hashlib.sha256(f.read_bytes()).hexdigest()
                                           for f in (stl,mf,stl.with_suffix('.step'))})
        print(label, mesh.extents, flush=True)
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in original_hashes.items())
    report['existing_model_files_unchanged'] = True
    (ROOT/'validation-roundover-1-8-r1.json').write_text(json.dumps(report,indent=2)+'\n')
    from roundover_datasheet import write
    write(report)


if __name__ == '__main__':
    main()
