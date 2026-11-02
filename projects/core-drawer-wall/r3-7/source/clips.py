"""Shallow tapered pads on the inside jaws pinch the cardboard locally."""
import math

def grip(r, part, centers):
    for x,y in centers:
        # Select a short angular portion of each existing jaw, wholly inside
        # its rim seat, then taper the pad toward the incoming cardboard edge.
        jaw = part.slice(1.) ^ (r.circle(r.ri+.04,x,y)-r.circle(r.ri-.3,x,y))
        for segment in jaw.decompose():
            if segment.area()<.4: continue
            lo,bot,hi,top=segment.bounds()
            angle=math.atan2((bot+top)/2-y,(lo+hi)/2-x)
            ux,uy=math.cos(angle),math.sin(angle)
            def point(radius,t):
                return (x+ux*radius-uy*t,y+uy*radius+ux*t)
            strip=r.poly([point(39.8,-1.7),point(42,-1.7),point(42,1.7),point(39.8,1.7)])
            root=strip ^ segment
            if root.area()<.2: continue
            pad=r.extr(root,0,2.9)
            # At midheight the rib extends 0.15 mm into a nominal 83 mm
            # cardboard bore. Only this intentional contact may overlap the core.
            bulge=r.extr(root.translate((ux*.71,uy*.71)),.75,1.65)
            part+=type(pad).batch_hull([pad,bulge])
    return part.simplify(.0005)
