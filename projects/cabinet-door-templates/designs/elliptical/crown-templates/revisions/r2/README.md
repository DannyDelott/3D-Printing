# Crown tracing templates R2

For Cabinet R7 option f: 17⅞″ door width, ¾″ crown, flat backs.
The maple veneer allowance is **0.6 mm on each side**, superseding R7's old 3/32″ assumption.

## Print set

- `rail-left` + `rail-right`: butt at the center, tape the joint and align both flat backs against a straightedge. One pair serves both rails.
- `stile-left` + `stile-right`: end-grain tracing patterns for the rectangular stile blanks.
- `panel-l-core`, `panel-c-core`, `panel-r-core`: shape the bare cores, before veneer. Straight edge registers to the bare core back.
- `panel-l-finished`, `panel-c-finished`, `panel-r-finished`: optional checks after applying veneer on both faces.

Print the supplied geometry flat, lettering up, at 100% scale. PLA; 0.20 mm layers; 4 walls; 20% gyroid; no supports or brim. Patterns are 2 mm thick. Largest part: 227.0125 × 38.10 mm. Printer model is not confirmed; estimates use a P1S with a 0.4 mm nozzle. Measure each print's width before using it.

## Use

Curved edge = front; straight edge = flat back. L and R are the cabinet's left and right as viewed from the front. Keep that orientation when tracing. At the opposite end of a blank, turn the template over while retaining its alignment to the same physical inner/outer edges.

For rails, mark the long narrow edge of the rectangular blank, bandsaw outside the line, and plane/scrape to it. For stiles and panel cores, trace both blank ends and hand-plane between the lines. The rail edge thickness is 19.05 mm and its center is 38.10 mm; start with additional cleanup allowance.

These profiles describe the curved faces of rectangular blanks. Cut the asymmetric outlines, flat tongues, shiplaps and shallow face channel afterward as separate operations. The curved profile is extended over stock that will later be removed at those edges. These are not finished joinery cross-sections or routing guides.

## Panel stack

The original assumed finished tongue envelope is 6.10 mm for a 6.35 mm groove. With 0.6 mm maple on each side, nominal core thickness at a flat tongue is 4.90 mm. The broad center reaches 23.95 mm core thickness and 25.15 mm finished thickness. Face veneer is offset normal to the circular surface; back veneer is a flat offset. Glue lines are modeled as zero thickness. Measure actual veneer and test the chosen core, glue and pressing method.

Side blank widths differ because the retained shiplaps all face the same direction: L 97.5125 mm, C 158.1000 mm, R 104.2125 mm. The visible center bay remains 6″. Use the supplied blank widths when positioning a template; do not center a side template on a differently sized blank.

The revised shadow-line cut is 0.2 mm deep and leaves approximately 0.4 mm of nominal face veneer. Test on an offcut before cutting the veneered panels.

## Files and checks

Each pattern has 3MF, STL and editable STEP. `index.html` provides the interactive preview; serve this folder over HTTP to use it. Dimensioned SVGs use millimetres; check scaling if printing them on paper. `source/build_templates.py` regenerates exact CAD using CadQuery 2.8 and trimesh from the saved reference data. `parameters.json`, `validation.json` and `slice-checks.json` record dimensions, geometry and slicing checks. Physical print accuracy and panel construction have not been validated.

R2 changes the construction notes to the 0.2 mm channel. Printable tracing geometry is identical to R1 and also fits the R8 door; cleat changes do not affect these profiles.
