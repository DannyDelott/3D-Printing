# 3D Printing

A home base for printable models, slicer projects, experiments, and notes.

The [static model library](site/README.md) provides searchable project pages, interactive previews, specifications, and downloads. Build it with `python3 site/build/build.py`; publish accepted updates with `python3 site/build/publish.py`.

Each idea lives in its own folder under [`projects/`](projects/). A project can contain printable files in `models/`, editable CAD or generator files in `source/`, photos in `images/`, and its own README with printing and provenance notes.

## Projects

| Project | What is here | Files |
| --- | --- | --- |
| [Cabinet door templates](projects/cabinet-door-templates/) | Curved rail and stile routing templates, with dovetail print variants | 3MF, STL, STEP + interactive datasheets |
| [Fingernail-profile caul](projects/fingernail-profile-clamping-caul/) | Shaped veneer-clamping cauls | 3MF, STL, STEP + generators |
| [Closet space saver rebuild](closet-space-saver-rebuilt/) | Parametric hex-panel basket | 3MF, STL, STEP + generator |
| [Closet space saver remix](closet-space-saver-hex/) | Earlier hex-cutout remix | 3MF, STL, STEP + generator |
| [Eighth-circle stencil](projects/quarter-circle-stencil/) | Labeled 1–10 inch, 45-degree furniture-layout curve stencil | 1 × STL + editable generator |
| [Cardboard can](projects/cardboard-can/) | Two-plate cardboard spool box with lid, ring, bottoms, and dividers | 1 × 3MF + plate previews |
| [Deckpass](projects/deckpass/) | Cable grommet for a desktop or cabinet counter | 1 × 3MF |
| [UHK foot](projects/uhk-foot/) | Replacement/support foot for an Ultimate Hacking Keyboard | 1 × 3MF |
| [Ping-pong ball tail attachment](projects/ping-pong-ball-tail-attachment/) | Multi-plate side-clip attachment variants | 1 × 3MF |
| [Gridfinity rebuilt bin](projects/gridfinity/rebuilt-bin-4x3x8/) | 4 × 3 × 8 standard bin project | 1 × 3MF |
| [Gridfinity Jae drawer](projects/gridfinity/jae-drawer/) | Baseplate and spacer for a 319 × 423 mm drawer | 2 × 3MF |
| [Gridfinity tea drawer](projects/gridfinity/tea-drawer/) | Multi-plate base for a 342 × 472 mm drawer | 1 × 3MF |
| [Gridfinity Jae filing cabinet](projects/gridfinity/jae-small-filing-cabinet/) | Baseplate iterations and bins for a small filing cabinet | 4 × 3MF |

## Repository conventions

- Use one kebab-case directory per idea or physical setup.
- Keep print-ready STL and slicer-ready 3MF files in `models/`.
- Put editable CAD, OpenSCAD, scripts, or generator inputs in `source/`.
- Document dimensions, material, printer settings, fit notes, and model provenance in the project README.
- Name meaningful revisions explicitly, such as `mount-v2.3mf`; use Git history for routine iteration.
- Avoid committing generated G-code because it is large and printer-specific.

Start a new idea with the [project README template](docs/project-template.md).

## File formats

- `.3mf` files in this repository are generally Bambu Studio projects and can include build plates, printer settings, thumbnails, and imported attribution.
- `.stl` files are portable triangle meshes; STL does not encode units, material, or slicer settings.

## Rights and attribution

This is a working collection, not a blanket-licensed model library. Some project files include imported or third-party models. See [NOTICE.md](NOTICE.md) and each project README before redistributing anything.
