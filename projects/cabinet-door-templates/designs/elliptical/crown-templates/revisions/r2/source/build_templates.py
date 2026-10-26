"""Full-size crown tracing patterns from Cabinet R7 option f, millimetres.

Run with CadQuery 2.8 and trimesh. X is door width, Y is stock thickness,
Z is printed-template thickness. Patterns describe rectangular blanks before
the asymmetric outlines, groove tongues and shiplaps are machined.
"""
from pathlib import Path
from xml.etree import ElementTree as ET
import hashlib
import json
import math
import zipfile
import cadquery as cq
import trimesh
from OCP.BRepMesh import BRepMesh_IncrementalMesh

OUT = Path(__file__).resolve().parents[1]
(OUT / 'models').mkdir(exist_ok=True)
ref = json.loads((OUT / 'source/door-reference.json').read_text())
p = ref['parameters']
DW = p['case_width'] - 2 * p['side_reveal']
BOW = p['door_bow']
RADIUS = DW * DW / (8 * BOW) + BOW / 2
MID = p['case_width'] / 2
VENEER = 0.6  # User correction: same maple veneer on both sides; supersedes R7.
THICKNESS = 2.0
parts = {}
scene = []

def export(name, shape):
    assert shape.isValid() and len(shape.Solids()) == 1, name
    shape.exportStep(str(OUT / 'models' / f'{name}.step'), write_pcurves=False)
    # Absolute deflection is essential: CadQuery's default relative tolerance
    # can flatten a broad shallow arc by tenths of a millimetre in STL/3MF.
    BRepMesh_IncrementalMesh(shape.wrapped, .005, False, .12)
    vertices, faces = shape.tessellate(.005, .12)
    mesh = trimesh.Trimesh([v.toTuple() for v in vertices], faces, process=True)
    mesh.fix_normals()
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0, name
    mesh.export(OUT / 'models' / f'{name}.stl')
    ns = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
    ET.register_namespace('', ns)
    root = ET.Element('{' + ns + '}model', unit='millimeter')
    resource = ET.SubElement(root, '{' + ns + '}resources')
    obj = ET.SubElement(resource, '{' + ns + '}object', id='1', type='model', name=name)
    me = ET.SubElement(obj, '{' + ns + '}mesh')
    vv = ET.SubElement(me, '{' + ns + '}vertices')
    ff = ET.SubElement(me, '{' + ns + '}triangles')
    for xyz in mesh.vertices:
        ET.SubElement(vv, '{' + ns + '}vertex', **dict(zip('xyz', map(str, xyz))))
    for f in mesh.faces:
        ET.SubElement(ff, '{' + ns + '}triangle', **{f'v{i+1}': str(v) for i, v in enumerate(f)})
    build = ET.SubElement(root, '{' + ns + '}build')
    ET.SubElement(build, '{' + ns + '}item', objectid='1')
    with zipfile.ZipFile(OUT / 'models' / f'{name}.3mf', 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr('_rels/.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr('3D/3dmodel.model', ET.tostring(root, encoding='utf-8', xml_declaration=True))
    loaded = cq.importers.importStep(str(OUT / 'models' / f'{name}.step')).val()
    assert loaded.isValid() and abs(loaded.Volume()-shape.Volume()) < .01
    return mesh

def pattern(name, label, a, b, base, group, kind='finished', note=''):
    # Core face is a normal 0.6 mm offset of the finished circular face.
    # Subtract back veneer from the datum too, so templates seat on bare core.
    radius = RADIUS - (VENEER if kind == 'core' else 0)
    cy = base + BOW - RADIUS - (VENEER if kind == 'core' else 0)
    def height(x):
        return cy + math.sqrt(radius * radius - x * x)
    w = b-a
    edges = [cq.Edge.makeLine((0, 0, 0), (w, 0, 0)),
             cq.Edge.makeLine((w, 0, 0), (w, height(b), 0)),
             cq.Edge.makeThreePointArc((w, height(b), 0), (w/2, height((a+b)/2), 0), (0, height(a), 0)),
             cq.Edge.makeLine((0, height(a), 0), (0, 0, 0))]
    blank = cq.Solid.extrudeLinear(cq.Wire.assembleEdges(edges), [], cq.Vector(0, 0, THICKNESS))
    # Recessed legends leave both tracing and reference edges intact.
    legend = cq.Workplane('XY').text(label, 3.1, .45, font='Arial', halign='center', valign='center', combine=True).val().translate((w/2, 7, THICKNESS-.45))
    datum = 'CORE BACK' if kind == 'core' else 'FLAT BACK'
    text = cq.Workplane('XY').text(datum, 2.3, .45, font='Arial', halign='center', valign='center', combine=True).val().translate((w/2, 2.9, THICKNESS-.45))
    assert blank.intersect(legend).Volume() > legend.Volume()*.99, (name, 'label outside silhouette')
    shape = blank.cut(legend).cut(text).clean()
    mesh = export(name, shape)
    hmax = height(max(a, min(0, b)))
    assert max(abs(mesh.extents[i]-v) for i,v in enumerate([w,hmax,THICKNESS])) < .01
    # Verify the exported polygonal tracing edge, not just the CAD circle.
    section=mesh.section(plane_origin=[0,0,1], plane_normal=[0,0,1])
    chord_errors=[]
    for loop in section.discrete:
        for q1,q2 in zip(loop,loop[1:]):
            if min(q1[1],q2[1])>0 and abs(q1[0]-q2[0])>1e-7:
                x=(q1[0]+q2[0])/2+a
                y=(q1[1]+q2[1])/2
                chord_errors.append(abs(math.hypot(x,y-cy)-radius))
    assert chord_errors and max(chord_errors)<.01, (name, chord_errors)
    meta = dict(id=name, label=label, group=group, kind=kind, width=w,
                maximum_height=hmax, template_thickness=THICKNESS,
                door_x=[a,b], radius=radius, circle_center_y=cy,
                left_height=height(a), right_height=height(b),
                datum=datum, note=note,
                size=[w,hmax,THICKNESS], volume_mm3=shape.Volume(),
                mesh_watertight=True, step_reimport_valid=True)
    meta['exported_arc_chord_error_mm']=max(chord_errors)
    # Independent sampled check against the original R7 sagitta equation.
    errors = []
    for j in range(501):
        x=a+(b-a)*j/500
        if kind == 'core':
            # Restore the backing datum and move radially out by face veneer.
            yy=height(x)+VENEER-(base+BOW-RADIUS)
            length=math.hypot(x,yy)
            errors.append(abs(length+VENEER-RADIUS))
        else:
            errors.append(abs(height(x)-(base+math.sqrt(RADIUS*RADIUS-x*x)-(RADIUS-BOW))))
    meta['profile_error_mm']=max(errors)
    assert max(errors)<1e-8
    parts[name]=meta
    scene.append(dict(**meta, vertices=mesh.vertices.round(5).tolist(), triangles=mesh.faces.tolist()))

pattern('rail-left', 'RAIL L', -DW/2, 0, p['door_thickness'], 'Rails', note='Left half, viewed from above with the door front at the top of the drawing. Butt at the centerline; align both straight back edges. Fits either rail.')
pattern('rail-right', 'RAIL R', 0, DW/2, p['door_thickness'], 'Rails', note='Right half. Same arc for top and bottom rails; this is the thickness profile, not their asymmetric elevation outline.')
pattern('stile-left', 'STILE L', -DW/2, -DW/2+p['stile_width'], p['stile_thickness'], 'Stiles', note='Outer door edge at left; inner/grooved edge at right. Trace rectangular blank ends before cutting the shaped rail joints.')
pattern('stile-right', 'STILE R', DW/2-p['stile_width'], DW/2, p['stile_thickness'], 'Stiles', note='Inner/grooved edge at left; outer door edge at right. Trace rectangular blank ends before cutting the shaped rail joints.')
for i, label in enumerate(['L','C','R'], 1):
    bounds=ref['parts'][f'Maple board {i}']['bounds'][0]
    a,b=[v-MID for v in bounds]
    for kind in ['core','finished']:
        pattern(f'panel-{label.lower()}-{kind}', f'PANEL {label} '+('CORE' if kind=='core' else 'FACE'), a,b,p['panel_thickness'], 'Panels',kind,
                'Full rectangular blank width, including later tongue/lap stock. Extend the field curve across the blank, then cut the perimeter and reduce tongues/laps separately. Left/right widths differ because the R7 shiplaps face one direction.')

params=dict(revision='R2', units='mm', source='Cabinet R7 / option f',
            door_width=DW, crown=BOW, radius=RADIUS, template_thickness=THICKNESS,
            front_veneer=VENEER, back_veneer=VENEER, panel_finished_base=p['panel_thickness'],
            perimeter_channel_depth=.2, perimeter_channel_width=1.5875, remaining_face_veneer=.4,
            confirmed='3/4-inch crown; flat backs; 0.6 mm maple on both panel faces (supersedes the R7 veneer parameter); original R7 frame dimensions; perimeter channel reduced to 0.2 mm.',
            assumptions='6.10 mm finished panel tongue envelope retained from R7. Glue-line thickness is zero in CAD. Actual veneer thickness, bending/pressing, core material and edge/lap construction must be resolved on a sample.',
            orientation='All drawings: left/right as seen from cabinet front; curved/front face up, flat back down. Trace the opposite blank end with the template flipped, keeping the same physical inner/outer edges.',
            parts=parts)
(OUT/'parameters.json').write_text(json.dumps(params,indent=2)+'\n')
(OUT/'scene.json').write_text(json.dumps(dict(parameters={k:v for k,v in params.items() if k!='parts'},parts=scene),separators=(',',':')))
# Full-scale SVGs also provide a dimensioned screen schematic, not a substitute
# for checking the physical printer scale. SVG coordinates are millimetres.
for n,t in parts.items():
    w,h=t['width'],t['maximum_height']
    def ht(x):return t['circle_center_y']+math.sqrt(t['radius']**2-x*x)
    points=[(0,h),(w,h)]+[(w-w*i/160,h-ht(t['door_x'][1]-w*i/160)) for i in range(161)]
    path=' '.join(f'{x+8:.5f},{y+8:.5f}' for x,y in points)
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w+16}mm" height="{h+32}mm" viewBox="0 0 {w+16} {h+32}"><rect width="100%" height="100%" fill="white"/><polygon points="{path}" fill="#dce7dc" stroke="#385342" stroke-width=".25"/><text x="{w/2+8}" y="{h/2+8}" font-size="3" text-anchor="middle" font-family="sans-serif">{t['label']}</text><text x="{w/2+8}" y="{h+6}" font-size="2.4" text-anchor="middle" font-family="sans-serif">{t['datum']}</text><path d="M8 {h+17}H{w+8} M8 {h+15}v4 M{w+8} {h+15}v4" stroke="#385342" stroke-width=".2"/><text x="{w/2+8}" y="{h+22}" font-size="3" text-anchor="middle" font-family="sans-serif">{w:.3f} mm / {w/25.4:.3f} in</text><text x="8" y="4" font-size="2.5" font-family="sans-serif">Left {t['left_height']:.3f} mm</text><text x="{w+8}" y="4" font-size="2.5" text-anchor="end" font-family="sans-serif">Right {t['right_height']:.3f} mm</text></svg>'''
    (OUT/f'{n}.svg').write_text(svg)
validation=dict(revision='R2', compatible_assembly='R8 option f; tracing profiles unchanged', perimeter_channel_depth_mm=.2, all_meshes_watertight=True, all_step_reimports_valid=True,
                maximum_profile_error_mm=max(x['profile_error_mm'] for x in parts.values()),
                maximum_exported_arc_chord_error_mm=max(x['exported_arc_chord_error_mm'] for x in parts.values()),
                rail_join_height_error_mm=abs(parts['rail-left']['right_height']-parts['rail-right']['left_height']),
                source_sha256=ref['source_sha256'], physical_print_validation='Not performed',
                scope='Arc and dimensions checked analytically against R7; not a full woodworking joinery or veneer layup validation.',
                files={n:hashlib.sha256((OUT/'models'/f'{n}.3mf').read_bytes()).hexdigest() for n in parts})
(OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
print(json.dumps({n:t['size'] for n,t in parts.items()},indent=2))
