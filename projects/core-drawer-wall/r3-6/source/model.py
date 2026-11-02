"""R3.6 outer pockets and linked rim clips, in millimetres. Print rear rails upright."""
from pathlib import Path
import importlib.util
import json
import sys
from rail import rim_pair
from pockets import make
from spacers import build

P = Path(__file__).resolve().parents[1]
OUT = P / 'models'
# Reuse the actual R3.5 core drawers and grip geometry.
def load_previous():
    old = P.parent / 'r3-5/source'
    sys.path.insert(0, str(old))
    local = {key: sys.modules.pop(key) for key in ('pockets','spacers')}
    try:
        spec = importlib.util.spec_from_file_location('old_drawers', old/'model.py')
        model = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(model)
    finally:
        sys.modules.update(local)
        sys.path.pop(0)
    return model

old = load_previous()
r = old.r
pockets = make(r,old.mount.M,build(r),old.ff)
models = {}
checks = {}
groups = []
installed = []

def export(name, pieces):
    plate = r.plate(pieces)
    mesh = r.trimesh.util.concatenate([mesh for _,mesh in plate])
    r.OUT = OUT
    r.write3(name,plate)
    (OUT/f'{name}-r3.3mf').rename(OUT/f'{name}-r3-6.3mf')
    mesh.export(OUT/f'{name}-r3-6.stl')
    checks[name] = dict(bounds=mesh.extents.round(2).tolist(),bodies=len(plate))

def mounted(base):
    cy = -31 if base else r.rise/3
    plain = r.junction(base)
    if not base:
        # Rim lips carry the load. A 3 mm jaw captures the tube while the
        # original deeper ledges still support the underside of the drawer.
        plain = (plain ^ r.extr(r.profile(False),-r.lip-.1,2.95)) + r.guide()
    rear = plain
    # Give the rear screw its own flat seat, separate from the socket below.
    pad = r.rnd(-7.5,cy-6.4,7.5,cy+7.5,2.4)
    for x,y in (r.centers[:2] if base else r.centers):
        pad -= r.circle(r.ro,x,y)
    rear += r.extr(pad,0,2.8)
    rear -= r.extr(r.circle(2.4,0,cy+2.8),-2,20)
    rear -= r.extr(r.circle(4.85,0,cy+2.8),2.8,22)
    return rim_pair(r,plain,rear,0,cy-4.5)

def top_pair():
    zone = r.box(-9,37,9,49)
    cap = (r.circle(46.4)-r.circle(39.8)) ^ zone
    jaws = ((r.circle(46.4)-r.circle(44.55))+(r.circle(40.9)-r.circle(39.8))) ^ zone
    clips = []
    for rear in (False,True):
        tab = r.rnd(-7.4,43.65,7.4,61.8 if rear else 51.5,2.35)
        clip = r.extr(cap+tab,-r.lip,0)+r.extr(jaws,0,4.2)+r.extr(tab-r.circle(44.55),0,1.25)
        if rear:
            clip += r.extr(r.circle(4.9,0,56.5),0,2.8)
            clip -= r.extr(r.circle(2.4,0,56.5),-3,9)
        clips.append(clip)
    return rim_pair(r,*clips,0,48.5)

def pieces(pair):
    return [('Front socket',pair[0]),('Rear rail',pair[1])]

def add(shape,x,y,z,color,key,kit=None):
    shape = shape.translate((x,y,z))
    installed.append((shape,key))
    mesh = r.mesh(r.world(shape))
    models[len(installed)] = mesh
    groups.append([len(mesh.faces),color,key,kit])

def install_pair(pair,x,y,key,color=2,kit=None):
    add(pair[0],x,y,0,color,key,kit)
    groups[-1].append("Front socket")
    add(r.rear(pair[1]),x,y,0,color,key,kit)
    groups[-1].append("Rear rail")

def screw(x,y):
    shaft = r.extr(r.circle(2.1),-14.85,4.2)
    head = r.extr(r.circle(4.55),2.8,5.1)
    add(r.rear(shaft+head),x,y,0,4,'wood-screw')

