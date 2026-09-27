"""Render a preview PNG from an STL. Uses trimesh, numpy, and matplotlib in the CAD venv."""
import sys
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

mesh = trimesh.load(sys.argv[1], force='mesh')
vertices = np.asarray(mesh.vertices)
vertices = vertices - (vertices.max(axis=0) + vertices.min(axis=0)) / 2
azimuth, elevation = np.radians([-28, 50])
c, s = np.cos(azimuth), np.sin(azimuth)
rotation = np.array([[1, 0, 0], [0, np.sin(elevation), -np.cos(elevation)], [0, np.cos(elevation), np.sin(elevation)]]) @ np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
vertices = vertices @ rotation.T
triangles = vertices[mesh.faces]
shade = .6 + .4 * np.maximum(0, np.asarray(mesh.face_normals) @ rotation.T @ np.array([-.35, .3, .88]))
order = np.argsort(triangles[:, :, 2].mean(axis=1))
figure, axes = plt.subplots(figsize=(10, 7), dpi=110)
axes.add_collection(PolyCollection(triangles[order, :, :2], facecolors=(shade[:, None] * np.array([.49, .57, .49]))[order], edgecolors='none', rasterized=True))
axes.set_aspect('equal')
low, high = vertices[:, :2].min(axis=0), vertices[:, :2].max(axis=0)
center = (low + high) / 2
span = max((high[0] - low[0]) / 1.42, high[1] - low[1]) * 1.12
axes.set_xlim(center[0] - span * .71, center[0] + span * .71)
axes.set_ylim(center[1] - span / 2, center[1] + span / 2)
axes.axis('off')
figure.subplots_adjust(0, 0, 1, 1)
figure.savefig(sys.argv[2], transparent=True)
