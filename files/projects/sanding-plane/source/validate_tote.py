"""Check exported parts and the hardware-free attachment's CAD clearances.

Run with the project's OCP/trimesh Python environment. CAD interference checks
verify the intended constraint directions, not friction or printed strength.
"""
from pathlib import Path
from zipfile import ZipFile
import json
import math
import sys
import numpy as np
import trimesh
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Cut
from OCP.STEPControl import STEPControl_Reader
from OCP.IFSelect import IFSelect_RetDone
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID, TopAbs_IN, TopAbs_ON
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt, gp_Ax1, gp_Dir, gp_Trsf
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_tote_grip as g
from generate_caul import crown_height


def common_volume(left, right):
    operation = BRepAlgoAPI_Common(left, right)
    operation.Build()
    assert operation.IsDone()
    return abs(g.volume(operation.Shape()))


def main():
    report = {}
    shapes = {}
    for stem in (
        'profile-jig-latch-plate', 'profile-jig-reusable-tote', 'profile-jig-reusable-knob',
        'magnate-5869-sanding-shoe-250mm',
        'profile-jig-dovetail-coupon-rail',
        'profile-jig-dovetail-coupon-socket',
        'profile-jig-knob-thread-test-stud', 'profile-jig-knob-thread-test-cap',
        'profile-jig-tote-mount-test-socket', 'profile-jig-tote-mount-test-foot',
    ):
        reader = STEPControl_Reader()
        assert reader.ReadFile(str(g.MODELS / f'{stem}.step')) == IFSelect_RetDone
        reader.TransferRoots()
        shape = reader.OneShape()
        shapes[stem] = shape
        assert BRepCheck_Analyzer(shape).IsValid()
        explorer = TopExp_Explorer(shape, TopAbs_SOLID)
        solids = 0
        while explorer.More():
            solids += 1
            explorer.Next()
        assert solids == 1
        mesh = trimesh.load_mesh(g.MODELS / f'{stem}.stl', force='mesh', process=True)
        assert mesh.is_watertight and mesh.is_winding_consistent
        assert len(mesh.split(only_watertight=False)) == 1
        with ZipFile(g.MODELS / f'{stem}.3mf') as archive:
            assert archive.testzip() is None
        loaded = trimesh.load(g.MODELS / f'{stem}.3mf')
        assert len(loaded.geometry) == 1
        assert all(m.is_watertight and m.is_winding_consistent for m in loaded.geometry.values())
        report[stem] = dict(step_valid=True, solid_count=1, meshes_watertight=True,
            mesh_extents_mm=mesh.extents.tolist(), archive_integrity=True)
    carrier = shapes['profile-jig-latch-plate']
    tote = shapes['profile-jig-reusable-tote']
    knob = shapes['profile-jig-reusable-knob']
    shoe = shapes['magnate-5869-sanding-shoe-250mm']
    rail_coupon = shapes['profile-jig-dovetail-coupon-rail']
    socket_coupon = shapes['profile-jig-dovetail-coupon-socket']
    fixed = g.boolean(BRepAlgoAPI_Cut, carrier, g.make_latch(g.LATCH_Y), 'isolating fixed carrier for release-clearance check')
    fixed_coupon = g.boolean(BRepAlgoAPI_Cut, socket_coupon, g.make_latch(g.COUPON_LATCH_Y), 'isolating fixed coupon')
    released_tooth = g.shifted(g.tooth(g.LATCH_Y), x=g.LATCH_RELEASE_TRAVEL)
    coupon_released_tooth = g.shifted(g.tooth(g.COUPON_LATCH_Y), x=g.LATCH_RELEASE_TRAVEL)
    checks = {
        'assembled_carrier_shoe': common_volume(carrier, shoe),
        'assembled_plate_tote': common_volume(carrier, tote),
        'assembled_plate_knob': common_volume(carrier, knob),
        'assembled_knob_tote': common_volume(knob, tote),
        'assembled_coupon_pair': common_volume(rail_coupon, socket_coupon),
        'released_tooth_shoe': common_volume(released_tooth, shoe),
        'released_tooth_coupon_rail': common_volume(coupon_released_tooth, rail_coupon),
    }
    for travel in (1, 10, 30, 60):
        withdrawn = g.shifted(shoe, y=-travel)
        checks[f'withdrawal_fixed_carrier_{travel}mm'] = common_volume(fixed, withdrawn)
        checks[f'withdrawal_released_tooth_{travel}mm'] = common_volume(released_tooth, withdrawn)
    for travel in (1, 20, 50):
        withdrawn = g.shifted(rail_coupon, y=-travel)
        checks[f'coupon_withdrawal_fixed_socket_{travel}mm'] = common_volume(fixed_coupon, withdrawn)
        checks[f'coupon_withdrawal_released_tooth_{travel}mm'] = common_volume(coupon_released_tooth, withdrawn)
    tip_probe = g.block(13.8, g.LATCH_Y-1, g.CARRIER_BOTTOM,
        g.LATCH_PAD_OUTER_X-13.8, 2, g.CARRIER_TOP-g.CARRIER_BOTTOM)
    checks['released_tip_clears_travel_stop'] = common_volume(fixed, g.shifted(tip_probe,x=g.LATCH_RELEASE_TRAVEL))
    # Compare actual CAD at the free arm: the tote must not fuse onto it.
    free_region = g.block(12.7,g.LATCH_Y-8,g.CARRIER_BOTTOM,12,g.LATCH_RELIEF_END+8,g.CARRIER_TOP-g.CARRIER_BOTTOM)
    full_free = BRepAlgoAPI_Common(carrier,free_region).Shape()
    coupon_free = BRepAlgoAPI_Common(g.shifted(socket_coupon,y=g.LATCH_Y-g.COUPON_LATCH_Y),free_region).Shape()
    checks['full_vs_coupon_free_arm_difference'] = abs(g.volume(BRepAlgoAPI_Cut(full_free,coupon_free).Shape())) + abs(g.volume(BRepAlgoAPI_Cut(coupon_free,full_free).Shape()))
    overhead = g.block(12.7,g.LATCH_Y-8,g.CARRIER_TOP+.05,12,g.LATCH_RELIEF_END+8,1)
    checks['fixed_body_above_free_arm'] = common_volume(fixed,overhead)
    mounts = g.grip_mounts
    checks['thread_coupon_assembled'] = common_volume(shapes['profile-jig-knob-thread-test-stud'],shapes['profile-jig-knob-thread-test-cap'])
    checks['tote_coupon_assembled'] = common_volume(shapes['profile-jig-tote-mount-test-socket'],shapes['profile-jig-tote-mount-test-foot'])
    for degrees in (90,180,360,720,1080):
        rotation=gp_Trsf()
        rotation.SetRotation(gp_Ax1(gp_Pnt(0,g.KNOB_Y,0),gp_Dir(0,0,1)),math.radians(degrees))
        moved=g.shifted(BRepBuilderAPI_Transform(knob,rotation,True).Shape(),z=mounts.THREAD_PITCH*degrees/360)
        checks[f'knob_unscrew_{degrees}deg'] = common_volume(carrier,moved)
    arm=mounts.release_arm(g,mounts.TOTE_MOUNT_YS[0])
    fixed_tote=g.boolean(BRepAlgoAPI_Cut,tote,arm,'isolating fixed tote for withdrawal checks')
    tip=BRepAlgoAPI_Common(arm,g.block(8,mounts.TOTE_MOUNT_YS[0]+8,9.5,5,5,4.5)).Shape()
    released_tip=g.shifted(tip,y=-mounts.MOUNT_RELEASE)
    for travel in (0,1,10,30,45):
        checks[f'tote_withdraw_fixed_{travel}mm']=common_volume(carrier,g.shifted(fixed_tote,x=-travel))
        checks[f'tote_withdraw_released_tip_{travel}mm']=common_volume(carrier,g.shifted(released_tip,x=-travel))
    report['grip_mounts']=dict(knob_major_diameter_mm=mounts.THREAD_MAJOR_DIAMETER,
        knob_pitch_mm=mounts.THREAD_PITCH,thread_radial_clearance_mm=mounts.THREAD_RADIAL_CLEARANCE,
        thread_axial_clearance_mm=mounts.THREAD_AXIAL_CLEARANCE,tote_mount_spacing_mm=mounts.TOTE_MOUNT_YS[1]-mounts.TOTE_MOUNT_YS[0],
        tote_fit_allowance_mm=mounts.MOUNT_CLEARANCE,tote_release_travel_mm=mounts.MOUNT_RELEASE,
        tote_tenon_cap_width_mm=2*mounts.TENON_CAP_HALF_WIDTH,tote_tenon_length_mm=27)
    # Nominal sole/bed surfaces touch without solid overlap. A 0.05 mm virtual
    # downward move measures bearing engagement, not elastic deformation.
    lowered_tote=g.shifted(tote,z=-.05)
    contact=BRepAlgoAPI_Common(carrier,lowered_tote).Shape()
    bearing_patches={}
    for name,y,length in [('front_toe',-1,11),('between_mounts',43,8),('rear_heel',77,3)]:
        probe=g.block(-10,y,mounts.PLATE_TOP-.05,20,length,.05)
        area=common_volume(contact,probe)/.05
        assert abs(area-20*length) < .01, (name,area)
        bearing_patches[name]=area
    report['tote_support_bed']=dict(sole_length_mm=mounts.TOTE_SOLE_END-mounts.TOTE_SOLE_START,
        bed_length_mm=mounts.TOTE_BED_END-mounts.TOTE_BED_START,
        nominal_vertical_bearing_gap_mm=mounts.GRIP_SOLE-mounts.PLATE_TOP,
        sampled_supported_patches_mm2=bearing_patches,
        engaged_area_at_0_05mm_virtual_downward_move_mm2=abs(g.volume(contact))/.05,
        limit='Geometric contact check only; not a force, stiffness, or print-fit validation.')
    failed_clearances = {label:value for label,value in checks.items() if value >= 1e-4}
    assert not failed_clearances, failed_clearances
    blocked = {
        'dovetail_blocks_1mm_lift': common_volume(g.shifted(carrier,z=1),shoe),
        'tote_tenons_block_1mm_lift': common_volume(carrier,g.shifted(tote,z=1)),
        'tote_tenons_block_1mm_foreaft': common_volume(carrier,g.shifted(tote,y=1)),
        'tote_release_stop_blocks_1_3mm_travel': common_volume(carrier,g.shifted(tip,y=-1.3)),
        'tote_catch_blocks_1mm_withdrawal': common_volume(carrier,g.shifted(tote,x=-1)),
        'knob_threads_block_1mm_straight_lift': common_volume(carrier,g.shifted(knob,z=1)),
        'rear_stop_blocks_1mm_overinsertion': common_volume(fixed,g.shifted(shoe,y=1)),
        'latch_blocks_1mm_withdrawal': common_volume(carrier,g.shifted(shoe,y=-1)),
        'coupon_latch_blocks_1mm_withdrawal': common_volume(socket_coupon,g.shifted(rail_coupon,y=-1)),
        'coupon_rear_stop_blocks_1mm_overinsertion': common_volume(fixed_coupon,g.shifted(rail_coupon,y=1)),
        'tip_guard_blocks_2_5mm_travel': common_volume(fixed,g.shifted(tip_probe,x=2.5)),
    }
    for label, value in blocked.items():
        assert value > .05, (label, value)
    report['nominal_and_release_clearances_common_volume_mm3'] = checks
    report['blocked_movements_common_volume_mm3'] = blocked
    report['latch_geometry'] = dict(material_for_test='PLA', beam_thickness_mm=g.LATCH_BEAM_THICKNESS,
        tooth_to_root_flare_mm=g.LATCH_ROOT_START, intended_release_travel_mm=g.LATCH_RELEASE_TRAVEL,
        tip_travel_to_guard_mm=g.LATCH_GUARD_INNER_X-g.LATCH_PAD_OUTER_X)
    # The rail/latch connection must not perforate the profile contact face.
    samples = 0
    for y in range(-120, 121, 5):
        for x in range(-15, 16):
            z = -(g.SHOE_MINIMUM_THICKNESS + crown_height(0) - crown_height(x)) + .5
            classifier = BRepClass3d_SolidClassifier(shoe, gp_Pnt(x, y, z), 1e-6)
            assert classifier.State() in (TopAbs_IN, TopAbs_ON)
            samples += 1
    report['continuous_contact_skin_samples_at_0_5mm'] = samples
    print_checks = {}
    for stem in ('profile-jig-reusable-tote', 'profile-jig-tote-mount-test-foot', 'profile-jig-tote-mount-test-socket'):
        mesh = trimesh.load_mesh(g.MODELS / f'{stem}.stl', force='mesh', process=True)
        assert abs(mesh.bounds[0,2]) < .001
        overhang = (mesh.triangles_center[:,2] > .001) & (mesh.face_normals[:,2] < -np.cos(np.pi/4)-1e-5)
        area = float(mesh.area_faces[overhang].sum())
        if stem.endswith('socket'):
            assert area < .001, (stem,area)
        else:
            # The only exception is the 2.3 x 1 mm square catch face. Its
            # opposite ends sit on 0.6 mm ribs, checked separately below.
            vertices = mesh.triangles[overhang].reshape(-1,3)
            assert np.allclose(np.ptp(vertices,axis=0), [2.3,1,0], atol=.002)
            assert np.allclose(vertices[:,2],24,atol=.002)
            assert abs(area-2.3) < .002
            assert abs(mesh.extents[2]-30) < .002
        print_checks[stem] = dict(on_build_plane=True,
            below_45_degree_area_mm2=area,
            exception='2.3 mm catch bridge between two integral ribs' if area else None)
    for z in (10.1,13.0):
        assert common_volume(arm,g.block(8.85,mounts.TOTE_MOUNT_YS[0]+11.5,z,.05,.5,.3)) > .007
    assert common_volume(arm,g.block(8.85,mounts.TOTE_MOUNT_YS[0]+11.5,10.8,.05,.5,1.9)) < 1e-5
    report['tote_print_geometry'] = print_checks
    for stem in ('profile-jig-assembled-preview', 'profile-jig-exploded-preview', 'profile-jig-latch-coupon-preview', 'profile-jig-latch-coupon-print-plate', 'profile-jig-knob-thread-test-print-plate', 'profile-jig-knob-section-preview', 'profile-jig-tote-mount-test-preview', 'profile-jig-tote-mount-test-print-plate'):
        with ZipFile(g.MODELS / f'{stem}.3mf') as archive:
            assert archive.testzip() is None
        assembly = trimesh.load(g.MODELS / f'{stem}.3mf')
        assert len(assembly.geometry) == (4 if stem in ('profile-jig-assembled-preview','profile-jig-exploded-preview') else 2)
        if stem == 'profile-jig-tote-mount-test-print-plate':
            boxes = sorted([part.bounds for part in assembly.geometry.values()],key=lambda box:box[0,0])
            assert boxes[1][0,0]-boxes[0][1,0] > 7.99
            assert all(abs(box[0,2]) < .001 for box in boxes)
        if stem == 'profile-jig-latch-coupon-print-plate':
            parts = list(assembly.geometry.values())
            boxes = sorted([part.bounds for part in parts], key=lambda box: box[0,0])
            assert boxes[1][0,0] - boxes[0][1,0] > 7.99
            assert all(abs(box[0,2]) < .001 for box in boxes)
            report['coupon_print_plate'] = dict(separate_parts=2, minimum_gap_mm=8, flat_on_build_plane=True)
            overhangs = {}
            for name, part in assembly.geometry.items():
                # Downward surfaces above the bed must rise at least 45 degrees
                # from horizontal. This excludes bed-contact faces, not bridges.
                above_bed = part.triangles_center[:,2] > .001
                unsupported = above_bed & (part.face_normals[:,2] < -np.cos(np.pi/4)-1e-5)
                area = float(part.area_faces[unsupported].sum())
                assert area < .001, (name, 'steep downward-facing area', area)
                overhangs[name] = dict(area_below_45_degrees_above_bed_mm2=area)
            report['coupon_overhang_geometry'] = overhangs
    report['physical_fit'] = 'Unverified. Test shoe-latch and tote-mount spring-back, retention, rocking and cycles, and knob thread fit, seating and resistance to loosening in PLA.'
    report['release_analysis_limit'] = 'Rigid tooth-position and fixed-body clearance checks only; not a flexure simulation or force/fatigue validation.'
    report['support_free_limit'] = 'Geometry checks cover the shoe coupon, side-down tote and tote coupon. Tote catch has a deliberate 2.3 mm bridge. See print-checks for separate slicer evidence. Full carrier, knob and shoe are not covered by these overhang checks. Physical bridge quality and flexure life remain untested.'
    (g.PROJECT / 'validation-modular-grips.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
