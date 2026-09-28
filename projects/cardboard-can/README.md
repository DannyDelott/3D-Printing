# Cardboard can

A stackable storage can made with a cardboard filament-spool core, a printed lid, ring, bottom, and optional four-compartment divider.

## Files

- [Complete Bambu project](models/cardboard-can.3mf) — one plate with a lid, ring, bottom, and divider; original geometry, placements, and print settings retained.
- [Validation record](validation.json) — source SHA-256, archive integrity, plate contents, and transformed mesh bounds.

Imported into the collection on September 27, 2026. The archive's embedded creation/modification date is September 28, 2026.

## Individual component plates

Each download contains one component, centered on a single P1S plate in its original print orientation. The Bambu projects retain the complete project’s printer, filament, process, and object settings. STL files contain the same geometry in millimeters.

| Component | Bambu project | STL |
| --- | --- | --- |
| Lid | [3MF](models/cardboard-can-lid.3mf) | [STL](models/cardboard-can-lid.stl) |
| Ring | [3MF](models/cardboard-can-ring.3mf) | [STL](models/cardboard-can-ring.stl) |
| Bottom | [3MF](models/cardboard-can-bottom.3mf) | [STL](models/cardboard-can-bottom.stl) |
| Divider | [3MF](models/cardboard-can-divider.3mf) | [STL](models/cardboard-can-divider.stl) |

The complete single-plate project is available above. Print individual components when you need a replacement or a different quantity.

## Plates and dimensions

| Plate | Contents |
| --- | --- |
| Complete set | Lid, ring, bottom, one divider |

| Part | Dimensions |
| --- | --- |
| Lid | 93 mm diameter × 10 mm |
| Ring | Approximately 93 mm diameter × 5 mm |
| Bottom | Approximately 93 mm diameter × 7.9 mm |
| Divider | 83 × 83 × 53.2 mm |

Dimensions come from the saved meshes in millimeters. The cardboard core is supplied separately and is not included in the previews.

## Print and assembly

The saved configuration uses a Bambu Lab P1S with a 0.4 mm nozzle, Generic PLA, 0.20 mm layers, three walls, 15% infill, and supports disabled. Use the complete single-plate project or choose an individual component plate. The embedded box instructions say to match the cardboard core's notch to the nub in the ring.

## Validation

The 3MF ZIP integrity check passed. The complete-set preview matches the retained first plate. The extra plate has been removed from the download; the four remaining objects retain their original geometry, placements, and print settings. Physical fit and print results are undocumented.

## Rebuild component plates

Run `closet-space-saver-hex/.venv/bin/python3 projects/cardboard-can/source/split_components.py` from the repository root. The script copies the original component meshes and settings, preserves their rotations, and changes only placement to center each part on its own plate. It also exports matching STL files and records dimensions and hashes in `component-plates.json`. Existing component previews are embedded in the 3MF files when available. Re-slice the resulting 3MFs before refreshing site estimates.

## Related projects and attribution

- [Organizer for recyclable cardboard spool box](https://makerworld.com/en/models/1964946-organizer-for-recyclable-cardboard-spool-box#profileId-2112438)
- [Lightweight Recycled Box | Stackable](https://makerworld.com/en/models/1198037-lightweight-recycled-box-stackable#profileId-1210954)

The related links were supplied by the project owner. Embedded box metadata names **sdaendi** as designer and **JSBG** for the “Improved printability” profile. It declares **Standard Digital File License**. The divider is named `Divider_4_Boxes.stl` with source `Divider_4_Bodies (1).3mf` in the archive. Embedded attribution is preserved; no new license is granted by this repository.
