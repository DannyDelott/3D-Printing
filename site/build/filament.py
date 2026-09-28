"""Render recorded slicer estimates only while their source models still match."""
import hashlib
from html import escape
import math


def render(project, records, root):
    sources = [(label, path) for label, path in project['downloads'] if path in records]
    if not sources:
        raise ValueError(f'{project["slug"]}: record a filament estimate for a selected download')
    rows = []
    notes = []
    for label, path in sources:
        record = records[path]
        if hashlib.sha256((root / path).read_bytes()).hexdigest() != record['sha256']:
            raise ValueError(f'Stale filament estimate: {path}; slice the updated model again')
        selected = project.get('filamentPlates')
        plates = [plate for plate in record['plates'] if selected is None or plate['plate'] in selected]
        if not plates or (selected is not None and set(selected) != {p['plate'] for p in plates}):
            raise ValueError(f'{path}: missing selected plate estimate')
        for plate in plates:
            if any(not math.isfinite(plate[key]) or plate[key] <= 0 for key in ('grams', 'cost')):
                raise ValueError(f'{path}: invalid filament estimate')
            name = label if len(sources) > 1 else 'Print estimate'
            if len(plates) > 1 or selected is not None:
                name += f' · Plate {plate["plate"]}'
            values = [f'≈{plate["grams"]:.1f} g']
            if plate.get('printTime'):
                values.append(plate['printTime'])
            values.append(f'≈${plate["cost"]:.2f}')
            estimate = ' · '.join(f'<span>{escape(value)}</span>' for value in values)
            rows.append(f'<tr><th scope="row">{escape(name)}</th><td class="print-estimate">{estimate}</td></tr>')
        rates = sorted({f['pricePerKg'] for plate in plates for f in plate['filaments']})
        price = ', '.join(f'${rate:.2f}/kg' for rate in rates)
        settings = record['settings']
        if record['basis'] == 'saved':
            basis = 'Saved 3MF settings'
        else:
            basis = (f'Assumed P1S / PLA · {float(settings["layer_height"]):.2f} mm layers · '
                     f'{settings["wall_loops"]} walls · {settings["sparse_infill_density"]} '
                     f'{settings["sparse_infill_pattern"]} infill · no supports')
            if settings['brim_type'] != 'no_brim':
                basis += ' · brim included'
        note = f'{basis} · {price}. USD, filament only.'
        if record.get('note'):
            note += ' ' + record['note']
        warnings = {plate['warning'] for plate in plates if plate.get('warning')}
        if warnings:
            note += (' Slicer flagged floating regions; review orientation or supports before printing.'
                     if all('floating regions' in warning for warning in warnings)
                     else ' Slicer warnings: ' + ' '.join(sorted(warnings)))
        if len(sources) > 1:
            note = label + ': ' + note
        notes.append(f'<p class="small muted">{escape(note)}</p>')
    return ''.join(rows), ''.join(notes)
