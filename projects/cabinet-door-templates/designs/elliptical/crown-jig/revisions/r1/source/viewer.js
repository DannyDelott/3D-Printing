import * as THREE from '../vendor/three.module.js';
import {OrbitControls} from '../vendor/OrbitControls.js';
import {toCreasedNormals} from '../vendor/BufferGeometryUtils.js';
const $=id=>document.getElementById(id),data=await fetch('scene.json').then(r=>r.json());
const scene=new THREE.Scene();scene.background=new THREE.Color('#f0f1ed');
const renderer=new THREE.WebGLRenderer({canvas:$('view'),antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.outputColorSpace=THREE.SRGBColorSpace;
const camera=new THREE.PerspectiveCamera(34,1,1,10000);camera.up.set(0,0,1);
const controls=new OrbitControls(camera,$('view'));controls.enableDamping=true;
scene.add(new THREE.HemisphereLight(0xffffff,0x9c998b,2.2));
const light=new THREE.DirectionalLight(0xffffff,2.8);light.position.set(-400,-600,1300);scene.add(light);
const bridge=new THREE.Group(),router=new THREE.Group();bridge.position.z=router.position.z=data.center_z;scene.add(bridge,router);
const wood=[];const palette={printed:0x618873,wood:0xc5a77c,tool:0x7b8990,metal:0xb6bfc3,work:0xbb854e};
for(const p of data.parts){const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(p.vertices.flat(),3));g.setIndex(p.triangles.flat());const mesh=new THREE.Mesh(toCreasedNormals(g,Math.PI/6),new THREE.MeshStandardMaterial({color:palette[p.kind],roughness:p.kind==='metal'?.35:.7,metalness:p.kind==='metal'?.65:0}));mesh.name=p.name;if(p.group==='bridge'||p.group==='router'){mesh.position.z=-data.center_z;(p.group==='bridge'?bridge:router).add(mesh);}else scene.add(mesh);if(p.group==='bridge'&&p.kind==='wood')wood.push(mesh);}
function reset(){camera.position.set(1050,-1350,1000);controls.target.set(0,0,60);$('cross').value=$('along').value=0;$('dimensions').checked=false;$('drawing').hidden=true;$('wood').checked=$('tool').checked=true;wood.forEach(m=>m.visible=true);router.visible=true;update();}
function update(){const t=Number($('cross').value)*Math.PI/180;bridge.rotation.y=router.rotation.y=t;router.position.y=Number($('along').value);$('cross-value').textContent=`${Math.round(data.parameters.target_radius*Math.sin(t))} mm`;}
$('reset').onclick=reset;$('end').onclick=()=>{camera.position.set(0,-1600,240);controls.target.set(0,0,65);};$('cross').oninput=$('along').oninput=update;$('wood').onchange=()=>wood.forEach(m=>m.visible=$('wood').checked);$('tool').onchange=()=>router.visible=$('tool').checked;$('dimensions').onchange=()=>{$('drawing').hidden=!$('dimensions').checked;};
const labels={'guide-1':'Guide 1 · outer left','guide-2':'Guide 2 · inner left','guide-3':'Guide 3 · inner right','guide-4':'Guide 4 · outer right','rail-foot':'Rail foot','guide-fit-coupon':'Guide fit coupon · use with foot','bridge-truck':'Bridge truck','roller-fit-coupon':'Roller fit coupon · use with one 608','alignment-pin':'Alignment pin','projection-gauge':'Unpowered projection gauge','travel-stop':'Travel stop'};
const checks=await fetch('validation.json').then(r=>r.json());
for(const [name,label] of Object.entries(labels)){const p=checks.parts[name];const item=document.createElement('div');item.className='download';item.innerHTML=`<strong>${label}</strong><p class="muted">${p.quantity} required · ${p.size.map(n=>n.toFixed(1)).join(' × ')} mm</p><a href="models/${name}.3mf">3MF</a><a href="models/${name}.step">STEP</a>`;$('downloads').append(item);}
reset();new ResizeObserver(()=>{const c=$('view');renderer.setSize(c.clientWidth,c.clientHeight,false);camera.aspect=c.clientWidth/c.clientHeight;camera.updateProjectionMatrix();}).observe($('view'));
function frame(){requestAnimationFrame(frame);controls.update();renderer.render(scene,camera);}frame();window.jig={scene,bridge,router,camera,controls,data};
