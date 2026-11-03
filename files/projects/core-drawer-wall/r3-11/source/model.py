"""Split-front drawer. Coordinates: x across, y vertical in use, w depth (mm)."""
from pathlib import Path
import sys,json,struct
import numpy as np
import manifold3d as mf
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'r3-8/source'))
import model as base
old=base.old;r=base.r;ex=r.extr;B=r.box
ff=old.ff;D=ff+2.4;F=D+3.45;rear=r.L+r.lip
def xw(poly,lo,hi):
    return ex(r.poly(poly),lo,hi).transform([[1,0,0,0],[0,0,1,0],[0,1,0,0]])
def yw(poly,lo,hi):
    return ex(r.poly(poly),lo,hi).transform([[0,0,1,0],[1,0,0,0],[0,1,0,0]])
def volume(a,b):return abs((a^b).volume())
# Both keys are solid. Pull forces act on their undercut shoulders.
# The lower lead grows out of the front wall at 45° as the tray builds.
key_top=9.;gap=.22
keys=mf.Manifold();channels=mf.Manifold()
for cx in [-24.,24.]:
    def key_section(allow=0):
        return [(cx-4-allow,D+.32-allow),(cx+4+allow,D+.32-allow),
                (cx+2.75+allow,F+.12),(cx-2.75-allow,F+.12)]
    lead=yw([(-12,F+.13),(-12,F),(-8,D-.5),(12,D-.5),(12,F+.13)],cx-6,cx+6)
    keys+=xw(key_section(),-12,key_top)^lead
    blank=ex(B(cx-5.8,-12.5,cx+5.8,11.25),D-.12,F-.12)
    channel=blank-xw(key_section(gap),-13,key_top+.04)
    channels+=channel
# One blind spring on the outside of the front wall. It only prevents the
# face from sliding up; it does not carry the pull. The tray wall stays closed.
spring=yw([(-20,F+.15),(-20,F-.05),(-17.9,F-2.10),(1.8,F-2.10),
           (1.8,F-.70),(-17,F-.70),(-17,F+.15)],-3,3)
bump=yw([(-.65,F-2.05),(-.5,F-2.72),(.05,F-2.72),(1.65,F-2.08)],-2.95,2.95)
spring+=bump
catch=ex(B(-3.5,-10,3.5,-.74),D-.1,F-2.27)
# A continuous perimeter and flat pads register the back of the label face.
lip=ex((r.section-old.s.ci)^B(-50,-45,50,12),D+.12,F+.1)
upper_lip=ex((r.section-r.section.offset(-1.45))^B(-50,12.15,50,40),D-.1,F-.07)
pads=sum((ex(r.rnd(x-3,-23,x+3,-14,1),D-.1,F-.07) for x in [-10.,10.]),mf.Manifold())
hood=ex(B(-24.5,r.top+.12,24.5,r.top+1.45),D-.14,-r.lip-.8)
face=(ex(r.circle(old.rad),ff,D)+upper_lip+channels+catch+pads+hood+old.cupwall)-old.pocket
# The hood root must remain inside the front disk, and clears the top edge as
# the assembled face slides down. The cup enters through an open-topped notch.
front_wall=ex(r.section,F,F+1.6)-ex(B(-19.4,5.85,19.4,42),F-.1,F+1.8)
space=ex(old.s.ci,F+1.6,rear-1.65)^ex(r.section,F,rear)
shell=(ex(r.section,F,rear)-ex(old.s.ci,F-.1,rear-1.65))+lip+front_wall+keys+spring
def body(n):
    fence=mf.Manifold()
    if n=='left-right':fence=ex(B(-.8,r.floor,.8,r.top),F,rear)
    if n=='front-back':fence=ex(B(-50,r.floor,50,r.top),21.2,22.8)
    # Slot for the cup while fitting the common face from above.
    if n=='left-right':fence-=ex(B(-2,5.75,2,r.top+.1),F-.1,ff+15.5)
    return (shell+(fence^space)).simplify(.001)
face=face.simplify(.001)
def tray_pose(m):return m.rotate((90,0,0))
def fit():
    for n in ['open','left-right','front-back']:
        b=body(n)
        for s in [b,face]:
            m=r.mesh(s)
            assert m.is_volume and m.is_watertight and len(m.split())==1, (n,s.bounding_box(),m.is_watertight)
        assert volume(face,b)<.001,(n,'rest',volume(face,b))
        # Test straight-down insertion, allowing only the flexible tab to move.
        for dy in np.arange(0,27,.25):
            overlap=face.translate((0,dy,0))^b
            assert abs((overlap-spring).volume())<.001,(n,dy,overlap.volume())
        for approach in np.arange(-24,0.1,.5):
            assert volume(face.translate((0,24,approach)),b)<.001,(n,'entry',approach)
        assert abs((ex(r.section,rear-1.64,rear)-b).volume())<.001,'incomplete back'
        assert volume(face.translate((0,0,-.7)),keys)>1,'no axial retention'
        assert volume(face.translate((0,1,0)),spring)>.01,'no detent'
        assert volume(face.translate((0,-.4,0)),keys)>1,'no seated stop'
        assert abs((face^ex(B(-55,-55,55,55),-r.lip-.79,70)).volume())<.001
        print(n, round((space-b-face).volume()/1000,1),r.mesh(b).bounds.tolist(),flush=True)
