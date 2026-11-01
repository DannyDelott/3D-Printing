// The STL has the exact generated assembly. Groups label consecutive triangles
// as clip, wall tab, cardboard, drawer or hardware so the reused core is visible.
const base=location.pathname.includes('/files/projects/')?'../../../../assets/three/':'../../../site/assets/three/';
const [T,{STLLoader},{OrbitControls}]=await Promise.all(['three.module.js','STLLoader.js','OrbitControls.js'].map(f=>import(base+f)));
const [g,counts]=await Promise.all([new STLLoader().loadAsync('models/wall-example-r3.stl'),fetch('preview-groups.json').then(r=>r.json())]);
let cursor=0;counts.forEach(([n,k])=>{g.addGroup(cursor,n*3,k);cursor+=n*3;});if(cursor!==g.attributes.position.count)throw Error('Assembly groups mismatch');
g.computeBoundingBox();g.center();const scene=new T.Scene();scene.background=new T.Color('#e9ede4');
const mat=c=>new T.MeshStandardMaterial({color:c,roughness:.85});scene.add(new T.Mesh(g,['#e1dfd2','#e1dfd2','#ac855f','#748f83','#565853'].map(mat)));
scene.add(new T.HemisphereLight(0xfffcf4,0x9eab99,2.15));
for(const [pos,power] of [[[70,-160,230],2.2],[[-170,-20,80],.55]]){const l=new T.DirectionalLight(0xfff9ee,power);l.position.set(...pos);scene.add(l);}
const canvas=document.querySelector('canvas');const r=new T.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true});r.setPixelRatio(Math.min(2,window.devicePixelRatio));
const cam=new T.OrthographicCamera(-1,1,1,-1,.1,1400);cam.up.set(0,0,1);
const ctl=new OrbitControls(cam,canvas);ctl.enablePan=false;ctl.minZoom=.4;ctl.maxZoom=4;function render(){r.render(scene,cam)}
function fit(){cam.position.set(285,-510,252);ctl.target.set(0,0,0);cam.zoom=1;ctl.update();resize()}
function resize(){const w=canvas.clientWidth,h=canvas.clientHeight;if(!w||!h)return;const hh=Math.max(132,166*h/w);cam.left=-hh*w/h;cam.right=-cam.left;cam.top=hh;cam.bottom=-hh;cam.updateProjectionMatrix();r.setSize(w,h,false);render()}
canvas.hidden=false;document.querySelector('#poster').hidden=true;ctl.addEventListener('change',render);document.querySelector('#reset').onclick=fit;new ResizeObserver(resize).observe(canvas);fit();canvas.dataset.ready='true';
