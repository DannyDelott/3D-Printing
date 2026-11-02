import numpy as np
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

def print_check(r, shape, balance=False):
    bottom,top=shape.bounding_box()[2::3]
    footprint=shape.slice(bottom+.01)
    previous=None
    for z in np.arange(bottom+.10,top,.2):
        layer=shape.slice(z)
        if previous is not None:
            assert all((piece^previous).area()>1e-7 for piece in layer.decompose()),('unsupported island',z-bottom)
        previous=layer
    values={'bed_contact_mm2':round(footprint.area(),1)}
    if balance:
        bed=unary_union([Polygon(ring) for ring in footprint.to_polygons()])
        margins=[]
        for z in np.arange(bottom+1,top,3):
            partial=shape.trim_by_plane((0,0,-1),-z)
            center=Point(r.mesh(partial).center_mass[:2])
            assert bed.covers(center),('center outside bed patch',z-bottom)
            margins.append(bed.boundary.distance(center))
        values['minimum_sampled_balance_margin_mm']=round(min(margins),2)
    return values
