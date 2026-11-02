"""Draw the two side pockets from the rear at the same scale."""
from model import P, pockets, r

def outline(section, origin):
    return ' '.join('M'+' L'.join(f'{origin-x*2.10:.2f},{315-y*2.10:.2f}' for x,y in ring)+'Z'
                    for ring in section.to_polygons())

def shape(geometry, origin, color):
    return f'<path d="{outline(geometry,origin)}" fill="{color}" fill-rule="evenodd"/>'

svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 550 280"><style>text{font:14px system-ui;fill:#263b32}</style>']
for origin, current in ((69,False),(332,True)):
    clip=r.box(-46,37,12,121)
    for x,y in [(0,0),(r.half,r.rise),(0,2*r.rise)]:
        svg.append(shape(clip ^ r.circle(44,x,y),origin,'#b99b73'))
    body=pockets['side_sweep'] if current else r.rnd(-43.35,43.6,-21.35,114.2,2.1)
    svg.append(shape(body,origin,'#7c9e8b'))
    upright=-3.7 if current else -14.5
    svg.append(shape(r.box(upright-1,44,upright+1,112),origin,'#3e5a4c'))
    svg.append(f'<text x="{origin-35}" y="45">'+('R3.6 · 36.55 mm' if current else 'R3.5 · 22 mm')+'</text>')
    svg.append(f'<text x="{origin-35}" y="266">'+('146.3 mL' if current else '88.6 mL')+'</text>')
svg+=['</svg>']
(P/'pocket-width.svg').write_text(''.join(svg))
