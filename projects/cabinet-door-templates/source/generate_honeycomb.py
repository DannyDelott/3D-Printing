#!/usr/bin/env python3
"""Perforate the chosen ellipse, preserving its perimeter and central joint zone."""
from project_paths import artifact_path, artifact_url, publish_html
import json
import math

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
import numpy as np
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.TopoDS import TopoDS
from OCP.gp import gp_Pnt, gp_Vec

from generate_ellipse import WIDTH, LEFT, RIGHT, THICKNESS, make_solid
from generate_template import MM, ROOT, export

RIM = 10.0
# Keep the original twelve hole locations, but shrink each opening so every
# existing web gains material. Do not add newly fitting holes in this revision.
LAYOUT_HEX_FLATS = 32.0
LAYOUT_WEB = 3.2
WEB = 10.0
HEX_FLATS = LAYOUT_HEX_FLATS + LAYOUT_WEB - WEB
CENTER_BAND = 3.5*MM
NAME = 'rail-template-elliptical-honeycomb-v3'


def main():
    _, ellipse, boundary, a, b, cy = make_solid()
    width=WIDTH*MM
    mid=width/2
    lo,hi=mid-CENTER_BAND/2,mid+CENTER_BAND/2
    radius=HEX_FLATS/math.sqrt(3)
    layout_radius=LAYOUT_HEX_FLATS/math.sqrt(3)
    pitch=LAYOUT_HEX_FLATS+LAYOUT_WEB
    x_pitch=pitch*math.sqrt(3)/2
    holes=[]
    wires=[]
    clearances=[]
    def height(x):
        return (cy-b*math.sqrt(1-(x/(a*MM))**2))*MM
    for col in range(math.ceil(width/x_pitch)):
        cx=RIM+layout_radius+col*x_pitch
        for row in range(math.ceil(RIGHT*MM/pitch)):
            yy=RIM+LAYOUT_HEX_FLATS/2+row*pitch+(col%2)*pitch/2
            layout_points=np.array([(cx+layout_radius*math.cos(k*math.pi/3),yy+layout_radius*math.sin(k*math.pi/3)) for k in range(6)])
            xmin,ymin=layout_points.min(axis=0); xmax,_=layout_points.max(axis=0)
            if xmin<RIM-1e-8 or xmax>width-RIM or ymin<RIM-1e-8:
                continue
            if not (xmax<=lo or xmin>=hi):
                continue
            if any(y>=height(x) for x,y in layout_points):
                continue
            polygon=BRepBuilderAPI_MakePolygon()
            for x,y in layout_points:
                polygon.Add(gp_Pnt(float(x),float(y),0))
            polygon.Close()
            hole=polygon.Wire()
            distance=BRepExtrema_DistShapeShape(hole,boundary)
            distance.Perform()
            assert distance.IsDone()
            if distance.Value()<RIM-1e-7:
                continue
            points=np.array([(cx+radius*math.cos(k*math.pi/3),yy+radius*math.sin(k*math.pi/3)) for k in range(6)])
            polygon=BRepBuilderAPI_MakePolygon()
            for x,y in points:
                polygon.Add(gp_Pnt(float(x),float(y),0))
            polygon.Close()
            hole=polygon.Wire()
            distance=BRepExtrema_DistShapeShape(hole,boundary)
            distance.Perform()
            assert distance.IsDone() and distance.Value()>=RIM
            holes.append(points)
            wires.append(hole)
            clearances.append(distance.Value())
    assert len(holes)==12
    face=BRepBuilderAPI_MakeFace(boundary)
    for wire in wires:
        face.Add(TopoDS.Wire_s(wire.Reversed()))
    solid=BRepPrimAPI_MakePrism(face.Face(),gp_Vec(0,0,THICKNESS)).Shape()
    info=export(solid,NAME)
    original=json.loads((artifact_path('validation-elliptical.json')).read_text())
    original_volume=original['analytic_volume_cm3']
    removed=len(holes)*math.sqrt(3)/2*HEX_FLATS**2*THICKNESS/1000
    assert abs(info['volume_cm3']-(original_volume-removed))<.03
    assert np.allclose(info['size_mm'],[width,RIGHT*MM,THICKNESS],atol=1e-4)
    min_web=float('inf')
    for i,wire in enumerate(wires):
        for other in wires[i+1:]:
            distance=BRepExtrema_DistShapeShape(wire,other)
            distance.Perform()
            assert distance.IsDone()
            min_web=min(min_web,distance.Value())
    assert min_web>=WEB-1e-7
    report={'curve':'unchanged exact elliptical arc','hole_count':len(holes),'hole_across_flats_mm':HEX_FLATS,'minimum_web_mm':min_web,'minimum_perimeter_rim_mm':min(clearances),'solid_center_band_mm':CENTER_BAND,'split_x_mm':mid,'solid_band_x_mm':[lo,hi],'solid_each_side_of_split_mm':CENTER_BAND/2,'requested_dovetail_width_mm':1.5*MM,'original_solid_volume_cm3':original_volume,'removed_volume_cm3':removed,'solid_volume_reduction_percent':removed/original_volume*100,'mesh':info,'status':'digital validation passed; filament usage depends on slicing settings; no physical load test'}
    (artifact_path('validation-honeycomb-v3.json')).write_text(json.dumps(report,indent=2)+'\n')

    x=np.linspace(0,width,801); y=np.array([height(v) for v in x])
    fig,ax=plt.subplots(figsize=(14,6.4),facecolor='#faf8f3')
    ax.set_aspect('equal'); ax.axis('off')
    ax.fill_between(x,0,y,color='#dcc29a')
    # Highlighted region is solid material, not a recess or raised feature.
    mask=(x>=lo)&(x<=hi)
    ax.fill_between(x[mask],0,y[mask],color='#c5b187')
    for points in holes:
        ax.add_patch(Polygon(points,facecolor='#faf8f3',edgecolor='#998568',lw=.6))
    ax.plot(x,y,color='#537790',lw=2.5)
    ax.plot([0,0,width,width],[LEFT*MM,0,0,RIGHT*MM],color='#998568',lw=1)
    ax.plot([mid,mid],[0,height(mid)],ls='--',lw=1,color='#53615b')
    ax.annotate('',(lo,-13),(hi,-13),arrowprops={'arrowstyle':'<->','color':'#53615b'})
    ax.text(mid,-23,'3½″ solid center band',ha='center',fontsize=12,color='#243e36')
    ax.text(mid,-33,'1¾″ of solid material on each side of your split',ha='center',fontsize=10,color='#53615b')
    ax.text(mid,height(mid)+13,'Split at 7¹⁵⁄₁₆″',ha='center',fontsize=10,color='#53615b')
    ax.set_xlim(-8,width+8);ax.set_ylim(-39,RIGHT*MM+8)
    fig.suptitle('Elliptical template · wider honeycomb webs',x=.07,y=.96,ha='left',fontsize=22,color='#243e36')
    fig.text(.07,.875,f'{len(holes)} through-openings · {min(clearances):.1f} mm minimum rim · {WEB:g} mm minimum webs · ¾″ thick',fontsize=12,color='#53615b')
    fig.text(.07,.045,f'{removed/original_volume*100:.1f}% less solid model volume. Actual filament savings depend on wall, infill, and top/bottom settings.',fontsize=10,color='#53615b')
    fig.subplots_adjust(left=.06,right=.96,top=.80,bottom=.11)
    fig.savefig(artifact_path('elliptical-honeycomb-v3-preview.png'),dpi=170,facecolor=fig.get_facecolor())
    plt.close(fig)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
