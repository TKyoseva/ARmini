"""2.5-D oblique render of the assembled carrier rev B from geom.json (written by conn_check.py):
modules, headers, JSTs and parts at their real heights, so the box clearance can be judged before the order.

    python conn_check.py ../AR-Mini_carrier_revB.kicad_pcb && python assembled_view.py geom.json
"""
import json, math
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Ellipse
from collections import defaultdict
import sys
g=json.load(open(sys.argv[1] if len(sys.argv)>1 else 'geom.json'))   # written by conn_check.py
by=defaultdict(list)
for p in g['pads']: by[p['ref']].append(p)

# oblique projection: top face at (x, y) as in the top view (y down on screen), height goes up-right
KX, KY = 0.42, -0.42
def P(x,y,z=0): return (x+KX*z, y+KY*z)
items=[]   # (sortkey, drawfn)
def box(x0,y0,x1,y1,z0,h,fc,ec='#222',lw=0.5,top=None,z=1):
    """extruded box from z0 to z0+h"""
    def draw(ax):
        z1=z0+h
        # right wall (x1 face) and top wall (y0 face) are visible with up-right extrusion
        right=[P(x1,y0,z0),P(x1,y1,z0),P(x1,y1,z1),P(x1,y0,z1)]
        front=[P(x0,y0,z0),P(x1,y0,z0),P(x1,y0,z1),P(x0,y0,z1)]
        ax.add_patch(Polygon(right,closed=True,fc=shade(fc,0.72),ec=ec,lw=lw))
        ax.add_patch(Polygon(front,closed=True,fc=shade(fc,0.86),ec=ec,lw=lw))
        ax.add_patch(Polygon([P(x0,y0,z1),P(x1,y0,z1),P(x1,y1,z1),P(x0,y1,z1)],closed=True,fc=top or fc,ec=ec,lw=lw))
    items.append(((round(z0,1),(y0+y1)/2), draw))
def cyl(cx,cy,r,z0,h,fc,ec='#222',lw=0.5,top=None):
    def draw(ax):
        z1=z0+h
        # body: polygon approximating the visible silhouette (left/bottom arc at z0 and right/top arc at z1 joined)
        pts=[]
        for a in [math.radians(t) for t in range(135,315+1,10)]: pts.append(P(cx+r*math.cos(a),cy+r*math.sin(a),z0))
        for a in [math.radians(t) for t in range(315,135-1,-10)]: pts.append(P(cx+r*math.cos(a),cy+r*math.sin(a),z1))
        ax.add_patch(Polygon(pts,closed=True,fc=shade(fc,0.8),ec=ec,lw=lw))
        ax.add_patch(Ellipse(P(cx,cy,z1),2*r,2*r,fc=top or fc,ec=ec,lw=lw))
    items.append(((round(z0,1),cy), draw))
def shade(c,f):
    import matplotlib.colors as mc
    r,g_,b=mc.to_rgb(c); return (r*f,g_*f,b*f)

fig,ax=plt.subplots(figsize=(15,11.5),dpi=130); ax.set_aspect('equal'); ax.axis('off')
# board
box(20,20,120,100,0,1.6,'#1f6b3a',ec='#0d3d20',lw=1.0,top='#2a8a4a')
items[-1]=((-1e9,0),items[-1][1])
# pads & silk on the top face (draw after board, before parts): just draw pad rings on the top face
def topface_post(ax):
    for p in g['pads']:
        x,y=P(p['x'],p['y'],1.6)
        r=max(p['sx'],p['sy'])/2
        ax.add_patch(Circle((x,y),r,fc='#d9b64a',ec='#8a6d1a',lw=0.3,zorder=1))
        if p['drill']: ax.add_patch(Circle((x,y),p['drill']/2,fc='#1f6b3a' if p['drill']<2 else '#f0f0f0',ec='none',zorder=1))
    for s in g['segs']:
        if s['layer']=='F.Cu':
            a=P(*s['a'],1.6); b=P(*s['b'],1.6); ax.plot([a[0],b[0]],[a[1],b[1]],color='#3f9a5c',lw=s['w']*2.2,solid_capstyle='round',zorder=1)
