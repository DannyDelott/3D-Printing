#!/usr/bin/env python3
"""Split the existing V3 CAD into a through-thickness sliding dovetail pair."""
from project_paths import artifact_path, artifact_url, publish_html
import json
import math
import numpy as np
import trimesh
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Cut
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.STEPControl import STEPControl_Reader
from OCP.IFSelect import IFSelect_RetDone
from OCP.gp import gp_Pnt, gp_Vec
from generate_template import ROOT, export
from generate_ellipse import WIDTH, LEFT, RIGHT, THICKNESS, Q

NAME = 'rail-template-dovetail-v4'
SPLIT = WIDTH * 25.4 / 2
HEAD, NECK, DEPTH, CLEARANCE = 38.1, 25.4, 19.05, 0.2


def prism(points):
    wire = BRepBuilderAPI_MakePolygon()
    for x, y in points:
        wire.Add(gp_Pnt(float(x), float(y), -1))
    wire.Close()
    return BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(wire.Wire()).Face(), gp_Vec(0, 0, THICKNESS+2)).Shape()


def offset_polygon(points, distance):
    """Mitered outward offset of this counterclockwise connector boundary."""
    p = np.asarray(points, dtype=float)
    edges = np.roll(p, -1, axis=0) - p
    normals = np.column_stack((edges[:, 1], -edges[:, 0]))
    normals /= np.linalg.norm(normals, axis=1)[:, None]
    return [point + np.linalg.solve(np.vstack((normals[i-1], normals[i])), [distance, distance]) for i, point in enumerate(p)]


def volume(shape):
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    return props.Mass()