def main():
    loc=[(-r.pitch,0,'open',0),(0,0,'front-back',-27),(r.pitch,0,None,0),
         (-r.half,r.rise,'open',0),(r.half,r.rise,'left-right',-41),
         (-r.pitch,2*r.rise,'open',-12),(0,2*r.rise,'front-back',0),(r.pitch,2*r.rise,'open',0)]
    for x,y,name,depth in loc:
        add(r.core,x,y,0,0,'core')
        if name:
            add(old.drawer(name),x,y,depth,1,'one-piece-'+name)
    feet=[]
    for sign in (1,-1):
        plain = r.junction(True,edge=sign)
        pair = rim_pair(r,plain,plain,sign*6.5,-31)
        if sign==1:
            export('fit',pieces(pair))
        feet.extend(pieces(pair))
        install_pair(pair,-sign*1.5*r.pitch,0,'dry-ends')
    export('dry-ends',feet)
    export('starter',[('Open drawer',old.drawer('open'))]+feet)
    base,upper,top=mounted(True),mounted(False),top_pair()
    export('base-mount',pieces(base))
    export('upper-mount',pieces(upper))
    export('top-clips',pieces(top))
    export('top-tier',pieces(upper)+pieces(top))
    for x in (-r.half,r.half):
        install_pair(base,x,0,'base-mount')
        middle=x<0
        install_pair(upper,x,0,'middle-mount' if middle else 'upper-mount',3 if middle else 2)
        if middle:screw(x,r.rise/3+2.8)
    install_pair(upper,0,r.rise,'upper-mount',2,'top-tier')
    install_pair(top,0,2*r.rise,'top-clips',3,'top-tier')
    screw(0,2*r.rise+56.5)
    sweeps=[]
    for name,sign in [('triangle-pocket',0),('left-pocket',1),('right-pocket',-1)]:
        tri=sign==0
        prefix='tri' if tri else 'side'
        frame=pockets[prefix+'_frame']
        axis=(0,61.45) if tri else (-3.0,r.rise)
        front,rear=rim_pair(r,frame(False),frame(True),*axis)
        tray=pockets[prefix+'_bin']
        profile=pockets[prefix+'_sweep']
        if sign==-1:
            front,rear,tray=[m.mirror((1,0,0)) for m in (front,rear,tray)]
            profile=profile.mirror((1,0))
        pair=(front,rear)
        items=pieces(pair)+[('Removable pocket',tray)]
        export(name,items)
        export(name+'-frame',items[:2])
        export(name+'-bin',items[2:])
        checks[name]['ml']=round(pockets[prefix+'_space'].volume()/1000,1)
        checks[name]['body_width_mm']=round(profile.bounds()[2]-profile.bounds()[0],2)
        starts=[(0,0,-16),(-r.half,r.rise,0),(r.half,r.rise,0)] if tri else [(-sign*r.pitch,0,0)]
        for x,y,depth in starts:
            install_pair(pair,x,y,name+'-frame',kit=name)
            add(tray,x,y,depth,1,name)
            body=r.extr(profile,-100,56)
            lip=r.extr(tray.project(),-100,-r.lip-.01)
            sweeps.append((len(installed)-1,(body+lip).translate((x,y,0))))
    for i,(shape,key) in enumerate(installed):
        for other,name in installed[:i]:
            volume=abs((shape ^ other).volume())
            assert volume<.001,(key,name,'installed',volume)
    for index,path in sweeps:
        for j,(part,name) in enumerate(installed):
            if j!=index:assert abs((path^part).volume())<.001,(installed[index][1],name,'withdrawal')
    # Main drawers travel straight through every clip and rail.
    for x,y,_,_ in loc:
        path=r.extr(r.section,-100,59).translate((x,y,0))
        for part,key in installed:
            if key.startswith('one-piece-'):continue
            assert abs((path^part).volume())<.001,(key,'core drawer travel')
    mesh=r.trimesh.util.concatenate(list(models.values()))
    mesh.export(OUT/'mock-assembly.stl')
    items=json.loads((P/'parts.json').read_text())
    assert {key for group in groups for key in group[2:4] if key}==set(items)
    (P/'colors.json').write_text(json.dumps(dict(rows=[3,2,3],groups=groups,items=items),indent=2)+'\n')
    (P/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')

if __name__=='__main__':main()
