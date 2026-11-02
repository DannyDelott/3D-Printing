"""Render the actual shell and rib section in print orientation."""
from model import drawer,old,P
m=drawer('open').transform([[0,1,0,0],[0,0,-1,0],[-1,0,0,0]])
def section(x):
    # Plot installed height horizontally and print height vertically.
    paths=[]
    for ring in m.slice(-x).to_polygons():
        xy=[(171+2.7*x,235+2.7*(v+old.ff)) for x,v in ring]
        paths.append('M'+' L'.join(f'{x:.2f},{v:.2f}' for x,v in xy)+' Z')
    return ' '.join(paths)
(P/'drawer-rear.svg').write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 275" role="img" aria-label="Print section at a rear rib"><style>text{{font:14px system-ui;fill:#25382d}}.note{{font-size:12px}}</style><rect width="560" height="275" fill="#f3f5ef"/><path fill="#527662" fill-rule="evenodd" d="{section(24)}"/><path stroke="#26392c" d="M34 236 H308"/><g stroke="#62726a" fill="none"><path d="M219 23 H322"/><path d="M199 56 L285 67 H322"/><path d="M248 232 H322"/></g><text x="332" y="27">Full, flat rear panel</text><text x="332" y="71">Sloped inner rib</text><text x="332" y="235">Round front on bed</text><text class="note" x="36" y="261">Open drawer · section 24 mm from center, print orientation</text></svg>''')
