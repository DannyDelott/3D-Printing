#!/usr/bin/env python3
"""Exact two-circle rail profile, printable meshes, and a dimensioned preview.

Input dimensions are inches; all CAD and mesh output coordinates are mm.
The two circular arcs share a tangent at half of the finished rail width.
"""
from __future__ import annotations

from project_paths import artifact_path, artifact_url, publish_html
import argparse
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.GC import GC_MakeArcOfCircle
from OCP.gp import gp_Pnt, gp_Vec
from OCP.IFSelect import IFSelect_RetDone
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCP.STEPControl import STEPControl_Reader
from OCP.StlAPI import StlAPI_Writer

ROOT = Path(__file__).resolve().parents[1]
MM = 25.4


class RailProfile:
    """Solve a tangent circular pair from width, end heights, and radii."""

    def __init__(self, width, left_height, right_height, radius_left, radius_right):
        self.width, self.left, self.right = width, left_height, right_height
        self.r1, self.r2 = radius_left, radius_right
        self.join = width / 2
        if min(width, left_height, right_height, radius_left, radius_right) <= 0:
            raise ValueError("All dimensions must be positive")
        # For a single-valued lower circular branch, all tangent sines stay (-1,1).
        lo = max(-1.0, -1 + self.join / self.r1) + 1e-10
        hi = min(1.0, 1 - self.join / self.r2) - 1e-10
        target = right_height - left_height
        def rise(s):
            a, b = s - self.join / self.r1, s + self.join / self.r2
            c = math.sqrt(1 - s*s)
            return self.r1 * (math.sqrt(1-a*a) - c) + self.r2 * (c - math.sqrt(1-b*b))
        if lo >= hi or not rise(lo) <= target <= rise(hi):
            raise ValueError("These radii cannot make this tangent, non-overhanging profile")
        for _ in range(100):
            mid = (lo + hi) / 2
            if rise(mid) < target:
                lo = mid
            else:
                hi = mid
        self.s = (lo + hi) / 2
        self.cx1 = self.join - self.r1 * self.s
        self.cy1 = self.left + math.sqrt(self.r1**2 - self.cx1**2)
        self.jy = self.cy1 - self.r1 * math.sqrt(1-self.s**2)
        self.cx2 = self.join - self.r2 * self.s
        self.cy2 = self.jy + self.r2 * math.sqrt(1-self.s**2)
        assert abs(self.height(0) - left_height) < 1e-8
        assert abs(self.height(width) - right_height) < 1e-8
        assert abs((self.join-self.cx1)/self.r1 - (self.join-self.cx2)/self.r2) < 1e-10

    def height(self, x):
        r, cx, cy = (self.r1, self.cx1, self.cy1) if x <= self.join else (self.r2, self.cx2, self.cy2)
        return cy - math.sqrt(r*r - (x-cx)**2)

    def solid(self, start, end, thickness):
        def point(x):
            return gp_Pnt(x, self.height(x), 0)
        wire = BRepBuilderAPI_MakeWire()
        wire.Add(BRepBuilderAPI_MakeEdge(gp_Pnt(start, 0, 0), gp_Pnt(end, 0, 0)).Edge())
        wire.Add(BRepBuilderAPI_MakeEdge(gp_Pnt(end, 0, 0), point(end)).Edge())
        cuts = sorted(set([start, end] + ([self.join] if start < self.join < end else [])), reverse=True)
        for a, b in zip(cuts, cuts[1:]):
            arc = GC_MakeArcOfCircle(point(a), point((a+b)/2), point(b)).Value()
            wire.Add(BRepBuilderAPI_MakeEdge(arc).Edge())
        wire.Add(BRepBuilderAPI_MakeEdge(point(start), gp_Pnt(start, 0, 0)).Edge())
        return BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(wire.Wire()).Face(), gp_Vec(0, 0, thickness)).Shape()


def export(shape, name):
    if not BRepCheck_Analyzer(shape).IsValid():
        raise ValueError(f"Invalid solid: {name}")
    step = STEPControl_Writer()
    step.Transfer(shape, STEPControl_AsIs)
    path = artifact_path(name+'.step').with_suffix('')
    if step.Write(str(path.with_suffix('.step'))) != IFSelect_RetDone:
        raise RuntimeError("STEP export failed")
    reread = STEPControl_Reader()
    assert reread.ReadFile(str(path.with_suffix('.step'))) == IFSelect_RetDone
    reread.TransferRoots()
    assert BRepCheck_Analyzer(reread.OneShape()).IsValid()
    BRepMesh_IncrementalMesh(shape, .01, False, math.radians(.25), True)
    writer = StlAPI_Writer()
    writer.ASCIIMode = False
    assert writer.Write(shape, str(path.with_suffix('.stl')))
    mesh = trimesh.load_mesh(path.with_suffix('.stl'), force='mesh', process=True)
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0
    assert len(mesh.split()) == 1
    # Give each individual part a convenient local origin for slicers.
    mesh.apply_translation(-mesh.bounds[0])
    mesh.export(path.with_suffix('.stl'))
    path.with_suffix('.3mf').write_bytes(mesh.export(file_type='3mf'))
    imported = trimesh.load(path.with_suffix('.3mf'), force='mesh')
    assert np.allclose(imported.extents, mesh.extents, atol=1e-5)
    return {'size_mm': mesh.extents.tolist(), 'volume_cm3': mesh.volume / 1000, 'triangles': len(mesh.faces), 'watertight': mesh.is_watertight, 'bodies': len(mesh.split())}


