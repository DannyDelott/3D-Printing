# Shared scripts

Scripts stay flat here. All artifact locations are declared in the design manifests and resolved by `project_paths.py`; CAD geometry and tolerances are unchanged by the folder organization.

| Purpose | Scripts |
| --- | --- |
| Original two-circle rail and shared export | `generate_template.py` |
| Bézier alternative and comparison samples | `refine_curves.py` |
| Elliptical rail, openings, matching stiles | `generate_ellipse.py`, `generate_honeycomb.py`, `generate_stiles.py` |
| Earlier explicit dovetail cuts | `generate_dovetail.py`, `generate_stile_dovetail.py` |
| Preserve and arrange the earlier stile session | `arrange_stile_plate.py` |
| Prepare native V5/V6 cuts | `prepare_native_dovetail.py --revision 5` or `--revision 6` |
| Round the native V6 joint into V7 | `round_native_dovetail.py` |
| Widen the rounded socket to 0.40 mm total for V8 | `widen_native_dovetail.py` |
| Set V9 total width clearance to 0.20 mm | `tune_native_dovetail.py` |
| Slice and verify rounded joints with saved P1S settings | `slice_rounded_dovetail.py --revision 9` (or `--revision 8`) |
| Rail V10: fifth matching short-side hexagon | `prepare_rail_v10.py`, `build_rail_v10_page.py` |
| Historical broad V9 stile joint | `prepare_stile_v9.py`, then `publish_approved_v9.py` |
| Half-inch complete templates and historical split stile | `generate_half_inch_templates.py`, `prepare_half_inch_stile.py` |
| Cabinet front illustrations | `front_views.py` |
| Comparison and revision navigation | `build_library.py`, `build_comparison.py` |
| Dedicated datasheets | `build_native_dovetail_page.py --revision 9`, `build_half_inch_page.py` |
| Links, manifests, and artifact preservation checks | `check_project.py` |
| Preview with redirects for old URLs | `serve.py --port 8767` |

Run these with the CAD Python environment documented in the root README. Geometry generators overwrite the revision outputs they own; page builders publish existing geometry. Native GUI-authored cuts remain under the corresponding revision’s `native-source/`.

`comparison.html.in` and `stile-dovetail.html.in` are HTML templates, not directly usable pages. Open `../index.html` or run the preview server.

To add a revision, declare its identity, status, artifact names, and relative paths in `designs/<design>/design.json`. Update the design’s selections only when that revision is deliberately chosen. Rebuild the library and comparison afterward.

Final 3MF imports are checked with `check_bambu_import.py <file.3mf>`, using Bambu’s own importer to verify nonzero geometry and matching dimensions. `slice_rounded_dovetail.py` runs this check after packaging; V8’s corrected export preserves the required XML namespaces.

Historical reinforced stile V10: run `prepare_stile_v10.py`, then `build_stile_v10_page.py`, `build_library.py`, `build_comparison.py`, and `build_half_inch_page.py`. The full-width coupon is extracted directly from the new stile. Its 0.20 mm fit was reported loose.

V11 tighter stile coupon comparison: `prepare_stile_v11.py`, then `build_stile_v11_page.py` and the library/comparison builders. It fixes V10’s flank intercept and tongue, changes only socket clearance, and engraves the socket backs. It does not regenerate the full stile.

V12 stile retention test: `prepare_stile_v12.py`, then `build_stile_v12_page.py`, `build_library.py`, and `build_comparison.py`. Its primary plate prints just the two labeled 0.05 / 0.00 mm sockets; reuse an intact V10/V11 tail. A four-piece plate is also available. The .05 fit was approved and subsequently applied to full stile V13.

Current approved stile V13: `prepare_stile_v13.py` applies the V12 .05 socket geometry to the full stile, preserves the V10 tail, and verifies both mating surfaces against the tested coupon. Run `build_stile_v13_page.py`, `build_library.py`, `build_comparison.py`, and `build_half_inch_page.py` to publish. The joint fit is approved; full-template strength remains untested.