def export(name,parts):
    from validation import print_check
    plate=r.plate(parts);r.OUT=P/'models';r.write3(name,plate)
    (r.OUT/(name+'-r3.3mf')).rename(r.OUT/(name+'-r3-11.3mf'))
    mesh=r.trimesh.util.concatenate([m for _,m in plate]);mesh.export(r.OUT/(name+'-r3-11.stl'))
    return dict(bounds=mesh.extents.round(2).tolist(),bodies=len(plate),
                bed_contact_mm2={label:print_check(r,m)['bed_contact_mm2'] for label,m in parts})

def generate():
    checks={}
    styles=['open','left-right','front-back']
    def pieces(n):return [(n+' tray, floor down',tray_pose(body(n))),('Common round face, label down',face)]
    for n in styles:
        checks[n]=export(n,pieces(n))
        checks[n]['ml']=round((space-body(n)-face).volume()/1000,1)
        mesh=r.trimesh.util.concatenate([r.mesh(r.world(m)) for m in (body(n),face)])
        mesh.export(P/'models'/(n+'-in-use.stl'))
    # Bench view: turn the separate face around so its sockets are visible
    # alongside the upright tray. This is not the insertion direction.
    bench=[r.mesh(r.world(body('open'))),r.mesh(r.world(face.rotate((0,180,0)).translate((92,0,-8))))]
    r.trimesh.util.concatenate(bench).export(P/'models/front-joint.stl')
    feet=[]
    for sign in [1,-1]:
        foot=base.grip(r,r.junction(True,edge=sign),r.centers[:2])
        feet+=base.pieces((foot,foot))
    checks['starter']=export('starter',pieces('open')+feet)
    clip=ex(B(-5,-21,31,12),ff-1,F+10)
    coupon_tray=(ex(B(-5,-21,31,12),F,F+1.6)+ex(B(-5,-21,31,-19.5),F,F+7)+keys+spring)^clip
    coupon_face=(ex(B(-5,-21,31,12),ff,D)+channels+catch+pads)^clip
    checks['front-fit']=export('front-fit',[('Rail and latch sample',tray_pose(coupon_tray)),('Face socket sample',coupon_face)])
    checks['front-fit'].update(rail_side_clearance_mm=gap,nominal_snap_deflection_mm=.45,rail_pull_undercut_mm=1.25)
    checks['face']=export('face',[('Common round face, label down',face)])
    (P/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    src=P.parent/'r3-10';meta=json.loads((src/'colors.json').read_text());raw=(src/'models/mock-assembly.stl').read_bytes()
    groups=[];blocks=[];idx=84;fixed=[]
    for g in meta['groups']:
        data=raw[idx:idx+50*g[0]];idx+=len(data)
        if g[2].startswith('one-piece-'):continue
        groups.append(g);blocks.append(data)
        vertices=np.frombuffer(data,np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')]))['v']
        t=r.trimesh.Trimesh(vertices.reshape(-1,3),np.arange(len(vertices)*3).reshape(-1,3),process=True)
        solid=mf.Manifold(mf.Mesh(t.vertices.astype('float32'),t.faces.astype('uint32')))
        assert solid.status()==mf.Error.NoError
        fixed.append(r.world(solid))
    assert idx==len(raw)
    for k,v in meta['items'].items():
        if v[2]:v[2]='../r3-10/'+v[2] if v[2].startswith('models/') else v[2]
    for n in styles:
        meta['items']['one-piece-'+n][1:]=['Floor-down tray with a separate slide-on front. The two rails carry the pull; the tab locks the face in place.','models/'+n+'-r3-11.3mf']
    meta['items']['drawer-face']=['Common round front','Slide down over both tray rails until seated. Optional glue pads are behind the front.','models/face-r3-11.3mf']
    for x,y,n in [(-r.pitch,0,'open'),(0,0,'front-back'),(-r.half,r.rise,'open'),(r.half,r.rise,'left-right'),(-r.pitch,2*r.rise,'open'),(0,2*r.rise,'front-back'),(r.pitch,2*r.rise,'open')]:
        for obj,key,role in [(body(n),'one-piece-'+n,'Tray'),(face,'drawer-face','Round front')]:
            mesh=r.mesh(r.world(obj.translate((x,y,0))))
            groups.append([len(mesh.faces),1,key,None,role]);blocks.append(r.trimesh.exchange.stl.export_stl(mesh)[84:])
        # Continuous withdrawal: only the conservative sliding section enters
        # the clips. The circular face always stays in front of them.
        path=(ex(r.section,-120,rear)+ex(r.circle(old.rad),-120,-r.lip-.8)).translate((x,y,0))
        for other in fixed:assert volume(path,other)<.002,(x,y,n,'withdrawal')
    meta['groups']=groups
    assert {k for g in groups for k in g[2:4] if k}==set(meta['items'])
    (P/'colors.json').write_text(json.dumps(meta,indent=2)+'\n')
    (P/'models/mock-assembly.stl').write_bytes(raw[:80]+struct.pack('<I',sum(g[0] for g in groups))+b''.join(blocks))
if __name__=='__main__':
    fit()
    generate()
