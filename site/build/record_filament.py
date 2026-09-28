"""Record a successful Bambu CLI slice for a catalog model without publishing G-code."""
import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
SETTINGS = ('printer_model', 'nozzle_diameter', 'filament_type', 'filament_density',
            'filament_cost', 'layer_height', 'wall_loops', 'sparse_infill_density',
            'sparse_infill_pattern', 'enable_support', 'brim_type', 'line_width')


def record(source, folder, assumed=False, note=None):
    result = json.loads((folder / 'result.json').read_text())
    if result['return_code'] != 0 or not result['sliced_plates']:
        raise ValueError('A successful, nonempty slice is required')
    with ZipFile(folder / 'sliced.3mf') as archive:
        settings = json.loads(archive.read('Metadata/project_settings.config'))
        model = ElementTree.fromstring(archive.read('3D/3dmodel.model'))
        application = model.find('{*}metadata[@name="Application"]').text
    rates = list(map(float, settings['filament_cost']))
    plates = []
    for plate in result['sliced_plates']:
        filaments = [dict(id=f['id'], grams=f['total_used_g'], pricePerKg=rates[f['id'] - 1])
                     for f in plate['filaments']]
        plates.append(dict(plate=plate['id'], grams=sum(f['grams'] for f in filaments),
                           cost=sum(f['grams'] * f['pricePerKg'] / 1000 for f in filaments),
                           filaments=filaments, warning=plate['warning_message']))
        if plate.get('total_predication'):
            hours, minutes = divmod(round(plate['total_predication'] / 60), 60)
            plates[-1]['printTime'] = f'{hours} h {minutes} min' if hours else f'{minutes} min'
    entry = dict(sha256=hashlib.sha256((ROOT / source).read_bytes()).hexdigest(),
                 slicer=application, basis='assumed' if assumed else 'saved',
                 settings={key: settings.get(key) for key in SETTINGS}, plates=plates)
    if note:
        entry['note'] = note
    path = ROOT / 'site/filament-estimates.json'
    records = json.loads(path.read_text())
    records[source] = entry
    path.write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', help='Repository-relative original model path')
    parser.add_argument('folder', type=Path, help='Contains result.json and sliced.3mf')
    parser.add_argument('--assumed', action='store_true', help='Slice uses assumed settings')
    parser.add_argument('--note', help='Units or placement assumptions to display')
    args = parser.parse_args()
    record(args.source, args.folder, args.assumed, args.note)
