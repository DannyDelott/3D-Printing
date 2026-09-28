"""Publishing checks that exercise the build's artifact and URL boundaries."""
import json
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree
from zipfile import ZipFile

import build
import filament


class PublishingTests(unittest.TestCase):
    def test_empty_archive_has_no_section_or_navigation(self):
        projects = json.loads((build.SITE / 'catalog.json').read_text())
        project = next(p for p in projects if p['slug'] == 'cardboard-can')
        html = build.project_page(build.project_views(project)[0], build.inventory([project]))
        self.assertNotIn('Project files & revisions', html)
        self.assertNotIn('href="#files"', html)

    def test_archive_remains_when_an_alternative_exists(self):
        projects = json.loads((build.SITE / 'catalog.json').read_text())
        project = next(p for p in projects if p['slug'] == 'cabinet-door-templates')
        html = build.project_page(build.project_views(project)[0], build.inventory([project]))
        self.assertIn('Project files & revisions', html)
        self.assertIn('Additional model files', html)

    def test_cardboard_complete_set_and_component_estimates_stay_separate(self):
        projects = json.loads((build.SITE / 'catalog.json').read_text())
        project = next(p for p in projects if p['slug'] == 'cardboard-can')
        self.assertEqual([v['id'] for v in project['views']], ['plate-1', 'lid', 'ring', 'bottom', 'divider'])
        first, second = [build.project_page(p, []) for p in build.project_views(project)[:2]]
        self.assertIn('≈82.4 g', first)
        self.assertIn('≈$1.65', first)
        self.assertNotIn('≈83.7 g', first)
        self.assertIn('≈21.9 g', second)
        self.assertIn('≈$0.44', second)
        self.assertNotIn('≈82.4 g', second)
        with ZipFile(build.ROOT / project['model']) as archive:
            model = ElementTree.fromstring(archive.read('3D/3dmodel.model'))
            settings = ElementTree.fromstring(archive.read('Metadata/model_settings.config'))
            self.assertEqual(len(settings.findall('plate')), 1)
            self.assertEqual(len(model.findall('{*}build/{*}item')), 4)

    def test_model_change_rejects_stale_estimate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'model.3mf').write_bytes(b'updated model')
            project = dict(slug='example', downloads=[['Model', 'model.3mf']])
            records = {'model.3mf': {'sha256': hashlib.sha256(b'old model').hexdigest()}}
            with self.assertRaisesRegex(ValueError, 'Stale filament estimate'):
                filament.render(project, records, root)

    def test_cardboard_component_plates_preserve_source_geometry_and_settings(self):
        models = build.ROOT / 'projects/cardboard-can/models'
        with ZipFile(models / 'cardboard-can.3mf') as original:
            for name, source_id in {'lid': '5', 'ring': '8', 'bottom': '11', 'divider': '2'}.items():
                with self.subTest(component=name), ZipFile(models / f'cardboard-can-{name}.3mf') as archive:
                    self.assertIsNone(archive.testzip())
                    model = ElementTree.fromstring(archive.read('3D/3dmodel.model'))
                    items = model.findall('{*}build/{*}item')
                    self.assertEqual([item.get('objectid') for item in items], [source_id])
                    objects = model.findall('{*}resources/{*}object')
                    self.assertEqual([obj.get('id') for obj in objects], [source_id])
                    component = objects[0].find('{*}components/{*}component')
                    path = component.get('{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}path').lstrip('/')
                    self.assertEqual(archive.read(path), original.read(path))
                    self.assertEqual(archive.read('Metadata/project_settings.config'), original.read('Metadata/project_settings.config'))
                    settings = ElementTree.fromstring(archive.read('Metadata/model_settings.config'))
                    plates = settings.findall('plate')
                    self.assertEqual(len(plates), 1)
                    self.assertEqual(len(plates[0].findall('model_instance')), 1)
                    self.assertEqual(plates[0].find('model_instance/metadata[@key="object_id"]').get('value'), source_id)

    def test_estimate_costs_match_saved_material_rates(self):
        records = json.loads((build.SITE / 'filament-estimates.json').read_text())
        for path, record in records.items():
            for plate in record['plates']:
                with self.subTest(source=path, plate=plate['plate']):
                    self.assertAlmostEqual(plate['grams'], sum(f['grams'] for f in plate['filaments']))
                    self.assertAlmostEqual(plate['cost'], sum(f['grams'] * f['pricePerKg'] / 1000 for f in plate['filaments']))

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
        self.assertEqual([p['activeView'] for p in views], ['assembly', 'exploded', 'build-plate', 'fit-coupon', 'body', 'shoe', 'knob', 'roundover-1-8', 'roundover-1-8-coupon'])
        plate_html = build.project_page(next(p for p in views if p['activeView'] == 'build-plate'), [])
        self.assertIn('data-model="../../../files/projects/sanding-plane/models/profile-jig-final-print-plate.stl"', plate_html)
        self.assertIn('profile-jig-final-print-plate-configured.3mf', plate_html)
        self.assertNotIn('profile-jig-profile-up-full-preview.3mf', build.project_page(views[0], []))
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

    def test_assembly_selector_links_to_shoes_and_preserves_component_navigation(self):
        projects = json.loads((build.SITE / 'catalog.json').read_text())
        plane = next(p for p in projects if p['slug'] == 'sanding-plane')
        for view in build.project_views(plane):
            html = build.project_page(view, [])
            self.assertEqual(html.count(' data-assembly-link'), 2)
            if view['activeView'] in ('assembly', 'exploded'):
                self.assertIn('id="assembly-shoe"', html)
                self.assertIn('value="roundover-1-8"', html)
                self.assertIn('data-details="' + build.href(build.project_path(view), 'projects/sanding-plane/roundover-1-8/index.html') + '"', html)
                self.assertIn('Magnate plate estimate', html)
                for shoe in plane['assemblyShoes']:
                    self.assertIn(shoe[view['assemblyMode']]['model'].split('/')[-1], html)
            else:
                self.assertNotIn('id="assembly-shoe"', html)

    def test_assembly_shoes_require_real_component_views_and_previews(self):
        projects = json.loads((build.SITE / 'catalog.json').read_text())
        plane = next(p for p in projects if p['slug'] == 'sanding-plane')
        plane['assemblyShoes'][0]['id'] = 'missing-shoe'
        with self.assertRaisesRegex(ValueError, 'distinct component views'):
            build.validate_catalog([plane])
        plane['assemblyShoes'][0]['id'] = 'shoe'
        plane['assemblyShoes'][0]['assembly']['model'] = 'assets/missing.stl'
        with self.assertRaisesRegex(ValueError, 'missing or unsafe path'):
            build.validate_catalog([plane])

    def test_assembly_previews_match_current_shoe_and_carrier_sources(self):
        projects = json.loads((build.SITE / 'catalog.json').read_text())
        plane = next(p for p in projects if p['slug'] == 'sanding-plane')
        evidence = json.loads((build.ROOT / plane['root'] / 'validation-assembly-previews.json').read_text())
        for shoe in plane['assemblyShoes'][1:]:
            for mode in ('assembly', 'exploded'):
                entry = evidence[f'{shoe["id"]}/{mode}']
                suffix = '-exploded' if mode == 'exploded' else ''
                paths = {'source_step_sha256': build.ROOT / shoe['source'],
                         'preview_sha256': build.SITE / shoe[mode]['model'],
                         'source_assembly_sha256': build.ROOT / plane['root'] / f'models/profile-jig-profile-up-full{suffix}-preview.3mf'}
                for key, path in paths.items():
                    self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry[key])

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