items.append(((-1e8,0), topface_post))
# ---- components ----
Z=1.6
# U1: two 1x22 female headers + DevKit PCB on top
for x in (44.0,69.4): box(x-1.27,21.27-1.27,x+1.27,74.61+1.27,Z,8.5,'#1a1a1a',top='#2a2a2a')
box(42.7,20.0-6.0,70.8,75.9,Z+8.5,1.6,'#b4232a',top='#c8323a')          # DevKit PCB (antenna end overhangs by 6)
box(47.5,20-6,65.9,20+19,Z+10.1,3.2,'#7d868f',top='#98a1aa')           # WROOM can + antenna area
box(47.5,20-6,65.9,20+1,Z+10.1,0.8,'#6b7a30',top='#8a9a40')             # antenna strip
box(46.5,70.5,52.5,75.9,Z+10.1,3.2,'#6e6e6e',top='#8a8a8a'); box(61,70.5,67,75.9,Z+10.1,3.2,'#6e6e6e',top='#8a8a8a')   # 2 USB-C
# U2: 2 female 1x6, 4 standoffs, module PCB, servo field, terminal, cap
for y in (22.86,77.12): box(78.11-1.27,y-1.27,90.81+1.27,y+1.27,Z,8.5,'#1a1a1a',top='#2a2a2a')
for x in (75.78,93.14):
    for y in (22.86,77.12): cyl(x,y,2.2,Z,8.5,'#c9a84c',top='#dcbe62')
box(71.5,20.5,97.42,79.48,Z+8.5,1.6,'#1b3f9c',top='#2552c2')
for i in range(16):
    y=30+i*2.54
    for j,c in enumerate(('#e8d12a','#d8332a','#222')):
        x=96.2-j*2.54; box(x-0.6,y-0.6,x+0.6,y+0.6,Z+10.1,6,c,ec='none')
cyl(76.5,31,4,Z+10.1,10,'#111',top='#333')                                # capacitor
box(74,36,81,43,Z+10.1,9,'#2f8f4e',top='#3aa85c')                          # V+ terminal
box(80,52,86,58,Z+10.1,1.2,'#222')                                         # PCA9685 chip
# U3: female 1x6 + 1x4, 4 standoffs, PCB, chip
box(99.77-1.27,51.985-1.27,99.77+1.27,64.685+1.27,Z,8.5,'#1a1a1a',top='#2a2a2a')
box(117.55-1.27,54.525-1.27,117.55+1.27,62.145+1.27,Z,8.5,'#1a1a1a',top='#2a2a2a')
for x in (101.04,116.28):
    for y in (47.54,69.13): cyl(x,y,2.2,Z,8.5,'#c9a84c',top='#dcbe62')
box(98.5,45.0,118.82,71.67,Z+8.5,1.6,'#1b3f9c',top='#2552c2')
box(106,56,111,61,Z+10.1,1.0,'#222')
# JST-XH vertical housings (white): pins along x or y
def jst(ref,n):
    ps=by[ref]; xs=[p['x'] for p in ps]; ys=[p['y'] for p in ps]
    if max(xs)-min(xs) > max(ys)-min(ys):   # along x
        L=n*2.5+2.4; box(min(xs)-2.45,ys[0]-2.9,max(xs)+2.45,ys[0]+2.9,Z,7,'#f2f2ec',ec='#999',top='#ffffff')
    else:
        box(xs[0]-2.9,min(ys)-2.45,xs[0]+2.9,max(ys)+2.45,Z,7,'#f2f2ec',ec='#999',top='#ffffff')
for ref,n in (('J1',2),('J2',3),('J3',3),('J4',6),('J5',6),('J6',4),('J7',4),('J8',4),('J9',2),('J10',3),('J11',4)): jst(ref,n)
# pin headers JP3, JP4 (male, black base + pins)
for ref in ('JP3','JP4'):
    ps=by[ref]; xs=[p['x'] for p in ps]; ys=[p['y'] for p in ps]
    box(min(xs)-1.27,min(ys)-1.27,max(xs)+1.27,max(ys)+1.27,Z,2.5,'#1a1a1a')
    for p in ps: box(p['x']-0.3,p['y']-0.3,p['x']+0.3,p['y']+0.3,Z+2.5,6,'#c9c9c9',ec='none')
