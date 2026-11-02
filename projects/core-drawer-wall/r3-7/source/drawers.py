"""A flat rear wall and a small bed facet on its side edge. All distances in mm."""
import math
import numpy as np
ANGLE=48.
HEEL=22.
AZIMUTH=65.

def print_pose(shape):
    c,s=math.cos(math.radians(ANGLE)),math.sin(math.radians(ANGLE))
    u,v=math.cos(math.radians(AZIMUTH)),math.sin(math.radians(AZIMUTH))
    return shape.transform([[s*u,s*v,c,0],[-v,u,0,0],[c*u,c*v,-s,0]])

def make_drawers(old):
    r=old.r
    extr=r.extr
    rear=r.L+r.lip
    front=old.ff
    mouth=-r.lip-.8
    def ring(section,depth):
        xy=np.asarray(section.to_polygons()[0])
        return np.column_stack([xy,np.full(len(xy),depth)])
    flare=old.mount.M.hull_points(np.concatenate([ring(r.section,mouth),ring(r.circle(old.rad),front+2.4)]))
    exterior=extr(r.section,front+.1,rear)+flare+extr(r.circle(old.rad),front,front+2.4)
    # One short facet creates a print bed at the outer corner of the closed end.
    # The rest of the rear is a plane perpendicular to the slide direction.
    tangent=math.tan(math.radians(ANGLE))
    def heel(inset):
        u,v=math.cos(math.radians(AZIMUTH)),math.sin(math.radians(AZIMUTH))
        edge=min(x*u+y*v for x,y in r.section.to_polygons()[0])
        limit=edge+HEEL+inset/math.cos(math.radians(ANGLE))
        region=r.poly([(limit-110*tangent,rear-110),(60,rear-110),(60,rear+2),(limit+2*tangent,rear+2)])
        return extr(region,-95,95).transform([[u,0,-v,0],[v,0,u,0],[0,1,0,0]])
    exterior=exterior^heel(0)
    cavity=extr(old.s.ci,front+1.9,rear-1.65)^heel(1.65)
    # Keep the mouth closed over the portion projecting beyond the rim.
    cavity-=extr(r.box(-50,r.top-1.35,50,55),front,-r.lip)
    cavity=cavity^exterior
    # Tie the deepest end of the finger recess into the near wall. It then
    # grows from existing plastic at this print angle instead of starting in air.
    root=extr(r.rnd(-41,16.4,-30,19.8,.8),front+1,front+15.5)
    cup=(old.mount.M.batch_hull([root,old.cupwall])^exterior)
    shell=(exterior-cavity+cup)-old.pocket
    def drawer(style):
        if style=='open':return shell
        if style=='left-right':
            divider=extr(r.box(-.8,r.floor,.8,r.top),front,rear)
        else:
            divider=extr(r.box(-50,r.floor,50,r.top),21.2,22.8)
        return shell+((divider^cavity)-old.pocket)
    def capacity(style):return round((cavity-drawer(style)).volume()/1000,1)
    return drawer,capacity,rear
