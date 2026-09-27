#!/usr/bin/env python3
"""Export the exact q=0.95 elliptical rail shown in the curve comparison."""
from project_paths import artifact_path, artifact_url, publish_html
import json
import math

import numpy as np
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.Geom import Geom_Ellipse
from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt, gp_Vec

from generate_template import MM, ROOT, export

WIDTH, LEFT, RIGHT, THICKNESS = 15.875, 3.0, 6.0, 19.05
Q = .95


def make_solid():
    a = WIDTH / Q
    b = (RIGHT-LEFT) / (1-math.sqrt(1-Q*Q))
    cy = LEFT+b
    # -Z normal makes increasing ellipse parameter traverse the routing edge
    # from its tall right end to its shallow left end, closing the face CCW.
    ellipse = Geom_Ellipse(gp_Ax2(gp_Pnt(0,cy*MM,0),gp_Dir(0,0,-1),gp_Dir(1,0,0)),a*MM,b*MM)
    wire = BRepBuilderAPI_MakeWire()
    for start,end in [((0,0),(WIDTH,0)),((WIDTH,0),(WIDTH,RIGHT))]:
        wire.Add(BRepBuilderAPI_MakeEdge(gp_Pnt(start[0]*MM,start[1]*MM,0),gp_Pnt(end[0]*MM,end[1]*MM,0)).Edge())
    wire.Add(BRepBuilderAPI_MakeEdge(ellipse,math.acos(Q),math.pi/2).Edge())
    wire.Add(BRepBuilderAPI_MakeEdge(gp_Pnt(0,LEFT*MM,0),gp_Pnt(0,0,0)).Edge())
    face = BRepBuilderAPI_MakeFace(wire.Wire()).Face()
    solid = BRepPrimAPI_MakePrism(face,gp_Vec(0,0,THICKNESS)).Shape()
    return solid, ellipse, wire.Wire(), a, b, cy


def main():
    solid, ellipse, _, a, b, cy = make_solid()

    # Compare the exact CAD ellipse against every displayed sample, ensuring the
    # exported model is the specific ellipse the user selected, not a refit.
    data = json.loads((artifact_path('curve-comparison-data.json')).read_text())
    shown = next(c['y'] for c in data['curves'] if c['id']=='ellipse')
    errors = []
    for x,y in zip(data['x'],shown):
        pt = ellipse.Value(math.acos(x/a))
        errors.append(max(abs(pt.X()-x*MM),abs(pt.Y()-y*MM)))
    assert max(errors)<1e-8
    info = export(solid,'rail-template-elliptical')
    area = WIDTH*cy - b*a/2*(Q*math.sqrt(1-Q*Q)+math.asin(Q))
    exact_volume = area*MM**2*THICKNESS/1000
    assert abs(info['volume_cm3']-exact_volume)/exact_volume<.0001
    assert np.allclose(info['size_mm'],[WIDTH*MM,RIGHT*MM,THICKNESS],atol=1e-4)
    report = {'curve':'exact elliptical arc from comparison','q':Q,'semi_axes_inches':[a,b],'center_inches':[0,cy],'width_inches':WIDTH,'end_heights_inches':[LEFT,RIGHT],'thickness_mm':THICKNESS,'max_preview_error_mm':max(errors),'analytic_volume_cm3':exact_volume,'mesh':info,'status':'digital validation passed; not physically printed or routed'}
    (artifact_path('validation-elliptical.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
