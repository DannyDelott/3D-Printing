#!/usr/bin/env python3
"""Matching curved-end stile templates for the confirmed 27-inch flush-height door."""
from project_paths import artifact_path, artifact_url, publish_html
import json
import math

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import numpy as np
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakePolygon, BRepBuilderAPI_Transform
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepGProp import BRepGProp
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.GProp import GProp_GProps
from OCP.Geom import Geom_Ellipse
from OCP.TopoDS import TopoDS
from OCP.gp import gp_Ax1, gp_Ax2, gp_Dir, gp_Pnt, gp_Trsf, gp_Vec

from generate_ellipse import WIDTH, LEFT, RIGHT, THICKNESS, Q, make_solid
from generate_template import MM, ROOT, export

DOOR_HEIGHT=27.0
STILE=2.25
WEB=10.0
HEX_FLATS=25.2
RIM=13.4
CENTER_BAND=3.5*MM


def volume(shape):
    props=GProp_GProps(); BRepGProp.VolumeProperties_s(shape,props)
    return props.Mass()


def main():
    bottom_rail, lower, _, a, b, cy=make_solid()
    def bottom(x): return cy-b*math.sqrt(1-(x/a)**2)
    def top(x): return DOOR_HEIGHT-bottom(WIDTH-x)
    upper=Geom_Ellipse(gp_Ax2(gp_Pnt(WIDTH*MM,(DOOR_HEIGHT-cy)*MM,0),gp_Dir(0,0,-1),gp_Dir(-1,0,0)),a*MM,b*MM)
    wire=BRepBuilderAPI_MakeWire()
    wire.Add(TopoDS.Edge_s(BRepBuilderAPI_MakeEdge(lower,math.acos(STILE/a),math.pi/2).Edge().Reversed()))
    wire.Add(BRepBuilderAPI_MakeEdge(gp_Pnt(STILE*MM,bottom(STILE)*MM,0),gp_Pnt(STILE*MM,top(STILE)*MM,0)).Edge())
    wire.Add(TopoDS.Edge_s(BRepBuilderAPI_MakeEdge(upper,math.acos(Q),math.acos((WIDTH-STILE)/a)).Edge().Reversed()))
    wire.Add(BRepBuilderAPI_MakeEdge(gp_Pnt(0,top(0)*MM,0),gp_Pnt(0,bottom(0)*MM,0)).Edge())
    boundary=wire.Wire()
    plain=BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(boundary).Face(),gp_Vec(0,0,THICKNESS)).Shape()
    ymin=bottom(0)*MM; ymax=top(STILE)*MM
    split=(ymin+ymax)/2
    band=[split-CENTER_BAND/2,split+CENTER_BAND/2]
    holes=[];hole_wires=[];rims=[]
    radius=HEX_FLATS/math.sqrt(3)
    pitch=HEX_FLATS+WEB
    cx=STILE*MM/2
    for row in range(math.ceil((ymax-ymin)/pitch)):
        center_y=ymin+RIM+HEX_FLATS/2+row*pitch
        points=np.array([(cx+radius*math.cos(k*math.pi/3),center_y+radius*math.sin(k*math.pi/3)) for k in range(6)])
        if not (points[:,1].max()<=band[0] or points[:,1].min()>=band[1]):continue
        if any(y<=bottom(x/MM)*MM or y>=top(x/MM)*MM for x,y in points):continue
        polygon=BRepBuilderAPI_MakePolygon()
        for x,y in points:polygon.Add(gp_Pnt(float(x),float(y),0))
        polygon.Close(); hole=polygon.Wire()
        dist=BRepExtrema_DistShapeShape(hole,boundary);dist.Perform()
        assert dist.IsDone()
        if dist.Value()<RIM-1e-7:continue
        holes.append(points);hole_wires.append(hole);rims.append(dist.Value())
    face=BRepBuilderAPI_MakeFace(boundary)
    for hole in hole_wires:face.Add(TopoDS.Wire_s(hole.Reversed()))
    left=BRepPrimAPI_MakePrism(face.Face(),gp_Vec(0,0,THICKNESS)).Shape()
    rotation=gp_Trsf();rotation.SetRotation(gp_Ax1(gp_Pnt(WIDTH*MM/2,DOOR_HEIGHT*MM/2,0),gp_Dir(0,0,1)),math.pi)
    right=BRepBuilderAPI_Transform(left,rotation,True).Shape()
    top_rail=BRepBuilderAPI_Transform(bottom_rail,rotation,True).Shape()
    # Stile boundaries must contact, without overlapping, the exact rail solids.
    for stile in (left,right):
        for rail in (bottom_rail,top_rail):
            assert abs(volume(BRepAlgoAPI_Common(stile,rail).Shape()))<1e-5
            contact=BRepExtrema_DistShapeShape(stile,rail);contact.Perform()
            assert contact.IsDone() and contact.Value()<1e-7
    assert abs((top(0)-bottom(0))-18)<1e-9
    for x in np.linspace(0,STILE,101):
        assert abs((DOOR_HEIGHT-top(x))-bottom(WIDTH-x))<1e-10
    web_distances=[]
    for i,hole in enumerate(hole_wires):
        for other in hole_wires[i+1:]:
            distance=BRepExtrema_DistShapeShape(hole,other);distance.Perform();assert distance.IsDone()
            web_distances.append(distance.Value())
    assert min(web_distances)>=WEB-1e-7
    reports={}
    for name,shape in [('stile-template-left-v1',left),('stile-template-right-v1',right)]:
        reports[name]=export(shape,name)
    removed=len(holes)*math.sqrt(3)/2*HEX_FLATS**2*THICKNESS
    assert abs(volume(plain)-removed-volume(left))<1e-5
    assert abs(volume(left)-volume(right))<1e-5
    report={'cabinet_height_inches':DOOR_HEIGHT,'door_height_inches':DOOR_HEIGHT,'vertical_clearance_inches':0,'mounting':'inset at sides; flush with cabinet at top and bottom','door_width_inches':WIDTH,'stile_width_inches':STILE,'thickness_mm':THICKNESS,'outer_edge_length_inches':top(0)-bottom(0),'inner_edge_length_inches':top(STILE)-bottom(STILE),'bounding_length_inches':(ymax-ymin)/MM,'left_assembly_y_inches':[ymin/MM,ymax/MM],'split_from_template_bottom_mm':split-ymin,'solid_center_band_mm':CENTER_BAND,'hole_count':len(holes),'minimum_web_mm':min(web_distances),'minimum_perimeter_rim_mm':min(rims),'rotation_reuse':'same template rotated 180 degrees makes opposite stile','joinery_allowance':'none; finished curved profile only','models':reports,'status':'digitally verified; no physical print or fit test'}
    (artifact_path('validation-stiles.json')).write_text(json.dumps(report,indent=2)+'\n')
    # Same-scale front and template views for assembly and fit review.
    fig,axes=plt.subplots(1,3,figsize=(12,10),gridspec_kw={'width_ratios':[3,1,1]},facecolor='#faf8f3')
    x=np.linspace(0,WIDTH,801); lower_y=np.array([bottom(v) for v in x]);upper_y=DOOR_HEIGHT-lower_y[::-1]
    ax=axes[0];ax.fill_between(x,0,lower_y,color='#dcc29a');ax.fill_between(x,upper_y,DOOR_HEIGHT,color='#dcc29a')
    for xx in [np.linspace(0,STILE,101),np.linspace(WIDTH-STILE,WIDTH,101)]:
        ax.fill_between(xx,[bottom(v) for v in xx],[top(v) for v in xx],color='#9ebfb5')
    ax.plot(x,lower_y,color='#537790',lw=1);ax.plot(x,upper_y,color='#537790',lw=1)
    ax.plot([0,0,WIDTH,WIDTH,0],[0,DOOR_HEIGHT,DOOR_HEIGHT,0,0],color='#998568',lw=1)
    ax.set_title('27″ door · stiles highlighted',color='#243e36',fontsize=13,pad=15)
    xx=np.linspace(0,STILE,201)
    for ax,is_right in zip(axes[1:],[False,True]):
        lo=np.array([bottom(v) for v in xx]);hi=np.array([top(v) for v in xx])
        points=np.column_stack([np.r_[xx,xx[::-1]],np.r_[lo,hi[::-1]]])
        hs=[p/MM for p in holes]
        if is_right:
            points=np.array([STILE,DOOR_HEIGHT])-points
            hs=[np.array([STILE,DOOR_HEIGHT])-p for p in hs]
        ax.add_patch(Polygon(points,facecolor='#dcc29a',edgecolor='#998568',lw=1))
        for h in hs:ax.add_patch(Polygon(h,facecolor='#faf8f3',edgecolor='#998568',lw=.7))
        sy=(DOOR_HEIGHT-split/MM) if is_right else split/MM
        ax.plot([0,STILE],[sy,sy],ls='--',color='#53615b',lw=.8)
        ax.set_xlim(-.6,STILE+.6)
        ax.set_title('Right template' if is_right else 'Left template',color='#243e36',fontsize=13,pad=15)
    for ax in axes:ax.set_aspect('equal');ax.set_ylim(-.6,27.6);ax.axis('off')
    fig.suptitle('Stile templates · 2¼″ wide',x=.065,y=.97,ha='left',fontsize=24,color='#243e36')
    fig.text(.065,.9,'27″ overall height • curved ends match the chosen ellipse • ¾″ template thickness',fontsize=12,color='#53615b')
    fig.text(.065,.045,f'Outside edge: 18″ · inside edge: {report["inner_edge_length_inches"]:.3f}″ · bounding length: {report["bounding_length_inches"]:.3f}″\n10 mm webs · 3½″ solid band at each template midpoint · rotate either template 180° for the other side',fontsize=11,color='#53615b',linespacing=1.7)
    fig.subplots_adjust(left=.065,right=.95,top=.82,bottom=.12,wspace=.27)
    fig.savefig(artifact_path('stile-templates-preview.png'),dpi=170,facecolor=fig.get_facecolor());plt.close(fig)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
