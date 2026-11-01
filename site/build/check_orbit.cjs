// Start a built library server and pass its root URL. Requires Playwright and Chrome.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const root=process.argv[2];assert.ok(root,'Pass the site root URL');
 const b=await chromium.launch({channel:'chrome',args:['--enable-unsafe-swiftshader']});
 try {
  const p=await b.newPage({viewport:{width:1280,height:900}});
  await p.goto(new URL('projects/core-drawer-wall/',root).href);
  const canvas=p.locator('#model-viewer:not([hidden])');await canvas.waitFor();
  await p.evaluate(async root=>{
   const {OrbitControls}=await import(new URL('assets/three/OrbitControls.js',root).href);
   const original=OrbitControls.prototype.update;
   OrbitControls.prototype.update=function(...args){const r=original.apply(this,args);window.cameraSample=this.object.position.toArray();return r;};
  },root);
  await canvas.scrollIntoViewIfNeeded();
  for(const button of ['#reset-view','#top-view','#reset-view']){
   await p.locator(button).click();
   const box=await canvas.boundingBox(), x=box.x+box.width/2,y=box.y+box.height/2;
   await p.mouse.move(x,y);await p.mouse.down();await p.mouse.move(x+2,y,{steps:2});
   const before=await p.evaluate(()=>window.cameraSample);
   await p.mouse.move(x+70,y,{steps:8});const after=await p.evaluate(()=>window.cameraSample);
   await p.mouse.up();assert.ok(Math.abs(before[2]-after[2])<0.02,'Horizontal drag tilted the model');
   if(button==='#reset-view')assert.ok(Math.hypot(before[0]-after[0],before[1]-after[1])>1,'Orbit did not move');
  }
  console.log('Horizontal mouse orbit remains level, including after Top and Reset.');
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
