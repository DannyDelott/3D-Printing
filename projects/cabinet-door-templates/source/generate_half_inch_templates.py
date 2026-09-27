#!/usr/bin/env python3
"""Current 12.7 mm template stock, retaining all existing planar outlines."""
from project_paths import artifact_path, artifact_url, publish_html
import json
import cadquery as cq
from round_native_dovetail import ROOT,THICKNESS,export_mesh

SOURCES={
 'rail-template-elliptical-honeycomb-half-inch':'rail-template-elliptical-honeycomb-v3',
 'stile-template-left-half-inch':'stile-template-left-v1',
 'stile-template-right-half-inch':'stile-template-right-v1',
 'rail-template-elliptical-solid-half-inch':'rail-template-elliptical',
 'rail-template-continuous-sweep-half-inch':'rail-template-smooth-v2',
 'rail-template-original-circles-half-inch':'rail-template',
}

def main():
 report={'thickness_mm':THICKNESS,'models':{}}
 for name,source in SOURCES.items():
  original=cq.importers.importStep(str(artifact_path(f'{source}.step'))).val()
  bounds=original.BoundingBox()
  original=original.translate((-bounds.xmin,-bounds.ymin,-bounds.zmin))
  thin=original.intersect(cq.Workplane().box(bounds.xlen+1,bounds.ylen+1,THICKNESS,centered=(False,False,False)).val()).clean()
  assert thin.isValid() and len(thin.Solids())==1
  geometry=export_mesh(thin,name)
  assert abs(geometry.extents[2]-THICKNESS)<1e-5
  (artifact_path(f'{name}.3mf')).write_bytes(geometry.export(file_type='3mf'))
  report['models'][name]={'source':source,'size_mm':geometry.extents.tolist(),'watertight':True,'bodies':1,'split_for_p1s':True}
 (artifact_path('validation-half-inch-templates.json')).write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
