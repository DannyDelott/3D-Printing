"""R3.10: closed side housings anchored to plywood. Installed axes X, up, depth."""
from pathlib import Path
import sys,json,struct
import numpy as np
import manifold3d as mf
P=Path(__file__).resolve().parents[1]
OLD=P.parent/'r3-8'
sys.path.insert(0,str(OLD/'source'))
# Previous source is loaded under its original sibling modules.
import importlib.util
spec=importlib.util.spec_from_file_location('baseline',OLD/'source/model.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
r=base.r
ex=r.extr;B=r.box;C=r.circle
M=base.old.mount.M
centers=[(0,0),(r.half,r.rise),(0,2*r.rise)]
previous=base.pockets
front=-r.lip
rear=r.L+r.lip
# Slightly narrower tray leaves room for a solid enclosure in the same half-gap.
sx=.90; sy=.87; dx=-25*(1-sx);dy=46.0-43.6*sy
sz=.931;dz=base.old.ff*(1-sz)
def sized(m):return m.scale((sx,sy,sz)).translate((dx,dy,dz))
profile=previous['side_sweep'].scale((sx,sy)).translate((dx,dy))
left,low,right,high=profile.bounds()
bore=profile.offset(.44,circular_segments=48)
# 1.55 mm closed sleeve; nominal core keep-outs apply over the full axial span.
outer=bore.offset(1.55,circular_segments=48)
for x,y in centers:
    assert (outer^C(44.12,x,y)).area()<.001,(x,y,'core proximity',(outer^C(44.12,x,y)).area())
# The rear clips and screw boss print on their back. The mouth has a separate
# light rim plate; its outer edge bears against the sleeve over its full height.
mouth_back=base.old.ff+2.65
tube=ex(outer-bore,mouth_back, rear)+ex(outer,rear-2.5,rear)
rear_clip=r.rear(base.grip(r,previous['side_frame'](True),centers))
tube+=rear_clip-ex(bore,mouth_back,rear-2.5)
link=B(right-2,73,-2,83)-bore
tube+=ex(link,rear-2.5,rear)
# Rear screw sits recessed, away from the drawer's rear end. 3/4 inch plywood.
x,y=-25,78
tube+=ex(C(5.2,x,y),rear-4.5,rear)
tube-=ex(C(2.4,x,y),rear-5,rear+.1)+ex(C(4.7,x,y),rear-4.6,rear-2.5)
# Side-entry snap keeper, with its head outside the closed housing. The two
# tines flex only for insertion/removal. Drawer pull loads act across the pin.
zstop=6.; pin_y=low+16; inside=left-.44; wall=inside-1.55; boss_x=wall-2.2
def axial(m):return m.transform([[0,0,1,0],[1,0,0,pin_y],[0,1,0,zstop]])
def shaft(radius,a,b):return axial(ex(C(radius),a,b))
tube+=shaft(4.6,boss_x,wall+.2)
tube-=shaft(2.48,boss_x-.1,inside+.1)
head=shaft(4.5,boss_x-1.8,boss_x)
stem=shaft(2.28,boss_x-.1,left+2.5)
# Shallow paired ramps rebound on the inside of the sleeve.
ridge=M.batch_hull([shaft(2.28,inside+.1,inside+.12),shaft(2.62,inside+.5,inside+.52)])
ridge+=M.batch_hull([shaft(2.62,inside+.5,inside+.52),shaft(2.28,inside+1.1,inside+1.12)])
slit=ex(B(boss_x+.25,pin_y-.48,left+3,pin_y+.48),zstop-5,zstop+5)
pin=(head+stem+ridge)-slit
# Rim face sits flush with the end of the outer cheek. Add a full-height
# upright and continuous four-sided return at the mouth, clear of the core.
support=base.build(r)
front_clip=base.grip(r,support(False),centers)
# The full rim face surrounds the sleeve; the tall outer upright now bears
# against a continuous sleeve cheek rather than ending in a free sliver.
window=outer.offset(.18,circular_segments=48).simplify(.012)
front_clip=(front_clip+ex(window.offset(1.65).simplify(.012),front,0))-ex(window,-3,15)
tray=sized(previous['side_bin'])
# Remove the old proud intermediate lip, which used to stop on a bare frame.
tray=(tray^ex(profile,base.old.ff+.05,60))+(tray^ex(B(-50,0,0,135),base.old.ff,base.old.ff+2.35))
face=(bore.offset(.85,circular_segments=48)^B(-50,low,0,130))
tray+=ex(face-profile,base.old.ff,base.old.ff+2.15)
# Close the blind finger cup with two printable shoulders and a short
# central bridge, instead of sweeping a flat roof over the full pull width.
cx=(-43.35-6.8)/2;cy=114.2-9.5;rings=[]
for d,d_y,hw,hh in [(-.06,0,7,4.1),(2.1,1.2,7,4.1),(6.,1.2,4.62,.65)]:
    xy=np.asarray(r.rnd(cx-hw-.16,cy+d_y-hh-.16,cx+hw+.16,cy+d_y+hh+.16,min(hh-.03,2.8)).to_polygons()[0])
    rings.append(np.column_stack([xy,np.full(len(xy),base.old.ff+d+(.12 if d>1 else 0))]))
cup=sized(M.hull_points(np.concatenate(rings)))^ex(profile,base.old.ff,0)
cx=cx*sx+dx;peak=cy*sy+dy+3.6
roof=r.poly([(cx-10,peak-9),(cx-1,peak),(cx+1,peak),(cx+10,peak-9),(cx+10,115),(cx-10,115)])
tray+=cup^ex(roof,base.old.ff,0)
tray_rear=tray.bounding_box()[5]
groove_lo=pin_y-3.3; groove_hi=pin_y+3.3
notch=ex(r.poly([(left-1.5,groove_lo),(left+3.1,groove_lo),(left+3.1,groove_hi),(left-1.5,groove_hi+4.6)]),-3,tray_rear-4.5)
reinforcement=ex(r.poly([(left-.1,groove_lo-6.2),(left+4.65,groove_lo-1.45),(left+4.65,groove_hi+1.45),(left-.1,groove_hi+6.2)]),-3,tray_rear-3)
tray=(tray+(reinforcement^ex(profile,-3,tray_rear-3)))-notch
travel=tray_rear-4.5-(zstop+2.62)
def intersect(a,b):return abs((a^b).volume())
def printable(s):return s.rotate((180,0,0))
def fit():
    for name,m in [('front',front_clip),('housing',tube),('drawer',tray)]:
        print(name,m.bounding_box(),len(m.decompose()),flush=True)
    assert intersect(front_clip,tube)<.001,('mouth interference',intersect(front_clip,tube))
    assert intersect(tube,pin)<.001 and intersect(front_clip,pin)<.001
    for dz in [0,travel]:
        assert max(intersect(tray.translate((0,0,-dz)),p) for p in [tube,front_clip,pin])<.001
    for height in (-.44,0,.44):
        for shift in (-.44,0,.44):
            assert intersect(pin,tray.translate((shift,height,-travel-1)))>.2,'stop bypass'

def plate(name,pieces):
    plate=r.plate(pieces)
    r.OUT=P/'models'
    r.write3(name,plate)
    (r.OUT/(name+'-r3.3mf')).rename(r.OUT/(name+'-r3-10.3mf'))
    mesh=r.trimesh.util.concatenate([m for _,m in plate]);mesh.export(r.OUT/(name+'-r3-10.stl'))
    return dict(bodies=len(pieces),bounds_mm=mesh.extents.round(2).tolist())

def generate():
    from validation import print_check
    fit()
    for z in np.arange(0,101,.75):
        solids=[front_clip,tube]+([pin] if z<travel else [])
        assert max(intersect(tray.translate((0,0,-z)),p) for p in solids)<.001
    src=P.parent/'r3-9'
    meta=json.loads((src/'colors.json').read_text())
    raw=(src/'models/mock-assembly.stl').read_bytes();index=84
    groups=[];facets=[];others=[]
    for g in meta['groups']:
        size=g[0]*50; data=raw[index:index+size]; index+=size
        if g[2].startswith(('left-pocket','right-pocket')):continue
        # Use the actual installed mesh so adjacent drawer fronts, rim clips,
        # cores, plywood screws and their locations all participate in the check.
        verts=np.frombuffer(data,dtype=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')]))['v']
        mesh=r.trimesh.Trimesh(verts.reshape(-1,3),np.arange(len(verts)*3).reshape(-1,3),process=True)
        solid=M(mf.Mesh(mesh.vertices.astype('float32'),mesh.faces.astype('uint32')))
        assert solid.status()==mf.Error.NoError
        others.append((g[2],r.world(solid)))
        facets.append(data);groups.append(g)
    checks={}
    for name,sgn in [('left-pocket',1),('right-pocket',-1)]:
        aa,bb,cc,dd=[s.simplify(.0005) if sgn==1 else s.mirror((1,0,0)).simplify(.0005) for s in [front_clip,tube,tray,pin]]
        for s in (aa,bb,cc,dd):assert len(s.decompose())==1
        origin=(-sgn*r.pitch,0,0)
        for key,s in [('front',aa),('housing',bb),('drawer',cc),('keeper',dd)]:
            placed=s.translate(origin)
            for k,other in others:
                v=intersect(placed,other)
                if k=='core' and key in ['front','housing'] and v>.001:
                    xmin,ymin,_,xmax,ymax,_=other.bounding_box()
                    band=ex(C(r.ID/2+.162,(xmin+xmax)/2,(ymin+ymax)/2),-.1,r.L+.1)
                    assert abs(((placed^other)-band).volume())<.001,(name,key,k,'core clash')
                else:assert v<.002,(name,key,k,v)
        for offset,height in [(travel,0),(100,0)]:
            item=cc.translate((origin[0],height,-offset))
            for k,other in others:assert intersect(item,other)<.002,(name,k,'sweep')
        parts=[('Front face frame',aa),('Enclosed housing, rear on bed',printable(bb)),('Removable keeper',dd.rotate((0,-sgn*90,0))),('Drawer, open side up',r.world(cc).rotate((0,0,90 if sgn==-1 else 0)))]
        preview=[r.mesh(r.world(obj)) for obj in (aa,bb,dd,cc.translate((0,0,-travel)))]
        r.trimesh.util.concatenate(preview).export(P/'models'/(name+'-in-use.stl'))
        for suffix,ps in [('',parts),('-frame',parts[:3]),('-bin',parts[3:])]:
            checks[name+suffix]=plate(name+suffix,ps)
        checks[name].update(clearance_mm=.44,stop_travel_mm=round(travel,2),engagement_at_stop_mm=round(tray_rear-travel-mouth_back,2),capacity_ml=round((sized(previous['side_space'])-cc).volume()/1000,1))
        for key,part in parts: checks[name][key]=print_check(r,part)
        for s,role,k,color in [(aa,'Front face frame',name+'-frame',2),(bb,'Fixed pocket housing',name+'-frame',2),(dd,'Removable travel keeper',name+'-frame',2),(cc,'Pocket drawer',name,1)]:
            placed=s.translate((origin[0],0,-20 if color==1 and sgn==1 else 0))
            mesh=r.mesh(r.world(placed));group=[len(mesh.faces),color,k,name if color==2 else None,role]
            groups.append(group); facets.append(r.trimesh.exchange.stl.export_stl(mesh)[84:])
        screw=ex(C(2.1,x*sgn,y),rear-2.5,rear+16.4)+ex(C(4.35,x*sgn,y),rear-4.25,rear-2.5)
        assert max(intersect(screw,v) for v in [aa,bb,cc,dd])<.002
        mesh=r.mesh(r.world(screw.translate(origin)))
        groups.append([len(mesh.faces),4,'wood-screw',None]);facets.append(r.trimesh.exchange.stl.export_stl(mesh)[84:])
        meta['items'][name]=[name.split('-')[0].capitalize()+' pocket','Enclosed housing and captive drawer. Pull the outside keeper to remove the bin.','models/'+name+'-r3-10.3mf']
        meta['items'][name+'-frame']=['Fixed '+name.split('-')[0]+' pocket','A full-depth sleeve with a backboard screw, a separate front face frame and a removable keeper.','models/'+name+'-frame-r3-10.3mf']
    for k,v in meta['items'].items():
        if v[2] and v[2].startswith('models/') and 'r3-10' not in v[2]:v[2]='../r3-9/'+v[2]
    meta['items']['wood-screw'][1]='Two screws anchor the middle and top clips; one screw in each side housing fixes its back to the plywood.'
    meta['groups']=groups
    (P/'models/mock-assembly.stl').write_bytes(raw[:80]+struct.pack('<I',sum(g[0] for g in groups))+b''.join(facets))
    (P/'colors.json').write_text(json.dumps(meta,indent=2)+'\n')
    (P/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
if __name__=='__main__':generate()
