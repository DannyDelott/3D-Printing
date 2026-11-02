"""Project the installed drawer at its rear plane and near the core mouth."""
from model import P,drawer,r,rear_plane
from drawers import ANGLE
part=drawer('open')
def path(section,origin):
    return ' '.join('M'+' L'.join(f'{origin-x*2.0:.2f},{144-y*2.0:.2f}' for x,y in line)+'Z'
                    for line in section.to_polygons())
def fill(cs,x,color):
    return f'<path d="{path(cs,x)}" fill="{color}" fill-rule="evenodd"/>'
s=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 590 275"><style>text{font:14px system-ui;fill:#284237}</style>']
s.append(fill(r.circle(r.OD/2)-r.circle(r.ID/2),120,'#b99a71'))
s.append(fill(r.section,120,'#adc0af'))
s.append(fill(part.slice(rear_plane-.01),120,'#648876'))
s+=['<text x="28" y="29">Rear view · open drawer</text>',
    '<text x="22" y="249">Flat wall across the 78.6 mm body</text>',
    '<path d="M176 200l40 18h53" fill="none" stroke="#375b48"/>',
    '<text x="273" y="222">Lower corner rests on the print bed</text>',
    '<text x="275" y="70">Round face Ø86.8 mm</text>',
    '<text x="275" y="100">Nominal bore Ø83 mm</text>',
    '<text x="275" y="130">0.8 mm ahead of the clips</text>',
    f'<text x="275" y="160">Print axis {ANGLE:g}° above the bed</text></svg>']
(P/'drawer-rear.svg').write_text(''.join(s))
