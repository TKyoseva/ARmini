import asyncio, json, sys
from playwright.async_api import async_playwright
import os
html=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','ar-mini-board.html'),encoding='utf-8').read()
doc=None
cards=[{"id":"t-aisler-revB","seq":32,"title":"Carrier rev B → Aisler","col":"today","start":1791735900000,"end":None,"rel":"R3b","result":"long","outcome":None,"created":1,"order":1,"from":"claude"},
 {"id":"t-print-thruster-mounts","seq":41,"title":"Print the thruster mounts","col":"done","start":1792002747000,"end":1792013067000,"rel":"R2a","result":"ok","outcome":"pass","created":2,"order":2,"from":"claude","media":"C041_2026-10-15_thruster-mounts","files":[{"path":"cad/stl/v1/thruster_arm.stl","note":"printed 14.10"},{"path":"docs/diagrams/AR-Mini_thruster_kickup_mount.png","note":""}]},
 {"id":"l001","seq":1,"title":"Cuifati thruster","col":"released","start":1,"end":2,"rel":"R1a","outcome":"partial","created":3,"order":3},
 {"id":"l004","seq":4,"title":"Backlog thing","col":"backlog","created":4,"order":4}]
rels=[{"id":"r1a","name":"R1a","goal":"floats","date":"2026-10-11","cut":1791722938063,"g":"g1","kind":"milestone"},{"id":"r2a","name":"R2a","goal":"thruster spins","date":"2026-10-16","cut":None,"g":"g1","kind":"milestone"}]
goals=[{"id":"g1","name":"G1","title":"Maker Portfolio v1 — Early Action","due":"2026-10-30","order":1,"criteria":["video","pdf"],"desc":"EA"},{"id":"g2","name":"G2","title":"Portfolio v2 — Regular Decision","due":"2026-12-30","order":2},{"id":"g3","name":"G3","title":"2027","due":"2027-12-31","order":3}]
ans=[{"id":"t-print-thruster-mounts","card":"t-print-thruster-mounts","seq":41,"title":"Thruster kick-up mount","challenge":"ch","options":[{"what":"a","src":"s","pick":True},{"what":"b","src":""}],"decision":"d","lesson":"l","activity":"publication","why":"w","impact":{"np":2,"fin":1,"sci":1,"note":"n"},"path":{"uni":[{"school":"MIT","what":"2.017"}],"grants":["UROP"],"competitions":["RoboBoat"]},"seed":True,"status":"final","written":"2026-10-15","by":"claude","horizon":"uni1"}]
stub="""
window.__writes=[];
const mk=(docs)=>({onSnapshot:(cb)=>{cb({docs:docs.map(d=>({id:d.id,data:()=>{const x=Object.assign({},d);delete x.id;return x;}}))});},add:async(d)=>{window.__writes.push(['add',d]);return{id:'new'}}});
const data={cards:%s,releases:%s,goals:%s,analyses:%s};
window.claude={use:async(name)=>{
  if(name==='db')return{collection:(p)=>mk(data[p]||[]),doc:(p)=>({update:async(d)=>{window.__writes.push(['update',p,d]);},set:async(d)=>{window.__writes.push(['set',p,d]);},delete:async()=>{window.__writes.push(['del',p]);}})};
  if(name==='user')return{id:async()=>'u_me'};
  if(name==='downloads')return{save:async()=>{}};
  return null;}};
"""%(json.dumps(cards),json.dumps(rels),json.dumps(goals),json.dumps(ans))
doc='<!doctype html><html><head><meta charset=utf8><meta name=viewport content="width=device-width,initial-scale=1"></head><body><script>(function(){'+stub+'})();</script>'+html.replace('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap','about:blank')+'</body></html>'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={"width":1200,"height":900})
        errs=[]; pg.on("pageerror",lambda e:errs.append(str(e))); pg.on("console",lambda m: errs.append("console."+m.type+": "+m.text) if m.type in("error",) else None)
        await pg.set_content(doc, wait_until="load"); await pg.wait_for_timeout(800)
        print("days:",await pg.text_content("#days"),await pg.text_content("#days-lab"))
        print("goals strip:",(await pg.inner_text("#goals")).replace("\n"," | "))
        print("relhint:",await pg.text_content("#relhint"))
        # open analysis details of the done card and check text
        print("ERRORS so far:",errs)
        t=await pg.inner_text("#l-done"); print("done col has seed chip:", "seed · Publication" in t, "| 'null' text present:", "null" in t)
        # open analysis
        await pg.evaluate("document.querySelectorAll('details.an').forEach(d=>d.open=true)")
        t=await pg.inner_text("#l-done"); print("analysis text sample:", t[:400].replace("\n"," / "))
        await pg.click("button[data-tab=road]"); await pg.wait_for_timeout(200)
        print("road kpis:",await pg.text_content("#rk-an"),await pg.text_content("#rk-seed"),await pg.text_content("#rk-cards"),await pg.text_content("#rk-cov"))
        print("road seeds:",(await pg.inner_text("#road-seeds"))[:300].replace("\n"," / "))
        print("road goals:",(await pg.inner_text("#road-goals"))[:300].replace("\n"," / "))
        await pg.click("button[data-tab=dash]"); await pg.wait_for_timeout(200)
        print("rel list:",(await pg.inner_text("#rel-list"))[:200].replace("\n"," / "))
        await pg.screenshot(path="shot_board.png",full_page=True)
        await pg.click("button.wide"); await pg.wait_for_timeout(100)
        # fill analysis form on backlog card? use today card
        await pg.evaluate("document.querySelectorAll('details').forEach(d=>d.open=true)")
        await pg.fill("#a-t-aisler-revB-ch","challenge text"); await pg.fill("#a-t-aisler-revB-op","opt A — src A ✓\nopt B"); await pg.select_option("#a-t-aisler-revB-ac","opensource"); await pg.select_option("#a-t-aisler-revB-np","1")
        await pg.fill("#a-t-aisler-revB-un","MIT: 2.678\nStanford: ME 210"); await pg.fill("#a-t-aisler-revB-gr","UROP, Sandbox"); await pg.select_option("#a-t-aisler-revB-se","1")
        await pg.click("#a-t-aisler-revB-ch >> xpath=ancestor::form//button[@type='submit']"); await pg.wait_for_timeout(200)
        w=await pg.evaluate("window.__writes"); print("writes:",json.dumps(w)[:600])
        await pg.screenshot(path="shot_today.png",full_page=True)
        print("ERRORS:",errs)
        await b.close()
asyncio.run(main())
