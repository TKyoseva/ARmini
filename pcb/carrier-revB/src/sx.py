import re
def parse(s):
    tok=re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', s)
    stack=[[]]
    for t in tok:
        if t=='(': stack.append([])
        elif t==')':
            l=stack.pop(); stack[-1].append(l)
        else: stack[-1].append(t[1:-1] if t.startswith('"') else t)
    return stack[0][0]
def kids(node,name): return [k for k in node[1:] if isinstance(k,list) and k and k[0]==name]
def first(node,name):
    k=kids(node,name); return k[0] if k else None
def load(path): return parse(open(path).read())
def footprints(root):
    out=[]
    for fp in kids(root,'footprint'):
        ref=[t for t in kids(fp,'property') if t[1]=='Reference'][0][2]
        at=first(fp,'at'); x,y=float(at[1]),float(at[2])
        pads=[]
        for p in kids(fp,'pad'):
            pa=first(p,'at'); sz=first(p,'size'); dr=first(p,'drill'); nt=first(p,'net')
            net = (nt[2] if len(nt)>2 else nt[1]) if nt else ''
            pads.append(dict(num=p[1],kind=p[2],shape=p[3],x=x+float(pa[1]),y=y+float(pa[2]),sx=float(sz[1]),sy=float(sz[2]),drill=float(dr[1]) if dr and dr[1].replace('.','',1).isdigit() else None,net=net))
        out.append(dict(ref=ref,x=x,y=y,pads=pads,name=fp[1]))
    return out
