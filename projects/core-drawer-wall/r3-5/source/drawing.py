from model import *
# True rear profile and front silhouette in their printed coordinates.
def svg(v):return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {v}"><style>text{{font:13px system-ui;fill:#274437}}</style>']
g=svg('400 230');m=drawer('open');sec=m.transform([[1,0,0,0],[0,0,1,0],[0,1,0,0]]).slice(12)
path=' '.join('M'+' L'.join(f'{95+x*2:.2f} {183-(z-ff)*2:.2f}' for x,z in points)+'Z' for points in sec.to_polygons())
g+=[f'<path d="{path}" fill="#7c9d88" fill-rule="evenodd" stroke="#45604e" stroke-width=".7"/>','<path d="M5 184h181" stroke="#284435" stroke-width="2"/><text x="9" y="210">Print bed</text><text x="207" y="38">Pitched rear wall</text><path d="M202 35L130 49" fill="none" stroke="#6e8575"/><text x="207" y="143">Closed finger cup</text><path d="M202 139L120 162" stroke="#6e8575"/><text x="207" y="179">Flat face · Ø86.8 mm</text><path d="M202 175L169 181" stroke="#6e8575"/></svg>']
(P/'section.svg').write_text(''.join(g))
g=svg('660 235')
g+=['<text x="16" y="24">TOP RIM · SIDE SECTION</text><path d="M63 151h355v7H63z" fill="#ba956f"/><path d="M58 128h12v38H57z M410 99h16v67h-16z" fill="#87a187"/><path d="M425 66h70v130h-70z" fill="#decfb9"/>','<path d="M59 128h358v3H59z" fill="#666e69"/><path d="M404 111h65v3h-65z M401 107h5v11h-5z" fill="#58625b"/><text x="49" y="190">Front keeper</text><text x="182" y="190">60 mm cardboard</text><text x="410" y="217">¾″ plywood</text><text x="154" y="82">2.5 × 200 mm cable tie</text><path d="M220 87l12 42" stroke="#667568"/><text x="487" y="81">#8 × ¾″ screw</text><path d="M505 86l-50 26" stroke="#667568"/></svg>']
(P/'mount.svg').write_text(''.join(g))
