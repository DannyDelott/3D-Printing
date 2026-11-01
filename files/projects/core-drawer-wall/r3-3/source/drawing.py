from model import *
d=print_pose(drawer('open'));section=d.transform([[0,1,0,0],[0,0,1,0],[1,0,0,0]]).slice(0)
x0,z0,x1,z1=section.bounds();K=1.72
def xy(u,v):return 28+K*(u-x0),184-K*(v-z0)
def pt(a):return ' '.join(f'{t:.2f}' for t in a)
path=' '.join('M'+' L'.join(pt(xy(*p)) for p in loop)+'Z' for loop in section.to_polygons())
lines=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 380 220"><style>text{font:13px system-ui;fill:#274437}</style><rect width="380" height="220" fill="#f0f3ed"/>',f'<path d="{path}" fill="#779b88" fill-rule="evenodd" stroke="#485f50" stroke-width=".6"/>','<path d="M12 184H220" stroke="#364c40" stroke-width="2"/><text x="24" y="205">Print bed</text>']
for y,w,h,title in [(13,58.4,40,'Rear wall'),(13,f+1,87,'Full circular face'),(-31,f-12,155,'Integral pull · 45°')]:
 u,v=xy(k*(w-y),k*(w+y));lines += [f'<path d="M{u:.2f} {v:.2f}L233 {h-4}" stroke="#677d70" fill="none"/><text x="237" y="{h}">{title}</text>']
(P/'section.svg').write_text(''.join(lines)+'</svg>')
