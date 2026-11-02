"""Rear rail and front socket. All coordinates in mm, measured from each rim inward."""

def rim_pair(r, front, back, x, y):
    """Two interlocking prints. The fork catches the front plate's outward face."""
    half = 2.0
    height = 2.6
    clearance = .25
    latch = .56
    # Both socket pads sit in the air between cardboard tubes.
    pad = r.rnd(x-3.45, y-2.65, x+3.45, y+2.65, .65)
    front += r.extr(pad, -r.lip, 1.8)
    socket = r.rnd(x-half-clearance, y-height/2-clearance,
                   x+half+clearance, y+height/2+clearance, .22)
    front -= r.extr(socket, -r.lip-1, 12)
    back += r.extr(pad, -r.lip, 2.6)
    # The fork is built upright from the rear plate. The shoulder emerges just
    # past the front rim. A 13 mm split gives each finger room to spring inward.
    shoulder = r.L + r.lip + .30
    rail_section = r.poly([(-half,0),(half,0),(half,shoulder-.45),
                           (half+latch,shoulder),(half+latch,shoulder+.38),
                           (half-.55,shoulder+2.2),(-half+.55,shoulder+2.2),
                           (-half-latch,shoulder+.38),(-half-latch,shoulder),
                           (-half,shoulder-.45)])
    rail = r.extr(rail_section, -height/2, height/2).transform(
        [[1,0,0,x],[0,0,1,y],[0,1,0,0]])
    rail -= r.extr(r.box(x-.68,y-3,x+.68,y+3), shoulder-13, shoulder+4)
    back += rail
    assert abs((r.rear(back) ^ front).volume()) < .001
    assert latch > clearance and 1.36 > 2*(latch-clearance)
    return front, back
