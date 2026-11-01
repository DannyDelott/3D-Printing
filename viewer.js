import * as THREE from './assets/three/three.module.js';
import { STLLoader } from './assets/three/STLLoader.js';
import { OrbitControls } from './assets/three/OrbitControls.js';
import { attachPicker } from './assembly-picker.js';
import { toCreasedNormals } from './assets/three/BufferGeometryUtils.js';

/** Shared renderer for interactive STL views and the generated PNG thumbnails. */
export async function createModelView(canvas, url, { width, height, thumbnail = false, faceGroups = null } = {}) {
  const source = await new STLLoader().loadAsync(url);
  function applyGroups(g) {
    if (!faceGroups) return;
    const colors = new Float32Array(g.attributes.position.count * 3);
    const palette = ['#b89467','#719885','#4c6359','#e5a45e','#778086'].map(c => new THREE.Color(c));
    let vertex = 0;
    for (const [count, index] of (faceGroups.groups ?? faceGroups)) for (let i=0; i<count*3; i++, vertex++) palette[index].toArray(colors, vertex*3);
    if (vertex !== g.attributes.position.count) throw new Error('Assembly colors do not match mesh');
    g.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
  }
  applyGroups(source);
  source.computeBoundingBox();
  let origin = source.boundingBox.getCenter(new THREE.Vector3());
  source.translate(-origin.x, -origin.y, -origin.z);
  let geometry = toCreasedNormals(source, Math.PI / 6);
  source.dispose();
  geometry.computeBoundingSphere();
  let radius = geometry.boundingSphere.radius;
  if (!(radius > 0) || !Number.isFinite(radius)) throw new Error('Empty model bounds');

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: thumbnail });
  renderer.setPixelRatio(thumbnail ? 1 : Math.min(window.devicePixelRatio || 1, 3));
  renderer.setClearColor(0xf4f6ef, 0);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  const scene = new THREE.Scene();
  const material = new THREE.MeshStandardMaterial({ color: faceGroups ? 0xffffff : 0x8b9c80, vertexColors: !!faceGroups, roughness: 0.65, metalness: 0 });
  const model = new THREE.Mesh(geometry, material);
  scene.add(model);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x747c69, 2.5));
  for (const [position, intensity] of [[[1, -2, 3], 3], [[-2, 1, 1], 1.5]]) {
    const light = new THREE.DirectionalLight(0xffffff, intensity);
    light.position.set(...position);
    scene.add(light);
  }
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, radius / 1000, radius * 12);
  // OrbitControls captures this axis at construction. STL build height is Z.
  camera.up.set(0, 0, 1);
  const controls = thumbnail ? null : new OrbitControls(camera, canvas);
  if (controls) {
    controls.rotateSpeed = 0.65;
    controls.minZoom = 0.3;
    controls.maxZoom = 12;
    controls.listenToKeyEvents(canvas);
  }
  let viewHeight;
  function render() {
    renderer.render(scene, camera);
    canvas.dataset.rendered = 'true';
    canvas.dataset.model = url;
  }
  function resize() {
    const w = width || canvas.clientWidth;
    const h = height || canvas.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.left = -viewHeight * w / h / 2;
    camera.right = -camera.left;
    camera.top = viewHeight / 2;
    camera.bottom = -camera.top;
    camera.updateProjectionMatrix();
    render();
  }
  function fit(top = false) {
    camera.position.copy(new THREE.Vector3(...(top ? [0, -0.0001, 1] : [0.9, -1.3, 1.1])).normalize().multiplyScalar(radius * 4));
    camera.lookAt(0, 0, 0);
    camera.updateMatrixWorld();
    // Fit actual projected vertices, including very long templates and thin coupons.
    const bounds = new THREE.Box3();
    const vertex = new THREE.Vector3();
    const positions = geometry.attributes.position;
    for (let i = 0; i < positions.count; i++) bounds.expandByPoint(vertex.fromBufferAttribute(positions, i).applyMatrix4(camera.matrixWorldInverse));
    // Projected bounds can be asymmetric around the orbit target.
    const halfWidth = Math.max(Math.abs(bounds.min.x), Math.abs(bounds.max.x));
    const halfHeight = Math.max(Math.abs(bounds.min.y), Math.abs(bounds.max.y));
    const aspect = (width || canvas.clientWidth) / (height || canvas.clientHeight);
    viewHeight = Math.max(halfHeight, halfWidth / aspect) * 2 * 1.22;
    camera.zoom = 1;
    if (controls) {
      controls.target.set(0, 0, 0);
      controls.update();
    }
    resize();
  }
  function zoomBy(factor) {
    camera.zoom = THREE.MathUtils.clamp(camera.zoom * factor, 0.3, 12);
    camera.updateProjectionMatrix();
    render();
  }
  canvas.hidden = false;
  fit();
  controls?.addEventListener('change', render);
  const observer = thumbnail ? null : new ResizeObserver(resize);
  observer?.observe(canvas);
  const disposePicker=thumbnail ? null : attachPicker({canvas,camera,model,geometry,material,assembly:faceGroups,url,render});
  let request = 0;
  return {
    fit, zoomBy,
    get loadedUrl() { return url; },
    async setModel(nextUrl, { refit = false } = {}) {
      const current = ++request;
      const source = await new STLLoader().loadAsync(nextUrl);
      if (current !== request) { source.dispose(); return; }
      if (refit) {
        source.computeBoundingBox();
        origin = source.boundingBox.getCenter(new THREE.Vector3());
      }
      // Assembly variants share coordinates and keep their camera. Individual
      // print selections request a fresh center and fit for their own geometry.
      source.translate(-origin.x, -origin.y, -origin.z);
      const next = toCreasedNormals(source, Math.PI / 6);
      source.dispose();
      next.computeBoundingSphere();
      const nextRadius = next.boundingSphere.radius + next.boundingSphere.center.length();
      if (!(nextRadius > 0) || !Number.isFinite(nextRadius)) {
        next.dispose();
        throw new Error('Empty model bounds');
      }
      geometry.dispose();
      geometry = next;
      model.geometry = geometry;
      radius = nextRadius;
      camera.far = radius * 12;
      camera.updateProjectionMatrix();
      url = nextUrl;
      if (refit) fit();
      else render();
    },
    dispose() {
      request++;
      observer?.disconnect();
      disposePicker?.();
      controls?.dispose();
      geometry.dispose();
      material.dispose();
      renderer.dispose();
    }
  };
}

export async function mountViewer(canvas, url) {
  const groups = canvas.closest('.viewer')?.dataset.faceGroups;
  const faceGroups = groups ? await fetch(groups).then(r => r.json()) : null;
  const view = await createModelView(canvas, url, {faceGroups});
  document.querySelector('#zoom-in').onclick = () => view.zoomBy(1.2);
  document.querySelector('#zoom-out').onclick = () => view.zoomBy(1 / 1.2);
  document.querySelector('#reset-view').onclick = () => view.fit();
  document.querySelector('#top-view').onclick = () => view.fit(true);
  canvas.addEventListener('keydown', event => {
    if (['+', '=', '-'].includes(event.key)) {
      event.preventDefault();
      view.zoomBy(event.key === '-' ? 1 / 1.2 : 1.2);
    }
  });
  canvas.addEventListener('webglcontextlost', event => {
    event.preventDefault();
    document.querySelector('#viewer-status').textContent = '3D rendering stopped. Reload to try again.';
    document.querySelector('#model-poster').hidden = false;
    canvas.hidden = true;
  });
  return view;
}
