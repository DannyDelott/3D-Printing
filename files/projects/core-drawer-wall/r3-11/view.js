const assets=location.pathname.includes('/files/projects/')?'../../../../':'../../../site/';
const {createModelView}=await import(assets+'viewer.js');
const canvas=document.querySelector('#orbit'), poster=document.querySelector('#poster'), select=document.querySelector('#model'), download=document.querySelector('#primary');
const colors=await fetch('colors.json').then(r=>r.json());
let view=null,request=0;
async function show(){
  const n=select.value, id=++request, assembly=n==='assembly', side=n.endsWith('pocket');
  const special={assembly:'mock-assembly',joint:'front-joint',print:'open-r3-11',face:'face-r3-11','front-fit':'front-fit-r3-11'};
  const model=special[n]||n+'-in-use',folder=side?'../r3-10/models/':'models/';
  const part=assembly?'starter':['joint','print'].includes(n)?'open':n;
  download.href=folder+part+(side?'-r3-10':'-r3-11')+'.3mf';
  download.textContent=assembly?'Download first-cell 3MF':side?'Download pocket kit 3MF':n==='face'?'Download face 3MF':n==='front-fit'?'Download fit sample 3MF':'Download tray and front 3MF';
  document.querySelector('#key').textContent=assembly?'Tan: cardboard · Sage: drawers · Dark green: connectors · Amber: wall mounts. Drag to rotate; scroll to zoom.':'Drag to rotate; scroll to zoom.';
  // Each selection has its own bounds and center. Ignore stale loads.
  const nextCanvas=canvas.cloneNode(false);nextCanvas.hidden=false;
  const old=document.querySelector('#orbit');old.replaceWith(nextCanvas);
  view?.dispose();view=null;
  const next=await createModelView(nextCanvas,folder+model+'.stl',{faceGroups:assembly?colors:null});
  if(id!==request){next.dispose();return;}view=next;poster.hidden=true;nextCanvas.dataset.ready=n;
}
select.onchange=()=>show().catch(showError);document.querySelector('#reset').onclick=()=>view?.fit();
function showError(e){poster.hidden=false;document.querySelector('#key').textContent='3D preview unavailable. The downloads below are available.';console.warn(e);}
await show().catch(showError);
