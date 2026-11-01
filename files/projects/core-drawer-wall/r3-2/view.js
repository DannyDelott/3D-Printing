const base=location.pathname.includes('/files/projects/')?'../../../../assets/three/':'../../../site/assets/three/';
const [T,{STLLoader},{OrbitControls}]=await Promise.all(['three.module.js','STLLoader.js','OrbitControls.js'].map(f=>import(base+f)));
const models=['open','left-right','front-back'];const canvas=document.querySelector('#orbit');const rr=new T.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true});rr.setPixelRatio(Math.min(2,devicePixelRatio));
const scene=new T.Scene();scene.background=new T.Color('#e9eee7');const cam=new T.OrthographicCamera(-1,1,1,-1,.1,1000);cam.up.set(0,0,1);const ctl=new OrbitControls(cam,canvas);ctl.enablePan=false;ctl.minZoom=.45;ctl.maxZoom=4;
scene.add(new T.HemisphereLight(0xfffcf5,0x747f72,1.7));for(const [pos,power] of [[[-80,-100,180],2.0],[[140,90,50],.8]]){const l=new T.DirectionalLight(0xfffcf5,power);l.position.set(...pos);scene.add(l);}
let active=null, sequence=0;const pool={};const colors=[0x799587,0x68897b,0x809280];
function render(){rr.render(scene,cam)}
function resize(){let w=canvas.clientWidth,h=canvas.clientHeight;if(!w||!h)return;let hh=Math.max(62,68*h/w);cam.left=-hh*w/h;cam.right=-cam.left;cam.top=hh;cam.bottom=-hh;cam.updateProjectionMatrix();rr.setSize(w,h,false);render()}
function reset(){cam.position.set(56,115,182);ctl.target.set(0,0,0);cam.zoom=1;ctl.update();resize()}
async function display(n){if(!models.includes(n))n='open';const id=models.indexOf(n), request=++sequence;if(!pool[n]){let g=await new STLLoader().loadAsync('models/'+n+'-assembled-r3-2.stl');g.center();pool[n]=new T.Mesh(g,new T.MeshStandardMaterial({color:colors[id],roughness:.8}));}if(request!==sequence)return;if(active)scene.remove(active);active=pool[n];scene.add(active);document.querySelectorAll('[data-choice]').forEach(e=>e.setAttribute('aria-pressed',String(e.dataset.choice===n)));document.querySelector('#picked').textContent=['Open','Left / right','Front / back'][id];document.querySelector('#primary').href='models/'+n+'-r3-2.3mf';render();canvas.dataset.ready=n;}
ctl.addEventListener('change',render);new ResizeObserver(resize).observe(canvas);document.querySelector('#reset').onclick=reset;for(const e of document.querySelectorAll('[data-choice]'))e.onclick=()=>display(e.dataset.choice);
reset();await display(new URLSearchParams(location.search).get('drawer'));
