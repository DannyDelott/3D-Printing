# Simple closet space saver — hex panels

From-scratch parametric rebuild inspired by [EmrakulVs15Squirtles' Closet Space Saver](https://makerworld.com/en/models/2953785-closet-space-saver#profileId-3309905). It does not import or repair the original mesh.

## Construction

- Five simple planar surfaces generated from one extruded cross-section and two end panels
- Published 250 × 220 × 220 mm envelope and 25-degree basket angle
- 2.0 mm hex-patterned mounting face with solid hole reinforcement zones
- Hex-patterned short bottom; narrow front return remains solid
- 1.4 mm end, back, and angled basket panels
- One repeated regular hexagon: 18 mm flat-to-flat, 20.78 mm point-to-point, with six equal 10.39 mm sides
- Exact 1.5 mm tangent radii at all six internal hex corners to reduce stress concentrations
- 10 mm straight perimeter rails; only complete hex cells are used
- Four 5 mm mounting holes

There are no fillets, curved patches, clipped cells, decorative ribs, or repaired source faces. The mounting face retains a straight 10 mm perimeter and solid 12 mm-radius pads around all four holes.

## Material

- Rebuilt solid volume: 219,709.6 mm³
- Original source solid volume: approximately 345,357.7 mm³
- CAD-volume reduction: approximately 36.4%
- Solid-PLA equivalent at 1.24 g/cm³: approximately 272.4 g, versus the original profile's stated 400 g

Actual slicer estimates depend on extrusion width and gap filling. The 1.4 mm lattice panels are intended to resolve as three 0.42–0.45 mm lines.

## Files

- `output/closet-space-saver-simple-small-hex-print-ready.3mf` — recommended slicer import
- `output/closet-space-saver-simple-small-hex-print-ready.stl` — print-oriented STL
- `output/closet-space-saver-simple-small-hex.step` — editable CAD exchange file
- `output/closet-space-saver-simple-small-hex.brep` — exact OpenCascade solid
- `output/closet-space-saver-simple-small-hex-design.stl` — design orientation
- `build_rebuilt_model.py` — parametric generator

## Validation

- Valid OpenCascade BREP
- One connected solid
- Watertight, consistently wound STL and 3MF
- One mesh body
- Verified 220 × 220 × 250 mm design extents

Not yet physically test-printed. Suggested starting point: 0.2 mm layers, 0.4 mm nozzle, three walls, no supports, supplied 3MF orientation.

## License

The concept and published dimensions were inspired by the CC BY-NC-SA 4.0 source model. This rebuild is shared under the same license.
