#!/usr/bin/env python3
"""Apply only the new stock thickness to the existing split stile design."""
from project_paths import artifact_path, artifact_url, publish_html
from zipfile import ZipFile
import json
import cadquery as cq
from round_native_dovetail import ROOT,THICKNESS,export_mesh
from prepare_native_dovetail import write_project

parts={}
for label in ['tongue','socket']:
 source=artifact_path(f'stile-template-left-dovetail-v2-{label}.step')
 shape=cq.importers.importStep(str(source)).val()
 box=shape.BoundingBox();shape=shape.translate((-box.xmin,-box.ymin,-box.zmin))
 shape=shape.intersect(cq.Workplane().box(box.xlen+1,box.ylen+1,THICKNESS,centered=(False,False,False)).val()).clean()
 geometry=export_mesh(shape,f'stile-template-left-dovetail-half-inch-{label}')
 assert abs(geometry.extents[2]-THICKNESS)<1e-5
 geometry.apply_translation(-geometry.bounds.mean(axis=0));parts[label.title()]=geometry
with ZipFile(artifact_path('stile-template-left-dovetail-v2-bambu.3mf')) as z:files={n:z.read(n) for n in z.namelist()}
report=write_project(files,parts,[(128,90),(128,166)],artifact_path('stile-template-left-dovetail-half-inch-bambu.3mf'),'HALF INCH stile - existing joint')
(artifact_path('validation-half-inch-stile.json')).write_text(json.dumps({'thickness_mm':THICKNESS,'joint':'Existing V2 joint retained; thickness change only. New rail radii and clearance are not applied to this joint.','parts':report},indent=2)+'\n')
print('Prepared 12.7 mm split stile; existing joint retained.')
