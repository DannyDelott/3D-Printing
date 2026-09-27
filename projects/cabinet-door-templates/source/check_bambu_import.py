#!/usr/bin/env python3
"""Reopen a delivered 3MF with Bambu's importer; reject empty/lost geometry.

A valid ZIP or a successful earlier slice does not prove the final serialized
file imports. Compare each imported object's dimensions and volume with its mesh.
"""
from pathlib import Path
import re
import subprocess
import tempfile
import trimesh
import numpy as np

BAMBU='/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'


def check_import(path):
    path=Path(path).resolve()
    with tempfile.TemporaryDirectory(prefix='bambu-import-check-') as tmp:
        result=subprocess.run([BAMBU,'--info',str(path)],cwd=tmp,capture_output=True,text=True,check=True)
    records=[]
    for block in re.split(r'^\[.*\.3mf\]\s*$',result.stdout,flags=re.M)[1:]:
        values=dict(re.findall(r'^(\w+)\s*=\s*(.+)$',block,re.M))
        records.append(values)
    expected=list(trimesh.load(path).geometry.values())
    assert len(records)==len(expected)>0, f'{path.name}: wrong number of imported objects: {len(records)}'
    actual=sorted(records,key=lambda r:float(r['volume']))
    for i,(record,mesh) in enumerate(zip(actual,sorted(expected,key=lambda m:m.volume)),1):
        volume=float(record['volume']);facets=int(record['number_of_facets'])
        assert volume>0 and facets>0, f'{path.name}: object {i} imports with {facets} facets and volume {volume}'
        assert int(record['number_of_parts'])==1, f'{path.name}: object {i} is not a single part'
        dimensions=[float(record['size_'+axis]) for axis in 'xyz']
        assert np.allclose(dimensions,mesh.extents,atol=1e-4), (dimensions,mesh.extents)
        assert np.isclose(volume,mesh.volume,rtol=1e-4), (volume,mesh.volume)
    return [{'volume_mm3':float(r['volume']),'facets':int(r['number_of_facets']),'dimensions_mm':[float(r['size_'+a]) for a in 'xyz']} for r in records]

if __name__=='__main__':
    import sys,json
    for path in sys.argv[1:]:
        print(Path(path).name,json.dumps(check_import(path)))
