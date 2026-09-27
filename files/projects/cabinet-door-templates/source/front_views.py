#!/usr/bin/env python3
"""Draw the existing rail alternatives with cabinet sides and 2.25-inch stiles.

Preview only: no model files are modified. The original rail span is maintained.
"""
from project_paths import artifact_path, artifact_url, publish_html
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
BG='#faf8f3'
WOOD='#dcc29a'
PANEL='#eee4d3'
EDGE='#998568'


def front(ax,c,data,stile=2.25,dimensions=False):
    w,h=data['width'],data['height_display']
    dx=.875
    x=np.array(data['x']); y=np.array(c['y'])
    ax.set_aspect('equal'); ax.axis('off')
    # Left to right: .75 side + .125 gap + 15.875 door + .125 gap + .375 hinge strip + .75 side.
    for start,width,color in [(0,.75,'#b6a386'),(16.875,.375,'#cabb9f'),(17.25,.75,'#b6a386')]:
        ax.add_patch(Rectangle((start,0),width,h,facecolor=color,edgecolor=EDGE,lw=.7))
    ax.add_patch(Rectangle((dx,0),w,h,facecolor=PANEL,edgecolor=EDGE,lw=.8))
    # Stiles are inside the overall door span and meet the curved rails, as drawn.
    for a,b in [(0,stile),(w-stile,w)]:
        xx=np.linspace(a,b,120)
        bottom=np.interp(xx,x,y)
        top=h-np.interp(w-xx,x,y)
        ax.fill_between(dx+xx,bottom,top,color=WOOD)
    ax.fill_between(dx+x,0,y,color=WOOD)
    ax.fill_between(dx+x,h-y[::-1],h,color=WOOD)
    ax.plot(dx+x,y,color=c['color'],lw=1.8)
    ax.plot(dx+x,h-y[::-1],color=c['color'],lw=1.8)
    for xx in [stile,w-stile]:
        ax.plot([dx+xx,dx+xx],[np.interp(xx,x,y),h-np.interp(w-xx,x,y)],color=EDGE,lw=1)
    ax.add_patch(Circle((dx+stile/2,(np.interp(stile/2,x,y)+h-np.interp(w-stile/2,x,y))/2),.625,facecolor='#665542',edgecolor='#44392e',lw=.6))
    if dimensions:
        for a,b,label in [(dx,dx+stile,'2¼″'),(dx+stile,dx+w-stile,'11⅜″'),(dx+w-stile,dx+w,'2¼″')]:
            ax.annotate('',(a,-1),(b,-1),arrowprops={'arrowstyle':'<->','lw':.8,'color':'#53615b','shrinkA':0,'shrinkB':0})
            ax.text((a+b)/2,-1.7,label,ha='center',va='center',fontsize=10,color='#53615b')
        ax.annotate('',(0,h+1),(18,h+1),arrowprops={'arrowstyle':'<->','lw':.8,'color':'#53615b','shrinkA':0,'shrinkB':0})
        ax.text(9,h+1.7,'18″ cabinet',ha='center',va='center',fontsize=10,color='#53615b')
    ax.set_xlim(-.6,18.6); ax.set_ylim(-2.4,h+2.5)


def main():
    data=json.loads((artifact_path('curve-comparison-data.json')).read_text())
    data.update({'stile_width':2.25,'cabinet_width':18,'door_offset':.875})
    fig,axes=plt.subplots(1,3,figsize=(14,10),facecolor=BG)
    fig.suptitle('The cabinet front, with 2¼″ stiles',x=.06,y=.96,ha='left',fontsize=25,color='#243e36')
    fig.text(.06,.905,'18″ cabinet · 15⅞″ door · 3″ / 6″ rail ends · 11⅜″ between the stiles',fontsize=13,color='#53615b')
    for ax,c in zip(axes,data['curves']):
        front(ax,c,data,dimensions=True)
        ax.set_title(c['title'],fontsize=12,color=c['color'],pad=15)
    fig.text(.06,.071,'Stiles sit within the door width and meet the curved rails, following your sketch.\nHinges and ⅜″ strip on right; knob centered on left stile. Round knob approximately 1¼″ diameter; joinery omitted.',fontsize=11,color='#53615b',linespacing=1.8)
    fig.text(.06,.023,'27″ cabinet and door height: flush at top and bottom, inset at sides. Panel shading is illustrative.',fontsize=9,color='#788079')
    fig.subplots_adjust(left=.055,right=.965,top=.81,bottom=.135,wspace=.16)
    fig.savefig(artifact_path('cabinet-front-right-hinge-comparison.png'),dpi=170,facecolor=BG)
    plt.close(fig)
    # Recommended option alone, large enough to inspect the side gaps and stile seams.
    fig,ax=plt.subplots(figsize=(7,10),facecolor=BG)
    front(ax,data['curves'][1],data,dimensions=True)
    ax.set_title('Continuous sweep · 2¼″ stiles',fontsize=17,color='#236b60',pad=15)
    fig.subplots_adjust(left=.1,right=.9,top=.91,bottom=.065)
    fig.savefig(artifact_path('cabinet-front-right-hinge-smooth.png'),dpi=170,facecolor=BG)
    plt.close(fig)
    from build_comparison import build
    build()
    (artifact_path('cabinet-front-right-hinge-dimensions.json')).write_text(json.dumps({'cabinet_width':18,'door_width':data['width'],'stile_width':2.25,'between_stiles':data['width']-4.5,'side_allowances':[.75,.125,.125,.375,.75],'door_offset':.875,'hinge_side':'right','hinge_strip_x_inches':16.875,'knob_side':'left','knob_diameter_inches':1.25,'knob_center_rule':'Centered across left stile and halfway between its two curved rail boundaries','display_height':data['height_display'],'units':'inches'},indent=2)+'\n')
    assert abs(.75+.375+.125+data['width']+.125+.75-18)<1e-9
    assert data['width']-2*2.25==11.375


if __name__=='__main__':
    main()
