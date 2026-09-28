"""Download preview coverage and 3MF placement regression checks."""
import json
import struct
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from zipfile import ZipFile

import build
import file_previews


class DownloadLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and 'download' in attrs:
            self.current = attrs | {'images': []}
            self.links.append(self.current)
        if tag == 'img' and self.current is not None:
            self.current['images'].append(attrs)

    def handle_endtag(self, tag):
        if tag == 'a':
            self.current = None


class FilePreviewTests(unittest.TestCase):
    def test_all_shown_print_files_have_matching_thumbnails(self):
        projects = json.loads((build.SITE / 'catalog.json').read_text())
        published = build.inventory(projects)
        seen = set()
        for project in projects:
            for view in build.project_views(project):
                parser = DownloadLinks()
                parser.feed(build.project_page(view, published))
                for link in parser.links:
                    path = unquote(urlsplit(link['href']).path)
                    if Path(path).suffix.lower() not in file_previews.FORMATS:
                        continue
                    source = (build.OUT / build.project_path(view)).parent / path
                    relative = source.resolve().relative_to(build.OUT.resolve()).as_posix()
                    original = build.SITE / relative if relative.startswith('assets/') else build.ROOT / relative.removeprefix('files/')
                    with self.subTest(file=relative, page=build.project_path(view)):
                        self.assertEqual(len(link['images']), 1)
                        image = link['images'][0]
                        expected = file_previews.thumbnail_path(original)
                        self.assertEqual(image['src'], build.href(build.project_path(view), expected))
                        self.assertTrue((build.SITE / expected).read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))
                        self.assertEqual(image['loading'], 'lazy')
                    seen.add(relative.removeprefix('files/'))
        self.assertTrue({p for p in published if Path(p).suffix.lower() in file_previews.FORMATS}.issubset(seen))

    def test_thumbnail_changes_when_source_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'part.stl'
            path.write_bytes(b'first revision')
            first = file_previews.thumbnail_path(path)
            path.write_bytes(b'second revision')
            self.assertNotEqual(first, file_previews.thumbnail_path(path))

    def test_3mf_preserves_nested_external_components_and_instances(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'model.3mf'
            with ZipFile(source, 'w') as archive:
                archive.writestr('_rels/.rels', '<Relationships><Relationship Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" Target="/3D/main.model"/></Relationships>')
                archive.writestr('3D/main.model', '''<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06"><resources>
                <object id="1"><components><component objectid="2" transform="1 0 0 0 1 0 0 0 1 2 0 0"/></components></object>
                <object id="2"><components><component objectid="3" p:path="/3D/parts.model"/></components></object>
                </resources><build><item objectid="1" transform="0 1 0 -1 0 0 0 0 1 10 20 30"/><item objectid="1"/></build></model>''')
                archive.writestr('3D/parts.model', '''<model><resources><object id="3"><mesh><vertices><vertex x="0" y="0" z="0"/><vertex x="1" y="0" z="0"/><vertex x="0" y="1" z="0"/></vertices><triangles><triangle v1="0" v2="1" v3="2"/></triangles></mesh></object></resources></model>''')
            before = source.read_bytes()
            result = file_previews.model_stl(source)
            self.assertEqual(struct.unpack_from('<I', result, 80)[0], 2)
            self.assertEqual(struct.unpack_from('<12fH', result, 84)[3:12], (10, 22, 30, 10, 23, 30, 9, 22, 30))
            self.assertEqual(struct.unpack_from('<12fH', result, 134)[3:12], (2, 0, 0, 3, 0, 0, 2, 1, 0))
            self.assertEqual(source.read_bytes(), before)

    def test_stl_geometry_is_passed_through_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'model.stl'
            data = b'solid preview\nendsolid preview\n'
            source.write_bytes(data)
            self.assertEqual(file_previews.model_stl(source), data)
