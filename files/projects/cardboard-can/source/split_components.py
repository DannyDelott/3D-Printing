"""Extract one unchanged component per plate from the saved cardboard-can project.

Run with the repository's CAD Python (numpy and trimesh required). Optional site
thumbnails are embedded when present; the complete single-plate project is untouched.
"""
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
import trimesh

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[1]
SOURCE = PROJECT / 'models/cardboard-can.3mf'
SOURCE_SHA = '6a294010b940751973e6dffe9b25356547d86dbde9933f0c3b4ecf7c4540b8ae'
CORE = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
PROD = 'http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
MODEL_REL = 'http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel'
PARTS = {'lid': '5', 'ring': '8', 'bottom': '11', 'divider': '2'}
ET.register_namespace('', CORE)
ET.register_namespace('p', PROD)
ET.register_namespace('BambuStudio', 'http://schemas.bambulab.com/package/2021')


def matrix(text):
    result = np.eye(4)
    result[:3, :] = np.array([float(n) for n in text.split()]).reshape(4, 3).T
    return result


def transform_text(value):
    return ' '.join(f'{n:.12g}' for n in value[:3, :].T.flat)


def xml(element):
    return ET.tostring(element, encoding='utf-8', xml_declaration=True)


def relationships(target, thumbnail=False):
    root = ET.Element('Relationships', xmlns=REL)
    ET.SubElement(root, 'Relationship', Target=target, Id='rel-1', Type=MODEL_REL)
    if thumbnail:
        ET.SubElement(root, 'Relationship', Target='/Metadata/plate_1.png', Id='rel-2',
                      Type=REL + '/metadata/thumbnail')
    return xml(root)


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA, 'Source changed; review object IDs and settings'
    report = {'source': 'models/cardboard-can.3mf', 'sourceSha256': SOURCE_SHA, 'components': {}}
    with ZipFile(SOURCE) as source:
        assert source.testzip() is None
        original = ET.fromstring(source.read('3D/3dmodel.model'))
        original_config = ET.fromstring(source.read('Metadata/model_settings.config'))
        for name, object_id in PARTS.items():
            model = copy.deepcopy(original)
            resources = model.find(f'{{{CORE}}}resources')
            for obj in list(resources):
                if obj.get('id') != object_id:
                    resources.remove(obj)
            component = resources.find(f'{{{CORE}}}object/{{{CORE}}}components/{{{CORE}}}component')
            mesh_path = component.get(f'{{{PROD}}}path').lstrip('/')
            mesh_doc = ET.fromstring(source.read(mesh_path))
            obj = mesh_doc.find(f'{{{CORE}}}resources/{{{CORE}}}object[@id="{component.get("objectid")}"]')
            vertices = np.array([[float(v.get(k)) for k in 'xyz'] for v in obj.findall(f'{{{CORE}}}mesh/{{{CORE}}}vertices/{{{CORE}}}vertex')])
            faces = np.array([[int(f.get(k)) for k in ('v1', 'v2', 'v3')] for f in obj.findall(f'{{{CORE}}}mesh/{{{CORE}}}triangles/{{{CORE}}}triangle')])
            build = model.find(f'{{{CORE}}}build')
            for item in list(build):
                if item.get('objectid') != object_id:
                    build.remove(item)
            item = build[0]
            placement = matrix(item.get('transform'))
            component_matrix = matrix(component.get('transform'))
            oriented = trimesh.transform_points(vertices, placement @ component_matrix)
            low, high = oriented.min(axis=0), oriented.max(axis=0)
            center = (low + high) / 2
            offset = np.array([128 - center[0], 128 - center[1], -low[2]])
            placement[:3, 3] += offset
            item.set('transform', transform_text(placement))
            placed = trimesh.transform_points(vertices, matrix(item.get('transform')) @ component_matrix)
            np.testing.assert_allclose(placed, oriented + offset, atol=1e-7)
            assert np.all(placed.min(axis=0) >= -1e-6) and np.all(placed.max(axis=0) <= 256)
            stl_mesh = trimesh.Trimesh(vertices=placed - [128, 128, 0], faces=faces, process=False)
            stl_path = PROJECT / f'models/cardboard-can-{name}.stl'
            stl_mesh.export(stl_path)
            checked = trimesh.load_mesh(stl_path, process=True)
            assert checked.is_watertight and checked.is_winding_consistent and len(checked.split()) == 1, name
            np.testing.assert_allclose(checked.extents, high-low, atol=2e-5)

            config = copy.deepcopy(original_config)
            for child in list(config):
                if child.tag == 'object' and child.get('id') == object_id:
                    continue
                config.remove(child)
            plate = ET.SubElement(config, 'plate')
            for key, value in [('plater_id', '1'), ('plater_name', name.title()), ('locked', 'false'),
                               ('filament_map_mode', 'Auto For Flush'), ('filament_maps', '1'), ('filament_volume_maps', '0')]:
                ET.SubElement(plate, 'metadata', key=key, value=value)
            instance = ET.SubElement(plate, 'model_instance')
            for key, value in [('object_id', object_id), ('instance_id', '0'), ('identify_id', '1')]:
                ET.SubElement(instance, 'metadata', key=key, value=value)
            thumbnail = ROOT / f'site/assets/cardboard-can-{name}.png'
            for metadata in list(model.findall(f'{{{CORE}}}metadata')):
                if metadata.get('name', '').startswith('Thumbnail_'):
                    model.remove(metadata)
            entries = {key: source.read(key) for key in ('[Content_Types].xml', 'Metadata/project_settings.config', mesh_path)}
            if thumbnail.exists():
                entries['Metadata/plate_1.png'] = thumbnail.read_bytes()
                for key in ('Thumbnail_Middle', 'Thumbnail_Small'):
                    metadata = ET.Element(f'{{{CORE}}}metadata', name=key)
                    metadata.text = '/Metadata/plate_1.png'
                    model.insert(0, metadata)
                ET.SubElement(plate, 'metadata', key='thumbnail_file', value='Metadata/plate_1.png')
            entries.update({'3D/3dmodel.model': xml(model), 'Metadata/model_settings.config': xml(config),
                            '3D/_rels/3dmodel.model.rels': relationships('/' + mesh_path),
                            '_rels/.rels': relationships('/3D/3dmodel.model', thumbnail.exists())})
            output = PROJECT / f'models/cardboard-can-{name}.3mf'
            with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
                for key, value in entries.items():
                    archive.writestr(key, value)
            with ZipFile(output) as archive:
                assert archive.testzip() is None
                assert archive.read(mesh_path) == source.read(mesh_path)
                assert archive.read('Metadata/project_settings.config') == source.read('Metadata/project_settings.config')
            report['components'][name] = dict(sourceObjectId=object_id, triangles=len(faces),
                dimensionsMm=[round(float(n), 4) for n in checked.extents], watertight=True,
                connectedBodies=1, originalGeometryPreserved=True, originalSettingsPreserved=True,
                stlSha256=hashlib.sha256(stl_path.read_bytes()).hexdigest(),
                projectSha256=hashlib.sha256(output.read_bytes()).hexdigest())
    (PROJECT / 'component-plates.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
