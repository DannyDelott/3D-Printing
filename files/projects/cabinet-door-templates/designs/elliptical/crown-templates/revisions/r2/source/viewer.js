import * as THREE from '../vendor/three.module.js';
import {OrbitControls} from '../vendor/OrbitControls.js';
import {toCreasedNormals} from '../vendor/BufferGeometryUtils.js';
const $=id=>document.getElementById(id);
const data=await fetch('scene.json').then(r=>r.json());
const scene=new THREE.Scene();scene.background=new THREE.Color('#f1f4ef');
const renderer=new THREE.WebGLRenderer({canvas:$('view'),antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;
const camera=new THREE.OrthographicCamera(-250,250,100,-100,.1,5000);camera.up.set(0,1,0);
const controls=new OrbitControls(camera,$('view'));controls.enableDamping=true;
scene.add(new THREE.HemisphereLight(0xffffff,0x8b998c,2.1));const light=new THREE.DirectionalLight(0xffffff,2.8);light.position.set(-200,80,350);scene.add(light);
let assembly=new THREE.Group();scene.add(assembly);let span=460,cy=20;
const groups={
 rails:{title:'Rail arc · two halves',ids:['rail-left','rail-right'],description:'One tracing arc for both rails. Butt the halves together and align the straight back edges. Trace onto the narrow edge of the rectangular stock.'},
 stiles:{title:'Left and right stile',ids:['stile-left','stile-right'],description:'Tape onto each rectangular blank’s end grain. The thicker edge faces the panel; the thinner edge faces the outside of the door.'},
 cores:{title:'Panel cores · before veneer',ids:['panel-l-core','panel-c-core','panel-r-core'],description:'L, C and R end-grain patterns. Align CORE BACK with the bare core’s flat back. Allowance: 0.6 mm maple on each side.'},
 faces:{title:'Panels · finished envelope',ids:['panel-l-finished','panel-c-finished','panel-r-finished'],description:'L, C and R finished-profile checks. Use after adding the face and backing veneer; use the CORE set for shaping the bare core.'}
};
const dim=x=>`${x.toFixed(3)} mm / ${(x/25.4).toFixed(3)}″`;
function fit(){const aspect=$('view').clientWidth/$('view').clientHeight,half=Math.max(span/2+18,45*aspect);camera.left=-half;camera.right=half;camera.top=half/aspect;camera.bottom=-half/aspect;camera.updateProjectionMatrix();}
function top(){camera.position.set(span/2,cy,600);controls.target.set(span/2,cy,0);camera.zoom=1;fit();controls.update();}
function load(key){const g=groups[key];assembly.traverse(o=>{o.geometry?.dispose();o.material?.dispose();});scene.remove(assembly);assembly=new THREE.Group();scene.add(assembly);let x=0;const selected=g.ids.map(id=>data.parts.find(p=>p.id===id));cy=Math.max(...selected.map(p=>p.maximum_height))/2;
 for(const p of selected){const geom=new THREE.BufferGeometry();geom.setAttribute('position',new THREE.Float32BufferAttribute(p.vertices.flat(),3));geom.setIndex(p.triangles.flat());const shaded=toCreasedNormals(geom,Math.PI/6);const pos=shaded.getAttribute('position'),colors=[];for(let i=0;i<pos.count;i++){const c=new THREE.Color(pos.getZ(i)>1.5&&pos.getZ(i)<1.6?0x304a38:0x789b81);colors.push(c.r,c.g,c.b);}shaded.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));const mesh=new THREE.Mesh(shaded,new THREE.MeshStandardMaterial({vertexColors:true,roughness:.7}));mesh.position.x=x;mesh.name=p.id;assembly.add(mesh);x+=p.width+(key==='rails'?0:12);}
 span=x-(key==='rails'?0:12);$('title').textContent=g.title;$('description').textContent=g.description;
 $('specs').innerHTML=[['Door crown','¾″ / 19.05 mm'],['Print thickness','2 mm / 0.079″'],['Face veneer','0.6 mm'],['Backing veneer','0.6 mm'],['Tracing edge','Exact circular profile']].map(([k,v])=>`<tr><td>${k}</td><td>${v}</td></tr>`).join('');
 $('cards').innerHTML=selected.map(p=>`<article class="card"><h3>${p.label}</h3><p>Width ${dim(p.width)}<br>Left height ${dim(p.left_height)}<br>Right height ${dim(p.right_height)}<br>Maximum ${dim(p.maximum_height)}</p><a class="primary" href="models/${p.id}.3mf">Download 3MF</a><a href="models/${p.id}.step">STEP</a><a href="models/${p.id}.stl">STL</a></article>`).join('');
 $('drawings').innerHTML=selected.map(p=>`<img src="${p.id}.svg" alt="Dimensioned ${p.label} tracing profile">`).join('');
 const u=new URL(location.href);u.searchParams.set('group',key);history.replaceState(null,'',u);top();window.templates={data,scene,camera,controls,selected};
}
$('group').onchange=()=>load($('group').value);$('top').onclick=top;$('orbit').onclick=()=>{camera.position.set(span/2+span*.18,cy-150,350);controls.target.set(span/2,cy,0);controls.update();};$('reset').onclick=()=>{$('dimensions').checked=false;$('drawings').hidden=true;top();};$('dimensions').onchange=()=>{$('drawings').hidden=!$('dimensions').checked;};
new ResizeObserver(()=>{const c=$('view');renderer.setSize(c.clientWidth,c.clientHeight,false);fit();}).observe($('view'));
function draw(){requestAnimationFrame(draw);controls.update();renderer.render(scene,camera);}draw();
const requested=new URLSearchParams(location.search).get('group'),initial=groups[requested]?requested:'rails';$('group').value=initial;load(initial);
