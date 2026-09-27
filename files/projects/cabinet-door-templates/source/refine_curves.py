#!/usr/bin/env python3
"""Compare continuous curves and export the recommended single Bezier rail."""
from project_paths import artifact_path, artifact_url, publish_html
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.Geom import Geom_BezierCurve
from OCP.TColgp import TColgp_Array1OfPnt
from OCP.gp import gp_Pnt, gp_Vec

from generate_template import RailProfile, export, MM, ROOT

WIDTH = 15.875
LEFT, RIGHT, THICKNESS = 3.0, 6.0, 19.05
EASE = .75


def bezier_height(t):
    return LEFT + (RIGHT-LEFT)*((1-EASE)*t*t + EASE*t*t*t)


def make_solid():
    # Uniformly spaced X controls give x(t)=width*t exactly.
    controls = [(0, LEFT), (WIDTH/3, LEFT), (2*WIDTH/3, LEFT+(RIGHT-LEFT)*(1-EASE)/3), (WIDTH, RIGHT)]
    poles = TColgp_Array1OfPnt(1, 4)
    # Traverse the upper edge from right to left to close a CCW wire.
    for i, (x,y) in enumerate(reversed(controls), 1):
        poles.SetValue(i, gp_Pnt(x*MM, y*MM, 0))
    curve = Geom_BezierCurve(poles)
    wire = BRepBuilderAPI_MakeWire()
    for a,b in [((0,0),(WIDTH,0)), ((WIDTH,0),(WIDTH,RIGHT))]:
        wire.Add(BRepBuilderAPI_MakeEdge(gp_Pnt(a[0]*MM,a[1]*MM,0),gp_Pnt(b[0]*MM,b[1]*MM,0)).Edge())
    wire.Add(BRepBuilderAPI_MakeEdge(curve).Edge())
    wire.Add(BRepBuilderAPI_MakeEdge(gp_Pnt(0,LEFT*MM,0),gp_Pnt(0,0,0)).Edge())
    shape = BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(wire.Wire()).Face(),gp_Vec(0,0,THICKNESS)).Shape()
    # Verify the CAD edge agrees with the displayed analytic curve.
    for t in np.linspace(0,1,101):
        point = curve.Value(1-float(t))
        assert abs(point.X()-WIDTH*MM*t)<1e-8
        assert abs(point.Y()-bezier_height(t)*MM)<1e-8
    return shape, controls


def main():
    t=np.linspace(0,1,801); x=WIDTH*t
    original=RailProfile(WIDTH*MM,LEFT*MM,RIGHT*MM,60*MM,18*MM)
    q=.95
    curves=[
        {'id':'original','title':'Original · two circles','note':'An abrupt change in curvature at the midpoint.','color':'#9a715a','y':[original.height(v*MM)/MM for v in x]},
        {'id':'bezier','title':'Continuous sweep · recommended','note':'One Bézier curve. The bend develops gradually.','color':'#236b60','y':bezier_height(t).tolist()},
        {'id':'ellipse','title':'Elliptical arc','note':'A smooth ellipse, with a tighter turn at the tall end.','color':'#537790','y':(LEFT+(RIGHT-LEFT)*(1-np.sqrt(1-(q*t)**2))/(1-math.sqrt(1-q*q))).tolist()},
    ]
    solid,controls=make_solid()
    info=export(solid,'rail-template-smooth-v2')
    # Analytic volume: integral of 3 + 3*(.25*t^2+.75*t^3).
    exact_volume=WIDTH*(LEFT+(RIGHT-LEFT)*((1-EASE)/3+EASE/4))*MM**2*THICKNESS
    assert abs(info['volume_cm3']*1000-exact_volume)/exact_volume < .0001
    assert np.allclose(info['size_mm'],[WIDTH*MM,RIGHT*MM,THICKNESS],atol=1e-4)
    report={'curve':'single cubic Bezier','ease':EASE,'controls_inches':controls,'midpoint_height_inches':bezier_height(.5),'formula_inches':'y = 3 + 0.75*t^2 + 2.25*t^3; x = 15.875*t; 0 <= t <= 1','mesh':info,'analytic_volume_cm3':exact_volume/1000,'status':'digital validation passed; not physically printed or routed'}
    (artifact_path('validation-smooth-v2.json')).write_text(json.dumps(report,indent=2)+'\n')
    data={'width':WIDTH,'height_display':27,'curves':curves,'x':x.tolist()}
    (artifact_path('curve-comparison-data.json')).write_text(json.dumps(data))
    from build_comparison import build
    build()
    background='#faf8f3'
    fig,axes=plt.subplots(2,3,figsize=(14,11),gridspec_kw={'height_ratios':[1,2.3]},facecolor=background)
    fig.suptitle('A smoother sweep for the cabinet rails',x=.055,ha='left',fontsize=24,color='#243e36')
    fig.text(.055,.924,'Same 15⅞″ width, 3″ / 6″ end heights, and ¾″ template thickness in every option.',fontsize=12,color='#53615b')
    for i,c in enumerate(curves):
        y=np.array(c['y']); a,b=axes[:,i]
        for ax in (a,b):
            ax.set_aspect('equal');ax.axis('off');ax.set_facecolor(background)
        a.set_title(c['title'],loc='left',fontsize=12,color=c['color'],pad=15)
        a.fill_between(x,0,y,color='#e4cfaa')
        a.plot(x,y,color=c['color'],lw=2)
        a.plot([0,0,WIDTH,WIDTH],[LEFT,0,0,RIGHT],color='#a39174',lw=.9)
        a.text(-.4,LEFT,'3″',ha='right',va='center',fontsize=10)
        a.text(WIDTH+.35,RIGHT,'6″',va='center',fontsize=10)
        a.set_xlim(-1.4,WIDTH+1.4);a.set_ylim(-1,8)
        h=27
        b.fill_between(x,0,y,color='#e4cfaa')
        b.fill_between(x,h-y[::-1],h,color='#e4cfaa')
        b.plot(x,y,color=c['color'],lw=2)
        b.plot(x,h-y[::-1],color=c['color'],lw=2)
        b.plot([0,0,WIDTH,WIDTH,0],[0,h,h,0,0],color='#a39174',lw=.9)
        b.set_xlim(-1.4,WIDTH+1.4);b.set_ylim(-1,h+1)
    fig.text(.055,.055,'Top rail is the bottom rail rotated 180°. Cabinet pair shown at a 27″ display height for comparison; joinery omitted.\nThe recommended sweep removes the slight dip and carries the rise farther toward the left, without a midpoint transition.',fontsize=11,color='#53615b',linespacing=1.8)
    fig.subplots_adjust(left=.055,right=.955,top=.85,bottom=.115,wspace=.23,hspace=.05)
    fig.savefig(artifact_path('curve-comparison.png'),dpi=160,facecolor=background)
    plt.close(fig)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
