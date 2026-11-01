// Associate STL triangle ranges with the parts they came from, in any camera view.
import * as THREE from './assets/three/three.module.js';

export function attachPicker({canvas, camera, model, geometry, material, assembly, url, render}) {
  const panel=document.querySelector('[data-assembly-inspector]');
  if(!panel || !assembly?.items) return null;
  const {items,groups}=assembly, directory=new Map();
  for(const row of document.querySelectorAll('[data-assembly-id]')) directory.set(row.dataset.assemblyId,row);
  const abort=new AbortController(), listen=(target,event,fn)=>target.addEventListener(event,fn,{signal:abort.signal});
  const drawerMaterial=material.clone(), coreMaterial=material.clone(); model.material=[material,drawerMaterial,coreMaterial];
  let start=0,selected='',hidden=false;
  const spans=groups.map(([faces,color,id,kit])=>{
    const first=start; start+=faces;
    geometry.addGroup(first*3,faces*3,color===1?1:color===0?2:0);
    return {first,end:start,id,kit,isDrawer:color===1};
  });
  const colors=geometry.getAttribute('color'), initial=colors.array.slice(), accent=new THREE.Color('#1688c8');
  const heading=panel.querySelector('[data-picked-name]'),purpose=panel.querySelector('[data-picked-use]'),link=panel.querySelector('[data-picked-link]'),toggle=panel.querySelector('[data-hide-drawers]'),selector=panel.querySelector('select');
  const base=new URL('../',new URL(url,document.baseURI));
  selector.replaceChildren(new Option('Identify a part…',''),...Object.entries(items).map(([id,v])=>new Option(v[0],id)));
  let down=null;
  function pick(id){
    if(id && !items[id])return;
    selected=id;selector.value=id;
    const record=items[id];
    heading.textContent=record?.[0] || 'Explore the assembly';
    purpose.textContent=record?.[1] || 'Click a part to identify it. Drag to rotate.';
    link.hidden=!record?.[2]; if(!link.hidden) {
      const part=directory.get(id)?.querySelector('a');
      link.textContent=part?'Part details & downloads →':'Download this part →';link.href=part?.href || new URL(record[2],base).href;
    }
    for(const [key,row] of directory){const active=key===id;row.classList.toggle('part-picked',active);if(active){const fold=row.closest('details');if(fold)fold.open=true;}}
    colors.array.set(initial);
    if(id)for(const span of spans){
      const hit=span.id===id || span.kit===id;
      for(let i=span.first*3,j=i*3;i<span.end*3;i++,j+=3) {
        if(hit)accent.toArray(colors.array,j);
        else for(let k=0;k<3;k++)colors.array[j+k]=initial[j+k]*.64+.17;
      }
    }
    colors.needsUpdate=true;canvas.dataset.selectedPart=id;render();
  }
  function drawers(hide){
    hidden=hide;drawerMaterial.visible=!hide;toggle.checked=hide;
    coreMaterial.transparent=hide;coreMaterial.opacity=hide ? .16 : 1;coreMaterial.depthWrite=!hide;coreMaterial.needsUpdate=true;
    if(hide && (selected.startsWith('one-piece-') || selected==='core'))pick('');
    canvas.dataset.drawersHidden=String(hide);render();
  }
  function show(id){
    if(hidden && (id.startsWith('one-piece-') || id==='core'))drawers(false);
    pick(id);
  }
  listen(toggle,'change',()=>drawers(toggle.checked));
  listen(selector,'change',()=>show(selector.value));
  for(const [id,row] of directory)if(items[id])listen(row,'click',e=>{
    if(e.defaultPrevented||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey||e.button!==0)return;
    e.preventDefault();show(id);
    if(matchMedia('(max-width: 760px)').matches)canvas.scrollIntoView({block:'start'});
  });
  const hitTest=new THREE.Raycaster(),point=new THREE.Vector2(),activePointers=new Set();
  listen(canvas,'pointerdown',e=>{
    activePointers.add(e.pointerId);down=e.button===0&&activePointers.size===1?{id:e.pointerId,x:e.clientX,y:e.clientY}:null;
  });
  listen(canvas,'pointermove',e=>{if(down && Math.hypot(e.clientX-down.x,e.clientY-down.y)>5)down=null;});
  listen(canvas,'pointercancel',e=>{activePointers.delete(e.pointerId);down=null;});
  listen(canvas,'pointerup',e=>{
    activePointers.delete(e.pointerId);
    if(!down || down.id!==e.pointerId)return; down=null;
    const b=canvas.getBoundingClientRect();
    point.set(2*(e.clientX-b.left)/b.width-1,1-2*(e.clientY-b.top)/b.height);
    hitTest.setFromCamera(point,camera);
    for(const hit of hitTest.intersectObject(model)){
      const span=spans.find(g=>hit.faceIndex>=g.first && hit.faceIndex<g.end);
      if(span && !(hidden&&(span.isDrawer||span.id==='core'))){pick(span.id);return;}
    }
    pick('');
  });
  panel.hidden=false;drawers(false);pick('');
  return ()=>{abort.abort();drawerMaterial.dispose();coreMaterial.dispose();panel.hidden=true;for(const row of directory.values())row.classList.remove('part-picked');};
}
