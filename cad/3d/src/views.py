import time, numpy as np, armesh as A, render as R
from PIL import Image, ImageDraw, ImageFont
FD='/usr/share/fonts/opentype/inter/'
def F(n,s): return ImageFont.truetype(FD+n,s)
def light_from(eye, target, side=0.5):
    e=np.array(eye,float)-np.array(target,float); e/=np.linalg.norm(e)
    s=np.cross([0,0,1],e); s/=np.linalg.norm(s)
    L=e*0.55+np.array([0,0,1.0])*0.75+s*side; return tuple(L/np.linalg.norm(L))
def shot(alpha, eye, target, W, H, fov=30, ortho=None, water=True, dummy=True, box_fix=True, side=0.5, ss=2):
    P=A.build(alpha=alpha, with_dummy=dummy, box_fix=box_fix); Wp=A.world(P, alpha)
    return R.render(Wp, eye=eye, target=target, W=W, H=H, fov=fov, ortho=ortho, water_z=A.draft if water else None,
                    light=light_from(eye,target,side), ss=ss)
if __name__=='__main__':
    t=time.time()
    hero = shot(A.deploy_a, (-780, 820, 560), (250, 0, 70), 2400, 1500, fov=31)
    hero.save('hero_deployed.png'); print('hero', time.time()-t)
