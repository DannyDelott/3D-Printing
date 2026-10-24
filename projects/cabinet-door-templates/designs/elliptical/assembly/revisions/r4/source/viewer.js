import * as THREE from '../vendor/three.module.js';
import {OrbitControls} from '../vendor/OrbitControls.js';
import {toCreasedNormals} from '../vendor/BufferGeometryUtils.js';
import {MODEL as A} from '../a/model-data.js';
import {MODEL as B} from '../b/model-data.js';
let panelFigure=new URLSearchParams(location.search).get('wood')==='curly'?'curly':'quilted';
const quiltTexture=new THREE.TextureLoader().load('textures/quilted-maple-reference.png');
quiltTexture.colorSpace=THREE.SRGBColorSpace;quiltTexture.wrapS=quiltTexture.wrapT=THREE.MirroredRepeatWrapping;
const MODELS={a:A,b:B};let MODEL=B;let choice='b';
let p=MODEL.parameters,d=MODEL.derived;const W=p.case_width,H=p.case_height,D=p.case_depth,G=p.door_gap,T=p.door_thickness;
const $=id=>document.getElementById(id), canvas=$('view');
const scene=new THREE.Scene();scene.background=new THREE.Color('#f2f0e9');
const renderer=new THREE.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.setClearColor('#f2f0e9');renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.15;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFShadowMap;quiltTexture.anisotropy=renderer.capabilities.getMaxAnisotropy();
const camera=new THREE.PerspectiveCamera(34,1,.1,10000),controls=new OrbitControls(camera,canvas);controls.enableDamping=true;controls.minDistance=45;controls.maxDistance=3500;
scene.add(new THREE.HemisphereLight(0xffffff,0xa9a49b,1.8));const key=new THREE.DirectionalLight(0xfff9f1,2.5);key.position.set(-500,1100,900);key.castShadow=true;key.shadow.mapSize.set(2048,2048);Object.assign(key.shadow.camera,{left:-800,right:800,top:800,bottom:-800,near:1,far:3000});key.shadow.bias=-.0001;key.shadow.normalBias=.25;key.target.position.set(W/2,H/2,0);scene.add(key.target);scene.add(key);const fill=new THREE.DirectionalLight(0xffffff,1.4);fill.position.set(600,350,-400);scene.add(fill);
function wood(axis,index=0,species='wood'){
 const mat=new THREE.MeshStandardMaterial({color:0xc99c78,roughness:.65,metalness:0,side:THREE.DoubleSide});
 mat.onBeforeCompile=s=>{s.uniforms.quiltMap={value:quiltTexture};s.uniforms.useQuilt={value:species==='maple'&&panelFigure==='quilted'?1:0};s.uniforms.grainAxis={value:axis==='x'?0:1};s.uniforms.grainSeed={value:species==='maple'?31:index*13.8};s.uniforms.isMaple={value:species==='maple'?1:0};s.uniforms.isBeech={value:species==='wood'?1:0};
 s.vertexShader='varying vec3 vTimberPos; varying vec3 vTimberNormal;\n'+s.vertexShader;
 s.vertexShader=s.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvTimberPos=position; vTimberNormal=normal;');
 s.fragmentShader=`varying vec3 vTimberPos; varying vec3 vTimberNormal;
 uniform sampler2D quiltMap; uniform float useQuilt; uniform float grainAxis; uniform float grainSeed; uniform float isBeech; uniform float isMaple;
 float timberHash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
 float timberNoise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);
 return mix(mix(timberHash(i),timberHash(i+vec2(1,0)),f.x),mix(timberHash(i+vec2(0,1)),timberHash(i+vec2(1,1)),f.x),f.y);}
 `+s.fragmentShader;
 s.fragmentShader=s.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
 vec3 a=abs(vTimberNormal); float across=grainAxis<0.5?vTimberPos.y:vTimberPos.x;
 float along=grainAxis<0.5?vTimberPos.x:vTimberPos.y;
 if(a.x>0.7 && grainAxis>0.5) across=vTimberPos.z;
 if(a.y>0.7 && grainAxis<0.5) across=vTimberPos.z;
 // Multiscale, stretched noise avoids the previous regular woven pattern.
 float slow=timberNoise(vec2(across*.07+grainSeed,along*.008));
 float drift=(slow-.5)*2.8+.16*sin(along*.025+grainSeed);
 float broad=timberNoise(vec2((across+drift)*.18+grainSeed,along*.016));
 float fiber=timberNoise(vec2((across+drift)*2.3+grainSeed,along*.22));
 float lines=(broad-.5)*.23+(fiber-.5)*.12;
 float ringPhase=(across+drift)*2.0+grainSeed;
 lines+=sin(ringPhase)*.035*(1.0-smoothstep(.5,2.0,fwidth(ringPhase)));
 vec2 rayUV=vec2(across*.38+grainSeed,along*1.2);
 float fleck=smoothstep(.65,.86,timberNoise(rayUV))*isBeech;
 fleck*=1.0-smoothstep(.7,2.0,max(fwidth(rayUV.x),fwidth(rayUV.y)));
 // Cut ends are perpendicular to the board's longitudinal grain. Keep the
 // pattern in board coordinates so it follows each member when exploded/opened.
 float endness=smoothstep(.75,.96,grainAxis<.5?a.x:a.y);
 vec2 crossSection=vec2(grainAxis<.5?vTimberPos.y:vTimberPos.x,vTimberPos.z);
 vec2 ringCenter=vec2(-90.0-grainSeed*.7,-170.0-grainSeed*.3);
 vec2 radial=crossSection-ringCenter;
 float radius=length(radial);
 float rings=radius*2.65+.18*sin(atan(radial.y,radial.x)*12.0+grainSeed);
 float ringAA=1.0-smoothstep(.45,1.8,fwidth(rings));
 float latewood=pow(.5+.5*sin(rings),8.0)*ringAA;
 vec2 poreCell=crossSection*2.5;
 float poreHash=fract(sin(dot(floor(poreCell),vec2(127.1,311.7)))*43758.5453);
 vec2 poreUV=fract(poreCell)-.5;
 poreUV-=vec2(poreHash-.5,timberHash(floor(poreCell)+12.8)-.5)*.5;
 float pores=(1.0-smoothstep(.07,.19,length(poreUV)))*step(.32,poreHash);
 pores*=1.0-smoothstep(.3,1.0,max(fwidth(poreCell.x),fwidth(poreCell.y)));
 float rayPhase=atan(radial.y,radial.x)*radius*.95;
 float rays=pow(.5+.5*sin(rayPhase),18.0)*(1.0-smoothstep(.4,1.6,fwidth(rayPhase)));
 float endTone=.88-.12*latewood-.06*pores+.045*rays;
 // Curly maple has transverse figure over longitudinal grain, not stripes
 // running down the board. Shared coordinates keep the figure quiet at seams.
 float curlPhase=along*.53+.8*sin(across*.035)+3.5*timberNoise(vec2(across*.045,along*.035));
 float curl=sin(curlPhase)*(.075+.035*timberNoise(vec2(across*.022,along*.013)));
 float mapleTone=1.0+curl+(fiber-.5)*.065+(broad-.5)*.055;
 diffuseColor.rgb*=mix(mix(1.0+lines-.18*fleck,mapleTone,isMaple),endTone,endness);
 // Photograph on the broad faces only; original aspect ratio retained.
 // 350 mm sample width is an illustrative figure scale, not measured stock.
 vec2 quiltUV=vec2((vTimberPos.x-57.15)/350.0,vTimberPos.y/(350.0*5567.0/595.0)+.18);
 vec3 quiltColor=texture2D(quiltMap,quiltUV).rgb;
 diffuseColor.rgb=mix(diffuseColor.rgb,quiltColor*.76,useQuilt*isMaple*smoothstep(.7,.98,a.z));
 `);};mat.customProgramCacheKey=()=>`timber-${species}-${axis}-${index}-${panelFigure}`;return mat;
}
function tigerEye(){
 const mat=new THREE.MeshPhysicalMaterial({color:0xffffff,roughness:.42,metalness:.05,clearcoat:.12,clearcoatRoughness:.3});
 mat.onBeforeCompile=s=>{
  s.vertexShader='varying vec3 vStonePos;\n'+s.vertexShader;
  s.vertexShader=s.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvStonePos=position;');
  s.fragmentShader='varying vec3 vStonePos;\n'+s.fragmentShader;
  s.fragmentShader=s.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
   float u=vStonePos.x+vStonePos.y*.26;
   float wave=u*.5+1.8*sin(vStonePos.y*.11)+.5*sin(vStonePos.y*.31);
   float band=.5+.5*sin(wave);
   vec3 amber=mix(vec3(.018,.005,.001),vec3(.30,.105,.012),smoothstep(.15,.8,band));
   float silk=pow(.5+.5*sin(wave*6.0+sin(vStonePos.y*.7)),8.0);
   amber=mix(amber,vec3(.48,.24,.035),silk*.32);
   diffuseColor.rgb*=amber;
  `);
 };mat.customProgramCacheKey=()=> 'tiger-eye-cabochon';return mat;
}
const mats={stone:tigerEye(),brass:new THREE.MeshStandardMaterial({color:0xb99551,metalness:.67,roughness:.32}),bronze:new THREE.MeshStandardMaterial({color:0x69543a,metalness:.32,roughness:.5}),steel:new THREE.MeshStandardMaterial({color:0x939da0,metalness:.7,roughness:.37}),cup:new THREE.MeshStandardMaterial({color:0x447c90,transparent:true,opacity:.65,metalness:.15,roughness:.5})};
const groups={wallCleat:new THREE.Group(),case:new THREE.Group(),door:new THREE.Group(),knifeDoor:new THREE.Group(),knifeFixed:new THREE.Group(),buttDoor:new THREE.Group(),buttFixed:new THREE.Group(),cup:new THREE.Group()};Object.values(groups).forEach(g=>scene.add(g));
const wall=new THREE.Mesh(new THREE.PlaneGeometry(5000,5000),new THREE.MeshStandardMaterial({color:0xe5e0d5,roughness:1,side:THREE.DoubleSide}));wall.position.set(W/2,H/2,-D-.4);wall.receiveShadow=true;scene.add(wall);
const meshes=[];
function buildParts(){
 for(const group of Object.values(groups)){
  for(const m of [...group.children]){m.traverse(o=>{if(o.geometry)o.geometry.dispose();if(o.material&&!Object.values(mats).includes(o.material))o.material.dispose();});group.remove(m);}
 }
 meshes.length=0;
 for(const [i,part] of MODEL.parts.entries()){
 let geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(part.vertices.flat(),3));geo.setIndex(part.triangles.flat());const indexed=geo;geo=toCreasedNormals(indexed,Math.PI/6);indexed.dispose();
 const mat=['wood','maple'].includes(part.material)?wood(part.grain,i,part.material):mats[part.material];if(part.material==='maple'){mat.color.setHex(0xd8c4a3);mat.roughness=.52;}const mesh=new THREE.Mesh(geo,mat);mesh.castShadow=true;mesh.receiveShadow=true;mesh.name=part.name;mesh.userData=part;groups[part.group].add(mesh);meshes.push(mesh);
 const edge=new THREE.LineSegments(new THREE.EdgesGeometry(geo,25),new THREE.LineBasicMaterial({color:part.material==='wood'?0x887354:0x695735,transparent:true,opacity:.43}));mesh.add(edge);
}
}
function block(group,name,x,y,z,w,h,dep,material){const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,dep),material);m.position.set(x+w/2,y+h/2,z+dep/2);m.name=name;group.add(m);return m;}
const buttAxis={x:W+4,z:G+T+4};
const axisLine=new THREE.Line(new THREE.BufferGeometry(),new THREE.LineDashedMaterial({color:0x70675b,dashSize:8,gapSize:6}));scene.add(axisLine);
const labels=[];
function label(text,pos){const el=document.createElement('div');el.className='dimension';el.textContent=text;$('viewport').appendChild(el);labels.push({el,pos:new THREE.Vector3(...pos)});}
label('18″ case',[W/2,-30,-D]);label('27″',[W+50,H/2,-D/2]);label('6″ case + door',[-30,0,(G+T-D)/2]);label('17⅞″ door',[W/2,H+35,G+T]);
buildParts();
const notes={knife:{text:'Mortised knife leaves retained in both panel layouts. Nine sampled swing positions clear the case through 110°. Hardware sizing and fastening remain provisional.',url:'https://brusso.com/products/center-pivot-hinges'}};
let mode='knife',angle=0,explosion=0,currentView='perspective';
function pivot(){return mode==='butt'?buttAxis:{x:d.axisX,z:d.axisZ};}
function rotateGroup(group,theta,px,pz){group.rotation.y=theta;group.position.set(px-Math.cos(theta)*px-Math.sin(theta)*pz,0,pz+Math.sin(theta)*px-Math.cos(theta)*pz);}
function update(){
 mode=$('hardware').value;angle=mode==='cup'?0:Number($('angle').value);explosion=Number($('explode').value)/100;
 $('angle').value=angle;$('angle-number').value=angle;$('angle').disabled=$('angle-number').disabled=mode==='cup';document.querySelectorAll('[data-angle]').forEach(b=>b.disabled=mode==='cup');
 const theta=angle*Math.PI/180, pv=pivot();for(const key of ['door','knifeDoor','buttDoor'])rotateGroup(groups[key],theta,pv.x,pv.z);
 const hardware=$('hardware-visible').checked;groups.knifeDoor.visible=groups.knifeFixed.visible=mode==='knife'&&hardware;groups.buttDoor.visible=groups.buttFixed.visible=mode==='butt'&&hardware;groups.cup.visible=mode==='cup'&&hardware;
 for(const mesh of meshes){
  const name=mesh.name, group=mesh.userData.group;
  mesh.position.set(0,0,0);
  if(group==='case'){
   mesh.material.transparent=$('xray').checked;mesh.material.opacity=$('xray').checked?.18:1;mesh.material.depthWrite=!$('xray').checked;
   if(name==='Case left')mesh.position.x=-60*explosion;if(name==='Case right')mesh.position.x=60*explosion;if(name==='Case top')mesh.position.y=60*explosion;if(name==='Case bottom')mesh.position.y=-60*explosion;if(name==='Cabinet cleat')mesh.position.z=-75*explosion;
  }else if(group==='door'){
   mesh.position.z=100*explosion;
   if(name==='Top rail')mesh.position.y=40*explosion;if(name==='Bottom rail')mesh.position.y=-40*explosion;
   if(name==='Left stile')mesh.position.x=-25*explosion;if(name==='Right stile')mesh.position.x=25*explosion;
   if(name.startsWith('Maple')){mesh.visible=$('panel').checked;mesh.position.z+=35*explosion;const i=Number(name.split(' ').at(-1))-1;mesh.position.x+=(i-(p.seam_offsets.length)/2)*12*explosion;}
   mesh.material.transparent=mode==='cup'&&mesh.userData.material==='wood';mesh.material.opacity=mode==='cup'&&mesh.userData.material==='wood'?.45:1;mesh.material.depthWrite=mode!=='cup';
  }else if(group==='knifeDoor')mesh.position.z=100*explosion;else if(group==='wallCleat')mesh.position.z=-120*explosion;
 }
 axisLine.geometry.dispose();axisLine.geometry=new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(pv.x,-30,pv.z),new THREE.Vector3(pv.x,H+30,pv.z)]);axisLine.computeLineDistances();axisLine.visible=$('pivot-visible').checked&&mode!=='cup'&&!explosion;
 $('hinge-note').textContent=notes[mode].text;$('hinge-source').href=notes[mode].url;
 $('clearance').textContent=explosion?'Exploded view · fit checks apply to assembled position':mode==='cup'?'Fit envelope only · linkage and swing unverified':mode==='knife'?'No solid overlap at nine checked positions, 0–110°':'Wood clears case in this axis study · mount fit unverified';
 $('view-subtitle').textContent=explosion?'Separated components · exact CAD parts':`${angle}° open · ${mode==='knife'?'mortised knife hinges':mode==='butt'?'butt mounting study':'cup fit envelope'}`;
 wall.visible=$('wall').checked;renderPlan();
}
function renderPlan(){
 const pv=pivot(),theta=angle*Math.PI/180;
 const transform=(x,z)=>[pv.x+Math.cos(theta)*(x-pv.x)+Math.sin(theta)*(z-pv.z),pv.z-Math.sin(theta)*(x-pv.x)+Math.cos(theta)*(z-pv.z)];
 const door=[[p.side_reveal,G],[W-p.side_reveal,G],[W-p.side_reveal,G+T],[p.side_reveal,G+T]].map(([x,z])=>transform(x,z));
 const bounds=[...door,[0,-D],[W,-D]];const minX=Math.min(-40,...bounds.map(a=>a[0]))-25,maxX=Math.max(W+45,...bounds.map(a=>a[0]))+25,minZ=-D-50,maxZ=Math.max(50,...bounds.map(a=>a[1]))+45;
 const scale=Math.min(760/(maxX-minX),230/(maxZ-minZ)),ox=400-scale*(minX+maxX)/2,oy=130-scale*(minZ+maxZ)/2;
 const point=([x,z])=>`${ox+x*scale},${oy+z*scale}`;
 const rect=(x,z,w,dep,fill)=>`<rect x="${ox+x*scale}" y="${oy+z*scale}" width="${w*scale}" height="${dep*scale}" fill="${fill}" stroke="#a99372" stroke-width=".7"/>`;
 $('plan').innerHTML=rect(0,-D,p.case_side_thickness,D,'#d6c09c')+rect(W-p.case_side_thickness,-D,p.case_side_thickness,D,'#d6c09c')+`<line x1="${ox-20}" y1="${oy}" x2="${ox+(W+30)*scale}" y2="${oy}" stroke="#70675b" stroke-dasharray="4 4"/><polygon points="${door.map(point).join(' ')}" fill="#e1bc84" stroke="#806845" stroke-width="1"/>`+(mode==='cup'?'':`<circle cx="${ox+pv.x*scale}" cy="${oy+pv.z*scale}" r="3.5" fill="#70675b"/><text x="${ox+pv.x*scale+9}" y="${oy+pv.z*scale-9}" font-size="11" fill="#70675b">Pivot</text>`)+`<text x="20" y="20" font-size="11" fill="#66736a">REAR</text><text x="20" y="248" font-size="11" fill="#66736a">FRONT</text><text x="${ox}" y="${oy-8}" font-size="10" fill="#70675b">Case face</text>`;
}
function view(name){
 currentView=name;controls.target.set(W/2,H/2,-D/3);camera.up.set(0,1,0);camera.fov=34;
 const center=controls.target.clone();
 if(name==='perspective'){
  scene.updateMatrixWorld(true); const bounds=new THREE.Box3(); for(const g of Object.values(groups))if(g.visible)bounds.union(new THREE.Box3().setFromObject(g));
  const sphere=bounds.getBoundingSphere(new THREE.Sphere());controls.target.copy(sphere.center);
  const halfFov=Math.min(17*Math.PI/180,Math.atan(Math.tan(17*Math.PI/180)*camera.aspect));
  camera.position.copy(sphere.center).add(new THREE.Vector3(700,440,1350).normalize().multiplyScalar(sphere.radius/Math.sin(halfFov)*1.08));
 }
 if(name==='front'){camera.position.set(W/2,H/2,1600);controls.target.set(W/2,H/2,0);}
 if(name==='back'){$('wall').checked=false;wall.visible=false;camera.position.set(W/2,H/2,-1700);controls.target.set(W/2,H/2,0);}
 if(name==='top'){controls.target.set(W/2,H/2,-50);camera.position.set(W/2,H/2+1700,-49.9);camera.up.set(0,0,-1);}
 if(name==='panel'){const x=W/2+p.seam_offsets.find(o=>o>0);controls.target.set(x,H*.58,G+10);camera.position.copy(controls.target).add(new THREE.Vector3(60,35,190));}
 if(name==='knob'){const knob=scene.getObjectByName('Tiger eye stone');scene.updateMatrixWorld(true);const box=new THREE.Box3().setFromObject(knob);box.getCenter(controls.target);camera.position.copy(controls.target).add(new THREE.Vector3(40,30,140));}
 if(name==='hinge'){const pv=pivot();controls.target.set(pv.x-15,H-8,pv.z-10);camera.position.copy(controls.target).add(new THREE.Vector3(130,135,180));}
 controls.update();camera.updateProjectionMatrix();document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===name)));
}
function setAngle(v){const value=Math.min(110,Math.max(0,Number(v)||0));$('angle').value=value;update();if(currentView==='perspective')view('perspective');}
for(const id of ['hardware','explode','xray','panel','hardware-visible','pivot-visible','dimensions','wall'])$(id).addEventListener('input',update);
$('angle').addEventListener('input',()=>setAngle($('angle').value));$('angle-number').addEventListener('input',()=>setAngle($('angle-number').value));
document.querySelectorAll('[data-angle]').forEach(b=>b.onclick=()=>setAngle(b.dataset.angle));document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>view(b.dataset.view));
$('reset').onclick=()=>{$('hardware').value='knife';$('angle').value=0;$('explode').value=0;$('xray').checked=false;$('pivot-visible').checked=false;for(const id of ['panel','dimensions','hardware-visible','wall'])$(id).checked=true;update();view('perspective');};
canvas.addEventListener('keydown',e=>{if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();setAngle(angle+(e.key==='ArrowRight'?5:-5));}});
function resize(){const w=canvas.clientWidth,h=canvas.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}new ResizeObserver(resize).observe(canvas);
function animate(){requestAnimationFrame(animate);controls.update();for(const l of labels){const pos=l.pos.clone();if(l.el.textContent==='17⅞″ door')pos.applyMatrix4(groups.door.matrixWorld);const v=pos.project(camera);l.el.style.left=`${(v.x/2+.5)*canvas.clientWidth}px`;l.el.style.top=`${(-v.y/2+.5)*canvas.clientHeight}px`;l.el.style.transform='translate(-50%,-50%)';l.el.style.display=$('dimensions').checked&&!['hinge','knob','panel'].includes(currentView)&&!(l.el.textContent==='6″ case + door'&&['front','back'].includes(currentView))&&!explosion&&v.z<1&&Math.abs(v.x)<.93&&Math.abs(v.y)<.93?'block':'none';}renderer.render(scene,camera);}
window.cabinetStudy={get model(){return MODEL},setAngle,view,scene,renderer,camera,getState:()=>({panelFigure,mode,angle,explosion,axis:pivot(),drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles})};
function chooseDesign(id){
 if(!MODELS[id])id='b';choice=id;MODEL=MODELS[id];p=MODEL.parameters;d=MODEL.derived;buildParts();
 document.querySelectorAll('[data-design]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.design===id)));
 $('option-title').textContent=p.label+' · '+(panelFigure==='quilted'?'Quilted maple':'Curly maple');
 $('panel-figure').value=panelFigure;
 document.querySelectorAll('[data-design] img').forEach(img=>{img.src=img.parentElement.dataset.design+'-'+panelFigure+'-front.png';});
 $('rail-profile').textContent='2¼″ / 4½″ · A retained';
 $('panel-count').textContent=id==='a'?'Three vertical boards':'Five; narrow center';
 $('option-note').textContent=id==='a'?'Three broad boards give the curve a quiet vertical rhythm. The center bay is laid out on 4½″; outer boards fit the retained opening. Pale maple keeps the contrast gentle.':'A 1½″ center bay hints at a vertical pupil, with 3″ bays on either side. The outer boards fit the opening. All five are maple; there is no dark center inlay.';
 document.querySelectorAll('[data-download]').forEach(a=>{a.href=id+'/cabinet-r4.'+a.dataset.download;a.download='cabinet-r4-'+id+'.'+a.dataset.download;});
 $('dimensions-link').href=id+'/parameters.json';$('checks-link').href=id+'/validation.json';
 update();view(currentView);const url=new URL(location.href);url.searchParams.set('option',id);url.searchParams.set('wood',panelFigure);history.replaceState({},'',url);
}
for(const b of document.querySelectorAll('[data-design]'))b.onclick=()=>chooseDesign(b.dataset.design);
$('panel-figure').onchange=()=>{panelFigure=$('panel-figure').value;chooseDesign(choice);};
resize();chooseDesign(new URLSearchParams(location.search).get('option')||'b');animate();
