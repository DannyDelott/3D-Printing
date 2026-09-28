# Model library

A static GitHub Pages site. Python's standard library builds HTML and copies the selected project artifacts. No package installation is needed. Search runs in the browser; interactive model previews load automatically on model pages. Three.js 0.186.1, STLLoader and OrbitControls are vendored under `assets/three/`, with their MIT license; no external viewer CDN is needed. The directory, specifications, and downloads work without JavaScript.

## Run locally

From the repository root:

```sh
python3 site/build/build.py
python3 -m http.server 8774 --bind 127.0.0.1 --directory _site
```

Open http://127.0.0.1:8774/.

```sh
python3 -m unittest discover -s site/build -p 'test_*.py'
```

The build checks every local HTML link, including original datasheets. Missing files stop the build. Relative URLs support the repository prefix used by GitHub Pages.

## Update a project

1. Keep geometry and source files in the existing project folder.
2. Update its entry in `site/catalog.json`: selected revision, print instructions, dimensions, fit results, downloads, preview image, and preview mesh.
3. Keep the image, interactive mesh, specifications, and selected downloads on the same revision. Use exact status labels; coupon approval does not establish full-part strength.
4. Group component models and their test coupons in `views`, with a shared `group` and separate model, preview, dimensions, and downloads for each view. Give compatible older coupons their actual revision; for example, Rail V10 uses the approved V9 joint coupon.
5. Add a dimensioned drawing or original datasheet link when available. Preserve source and license information. Show the attribution sentence and optional inspiration links below downloads, without a heading or source-code download links. Optional `related` entries are `[label, URL]` pairs.
6. Build and check the page before pushing to `main`.

The catalog `root` includes model formats, original HTML datasheets, images, source scripts, documentation, and validation files. `archive/`, environments, scratch `work/`, and `.gcode.3mf` files are excluded. Older standalone closet projects publish their output and source folders and top-level source/notes. `_site/publication.json` lists the exact project artifacts in the deployment.

Some existing Bambu projects have a derived STL in `site/assets/` for viewing. Download links always use the original project files. Re-export those previews when geometry changes. The original HTML datasheets retain their existing design.

## Publish

After committing the accepted changes on `main`, run:

```sh
python3 site/build/publish.py
```

This builds and checks the site, verifies that published inputs are committed, pushes `main`, and updates `gh-pages`. GitHub Pages automatically deploys that branch. Wait for the Pages deployment and verify `build-info.json` matches the source commit before reporting the site live.

The repository is public. Pages uses **Deploy from a branch → gh-pages → / (root)**. This supported branch-based setup avoids the additional OAuth workflow permission required to create custom Actions workflows. No extra credentials are stored.

## UI conventions

The accepted direction is the compact index (prototype C).

- Use a plain project directory without an app name, logo, or branded header.
- Lead with project names, categories, and search; omit revision subtitles from the index. Omit the design status column; keep fit evidence on model pages.
- Use factual labels and instructions. No promotional headline, introductory copy, narrative footer, or project-page description.
- Project pages group preview, specifications, print instructions, validation, downloads, source attribution, and earlier files. Omit status badges, repeated revision labels, and preview captions; keep fit evidence in Validation.
- Keep the index readable on phones; hide secondary columns and retain project names.
- Use white backgrounds, subdued green model previews, dark text, and thin separators.

The discarded variants remain local in `site-prototype/` and are not part of the build or deployment.

## Filament estimates

Every model page shows recorded Bambu Studio slice estimates below its specifications. `site/filament-estimates.json` stores source SHA-256 hashes, settings, per-plate grams, material prices, costs, and slicer warnings. The build rejects changed model files until their estimates are refreshed. Empty file/revision sections and their navigation links are omitted.

Estimates use each configured 3MF's saved settings and material cost per kilogram, interpreted as USD. Each plate and each alternative file has its own row; alternative prints are not added together. `filamentPlates` selects the relevant plates for a catalog view, as on Cardboard can. Costs cover filament only.

For geometry-only files, the estimates use P1S / PLA, a 0.4 mm nozzle, 0.20 mm layers, 0.42 mm line width, 1.24 g/cm³ density, $20/kg, and no supports. Wall counts, infill, and brims follow project notes: caul 4 walls / 20%; tote and coupon 5 walls / 30% / outer brim; closet remix 2 walls / 15%; stencil and handle 3 walls / 15%. Assumed infill is gyroid. The handle's STL units are assumed to be millimeters. Only temporary estimation copies were configured and positioned; original downloads are unchanged.

To refresh a configured project, slice it with the installed Bambu Studio CLI, retaining the saved orientation and arrangement:

```sh
/Applications/BambuStudio.app/Contents/MacOS/BambuStudio --orient 0 --arrange 0 --slice 0 --outputdir /tmp/model-estimate --export-3mf sliced.3mf /absolute/path/to/model.3mf
python3 site/build/record_filament.py projects/example/models/model.3mf /tmp/model-estimate
```

For geometry-only files, first configure a temporary Bambu project with the documented assumptions and slice it. Record the original geometry path with `--assumed` and optional `--note`. Review slicer warnings, keep the recorded source and sliced geometry in sync, then rebuild. G-code and sliced projects stay out of the publication.

## Model previews

`viewer.js` uses the STL loader, antialiased rendering, crease-aware normals and orbit controls. Detail pages open in 3D automatically, with the PNG retained as a no-JavaScript or WebGL-failure fallback. Downloads always retain their original geometry.

Regenerate the PNG thumbnails with the same renderer after changing a mesh:

```sh
python3 site/build/build.py
python3 site/build/previews.py
```

Open http://127.0.0.1:8775/_previews and choose **Generate thumbnails**. This local-only tool writes catalog PNGs into `site/assets/`; rebuild afterward. The generator is not published.
