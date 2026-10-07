import json, base64, numpy as np, armesh as A
from collections import defaultdict
P = A.build(alpha=A.deploy_a, with_dummy=True, box_fix=True)
def edges_of(tris, ang=33):
    cosT = np.cos(np.radians(ang))
    n = np.cross(tris[:,1]-tris[:,0], tris[:,2]-tris[:,0]); ln = np.linalg.norm(n,axis=1); ok = ln>1e-9
    tris = tris[ok]; n = n[ok]/ln[ok,None]
    E = defaultdict(list)
    key = lambda p: (round(p[0],2), round(p[1],2), round(p[2],2))
    for i,t in enumerate(tris):
        k = [key(p) for p in t]
        for a,b in ((0,1),(1,2),(2,0)):
            e = (k[a],k[b]) if k[a] < k[b] else (k[b],k[a])
            E[e].append(i)
    out = []
    for e, fs in E.items():
        if len(fs)==1 or len(fs)>2: out.append(e)
        else:
            if abs(np.dot(n[fs[0]], n[fs[1]])) < cosT: out.append(e)
    return np.array(out, float).reshape(-1,6)
def b64(arr):
    q = np.round(np.asarray(arr)*10).astype('<i2')
    assert np.abs(np.asarray(arr)*10).max() < 32767
    return base64.b64encode(q.tobytes()).decode()
parts = []
ntri = nedge = 0
for p in P:
    t = p['tris']
    if p['col'] in ('rubber',) and 'grouser' in p['name']:
        e = np.zeros((0,6))
    else:
        e = edges_of(t)
    parts.append(dict(n=p['name'], k=p['col'], x=p['xf'][0], p=list(p['xf'][1]) if p['xf'][0]=='arm' else None,
                      v=b64(t.reshape(-1,3)), e=b64(e.reshape(-1,3)) if len(e) else ''))
    ntri += len(t); nedge += len(e)
cols = {k: [round(c/255,3) for c in v] for k,v in A.COL.items()}
cx0, cz0, rz0 = A.cradle_pos(A.deploy_a)
data = dict(parts=parts, cols=cols, cx0=cx0, cz0=cz0, deploy=A.deploy_a, stow=A.stow_a, draft=A.draft,
            pbox_lift=A.hull_H + 6 + A.beam - A.ch_H)
js = json.dumps(data, separators=(',',':'))
open('model.json','w').write(js)
print('tris', ntri, 'edges', nedge, 'json KB', len(js)//1024)
