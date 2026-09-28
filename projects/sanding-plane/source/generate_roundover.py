"""R2: 1/8-inch outside-roundover shoe; reuse the proven profile-up lock.

Run with the repository CAD Python. Only the two new shoes are exported.
Assembly +Z faces the handles; print orientation places the rail cap down.
The 90-degree concave arc has short, outward-flared shoulders. Radius
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
PREFIX = 'roundover-1-8-r2'
SHOULDER_LENGTH = 2.5
FLARE_DEGREES = 3.0
BACK_THICKNESS = 10.0
ROOT = d.g.PROJECT


def shoulder_end(thickness):
    a = TOOL_RADIUS / math.sqrt(2)
    z = -thickness - TOOL_RADIUS + a
    angle = math.radians(45-FLARE_DEGREES)
    return a + SHOULDER_LENGTH*math.cos(angle), z-SHOULDER_LENGTH*math.sin(angle)


def blank(length, thickness):
    r = TOOL_RADIUS
    a = r / math.sqrt(2)
    z = -thickness - r + a
    b, end_z = shoulder_end(thickness)
    # The broad body returns toward the carrier beyond the short shoulders;
    # it cannot form the long registration faces of R1.
    return (cq.Workplane('XZ').moveTo(-WIDTH/2, 0).lineTo(WIDTH/2, 0)
            .lineTo(WIDTH/2, -BACK_THICKNESS).lineTo(b, end_z).lineTo(a, z)
            .threePointArc((0, -thickness), (-a, z))
            .lineTo(-b, end_z).lineTo(-WIDTH/2, -BACK_THICKNESS)
            .close().extrude(length/2, both=True).val().wrapped)


def contact_checks():
    a = TOOL_RADIUS/math.sqrt(2)
    z = -d.PROFILE_THICKNESS-TOOL_RADIUS+a
    b,end_z = shoulder_end(d.PROFILE_THICKNESS)
    # Nominal wood tangent shifted inward by the assumed paper thickness.
    # Rotate each adjoining flat toward the shoulder by up to 3 degrees about
    # its nominal tangency point. This bounds shoulder clearance, not wood fit.
    wood_a = RADIUS/math.sqrt(2)
    wood_z = -d.PROFILE_THICKNESS-TOOL_RADIUS+wood_a
    clearances = {}
    for deviation in (0, 1, 2, 3):
        angle = math.radians(45-deviation)
        normal = np.array([math.sin(angle), math.cos(angle)])
        samples = [(a,z),(b,end_z),(WIDTH/2,-BACK_THICKNESS)]
        gaps = [float(np.dot(np.array([x-wood_a,zz-wood_z]),normal)) for x,zz in samples]
        assert min(gaps) > .29,(deviation,gaps)
        clearances[str(deviation)] = round(min(gaps),4)
    return dict(shoulder_length_mm=SHOULDER_LENGTH,flare_per_side_degrees=FLARE_DEGREES,
                shoulder_opening_degrees=90+2*FLARE_DEGREES,
                minimum_bare_shoulder_clearance_mm_by_flat_deviation_degrees=clearances,
                abrasive_backing_arc_length_mm=TOOL_RADIUS*math.pi/2,
                instruction='Apply approximately 5 mm wide PSA abrasive to the curved seat only; leave shoulders bare.')


def main():
    originals = list((ROOT/'models').glob('profile-jig-*')) + list((ROOT/'models').glob('roundover-1-8-r1-*'))
    original_hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in originals if p.is_file()}
    report = dict(revision='R2', bit_url='https://www.amazon.com/dp/B0C5DVBNLS',
                  nominal_radius_mm=RADIUS, assumed_paper_thickness_mm=PAPER,
                  printed_radius_mm=TOOL_RADIUS, arc_degrees=90,
                  contact=contact_checks(),
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
    (ROOT/'validation-roundover-1-8-r2.json').write_text(json.dumps(report,indent=2)+'\n')
    from roundover_datasheet import write
    write(report)


if __name__ == '__main__':
    main()
