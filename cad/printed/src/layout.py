import trimesh, numpy as np, json, os
exec(open('parts.py').read())
os.makedirs('out/stl',exist_ok=True)
M={}
for n,f,q,*_ in P:
    m=trimesh.load(f)
    if len(m.faces)>150000:
        m=m.simplify_quadric_decimation(face_count=120000)
    M[n]=m
# light copies for STEP
GAP=25; ROWW=640
pos={}
# row 0: hulls end-to-end as in the boat
hf,ha=M['hull_fore'],M['hull_aft']
off=-np.array([hf.bounds[0][0],hf.bounds[0][1],0])
pos['hull_fore']=off; pos['hull_aft']=off
# remaining: shelf pack, tallest footprint first
rest=[p[0] for p in P if p[0] not in('hull_fore','hull_aft')]
rest.sort(key=lambda n:-M[n].extents[1])
x=0; y=100+GAP; rowh=0
for n in rest:
    e=M[n].extents
    if x+e[0]>ROWW: x=0; y+=rowh+GAP; rowh=0
    pos[n]=np.array([x,y,0])-M[n].bounds[0]
    x+=e[0]+GAP; rowh=max(rowh,e[1])
sc=trimesh.Scene()
place={}
for n,f,q,card,mat,col,note in P:
    m=M[n].copy(); m.apply_translation(pos[n])
    c=trimesh.visual.color.hex_to_rgba(col); m.visual.face_colors=c
    label=f'{n} x{q} ({card.replace(" · ","+")}, {mat})'
    sc.add_geometry(m,node_name=n,geom_name=n)
    place[n]=m
    M[n].export(f'out/stl/{n}.stl')
sc.export('out/AR-Mini_printed_parts.3mf')
allm=trimesh.util.concatenate(list(place.values()))
print('layout extents',allm.extents.round(0))
np.save('pos.npy',{k:v for k,v in pos.items()},allow_pickle=True)
json.dump({k:v.tolist() for k,v in pos.items()},open('pos.json','w'))
