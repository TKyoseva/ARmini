"""Dump the geometry of a .kicad_pcb (footprints, pads, nets, segments, vias) to fps.json and print a summary
(nets without tracks, segment widths, silk texts, Edge.Cuts items). Used on 13.10 and 15.10 to check carrier rev B without KiCad.

    python geom_export.py ../AR-Mini_carrier_revB.kicad_pcb
"""
import re, sys, json
import sys
txt=open(sys.argv[1] if len(sys.argv)>1 else 'AR-Mini_carrier_revB.kicad_pcb').read()
# s-expression parser
def parse(s):
    tok=re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', s)
    stack=[[]]
    for t in tok:
        if t=='(': stack.append([])
        elif t==')':
            l=stack.pop(); stack[-1].append(l)
        else: stack[-1].append(t[1:-1] if t.startswith('"') else t)
    return stack[0][0]
root=parse(txt)
def kids(node,name): return [k for k in node[1:] if isinstance(k,list) and k and k[0]==name]
def first(node,name):
    k=kids(node,name); return k[0] if k else None
nets={}
for n in kids(root,'net'): nets[int(n[1])]=n[2]
print('nets',len(nets))
fps=[]
for f in kids(root,'footprint'):
    at=first(f,'at'); layer=first(f,'layer')[1]
    ref=val=None
    for p in kids(f,'property'):
        if p[1]=='Reference': ref=p[2]
        if p[1]=='Value': val=p[2]
    pads=[]
    for p in kids(f,'pad'):
        pat=first(p,'at'); sz=first(p,'size'); dr=first(p,'drill'); nt=first(p,'net')
        pads.append(dict(n=p[1],type=p[2],shape=p[3],x=float(pat[1]),y=float(pat[2]),sx=float(sz[1]),sy=float(sz[2]),drill=float(dr[1]) if dr else None,net=(nt[2] if len(nt)>2 else nt[1]) if nt else ''))
    fps.append(dict(lib=f[1],ref=ref,val=val,x=float(at[1]),y=float(at[2]),rot=float(at[3]) if len(at)>3 else 0,layer=layer,pads=pads))
print('footprints',len(fps))
for f in fps:
    print(f"{f['ref']:5} {f['val'] or '':30} at ({f['x']:6.2f},{f['y']:6.2f}) rot {f['rot']:5.1f} {f['layer']:5} pads {len(f['pads'])}  nets: {', '.join(dict.fromkeys(p['net'] for p in f['pads']))[:110]}")
segs=kids(root,'segment'); vias=kids(root,'via'); zones=kids(root,'zone'); grl=kids(root,'gr_line')+kids(root,'gr_arc')+kids(root,'gr_rect')+kids(root,'gr_circle'); grt=kids(root,'gr_text')
print('segments',len(segs),'vias',len(vias),'zones',len(zones),'graphics',len(grl),'texts',len(grt))
for z in zones: print(' zone net',(first(z,'net_name') or ['','(keepout)'])[1],'layer',first(z,'layer')[1] if first(z,'layer') else first(z,'layers'))
from collections import Counter
print(Counter((first(s,'layer')[1],first(s,'width')[1]) for s in segs))
# unconnected? count pads with nets vs segments per net
netpads=Counter(p['net'] for f in fps for p in f['pads'] if p['net'])
netsegs=Counter((lambda q:(q[2] if len(q)>2 else q[1]))(first(s,"net")) for s in segs)
for n,c in sorted(netpads.items()):
    if c>1 and netsegs.get(n,0)==0 and n!='GND': print('NET WITHOUT TRACKS',n,c)
for t in grt: print('text',t[1][:60],first(t,'layer')[1])
json.dump(dict(fps=fps,nets=nets),open('fps.json','w'))
edge=[g for g in grl if first(g,'layer') and first(g,'layer')[1]=='Edge.Cuts']
print('edge items',len(edge))
