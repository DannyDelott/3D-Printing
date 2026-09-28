"""Build selectable assembly previews from shoe STEP files in assembly coordinates.

Carrier and knob come from the approved full assembly, with their transforms
preserved. Outputs are viewing meshes, not print plates. Run with CAD Python.
"""
import hashlib
import json
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.StlAPI import StlAPI_Writer

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT/'projects/sanding-plane'


def main():
    project = next(p for p in json.loads((ROOT/'site/catalog.json').read_text()) if p['id']=='sanding-plane')
    report = {}
    for shoe in project['assemblyShoes']:
        # Existing Magnate previews remain the approved source assembly itself.
        if shoe['id'] == 'shoe':
            continue
        source = ROOT/shoe['source']
        solid = cq.importers.importStep(str(source)).val()
        assert solid.isValid() and len(solid.Solids())==1
        BRepMesh_IncrementalMesh(solid.wrapped,.025,False,.006,True)
        temp=PROJECT/'work/assembly-shoe.stl'
        temp.parent.mkdir(exist_ok=True)
        writer=StlAPI_Writer();writer.ASCIIMode=False
        assert writer.Write(solid.wrapped,str(temp))
        replacement=trimesh.load_mesh(temp,process=True)
        assert replacement.is_watertight
        for mode in ('assembly','exploded'):
            suffix = '-exploded' if mode=='exploded' else ''
            original=PROJECT/f'models/profile-jig-profile-up-full{suffix}-preview.3mf'
            scene=trimesh.load(original)
            parts={}
            for node in scene.graph.nodes_geometry:
                transform,name=scene.graph[node]
                mesh=scene.geometry[name].copy()
                mesh.apply_transform(transform)
                parts[name]=mesh
            new_shoe=replacement.copy()
            if mode=='exploded':new_shoe.apply_translation([0,0,-25])
            # Rail cap and length must match the removed shoe in each view.
            assert np.allclose(new_shoe.bounds[:,1],parts['Shoe'].bounds[:,1],atol=.001)
            assert abs(new_shoe.bounds[1,2]-parts['Shoe'].bounds[1,2])<.001
            parts['Shoe']=new_shoe
            if mode=='assembly':
                for name in ('Body','Knob'):
                    collision=trimesh.boolean.intersection([new_shoe,parts[name]],engine='manifold')
                    assert abs(collision.volume)<.02,(name,collision.volume)
            output=ROOT/'site'/shoe[mode]['model']
            mesh=trimesh.util.concatenate(list(parts.values()))
            assert mesh.is_watertight and len(mesh.split())==3
            mesh.export(output)
            report[f"{shoe['id']}/{mode}"]=dict(
                source_step_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                source_assembly_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
                preview_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                bounds_mm=mesh.bounds.tolist(),bodies=3,
                carrier_and_knob='Unmodified meshes and assembly transforms from source 3MF')
            print(output.relative_to(ROOT))
    (PROJECT/'validation-assembly-previews.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
