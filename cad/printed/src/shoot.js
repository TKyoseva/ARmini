const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const jobs=JSON.parse(fs.readFileSync(process.argv[2]));
const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const p=await b.newPage();
for(const j of jobs){await p.setViewportSize({width:j.w,height:j.h});
await p.goto('http://localhost:8765/render.html#'+encodeURIComponent(JSON.stringify(j)));
await p.reload(); await p.waitForFunction('window.DONE',null,{timeout:300000});
await p.locator('canvas').screenshot({path:j.out,omitBackground:true}); console.log(j.out);}
await b.close();})();
