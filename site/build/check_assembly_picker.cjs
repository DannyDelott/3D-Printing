// Exercise the actual model, using mouse hits on rendered surfaces and the corresponding list rows.
const {chromium}=require('playwright'),assert=require('node:assert/strict');
(async()=>{
 const root=process.argv[2],b=await chromium.launch({channel:'chrome',args:['--enable-unsafe-swiftshader']});
 try{
  const p=await b.newPage({viewport:{width:1320,height:950}});
  await p.goto(new URL('projects/core-drawer-wall/',root).href);
  const c=p.locator('#model-viewer:not([hidden])'),panel=p.locator('[data-assembly-inspector]:visible');
  await panel.waitFor();await c.scrollIntoViewIfNeeded();const box=await c.boundingBox();
  const hitIds=new Set();
  for(const yy of [.36,.50,.64,.75])for(const xx of [.35,.44,.53,.60,.66]){
   await p.mouse.click(box.x+xx*box.width,box.y+yy*box.height);
   const id=await c.getAttribute('data-selected-part');
   if(!id)continue;hitIds.add(id);
   assert.equal(await p.locator('[data-assembly-id].part-picked').getAttribute('data-assembly-id'),id.replace(/-pocket-frame$/, '-pocket'));
  }
  assert.ok([...hitIds].some(s=>s.startsWith('one-piece-')) && hitIds.has('core'),'Physical hits must identify both a printed drawer and cardboard');
  await p.locator('[data-assembly-id="middle-mount"] a').click();assert.equal(await c.getAttribute('data-selected-part'),'middle-mount');
  assert.ok((await panel.locator('[data-picked-link]').getAttribute('href')).includes('/middle-mount/'));
  await panel.getByLabel('Reveal connectors').check();assert.equal(await c.getAttribute('data-drawers-hidden'),'true');
  await c.scrollIntoViewIfNeeded();const bb=await c.boundingBox(),x=bb.x+bb.width*.52,y=bb.y+bb.height*.50;
  const exposed=new Set();
  for(const yy of [.33,.51,.65,.74,.81])for(const xx of [.37,.44,.51,.57,.64,.70]){
   await p.mouse.click(bb.x+bb.width*xx,bb.y+bb.height*yy);
   const id=await c.getAttribute('data-selected-part');if(id)exposed.add(id);
  }
  assert.ok([...exposed].some(id=>['upper-mount','base-mount','dry-ends','middle-mount','top-clips','left-pocket-frame','right-pocket-frame'].includes(id)),'A visible connector must be selectable through the translucent cardboard');
  await panel.locator('select').selectOption('middle-mount');
  await c.scrollIntoViewIfNeeded();
  await p.mouse.move(x,y);await p.mouse.down();await p.mouse.move(x+60,y,{steps:8});await p.mouse.up();
  assert.equal(await c.getAttribute('data-selected-part'),'middle-mount','A drag must not repick');
  for(const id of ['left-pocket','right-pocket']){await p.locator('[data-assembly-id="'+id+'"] a').click();assert.equal(await c.getAttribute('data-selected-part'),id);assert.ok((await panel.locator('[data-picked-link]').getAttribute('href')).includes('/'+id+'/'));}
  // Orbit and zoom the isolated print without moving the wall.
  const isolated=p.locator('[data-part-preview] canvas');
  assert.equal(await isolated.getAttribute('data-selected-part'),'right-pocket');
  const wallBefore=await c.screenshot();
  const partBefore=await isolated.screenshot();
  const partBox=await isolated.boundingBox();
  await p.evaluate(()=>window.scrollBy(0,220));
  assert.deepEqual(await isolated.boundingBox(),partBox,'The isolated part stays visible when scrolling away from the list');
  await c.scrollIntoViewIfNeeded();
  const px=partBox.x+partBox.width/2,py=partBox.y+partBox.height/2;
  await p.mouse.move(px,py); await p.mouse.down(); await p.mouse.move(px+40,py+18,{steps:8}); await p.mouse.up();
  assert.notDeepEqual(await isolated.screenshot(),partBefore);
  assert.deepEqual(await c.screenshot(),wallBefore);
  await p.mouse.move(px,py); const beforeZoom=await isolated.screenshot(); await p.mouse.wheel(0,-180);
  await p.waitForFunction(()=>document.querySelector('[data-part-preview] canvas').dataset.rendered==='true');
  assert.notDeepEqual(await isolated.screenshot(),beforeZoom);
  await p.locator('[data-part-close]').click();assert.ok(await isolated.isHidden());
  await panel.locator('select').selectOption('top-tier');assert.equal(await c.getAttribute('data-selected-part'),'top-tier');
  assert.equal(await isolated.getAttribute('data-selected-part'),'top-tier');
  await p.locator('[data-assembly-id="one-piece-left-right"] a').click();assert.equal(await c.getAttribute('data-drawers-hidden'),'false');
  await panel.locator('[data-picked-link]').click();assert.ok(p.url().includes('/one-piece-left-right/'));
  console.log('Clicked mesh surfaces:',[...hitIds,...exposed].join(', '),'; list selection, orbit, connector reveal and part link passed.');
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
