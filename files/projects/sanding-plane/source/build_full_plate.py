"""Package the current, already-oriented full sander meshes on one P1S plate."""
import hashlib,json
import numpy as np
import trimesh
import generate_profile_up as d
import slice_tote

STEM='profile-jig-final-print-plate'


def main():
    shapes=[];sources={}
    for part,label in [('body','Carrier'),('shoe','Shoe'),('knob','Knob')]:
        path=d.g.MODELS/f'{d.PREFIX}-full-{part}.3mf'
        scene=trimesh.load(path)
        assert len(scene.geometry)==1
        mesh=next(iter(scene.geometry.values())).copy()
        assert mesh.is_watertight and mesh.is_winding_consistent
        assert abs(mesh.bounds[0,2])<1e-5
        shapes.append((label,mesh,d.c.COLORS[part]))
        sources[label]=dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    # Preserve orientation, leave 8 mm gaps and export three independent objects.
    d.g.export_assembly(shapes,STEM,layout_on_plate=True)
    scene=trimesh.load(d.g.MODELS/f'{STEM}.3mf')
    assert np.all(scene.extents[:2]<236),scene.extents
    assert len(scene.geometry)==3
    for mesh,(_,original,_) in zip(scene.geometry.values(),shapes):
        assert np.array_equal(mesh.faces,original.faces)
        assert np.allclose(mesh.vertices-mesh.bounds[0],original.vertices-original.bounds[0],atol=1e-5)
    slice_tote.package(STEM,supports=True,support_parts={'Carrier'})
    report=dict(source_models=sources,layout_dimensions_mm=scene.extents.tolist(),
        bed_mm=[256,256],minimum_object_gap_mm=8,support_parts=['Carrier'],
        orientation=dict(Carrier='Side down',Shoe='Rail cap down, profile up',Knob='Crown down, tip up'))
    (d.g.PROJECT/'validation-final-plate.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
