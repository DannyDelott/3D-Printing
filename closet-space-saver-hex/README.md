# Closet Space Saver — hex-cutout remix

Print-friendly remix of [Closet Space Saver by EmrakulVs15Squirtles](https://makerworld.com/en/models/2953785-closet-space-saver#profileId-3309905).

## What changed

- Replaced the square grids on all five perforated faces with staggered hexagonal openings.
- Used vertically elongated, point-up hexagons with 45-degree roof facets on faces that rise during printing. This avoids the horizontal bridge at the top of each square opening.
- Preserved the source model's overall dimensions, 25-degree basket angle, hook geometry, 5 mm outer fillets, and four mounting holes.
- Omitted the source's final 0.9 mm edge-fillet feature. That feature is already topologically invalid in the original FreeCAD file and is the likely cause of the published model's “floating regions” slicer warning.

## Files

- `output/closet-space-saver-hex-print-ready.3mf` — recommended slicer import; already oriented like the author's print profile.
- `output/closet-space-saver-hex-print-ready.stl` — print-oriented STL.
- `output/closet-space-saver-hex-design.step` — editable CAD exchange file in the source/design orientation.
- `output/closet-space-saver-hex-design.brep` — exact OpenCascade solid.
- `output/closet-space-saver-hex-design.stl` — mesh in the source/design orientation.
- `build_hex_model.py` — reproducible geometry-generation script; dimensions and cell sizes are constants near the top.

## Validation

- OpenCascade BREP check: valid
- Connected solids: 1
- STL and 3MF: watertight, consistently wound, one body
- Design-orientation mesh extents: 220 × 220 × 250 mm
- Solid volume: 382,058.8 mm³

The 3MF contains geometry and orientation only; choose the filament, machine, wall count, and layer settings appropriate for your printer. The original author's starting point was PLA, 0.2 mm layers, two walls, and 15% infill.

## Attribution and license

Original model © EmrakulVs15Squirtles, licensed under [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-nc-sa/4.0/). This remix is distributed under the same license.
