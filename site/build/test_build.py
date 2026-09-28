"""Publishing checks that exercise the build's artifact and URL boundaries."""
import json
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build


class PublishingTests(unittest.TestCase):
    def test_coupon_page_uses_matching_model_dimensions_and_downloads(self):
        projects = json.loads((build.SITE / 'catalog.json').read_text())
        cabinet = next(p for p in projects if p['slug'] == 'cabinet-door-templates')
        views = build.project_views(cabinet)
        coupon = next(p for p in views if p['activeView'] == 'rail-coupon')
        html = build.project_page(coupon, [])
        self.assertIn('rail-native-dovetail-v9-fit-test.stl', html)
        self.assertIn('0.20 mm total', html)
        self.assertNotIn('stile-template-left-dovetail-v13-bambu.3mf', html)
        self.assertNotIn('rail-template-native-dovetail-v10-bambu.3mf', html)
        self.assertIn('href="../index.html"', html)
        self.assertIn('href="../stile-coupon/index.html"', html)

    def test_stile_coupon_preserves_its_own_tolerance(self):
        projects = json.loads((build.SITE / 'catalog.json').read_text())
        cabinet = next(p for p in projects if p['slug'] == 'cabinet-door-templates')
        coupon = next(p for p in build.project_views(cabinet) if p['activeView'] == 'stile-coupon')
        html = build.project_page(coupon, [])
        self.assertIn('stile-dovetail-v13-fit-test-bambu.3mf', html)
        self.assertIn('0.05 mm total', html)
        self.assertNotIn('0.20 mm total', html)

    def test_sanding_plane_contains_approved_coupon_and_configured_plate(self):
        projects = json.loads((build.SITE / 'catalog.json').read_text())
        plane = next(p for p in projects if p['slug'] == 'sanding-plane')
        views = build.project_views(plane)
        self.assertEqual({p['activeView'] for p in views}, {'assembly', 'fit-coupon', 'body', 'shoe', 'knob'})
        coupon = next(p for p in views if p['activeView'] == 'fit-coupon')
        html = build.project_page(coupon, [])
        self.assertIn('sanding-plane-coupon.stl', html)
        self.assertIn('profile-jig-taper-lock-coupon-print-plate-configured.3mf', html)
        self.assertIn('profile-jig-profile-up-coupon-body.3mf', html)
        self.assertIn('90°', html)
        root = build.ROOT / plane['root']
        evidence = json.loads((root / 'validation-final-plate.json').read_text())
        for part in evidence['source_models'].values():
            self.assertEqual(hashlib.sha256((root / 'models' / part['file']).read_bytes()).hexdigest(), part['sha256'])
        plate = next(path for label, path in views[0]['downloads'] if 'Bambu project' in label)
        self.assertEqual(hashlib.sha256((build.ROOT / plate).read_bytes()).hexdigest(), evidence['configured_sha256'])

    def test_inventory_excludes_environment_archive_and_gcode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = ['NOTICE.md', 'projects/example/models/part.3mf',
                     'projects/example/archive/old.3mf', 'projects/example/.venv/private.py',
                     'projects/example/models/private.gcode.3mf', 'projects/example/secret.env']
            for name in paths:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            with patch.object(build, 'ROOT', root):
                self.assertEqual(build.inventory([{'root': 'projects/example'}]),
                                 ['NOTICE.md', 'projects/example/models/part.3mf'])

    def test_link_checker_handles_encoded_names_and_nested_pages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'projects/example').mkdir(parents=True)
            (root / 'files').mkdir()
            (root / 'files/my part.3mf').touch()
            (root / 'projects/example/index.html').write_text(
                '<a href="../../files/my%20part.3mf" download>Download</a>'
                '<a href="https://example.com">Source</a>')
            with patch.object(build, 'OUT', root):
                build.check_links()

    def test_missing_model_prevents_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'index.html').write_text('<div data-model="missing.stl"></div>')
            with patch.object(build, 'OUT', root), self.assertRaisesRegex(ValueError, 'missing.stl'):
                build.check_links()

    def test_parent_escape_prevents_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'outside.txt').touch()
            (root / 'output').mkdir()
            (root / 'output/index.html').write_text('<a href="../outside.txt">File</a>')
            with patch.object(build, 'OUT', root / 'output'), self.assertRaisesRegex(ValueError, 'outside.txt'):
                build.check_links()


if __name__ == '__main__':
    unittest.main()