# resistors (axial, lying), caps, TO-92, LEDs, buzzer, DIP socket, test points, solder jumpers
for ref,ps in by.items():
    if ref.startswith('R') and len(ps)==2:
        x0,x1=sorted(p['x'] for p in ps); y=ps[0]['y']
        box(x0+0.8,y-1.1,x1-0.8,y+1.1,Z+0.3,2.2,'#c8a26a',top='#d9b57c')
    if ref in ('C2','C3','C5'):
        x0,x1=sorted(p['x'] for p in ps); y=ps[0]['y']
        box((x0+x1)/2-1.6,y-0.9,(x0+x1)/2+1.6,y+0.9,Z,3.5,'#e0b83a',top='#eec84a')
    if ref in ('Q2','Q3'):
        xs=sorted(p['x'] for p in ps); x0,x1=xs[0],xs[-1]; y=ps[0]['y']
        box(x0-0.5,y-1.8,x1+0.5,y+1.8,Z+1.5,4.5,'#111',top='#2a2a2a')
    if ref.startswith('LED'):
        y0,y1=sorted(p['y'] for p in ps); x=ps[0]['x']
        c={'LED1':'#2ecc40','LED2':'#f1c40f','LED3':'#e74c3c'}[ref]; cyl(x,(y0+y1)/2,1.6,Z+1.0,5.0,c,top=c)
    if ref=='BZ1':
        xs=sorted(p['x'] for p in ps); x0,x1=xs[0],xs[-1]; y=ps[0]['y']; cyl((x0+x1)/2,y,6,Z,9,'#111',top='#222')
    if ref.startswith('TP'):
        pass
# U6 DIP socket (DNP)
box(29.0,77.5,38.6,94.8,Z,3.5,'#1a1a1a',top='#2a2a2a')
# draw all
for k,fn in sorted(items,key=lambda t:t[0]): fn(ax)
# labels
def lab(x,y,z,t,color='white',fs=7.5,ha='center',bold=False):
    sx,sy=P(x,y,z); ax.text(sx,sy,t,color=color,fontsize=fs,ha=ha,va='center',fontweight='bold' if bold else 'normal',zorder=20)
lab(56.7,50,11.7,'ESP32-S3-DevKit-Lipo',fs=8,bold=True); lab(56.7,56,11.7,'(на 2 гребена, вади се)',fs=7)
lab(56.7,12,13.3,'антена: извън ръба',color='#333',fs=7.5)
lab(56.7,80,2,'USB-C ×2: buck + Mac',color='#eee',fs=7)
lab(84.5,47,10.1,'PCA9685',color='white',fs=8,bold=True); lab(84.5,50,10.1,'16 × 3 серво поле →',fs=6.5)
lab(108.6,66,10.1,'BNO055',color='white',fs=8,bold=True)
lab(29,41.5,8,'JP3 Pi UART',color='#333',fs=6,ha='left'); 
for ref,t,dx,dy in (('J6','THERM FWD',0,-6),('J7','THERM POD',6.5,0),('J8','SERVO BUS',6.5,0),('J9','LEAK',6.5,0),('J2','ESC L',0,-6),('J3','ESC R',0,-6),('J4','BTS L',0,-6),('J5','BTS R',0,-6),('J1','VBAT',0,-6),('J10','KILL',-8,0),('J11','IMU EXT',0,-5)):
    ps=by[ref]; cx=sum(p['x'] for p in ps)/len(ps); cy=sum(p['y'] for p in ps)/len(ps); lab(cx+dx,cy+dy,7,t,color='#222',fs=6.5,ha='left' if dx>0 else ('right' if dx<0 else 'center'))
lab(33.8,86,3.5,'U6 (не се слага)',color='#ccc',fs=6)
lab(104,88,9,'зумер',color='#eee',fs=6.5); lab(119.5,80,6,'LED ×3',color='#222',fs=6.5,ha='left')
lab(113,40,6,'Q2',color='#222',fs=6); lab(102.5,78,6,'Q3',color='#222',fs=6)
ax.set_xlim(14,140); ax.set_ylim(104,0)
ax.set_title('AR-Mini carrier rev B · 100 × 80 mm · така ще изглежда сглобена (поглед отгоре-отпред; височините са реални, в мащаб ~0.4)',fontsize=10)
plt.tight_layout(); plt.savefig('AR-Mini_carrier_revB_assembled.png'); print('ok')
