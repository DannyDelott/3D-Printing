import * as THREE from './assets/three/three.module.js';
import { STLLoader } from './assets/three/STLLoader.js';
import { OrbitControls } from './assets/three/OrbitControls.js';
import { toCreasedNormals } from './assets/three/BufferGeometryUtils.js';

/** Shared renderer for interactive STL views and the generated PNG thumbnails. */
export async function createModelView(canvas, url, { width, height, thumbnail = false } = {}) {
  const source = await new STLLoader().loadAsync(url);
  source.center();
  const geometry = toCreasedNormals(source, Math.PI / 6);
  source.dispose();
  geometry.computeBoundingSphere();
  const radius = geometry.boundingSphere.radius;
  if (!(radius > 0) || !Number.isFinite(radius)) throw new Error('Empty model bounds');

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: thumbnail });
  renderer.setPixelRatio(thumbnail ? 1 : Math.min(window.devicePixelRatio || 1, 3));
  renderer.setClearColor(0xf4f6ef, 0);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  const scene = new THREE.Scene();
  const material = new THREE.MeshStandardMaterial({ color: 0x8b9c80, roughness: 0.65, metalness: 0 });
  scene.add(new THREE.Mesh(geometry, material));
  scene.add(new THREE.HemisphereLight(0xffffff, 0x747c69, 2.5));
  for (const [position, intensity] of [[[1, -2, 3], 3], [[-2, 1, 1], 1.5]]) {
    const light = new THREE.DirectionalLight(0xffffff, intensity);
    light.position.set(...position);
    scene.add(light);
  }
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, radius / 1000, radius * 12);
  const controls = thumbnail ? null : new OrbitControls(camera, canvas);
  if (controls) {
    controls.minZoom = 0.3;
    controls.maxZoom = 12;
    controls.listenToKeyEvents(canvas);
  }
  let viewHeight;
  function render() {
    renderer.render(scene, camera);
    canvas.dataset.rendered = 'true';
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
    camera.up.set(0, top ? 1 : 0, top ? 0 : 1);
    camera.position.copy(new THREE.Vector3(...(top ? [0, 0, 1] : [0.9, -1.3, 1.1])).normalize().multiplyScalar(radius * 4));
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
  const observer = thumbnail ? null : new ResizeObserver(() => fit());
  observer?.observe(canvas);
  return {
    fit, zoomBy,
    dispose() {
      observer?.disconnect();
      controls?.dispose();
      geometry.dispose();
      material.dispose();
      renderer.dispose();
    }
  };
}

export async function mountViewer(canvas, url) {
  const view = await createModelView(canvas, url);
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
}
