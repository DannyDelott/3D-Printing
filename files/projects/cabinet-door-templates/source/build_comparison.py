#!/usr/bin/env python3
"""Build each design group from its downloadable component models."""
from project_paths import artifact_path, artifact_url, publish_html, DESIGNS
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parents[1]


def mesh_payload(name, expected, hole_count, horizontal=False):
    path=artifact_path(f'{name}.3mf')
    mesh=trimesh.load(path,force='mesh',process=True)
    assert mesh.is_watertight and len(mesh.split())==1
    assert np.allclose(mesh.extents,expected['size_mm'])
    # Recover the outer contour and all hole loops from the exported top face.
    top=mesh.faces[mesh.face_normals[:,2]>.99]
    edges=Counter(tuple(sorted((int(a),int(b)))) for f in top for a,b in zip(f,np.roll(f,-1)))
    remaining={edge for edge,count in edges.items() if count==1}
    adjacent=defaultdict(list)
    for a,b in remaining:
        adjacent[a].append(b);adjacent[b].append(a)
    assert all(len(v)==2 for v in adjacent.values())
    loops=[]
    while remaining:
        start,current=min(remaining)
        loop=[start];previous=start
        remaining.remove(tuple(sorted((start,current))))
        while current!=start:
            loop.append(current)
            nxt=next(v for v in adjacent[current] if v!=previous)
            remaining.remove(tuple(sorted((current,nxt))))
            previous,current=current,nxt
        loops.append(mesh.vertices[loop,:2])
    area=lambda points: abs(np.sum(points[:,0]*np.roll(points[:,1],-1)-points[:,1]*np.roll(points[:,0],-1)))/2
    loops.sort(key=area,reverse=True)
    assert len(loops)==hole_count+1
    assert all(len(p)==6 for p in loops[1:])
    centered=mesh.triangles-mesh.bounds.mean(axis=0)
    normals=np.repeat(mesh.face_normals[:,None,:],3,axis=1)
    if horizontal:
        rotation=np.array([[0,1,0],[-1,0,0],[0,0,1]])
        centered=centered@rotation.T;normals=normals@rotation.T
    vertices=np.concatenate([centered,normals],axis=2).astype(np.float32)
    view_bounds=mesh.extents[[1,0,2]] if horizontal else mesh.extents
    return {'file':name,'downloads':{ext:artifact_url(f'{name}.{ext}') for ext in ['3mf','stl','step']},'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'vertices':vertices.reshape(-1).round(6).tolist(),'bounds_mm':mesh.extents.tolist(),'view_bounds_mm':view_bounds.tolist(),'outline_inches':(loops[0]/25.4).round(6).tolist(),'holes_inches':[(p/25.4).round(6).tolist() for p in loops[1:]],'horizontal':horizontal}



def split_payload(part, stem, sliced, flip=False, reinforced=False):
    scene=trimesh.load(artifact_path(stem+'.3mf'))
    geometry=scene.to_geometry()
    assert geometry.is_watertight and len(geometry.split())==2
    if flip:
        center=geometry.bounds.mean(axis=0)
        geometry.apply_translation(-center)
        geometry.apply_transform(trimesh.transformations.rotation_matrix(np.pi,[0,0,1]))
        geometry.apply_translation(center)
    vertices=np.concatenate([geometry.triangles-geometry.bounds.mean(axis=0),np.repeat(geometry.face_normals[:,None,:],3,axis=1)],axis=2)
    loops=[loop[:,:2]/25.4 for loop in geometry.section([0,0,1],[0,0,6.35]).discrete]
    if part.get('horizontal'):
        loops=[np.column_stack([2.25-loop[:,1],loop[:,0]]) for loop in loops]
    part.update(file=stem,kind='split',revision=stem.rsplit('-',1)[-1].upper(),vertices=vertices.reshape(-1).round(6).tolist(),
                view_bounds_mm=geometry.extents.tolist(),split_outlines_inches=[loop.round(6).tolist() for loop in loops],
                sha256=hashlib.sha256(artifact_path(stem+'.3mf').read_bytes()).hexdigest(),
                downloads={'3mf':artifact_url(sliced),'step':artifact_url(stem+'.step'),'stl':artifact_url(stem+'.stl')},
                status='Full V13 fit failed · socket arms bow' if reinforced else 'V9 coupon fit approved · full template strength untested')
    part['fields'] += [['Dovetail clearance','0.05 mm total' if reinforced else '0.20 mm total'],['Joint fit','Full print failed' if reinforced else 'Coupon approved']]
    if reinforced:part['fields'] += [['Socket width','36.85 mm nominal'],['Side arms','10.15 mm nominal · 10.01 mm at rounded lip']]
    return part

def coupon_payload(stile=False):
    selection=next(d for d in DESIGNS if d['id']=='elliptical')['selection']
    revision=selection['split_stiles'] if stile else selection['approved_joint']['revision']
    name=selection['stile_fit_test' if stile else 'fit_test'].removesuffix('-sliced.3mf')
    report=json.loads(artifact_path(f'validation-stile-dovetail-{revision}.json' if stile else f'validation-native-dovetail-{revision}.json').read_text())
    settings=report['settings']; estimate=report['test_slice']
    path=artifact_path(f'{name}-bambu.3mf' if stile else f'{name}.3mf')
    scene=trimesh.load(path)
    assert len(scene.geometry)==2
    geometry=scene.to_geometry()
    assert geometry.is_watertight and abs(geometry.extents[2]-12.7)<1e-5
    section=geometry.section(plane_origin=[0,0,6.35],plane_normal=[0,0,1])
    outlines=[((loop[:,:2]-geometry.bounds[0,:2])/25.4).round(6).tolist() for loop in section.discrete]
    assert len(outlines)==2
    vertices=np.concatenate([geometry.triangles-geometry.bounds.mean(axis=0),np.repeat(geometry.face_normals[:,None,:],3,axis=1)],axis=2)
    assert artifact_path(f'{name}.stl').is_file(), 'Generate the selected coupon STL before publishing'
    return {'file':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'vertices':vertices.reshape(-1).round(6).tolist(),
            'bounds_mm':geometry.extents.tolist(),'view_bounds_mm':geometry.extents.tolist(),'outlines_inches':outlines,'holes_inches':[],
            'status':'V12 coupon passed · full V13 print failed' if stile else 'Physical coupon fit approved by user','horizontal':False,'kind':'coupon','revision':revision.upper(),'title':'Stile fit coupon' if stile else 'Rail fit coupon','description':'Actual 2¼″ stile width · reinforced arms' if stile else 'Rounded joint · two test pieces · ½″ thick',
            'downloads':{'3mf':artifact_url(f'{name}-sliced.3mf'),'stl':artifact_url(f'{name}.stl')},
            'fields':([['Stile width','57.15 mm'],['Socket width','36.85 mm nominal'],['Side arms','10.15 mm nominal · 10.01 mm at rounded lip']] if stile else []) + [['Thickness','½″ · 12.70 mm'],['External radius','0.30 mm'],['Internal radius','0.20 mm'],['Total width clearance',f"{settings['width_tolerance_mm']:.2f} mm · {settings['width_tolerance_mm']/2:.3f} per side"],['Depth clearance',f"{settings['depth_tolerance_mm']:.2f} mm"],['Taper','2°'],['Print estimate',f"{round(estimate['seconds']/60)} min · {estimate['grams']:.2f} g"]],
            'note':'Reference coupon with the same mating surfaces as your successful V12 .05 test. The full V13 print was subsequently reported too tight with bowed socket arms. Keep both top faces up and slide together along the thickness.' if stile else 'This V9 coupon passed the physical fit test. It remains the joint used by the current rail. The narrower V13 stile has its own coupon.'}


def build():
    half=json.loads((artifact_path('validation-half-inch-templates.json')).read_text())['models']
    name='rail-template-elliptical-honeycomb-v10'
    report=json.loads((artifact_path('validation-rail-v10.json')).read_text())
    data=json.loads((artifact_path('curve-comparison-data.json')).read_text())
    data['print']={**mesh_payload(name,report['mesh'],report['hole_count']),'revision':'½″','center_band_inches':[v/25.4 for v in report['solid_band_x_mm']],'split_inches':report['split_x_mm']/25.4,'web_mm':round(report['minimum_web_mm'],3),'rim_mm':round(report['minimum_perimeter_rim_mm'],3),'title':'Rail template','description':'Elliptical honeycomb · ½″','fields':[['Width','15⅞″'],['End heights','3″ / 6″'],['Thickness','½″'],['Minimum webs','10 mm'],['Solid center','3½″']]}
    data['print']['fields'] += [['Hexagons','5 short side · 8 tall side']]
    data['parts']={'rail':data['print']}
    stiles=json.loads((artifact_path('validation-stiles.json')).read_text())
    for side in ['left','right']:
        name=f'stile-template-{side}-half-inch'
        data['parts'][side]={**mesh_payload(name,half[name],stiles['hole_count'],True),'revision':'½″','title':f'{side.title()} stile template','description':'Curved ends for the 27″ door · ½″','split_inches':stiles['split_from_template_bottom_mm']/25.4,'fields':[['Width','2¼″'],['Outside edge','18″'],['Inside edge',f'{stiles["inner_edge_length_inches"]:.3f}″'],['Bounding length',f'{stiles["bounding_length_inches"]:.3f}″'],['Thickness','½″'],['Minimum webs','10 mm'],['Solid center','3½″']]}
    split_payload(data['parts']['rail'],'rail-template-native-dovetail-v10','rail-template-native-dovetail-v10-sliced.3mf')
    data['parts']['rail'].update(description='13 hexagons · five on the short side · approved V9 joint',note='Two pieces arranged for the P1S. Assemble with both printed top faces facing the same way; rotate the assembled template 180° in plane for the upper rail.')
    for side in ['left','right']:
        split_payload(data['parts'][side],'stile-template-left-dovetail-v13','stile-template-left-dovetail-v13-sliced.3mf',flip=side=='right',reinforced=True)
        data['parts'][side].update(description='Curved ends · narrower dovetail · thicker socket arms',note='Your successful V12 .05 coupon fit is now applied to this full V13 stile: 0.05 mm total width clearance, with the tail preserved. Side arms are 10.15 mm nominal, about 10.01 mm at the rounded lip. One assembled template rotates 180° in plane for the opposite stile. The full V13 print was reported too tight with bowed socket arms. Hold further full-stile prints pending correction.')
    data['parts']['coupon']=coupon_payload()
    data['parts']['stile-coupon']=coupon_payload(stile=True)
    data['designs']={'ellipse':{'title':'Elliptical arc','summary':'Chosen design · two reusable templates make the four frame pieces. Rotate the rail or stile 180° in its plane for the opposite side.','parts':data['parts']}}
    for key,name,report_file in [('original','rail-template','validation.json'),('bezier','rail-template-smooth-v2','validation-smooth-v2.json')]:
        validation=json.loads((artifact_path(report_file)).read_text())
        expected=validation['files'][name] if key=='original' else validation['mesh']
        name={'original':'rail-template-original-circles-half-inch','bezier':'rail-template-continuous-sweep-half-inch'}[key]
        expected=half[name]
        title='Original circles' if key=='original' else 'Continuous sweep'
        part={**mesh_payload(name,expected,0),'title':'Rail template','description':title+' · solid template','revision':'Original' if key=='original' else 'V2','fields':[['Width','15⅞″'],['End heights','3″ / 6″'],['Thickness','½″']]}
        data['designs'][key]={'title':title,'summary':'Earlier curve design · rail template available. Matching stile print files have only been made for the elliptical design.','parts':{'rail':part}}
    data['height_display']=stiles['door_height_inches']
    # Store each mesh once; duplicate vertex arrays can exceed the browser bridge limit.
    data['print']={key:data['print'][key] for key in ['outline_inches','holes_inches','split_inches']}
    del data['parts']
    from build_library import library_markup
    template=(ROOT/'source'/'comparison.html.in').read_text().replace('/*DESIGN_LIBRARY*/',library_markup())
    publish_html(artifact_path('curve-comparison.html'), template.replace('/*CURVE_DATA*/',json.dumps(data,separators=(',',':'))))
    print('Built three design groups with current template models and the selected fit coupon')


if __name__=='__main__':
    build()
