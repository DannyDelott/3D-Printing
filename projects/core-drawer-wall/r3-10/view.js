const assets=location.pathname.includes('/files/projects/')?'../../../../':'../../../site/';
const {createModelView}=await import(assets+'viewer.js');
const canvas=document.querySelector('#orbit'), poster=document.querySelector('#poster'), select=document.querySelector('#model'), download=document.querySelector('#primary');
const colors=await fetch('colors.json').then(r=>r.json());
let view=null,request=0;
async function show(){
  const n=select.value, id=++request, assembly=n==='assembly', side=n.endsWith('pocket');
  const model=assembly?'mock-assembly':n==='print'?'open-r3-8':n+'-in-use';
  const part=assembly?'starter':n==='print'?'open':n;
  download.href=side?'models/'+n+'-r3-10.3mf':assembly?'../r3-8/models/starter-r3-8.3mf':'../r3-8/models/'+part+'-r3-8.3mf';
  download.textContent=assembly?'Download first-cell 3MF':side?'Download complete pocket 3MF':'Download selected drawer 3MF';
  document.querySelector('#key').textContent=assembly?'Tan: cardboard · Sage: drawers · Dark green: connectors · Amber: wall mounts. Drag to rotate; scroll to zoom.':'Drag to rotate; scroll to zoom.';
  // Each selection has its own bounds and center. Ignore stale loads.
  const nextCanvas=canvas.cloneNode(false);nextCanvas.hidden=false;
  const old=document.querySelector('#orbit');old.replaceWith(nextCanvas);
  view?.dispose();view=null;
  const next=await createModelView(nextCanvas,(assembly||side?'models/':'../r3-8/models/')+model+'.stl',{faceGroups:assembly?colors:null});
  if(id!==request){next.dispose();return;}view=next;poster.hidden=true;nextCanvas.dataset.ready=n;
}
select.onchange=()=>show().catch(showError);document.querySelector('#reset').onclick=()=>view?.fit();
function showError(e){poster.hidden=false;document.querySelector('#key').textContent='3D preview unavailable. The downloads below are available.';console.warn(e);}
await show().catch(showError);
