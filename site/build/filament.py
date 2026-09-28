"""Render recorded slicer estimates only while their source models still match."""
import hashlib
from html import escape
import math


def render(project, records, root):
    sources = [(label, path) for label, path in project['downloads'] if path in records]
    if not sources:
        raise ValueError(f'{project["slug"]}: record a filament estimate for a selected download')
    groups = []
    for label, path in sources:
        record = records[path]
        if hashlib.sha256((root / path).read_bytes()).hexdigest() != record['sha256']:
            raise ValueError(f'Stale filament estimate: {path}; slice the updated model again')
        selected = project.get('filamentPlates')
        plates = [plate for plate in record['plates'] if selected is None or plate['plate'] in selected]
        if not plates or (selected is not None and set(selected) != {p['plate'] for p in plates}):
            raise ValueError(f'{path}: missing selected plate estimate')
        rows = ''
        for plate in plates:
            if any(not math.isfinite(plate[key]) or plate[key] <= 0 for key in ('grams', 'cost')):
                raise ValueError(f'{path}: invalid filament estimate')
            rows += f'<tr><th scope="row">Plate {plate["plate"]}</th><td>≈{plate["grams"]:.1f} g</td><td>≈${plate["cost"]:.2f}</td></tr>'
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
        heading = f'<h3>{escape(label)}</h3>' if len(sources) > 1 else ''
        groups.append(f'''{heading}<table class="specs filament-specs"><thead><tr><th scope="col">Print</th><th scope="col">Filament</th><th scope="col">Cost</th></tr></thead><tbody>{rows}</tbody></table>
<p class="small muted">{escape(note)}</p>''')
    return '<section class="filament-estimate"><h2>Filament estimate</h2>' + ''.join(groups) + '</section>'
