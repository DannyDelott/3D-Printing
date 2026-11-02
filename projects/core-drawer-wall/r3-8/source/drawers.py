"""Monolithic drawers printed label face down; z is depth into the core."""
import numpy as np

def print_pose(shape):
    return shape

def make_drawers(old):
    r=old.r
    rear=r.L+r.lip
    front=old.ff
    mouth=-r.lip-.8
    def ring(section,depth):
        xy=np.asarray(section.to_polygons()[0])
        return np.column_stack([xy,np.full(len(xy),depth)])
    flare=old.mount.M.hull_points(np.concatenate([ring(r.section,mouth),ring(r.circle(old.rad),front+2.4)]))
    exterior=r.extr(r.section,front+.1,rear)+flare+r.extr(r.circle(old.rad),front,front+2.4)
    cavity=r.extr(old.s.ci,front+1.9,rear-1.65)^exterior
    cavity-=r.extr(r.box(-50,r.top-1.35,50,55),front,-r.lip)
    # Thin permanent ribs grow in from the side walls. The few millimetres
    # of roof between ribs bridge when the straight transverse panel starts.
    def ribs(end):
        # Fill the rib along its upper side through the panel, so it stays
        # attached at both ends and presents a continuous line at roof height.
        bands=sum((r.extr(r.box(-46,y-.7,46,y+.7),front,end+.02)
                   for y in [-22,-9,4,17,30.5]),old.mount.M())
        # Pitch the ribs toward the floor/open bin so loose screws can
        # slide out of the rear corners rather than sitting on a ledge.
        bands=bands.transform([[1,0,0,0],[0,1,.8,-.8*end],[0,0,1,0]])
        return bands-old.rear_limit(end-1.2,4)
    back_ribs=ribs(rear-1.65)
    shell=(exterior-(cavity-back_ribs)+old.cupwall)-old.pocket
    def drawer(style):
        if style=='open':return shell.simplify(.001)
        if style=='left-right':
            divider=r.extr(r.box(-.8,r.floor,.8,r.top),front,rear)
        else:
            divider=r.extr(r.box(-50,r.floor,50,r.top),21.2,22.8)+ribs(21.2)
        return (exterior-(cavity-back_ribs-divider)+old.cupwall-old.pocket).simplify(.001)
    def capacity(style):return round((cavity-drawer(style)).volume()/1000,1)
    return drawer,capacity,rear
