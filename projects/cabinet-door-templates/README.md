# Cabinet door templates

Routing templates for the rails and stiles of an 18″ × 27″ cabinet. The 15⅞″ × 27″ door is inset at its sides and flush at its top and bottom, with 2¼″ stiles. Hinges and the ⅜″ hinge strip go on the right; the knob is centered on the left stile.

**Start with [the interactive comparison and design library](index.html).** Each design groups its rails, stiles, revision status, and downloads.

| Design | Contents |
| --- | --- |
| [Elliptical](designs/elliptical/README.md) | Chosen curve; matching rails and stiles, honeycomb and dovetail revisions |
| [Continuous sweep](designs/continuous-sweep/README.md) | Bézier alternative; rail templates only |
| [Original circles](designs/original-circles/README.md) | Original two-circle profile; rail templates only |

## Current working files

- [V10 rail and datasheet](designs/elliptical/rails/revisions/v10/datasheet.html): five short-side hexagons and eight tall-side hexagons, unchanged approved V9 joint, 12.70 mm thick, 0.20 mm total width clearance (0.10 mm per side). V7 was tight and damaged the pin; V8 at 0.40 mm was too loose. The user confirmed the V9 coupon fits great. Joint fit is approved; full template strength remains untested.
- [V13 stile · full fit failed](designs/elliptical/stiles/revisions/v13/datasheet.html): applies the successful V12 .05 coupon fit to the full ½″ stile. Total width clearance is 0.05 mm (0.025 mm per side), with the tail preserved, 0.30/0.20 mm external/internal radii and 2° taper. Two halves are arranged and sliced for the P1S: about 2h 40m and 141.3 g. The V12 .05 coupon passed, but the full V13 print was subsequently reported too tight with bowed socket arms. Hold further full-stile prints pending correction.
- [All half-inch templates](designs/comparison/half-inch-templates.html): unsplit outlines and split print projects.

The design manifests record these selections and their compatibility. Earlier templates retain their original thickness and tolerances. Do not combine halves from different joint revisions.

## Where things live

```text
designs/<design>/design.json                 Dimensions, selected revisions, artifact ownership
designs/<design>/<rails|stiles>/revisions/   One folder per revision
source/                                     Shared Python scripts and HTML templates, kept flat
archive/                                    Session backups, old project notes, migration record
```

Each revision has a README and datasheet. Its files are grouped in `models/`, `native-source/`, `fit-test/`, `images/`, and `validation/` as applicable. Native Bambu sources are preserved inputs. `designs/comparison/` holds the few assets and reports shared across designs.

## Build and preview

From the repository root, using the CAD environment:

```sh
closet-space-saver-hex/.venv/bin/python3 projects/cabinet-door-templates/source/build_library.py
closet-space-saver-hex/.venv/bin/python3 projects/cabinet-door-templates/source/build_comparison.py
closet-space-saver-hex/.venv/bin/python3 projects/cabinet-door-templates/source/check_project.py
python3 projects/cabinet-door-templates/source/serve.py --port 8767
```

The server preserves old bookmarked URLs through redirects. The new entry point is `http://127.0.0.1:8767/`.

Generators resolve inputs and outputs through `source/project_paths.py` and the design manifests. Register new revision files in their owning manifest before generating them. Publishing does not establish physical print approval.

See [the shared script guide](source/README.md), [domain glossary](CONTEXT.md), and [archived project history](archive/project-history.md) for reproduction details and earlier decisions.
