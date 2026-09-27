# Model library

A static GitHub Pages site. Python's standard library builds HTML and copies the selected project artifacts. No package installation is needed. Search runs in the browser; model previews load only when requested. The directory, specifications, and downloads work without JavaScript.

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
4. Add a dimensioned drawing or original datasheet link when available. Preserve source and license information.
5. Build and check the page before pushing to `main`.

The catalog `root` includes model formats, original HTML datasheets, images, source scripts, documentation, and validation files. `archive/`, environments, scratch `work/`, and `.gcode.3mf` files are excluded. Older standalone closet projects publish their output and source folders and top-level source/notes. `_site/publication.json` lists the exact project artifacts in the deployment.

Some existing Bambu projects have a derived STL in `site/assets/` for viewing. Download links always use the original project files. Re-export those previews when geometry changes. The original HTML datasheets retain their existing design.

## Publish

Updates may be pushed directly to `main` after checks; no PR or user code review is required for this project. `.github/workflows/pages.yml` validates the site and deploys updates to `main` to the `github-pages` environment. It also validates any optional pull requests. A manual workflow run on `main` can republish the current revision.

Enable **Settings → Pages → Source → GitHub Actions** once. Private repositories require a GitHub plan that supports Pages. Do not change repository visibility as part of site setup. Review site visibility and project-specific redistribution rights before the first deployment.

## UI conventions

The accepted direction is the compact index (prototype C).

- Lead with project names, revisions, status, categories, and search.
- Use factual labels and instructions. No promotional headline, introductory copy, narrative footer, or project-page description.
- Project pages group preview, specifications, print instructions, validation, downloads, source attribution, and earlier files.
- Keep the index readable on phones; hide secondary columns and retain names and revisions.
- Use white backgrounds, subdued green model previews, dark text, and thin separators.

The discarded variants remain local in `site-prototype/` and are not part of the build or deployment.
