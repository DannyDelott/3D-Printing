// Run with the browser tool's code runner while the assembly viewer is open.
// This inspects actual rendered normals on planar CAD faces, not material flags.
async (page) => {
  return await page.evaluate(() => {
    const reports = [];
    for (const name of ['Case left', 'Case right', ...cabinetStudy.model.parts.filter(p => p.material === 'walnut').map(p => p.name)]) {
      const mesh = cabinetStudy.scene.getObjectByName(name), g = mesh.geometry;
      const p = g.attributes.position, n = g.attributes.normal, index = g.index;
      let planar = 0, bad = 0;
      const count = index ? index.count : p.count;
      for (let t = 0; t < count; t += 3) {
        const ids = [0, 1, 2].map(k => index ? index.getX(t + k) : t + k);
        const v = ids.map(i => [p.getX(i), p.getY(i), p.getZ(i)]);
        const a = v[1].map((x, k) => x - v[0][k]), b = v[2].map((x, k) => x - v[0][k]);
        const c = [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
        const area2 = Math.hypot(...c);
        if (area2 < 100) continue;
        const normal = c.map(x => x/area2);
        const planeAxis = name.startsWith('Walnut') ? 2 : 0;
        if (Math.abs(normal[planeAxis]) < .99999) continue;
        planar++;
        if (ids.some(i => normal[0]*n.getX(i)+normal[1]*n.getY(i)+normal[2]*n.getZ(i) < .999)) bad++;
      }
      if (!planar || bad || mesh.material.opacity !== 1 || mesh.material.transparent) {
        throw new Error(`${name}: ${bad}/${planar} planar triangles have false smooth normals; opacity=${mesh.material.opacity}`);
      }
      reports.push({name, planarTriangles: planar, incorrectNormals: bad, opaque: true});
    }
    return reports;
  });
}
