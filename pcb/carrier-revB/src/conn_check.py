"""Rough connectivity / keep-out / width check of a .kicad_pcb without KiCad (union-find on track endpoints).
kicad-cli DRC is the authority: nets that reach a pad only through the GND pour or through a shared pad
report here as split groups (known false positives, e.g. +3V3, +5V, EN). Useful for: track widths per net,
tracks or vias inside the antenna keep-out, Edge.Cuts geometry, silk texts.

    python conn_check.py ../AR-Mini_carrier_revB.kicad_pcb
"""
import re, json
from collections import defaultdict, Counter
import sys
from sx import parse, kids, first, load
root=load(sys.argv[1] if len(sys.argv)>1 else 'AR-Mini_carrier_revB.kicad_pcb')
def netof(node):
    n=first(node,'net'); return (n[2] if len(n)>2 else n[1]) if n else ''
fps=[]
for f in kids(root,'footprint'):
    at=first(f,'at'); ref=[p[2] for p in kids(f,'property') if p[1]=='Reference'][0]
    fx,fy=float(at[1]),float(at[2]); rot=float(at[3]) if len(at)>3 else 0
    import math
    for p in kids(f,'pad'):
        pat=first(p,'at'); px,py=float(pat[1]),float(pat[2])
        a=math.radians(rot); x=fx+px*math.cos(a)+py*math.sin(a); y=fy-px*math.sin(a)+py*math.cos(a)
        lay=first(p,'layers'); layers=set()
        for l in lay[1:]:
            if l=='*.Cu': layers|={'F.Cu','B.Cu'}
            elif l.endswith('.Cu'): layers.add(l)
        sz=first(p,'size'); dr=first(p,'drill')
        drill=float(dr[1]) if dr and dr[1].replace('.','',1).isdigit() else None
        fps.append(dict(ref=ref,pad=p[1],x=round(x,3),y=round(y,3),layers=layers,net=netof(p),type=p[2],shape=p[3],sx=float(sz[1]),sy=float(sz[2]),drill=drill))
segs=[]
for s in kids(root,'segment'):
    a=first(s,'start'); b=first(s,'end'); segs.append(dict(a=(round(float(a[1]),3),round(float(a[2]),3)),b=(round(float(b[1]),3),round(float(b[2]),3)),layer=first(s,'layer')[1],net=netof(s),w=float(first(s,'width')[1])))
vias=[]
for v in kids(root,'via'):
    a=first(v,'at'); vias.append(dict(x=round(float(a[1]),3),y=round(float(a[2]),3),net=netof(v)))
zones=[(netof(z), (first(z,'layers') or first(z,'layer'))[1:], bool(first(z,'keepout'))) for z in kids(root,'zone')]
print('zones',zones)
# keepout zones?
for z in kids(root,'zone'):
    ko=first(z,'keepout'); 
    if ko: print('keepout zone', [k for k in ko[1:]], 'layers', first(z,'layers') or first(z,'layer'))
# connectivity per net
bynet=defaultdict(lambda: dict(pads=[],segs=[],vias=[]))
for p in fps:
    if p['net']: bynet[p['net']]['pads'].append(p)
for s in segs: bynet[s['net']]['segs'].append(s)
for v in vias: bynet[v['net']]['vias'].append(v)
TOL=0.05
def key(pt,layer): return (pt,layer)
problems=[]
for net,d in sorted(bynet.items()):
    if net=='GND': continue
    # union-find over endpoints
    parent={}
    def find(k):
        parent.setdefault(k,k)
        while parent[k]!=k: parent[k]=parent[parent[k]]; k=parent[k]
        return k
    def union(a,b): parent[find(a)]=find(b)
    nodes=[]  # (pt, layer, tag)
    for s in d['segs']:
        union(key(s['a'],s['layer']),key(s['b'],s['layer']))
    for v in d['vias']:
        union(key((v['x'],v['y']),'F.Cu'),key((v['x'],v['y']),'B.Cu'))
    # pads: union each pad's point on its layers; pad connects to segment endpoints within TOL
    pts=defaultdict(list)
    for k in list(parent): pts[k[1]].append(k)
    padkeys=[]
    for p in d['pads']:
        pk=('pad',p['ref'],p['pad']); padkeys.append(pk); parent.setdefault(pk,pk)
        for l in p['layers']:
            for k in pts[l]:
                if abs(k[0][0]-p['x'])<=TOL+0.9 and abs(k[0][1]-p['y'])<=TOL+0.9:   # within pad radius-ish
                    union(pk,k)
        if len(p['layers'])==2: union(key((p['x'],p['y']),'F.Cu'),key((p['x'],p['y']),'B.Cu'))
    groups=Counter(find(pk) for pk in padkeys)
    if len(d['pads'])>1 and len(groups)>1:
        problems.append((net,len(d['pads']),len(groups),[ (p['ref'],p['pad']) for p in d['pads']]))
print('nets',len(bynet),'nets with pads >1 and unconnected groups:',len(problems))
for p in problems: print(' ',p)
# widths
print(Counter((s['layer'],s['w']) for s in segs))
print('power net widths:',{n:Counter(s['w'] for s in d['segs']) for n,d in bynet.items() if n in ('+5V','12V_IN','12V_PROT','5V_RAW','+3V3')})
# keepout check: tracks/vias/pads inside (26.2,0,47.2,12)
ko=(26.2,0,47.2,12)
inside=[s for s in segs if ko[0]<s['a'][0]<ko[2] and ko[1]<s['a'][1]<ko[3] or ko[0]<s['b'][0]<ko[2] and ko[1]<s['b'][1]<ko[3]]
print('tracks touching antenna keepout:',len(inside), [ (s['net'],s['layer']) for s in inside][:10])
print('vias in keepout:',[v for v in vias if ko[0]<v['x']<ko[2] and ko[1]<v['y']<ko[3]])
# edge
for g in kids(root,'gr_rect')+kids(root,'gr_line')+kids(root,'gr_arc'):
    l=first(g,'layer')
    if l and l[1]=='Edge.Cuts': print('edge',g[0],first(g,'start'),first(g,'end'))
for t in kids(root,'gr_text'): print('text',repr(t[1][:50]),first(t,'layer')[1],first(t,'at')[1:3])
json.dump(dict(pads=[dict(p,layers=sorted(p['layers'])) for p in fps],segs=segs,vias=vias),open('geom.json','w'))
