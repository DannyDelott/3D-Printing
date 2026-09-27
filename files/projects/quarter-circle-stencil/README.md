# Eighth-circle stencil

A lightweight 45-degree drawing stencil for tracing circular arcs while laying out furniture designs on graph paper.

## Status

Ready for first test print.

## Files

| File | Purpose |
| --- | --- |
| `models/eighth-circle-stencil-1-to-10-inch.stl` | Print-ready one-piece stencil |
| `source/generate_stencil.py` | Dependency-free parametric STL generator |
| `images/eighth-circle-stencil-preview.svg` | Top-view reference preview |

## Fit and dimensions

- Ten concentric 45-degree rails provide 19 useful labeled radii from 1 through 10 inches in 0.5-inch increments.
- Every inner and outer curved edge has its own number. The numbers omit inch marks to keep them easy to read.
- Integer radii are on the outside edges; half-inch radii from 1.5 through 9.5 are on the inside edges. The obstructed 0.5-inch inner edge is intentionally unlabeled.
- The two straight sector spines converge at the rounded circle-center corner.
- Footprint: approximately 232.9 × 232.9 mm. The 45-degree sector is oriented diagonally to preserve the exact 10-inch radius while fitting inside a 250 × 250 mm bed.
- Body thickness: 3.2 mm; raised labels add 0.4 mm, for a 3.6 mm maximum thickness.
- Each curved rail is exactly 12.7 mm (0.5 inch) wide; each sector spine is 6 mm wide.

## Print notes

- Import the STL into Bambu Studio as millimetres and keep it flat on the bed.
- Print at 0.20 mm layer height with a 0.4 mm nozzle, 3 walls, and no supports.
- PLA is recommended for stiffness and dimensional stability. A light color makes the raised labels easiest to read.
- Center the part on the plate. Its approximately 232.9 mm square footprint leaves about 8.5 mm per side on a 250 × 250 mm bed.
- A narrow skirt may fit, but check Bambu Studio's printable-area preview and any printer-specific exclusion zones before sending the job.
- For contrasting lettering at 0.20 mm layers, insert a filament color change after layer 16 when the 3.2 mm body finishes; the final two layers form the raised labels.
- Let the part cool before removal so the long, thin rails stay flat.

## Use

Align the rounded corner where the two straight spines converge with the desired circle center. The spines mark the beginning and end of the 45-degree sector. Trace along the curved edge beside the desired number.

Because each rail is supported at its two endpoints, the tracing edge is continuous for essentially the entire 45-degree arc. Use light pencil pressure to avoid flexing a rail.

## Regeneration

Run:

```sh
python3 -m pip install -r source/requirements.txt
python3 source/generate_stencil.py
```

The main dimensions and the radius range are constants near the top of the script.

## Provenance

- Designer: OpenAI Codex, for Danny
- Original source: newly generated for this project
- License: no license declared; personal project
