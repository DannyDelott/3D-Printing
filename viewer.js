/** Load one binary STL on demand. The static preview and downloads work without WebGL. */
export async function mountViewer(canvas, url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Model request failed: ${response.status}`);
  const raw = await response.arrayBuffer();
  if (raw.byteLength < 84) throw new Error('Invalid STL header');
  const view = new DataView(raw);
  const count = view.getUint32(80, true);
  if (!count || raw.byteLength !== 84 + count * 50) throw new Error('Invalid binary STL');
  const data = new Float32Array(count * 18);
  const min = [Infinity, Infinity, Infinity];
  const max = [-Infinity, -Infinity, -Infinity];
  for (let i = 0; i < count; i++) {
    const offset = 84 + i * 50;
    for (let vertex = 0; vertex < 3; vertex++) {
      for (let axis = 0; axis < 3; axis++) {
        const value = view.getFloat32(offset + 12 + vertex * 12 + axis * 4, true);
        if (!Number.isFinite(value)) throw new Error('Invalid STL vertex');
        data[i * 18 + vertex * 6 + axis] = value;
        data[i * 18 + vertex * 6 + axis + 3] = view.getFloat32(offset + axis * 4, true);
        min[axis] = Math.min(min[axis], value);
        max[axis] = Math.max(max[axis], value);
      }
    }
  }
  const center = min.map((value, axis) => (value + max[axis]) / 2);
  const bounds = min.map((value, axis) => max[axis] - value);
  const span = Math.max(...bounds);
  if (!(span > 0)) throw new Error('Empty model bounds');
  for (let i = 0; i < data.length; i += 6) {
    for (let axis = 0; axis < 3; axis++) data[i + axis] -= center[axis];
  }

  const gl = canvas.getContext('webgl', { antialias: true, alpha: true });
  if (!gl) throw new Error('WebGL unavailable');
  const program = gl.createProgram();
  function attachShader(type, source) {
    const shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw new Error('Shader compilation failed');
    gl.attachShader(program, shader);
    gl.deleteShader(shader);
  }
  attachShader(gl.VERTEX_SHADER, `
    attribute vec3 position;
    attribute vec3 normal;
    uniform mat3 rotation;
    uniform vec2 scale;
    uniform float depth;
    varying vec3 n;
    void main() {
      vec3 p = rotation * position;
      gl_Position = vec4(p.x * scale.x, p.y * scale.y, -p.z / depth, 1.0);
      n = rotation * normal;
    }
  `);
  attachShader(gl.FRAGMENT_SHADER, `
    precision mediump float;
    varying vec3 n;
    void main() {
      float light = .55 + .45 * max(0.0, dot(normalize(n), normalize(vec3(-.35, .5, 1.0))));
      gl_FragColor = vec4(vec3(.60, .69, .55) * light, 1.0);
    }
  `);
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error('WebGL linking failed');
  gl.useProgram(program);
  const buffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
  for (const [name, offset] of [['position', 0], ['normal', 12]]) {
    const id = gl.getAttribLocation(program, name);
    gl.enableVertexAttribArray(id);
    gl.vertexAttribPointer(id, 3, gl.FLOAT, false, 24, offset);
  }
  const rotation = gl.getUniformLocation(program, 'rotation');
  const scale = gl.getUniformLocation(program, 'scale');
  gl.enable(gl.DEPTH_TEST);
  gl.clearColor(0, 0, 0, 0);
  gl.uniform1f(gl.getUniformLocation(program, 'depth'), span * 2);
  let azimuth = -.30;
  let tilt = .70;
  let zoom = 1;
  let pointer;

  function render() {
    const ratio = Math.min(devicePixelRatio || 1, 2);
    const width = Math.max(1, Math.round(canvas.clientWidth * ratio));
    const height = Math.max(1, Math.round(canvas.clientHeight * ratio));
    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width;
      canvas.height = height;
    }
    gl.viewport(0, 0, width, height);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    const c = Math.cos(azimuth), s = Math.sin(azimuth), ct = Math.cos(tilt), st = Math.sin(tilt);
    gl.uniformMatrix3fv(rotation, false, new Float32Array([c, ct * s, st * s, -s, ct * c, st * c, 0, -st, ct]));
    const projectedWidth = Math.abs(c) * bounds[0] + Math.abs(s) * bounds[1];
    const projectedHeight = Math.abs(ct * s) * bounds[0] + Math.abs(ct * c) * bounds[1] + Math.abs(st) * bounds[2];
    const pixels = zoom * Math.min(width / (projectedWidth * 1.15), height / (Math.max(projectedHeight, span * .1) * 1.25));
    gl.uniform2f(scale, 2 * pixels / width, 2 * pixels / height);
    gl.drawArrays(gl.TRIANGLES, 0, data.length / 6);
    canvas.dataset.rendered = 'true';
  }
  function zoomBy(factor) {
    zoom = Math.max(.3, Math.min(4, zoom * factor));
    render();
  }
  canvas.onpointerdown = event => {
    pointer = { x: event.clientX, y: event.clientY };
    canvas.setPointerCapture(event.pointerId);
  };
  canvas.onpointermove = event => {
    if (!pointer) return;
    azimuth += (event.clientX - pointer.x) * .008;
    tilt += (event.clientY - pointer.y) * .008;
    pointer = { x: event.clientX, y: event.clientY };
    render();
  };
  canvas.onpointerup = canvas.onpointercancel = () => { pointer = null; };
  canvas.onwheel = event => { event.preventDefault(); zoomBy(Math.exp(-event.deltaY * .001)); };
  canvas.onkeydown = event => {
    if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', '+', '-', '='].includes(event.key)) return;
    event.preventDefault();
    if (event.key === 'ArrowLeft') azimuth -= .12;
    if (event.key === 'ArrowRight') azimuth += .12;
    if (event.key === 'ArrowUp') tilt -= .12;
    if (event.key === 'ArrowDown') tilt += .12;
    if (event.key === '+' || event.key === '=') zoomBy(1.1);
    if (event.key === '-') zoomBy(1 / 1.1);
    render();
  };
  document.querySelector('#zoom-in').onclick = () => zoomBy(1.2);
  document.querySelector('#zoom-out').onclick = () => zoomBy(1 / 1.2);
  document.querySelector('#reset-view').onclick = () => { azimuth = -.30; tilt = .70; zoom = 1; render(); };
  document.querySelector('#top-view').onclick = () => { azimuth = 0; tilt = 0; zoom = 1; render(); };
  canvas.addEventListener('webglcontextlost', event => {
    event.preventDefault();
    document.querySelector('#viewer-status').textContent = '3D rendering stopped. Reload the page to try again.';
    document.querySelector('#model-poster').hidden = false;
    canvas.hidden = true;
  });
  canvas.hidden = false;
  new ResizeObserver(render).observe(canvas);
  render();
}