def main():
    reader = STEPControl_Reader()
    assert reader.ReadFile(str(artifact_path('rail-template-elliptical-honeycomb-v3.step'))) == IFSelect_RetDone
    reader.TransferRoots()
    original = reader.OneShape()
    a = WIDTH/Q
    b = (RIGHT-LEFT)/(1-math.sqrt(1-Q*Q))
    center_height = (LEFT+b-b*math.sqrt(1-(WIDTH/2/a)**2))*25.4
    cy = center_height/2
    boundary = [(-10,-10),(SPLIT,-10),(SPLIT,cy-NECK/2),(SPLIT+DEPTH,cy-HEAD/2),
                (SPLIT+DEPTH,cy+HEAD/2),(SPLIT,cy+NECK/2),(SPLIT,200),(-10,200)]
    male_mask = prism(boundary)
    female_mask = prism(offset_polygon(boundary, CLEARANCE))
    parts = [BRepAlgoAPI_Common(original, male_mask).Shape(), BRepAlgoAPI_Cut(original, female_mask).Shape()]
    assert volume(BRepAlgoAPI_Common(*parts).Shape()) < 1e-5
    assert all(volume(BRepAlgoAPI_Cut(p,original).Shape()) < 1e-5 for p in parts)
    removed = volume(original)-sum(volume(p) for p in parts)
    assert 0 < removed < 1000
    meshes = []
    info = {}
    for label, part in zip(['left','right'],parts):
        info[label] = export(part,f'{NAME}-{label}')
        assert max(info[label]['size_mm'][:2]) < 246
        mesh = trimesh.load_mesh(artifact_path(f'{NAME}-{label}.stl'))
        meshes.append(mesh)
    # Keep the scene as two independent model objects, in their assembled coordinates.
    meshes[1].apply_translation([SPLIT+CLEARANCE,0,0])
    scene = trimesh.Scene()
    for label,mesh in zip(['Left - dovetail tongue','Right - dovetail socket'],meshes):
        scene.add_geometry(mesh,geom_name=label,node_name=label)
    (artifact_path(f'{NAME}.3mf')).write_bytes(scene.export(file_type='3mf'))
    loaded = trimesh.load(artifact_path(f'{NAME}.3mf'))
    assert len(loaded.geometry) == 2
    assert np.allclose(loaded.extents,[WIDTH*25.4,RIGHT*25.4,THICKNESS],atol=1e-4)
    report = {'revision':NAME,'split_x_mm':SPLIT,'head_width_mm':HEAD,'neck_width_mm':NECK,
              'engagement_mm':DEPTH,'normal_clearance_mm':CLEARANCE,'thickness_mm':THICKNESS,
              'joint_center_y_mm':cy,'removed_clearance_volume_mm3':removed,'parts':info,
              'status':'Valid CAD; watertight single-body halves; two-object 3MF; physical fit untested.'}
    (artifact_path('validation-dovetail-v4.json')).write_text(json.dumps(report,indent=2)+'\n')
    # Reuse the project's offline orbit/zoom viewer with this revision's actual mesh.
    displayed = [mesh.copy() for mesh in meshes]
    displayed[1].apply_translation([12,0,0])
    combined = trimesh.util.concatenate(displayed)
    center = combined.bounds.mean(axis=0)
    vertices = np.concatenate((combined.triangles-center,np.repeat(combined.face_normals[:,None,:],3,axis=1)),axis=2)
    data = {'print':{'vertices':np.round(vertices.reshape(-1),5).tolist(),'bounds_mm':combined.extents.tolist()}}
    source = (ROOT/'source/comparison.html.in').read_text()
    viewer = source[source.index('function startPreview()'):source.index('</script>')]
    # Top faces produce an exact mesh-derived schematic, including holes and seam.
    paths=[]
    for mesh,color in zip(meshes,['#cba778','#789b94']):
        triangles=mesh.triangles[mesh.face_normals[:,2]>.99,:,:2]
        d=' '.join('M'+' L'.join(f'{x:.3f},{-y:.3f}' for x,y in tri)+' Z' for tri in triangles)
        paths.append(f'<path d="{d}" fill="{color}"/>')
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Rail template · dovetail V4</title>
<style>body{margin:32px auto;max-width:1040px;padding:0 24px;background:#faf8f3;color:#243e36;font:16px system-ui}h1{font-size:32px;margin-bottom:8px}p{line-height:1.5}a,button{display:inline-block;border:1px solid #789b94;border-radius:7px;padding:10px 15px;background:transparent;color:#243e36;text-decoration:none;cursor:pointer}a.primary{background:#243e36;color:white}canvas{width:100%;height:370px;touch-action:none;border:1px solid #ddd4c6;border-radius:12px}svg{width:100%;height:310px}table{border-collapse:collapse;width:100%;margin:20px 0}td{padding:10px;border-bottom:1px solid #ddd4c6}td:last-child{text-align:right}small{color:#53615b}</style>
<h1>Rail template · dovetail V4</h1><p>Two printable halves of the elliptical honeycomb template, joined by a sliding dovetail.</p>
<p><a class="primary" href="models/NAME.3mf" download>Download 3MF · two objects</a> <a href="models/NAME-left.3mf" download>Left half</a> <a href="models/NAME-right.3mf" download>Right half</a></p>
<canvas id="print-canvas" tabindex="0" aria-label="Interactive 3D preview: drag to orbit; scroll to zoom"></canvas><p id="print-error" hidden></p><p><button id="view-reset">Reset</button> <button id="view-top">Top</button> <button id="zoom-in">+</button> <button id="zoom-out">−</button> <small>Drag to orbit · scroll to zoom · halves shown 12 mm apart</small></p>
<svg viewBox="-20 -180 450 230" role="img" aria-label="Assembled top view with dimensions">PATHS<g fill="#243e36" font-size="8" font-family="system-ui"><text x="140" y="28">403.225 mm overall</text><text x="5" y="-85">76.2 mm</text><text x="344" y="-162">152.4 mm</text><text x="140" y="43">Split at 201.6125 mm · thickness 19.05 mm</text></g><path d="M0 6 V18 H403.225 V6" fill="none" stroke="#53615b" stroke-width=".6"/></svg>
<table><tr><td>Dovetail head / neck</td><td>38.1 / 25.4 mm</td></tr><tr><td>Engagement</td><td>19.05 mm</td></tr><tr><td>Clearance, normal to mating surfaces</td><td>0.2 mm</td></tr><tr><td>Left half</td><td>220.663 × 89.496 × 19.05 mm</td></tr><tr><td>Right half</td><td>201.413 × 152.4 × 19.05 mm</td></tr></table>
<p>Print both halves flat at 100% scale. Each fits a P1S bed; the saved Bambu project arranges both on one plate. Slide the tongue into the socket through the thickness. The joint stays within the original solid center band. PLA clearance is a starting assumption; physical fit is untested. Check the routing edge is flush and secure the assembled template before use.</p><p><small>Digitally checked: two valid CAD solids, watertight meshes, no overlap, original outline retained except for the joint clearance.</small></p><script>const data=DATA;data.print.view_bounds_mm=data.print.bounds_mm;let activePrint=data.print,previewRenderer=null;VIEWER</script></html>'''
    # Dimensions in the datasheet are calculated from the exported revision.
    html=html.replace('220.663 × 89.496',f"{info['left']['size_mm'][0]:.3f} × {info['left']['size_mm'][1]:.3f}")
    html=html.replace('201.413 × 152.4',f"{info['right']['size_mm'][0]:.3f} × {info['right']['size_mm'][1]:.3f}")
    html=html.replace('NAME',NAME).replace('PATHS',''.join(paths)).replace('DATA',json.dumps(data,separators=(',',':'))).replace('VIEWER',viewer)
    publish_html(artifact_path('dovetail-v4.html'), html)
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
