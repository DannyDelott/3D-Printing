"""Publishing checks that exercise the build's artifact and URL boundaries."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build


class PublishingTests(unittest.TestCase):
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
