"""Content-addressed download thumbnails and geometry for the local renderer."""
import hashlib
import posixpath
import struct
from xml.etree import ElementTree as ET
from zipfile import ZipFile


FORMATS = {'.stl', '.3mf'}


def thumbnail_path(source):
    return 'assets/file-previews/' + hashlib.sha256(source.read_bytes()).hexdigest() + '.png'


def model_stl(source):
    """Flatten the 3MF build, including nested/external components and placement.

    Only viewing geometry is derived; the original download is never rewritten.
    STL input already works with the site's shared renderer.
    """
    if source.suffix.lower() == '.stl':
        return source.read_bytes()
    with ZipFile(source) as archive:
        documents = {}

        def document(path):
            if path not in documents:
                root = ET.fromstring(archive.read(path))
                documents[path] = (root, {obj.get('id'): obj for obj in root.findall('{*}resources/{*}object')})
            return documents[path]

        def triangles(path, object_id, transforms, ancestors=()):
            key = (path, object_id)
            if key in ancestors:
                raise ValueError(f'Cyclic 3MF component: {key}')
            _, objects = document(path)
            obj = objects[object_id]
            mesh = obj.find('{*}mesh')
            if mesh is not None:
                vertices = []
                for vertex in mesh.findall('{*}vertices/{*}vertex'):
                    point = tuple(float(vertex.get(axis)) for axis in 'xyz')
                    for matrix in reversed(transforms):
                        point = tuple(sum(point[j] * matrix[j * 3 + i] for j in range(3)) + matrix[9 + i] for i in range(3))
                    vertices.append(point)
                for face in mesh.findall('{*}triangles/{*}triangle'):
                    yield tuple(value for key in ('v1', 'v2', 'v3') for value in vertices[int(face.get(key))])
            for child in obj.findall('{*}components/{*}component'):
                child_path = child.get('{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}path')
                if child_path:
                    child_path = child_path.lstrip('/') if child_path.startswith('/') else posixpath.normpath(posixpath.join(posixpath.dirname(path), child_path))
                yield from triangles(child_path or path, child.get('objectid'), transforms + transform(child), ancestors + (key,))

        def transform(element):
            value = element.get('transform')
            if not value:
                return []
            matrix = [float(n) for n in value.split()]
            if len(matrix) != 12:
                raise ValueError('Expected a 3MF transform with 12 values')
            return [matrix]

        relationships = ET.fromstring(archive.read('_rels/.rels'))
        start = next(rel.get('Target').lstrip('/') for rel in relationships if rel.get('Type', '').endswith('/3dmodel'))
        root, _ = document(start)
        data = bytearray(84)
        count = 0
        for item in root.findall('{*}build/{*}item'):
            for triangle in triangles(start, item.get('objectid'), transform(item)):
                data.extend(struct.pack('<12fH', 0, 0, 0, *triangle, 0))
                count += 1
        if not count:
            raise ValueError(f'No build geometry in {source}')
        struct.pack_into('<I', data, 80, count)
        return bytes(data)
