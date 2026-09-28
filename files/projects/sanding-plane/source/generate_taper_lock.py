"""Taper-seat coupon trial; reuse the existing revision D threaded carrier.

Generate the proven coupon. The full sander uses the same tapered interface.
The print plate contains two replacement parts; the carrier is reusable.
"""
import json
import numpy as np
import generate_profile_up as d

PREFIX='profile-jig-taper-lock-coupon'


def main():
    p,y,edges=d.parts(coupon=True,tapered=True)
    checks=d.validate(p,y)
    checks.update(d.validate_taper(p,y))
    gap=checks['seated_tip_floor_gap_mm']
    # Reuse is backed by the exported mesh, not just matching overall bounds.
    mesh=d.c.cad_mesh(d.orientation('body',p['body'],True))
    mesh.apply_translation(-mesh.bounds[0])
    old=next(iter(d.trimesh.load(d.g.MODELS/'profile-jig-profile-up-coupon-body.3mf').geometry.values()))
    assert np.array_equal(mesh.vertices,old.vertices) and np.array_equal(mesh.faces,old.faces)
    report=dict(status='Danny physically tested the tapered coupon and reported no shifting. Long-term wear and full-size loading remain untested.',
        interface=dict(included_angle_degrees=90,seat_mouth_diameter_mm=2*d.PIN_RADIUS,
            pocket_floor_diameter_mm=2*d.TAPER_FLOOR_RADIUS,pocket_depth_mm=3,
            blunt_tip_diameter_mm=2*(d.TAPER_FLOOR_RADIUS+d.TAPER_TIP_GAP),
            seated_tip_floor_gap_mm=round(gap,3),nominal_flank_gap_when_seated_mm=0,
            release_turns=1,release_lift_mm=d.RELEASE_LIFT,coupon_length_mm=70),
        reused_carrier='Exact vertex and triangle match to profile-jig-profile-up-coupon-body.3mf',
        print_plate_parts=['shoe','knob'],geometry=checks,rounded_edges=edges)
    report['meshes']=d.export(p,PREFIX,True,print_parts=('shoe','knob'))
    (d.g.PROJECT/'validation-taper-lock.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Taper coupon exported; carrier reuse, seating, release and withdrawal checks passed.')

if __name__=='__main__':main()