def preview(p, thickness, dest):
    fig, (ax, cabinet) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [1, 1.1]}, facecolor='#faf8f3')
    fig.suptitle('Cabinet rail routing template', x=.07, ha='left', fontsize=23, color='#243e36')
    fig.text(.07, .925, 'Exact circular arcs • smooth tangent at the midpoint • dimensions in inches', fontsize=11, color='#535f59')
    x = np.linspace(0, p.width, 501)
    y = np.array([p.height(a) for a in x])
    xi, yi = x/MM, y/MM
    w, j = p.width/MM, p.join/MM
    for a in (ax, cabinet):
        a.set_aspect('equal'); a.axis('off'); a.set_facecolor('#faf8f3')
    ax.fill_between(xi, 0, yi, color='#e4cfaa')
    left = xi <= j
    ax.plot(xi[left], yi[left], color='#347c70', lw=3)
    ax.plot(xi[~left], yi[~left], color='#c47741', lw=3)
    ax.plot([0,0,w,w], [p.left/MM,0,0,p.right/MM], color='#7a705e', lw=1)
    ax.plot([j,j], [0,p.jy/MM], '--', color='#7a705e', lw=1)
    ax.annotate('', (0,-.7), (w,-.7), arrowprops={'arrowstyle':'<->','color':'#535f59'})
    ax.text(j,-1.15,f'{w:g}″ overall  /  {p.width:.3f} mm', ha='center', fontsize=12)
    ax.text(-.25,p.left/MM/2,f'{p.left/MM:g}″', ha='right', va='center', fontsize=12)
    ax.text(w+.25,p.right/MM/2,f'{p.right/MM:g}″', va='center', fontsize=12)
    ax.text(j*.46, 1.4, f'R {p.r1/MM:g}″', ha='center', color='#347c70', fontsize=16)
    ax.text(j*1.5, 1.4, f'R {p.r2/MM:g}″', ha='center', color='#aa5f2d', fontsize=16)
    ax.text(j, -.22, f'midpoint {j:g}″', ha='center', va='top', fontsize=9)
    ax.set_xlim(-1.6,w+1.6); ax.set_ylim(-1.6,7)
    # Top rail is the very same profile rotated 180 degrees in its plane.
    # Display door/rail relationship at reduced height; not a cabinet construction drawing.
    h = 15
    cabinet.fill_between(xi, 0, yi, color='#e4cfaa')
    cabinet.fill_between(xi, h-yi[::-1], h, color='#e4cfaa')
    cabinet.plot(xi, yi, color='#347c70', lw=2)
    cabinet.plot(xi, h-yi[::-1], color='#347c70', lw=2)
    cabinet.plot([0,0,w,w,0], [0,h,h,0,0], color='#7a705e', lw=1)
    cabinet.text(w+.7, h/2, 'Same template for both rails\nRotate 180° for the top rail\n\nCabinet view shortened vertically', va='center', fontsize=11, color='#535f59')
    cabinet.set_xlim(-1.6,w+10); cabinet.set_ylim(-.3,h+.3)
    fig.text(.07,.035, f'18″ − 2 × 3/4″ sides − 3/8″ hinge strip − 2 × 1/8″ gaps = 15 7/8″ finished width.\n3/4″ ({thickness:g} mm) thick • one solid for slicer splitting • zero offset for a matching bearing and cutter.', fontsize=10, color='#535f59')
    fig.subplots_adjust(left=.07,right=.95,top=.89,bottom=.1,hspace=.17)
    fig.savefig(dest, dpi=170, facecolor=fig.get_facecolor())
    plt.close(fig)


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('--width', type=float, default=15.875)
    a.add_argument('--left-height', type=float, default=3)
    a.add_argument('--right-height', type=float, default=6)
    a.add_argument('--radius-left', type=float, default=60)
    a.add_argument('--radius-right', type=float, default=18)
    a.add_argument('--thickness-mm', type=float, default=19.05)
    args = a.parse_args()
    if args.thickness_mm <= 0:
        a.error('Thickness must be positive')
    p = RailProfile(*(v*MM for v in (args.width,args.left_height,args.right_height,args.radius_left,args.radius_right)))
    full = p.solid(0,p.width,args.thickness_mm)
    result = {'status':'user dimensions confirmed; CAD and mesh validated; not physically printed or routed', 'parameters':vars(args), 'join_height_inches':p.jy/MM, 'circle_centers_mm':[[p.cx1,p.cy1],[p.cx2,p.cy2]], 'tangent_angle_degrees':math.degrees(math.asin(p.s)), 'files':{}}
    result['files']['rail-template'] = export(full,'rail-template')
    preview(p,args.thickness_mm,artifact_path('rail-preview.png'))
    (artifact_path('validation.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
