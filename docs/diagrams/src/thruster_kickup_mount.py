import math
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Rectangle, FancyArrowPatch
from matplotlib.path import Path
from matplotlib.patches import PathPatch

def chull(pts):
    pts=sorted(set(pts))
    def cross(o,a,b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo=[]; 
    for p in pts:
        while len(lo)>=2 and cross(lo[-2],lo[-1],p)<=0: lo.pop()
        lo.append(p)
    up=[]
    for p in reversed(pts):
        while len(up)>=2 and cross(up[-2],up[-1],p)<=0: up.pop()
        up.append(p)
    return lo[:-1]+up[:-1]
def circ(cx,cy,r,n=72): return [(cx+r*math.cos(2*math.pi*i/n),cy+r*math.sin(2*math.pi*i/n)) for i in range(n)]
def rect(x0,y0,x1,y1): return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
def rot(pts,cx,cy,deg):
    a=math.radians(deg); c,s=math.cos(a),math.sin(a)
    return [(cx+(x-cx)*c-(y-cy)*s, cy+(x-cx)*s+(y-cy)*c) for x,y in pts]

draft=42; tp_z=79; pivot_z=75; aft=47; axis_z=draft-10-72.27/2; face_z=axis_z+47.10; pz=axis_z+47.10+2.5-pivot_z  # -29.5 rel
lock_a=math.degrees(math.atan2(pz,aft))

def side(ax, pin_x, title, show_stowed=False, show_collision=False):
    ax.set_aspect('equal'); ax.axis('off'); ax.set_title(title,fontsize=9.5,loc='left',pad=2)
    # water & hull
    ax.add_patch(Rectangle((-120,-60),300,draft+60,fc='#cfe6f5',ec='none',zorder=0))
    ax.text(pin_x+aft,axis_z-50,'тръстер: дюза Ø72 × 112, призрак',ha='center',fontsize=7,color='#3b5b74')
    ax.plot([-120,180],[draft,draft],color='#2a7fb8',lw=1,ls='--'); ax.text(176,draft+1.5,'водолиния z 42',ha='right',fontsize=7,color='#2a7fb8')
    ax.add_patch(Rectangle((-120,0),114,120,fc='#f1efe6',ec='#888',lw=1,zorder=1))                     # hull aft section (stern at x=-6)
    ax.text(-38,60,'корпус\n(кърма)',ha='center',va='center',fontsize=8,color='#666')
    ax.add_patch(Rectangle((-6,44),6,70,fc='#e2dfd0',ec='#888',lw=0.8,zorder=1.5)); ax.text(-3,117,'транец\nпад',ha='center',va='bottom',fontsize=6.5,color='#666')
    # bracket plate + lug
    ax.add_patch(Rectangle((0,47),6,64,fc='#444',ec='k',lw=0.8,zorder=3))
    lug=chull(rect(0,61,1,89)+circ(pin_x,pivot_z,14))
    ax.add_patch(Polygon(lug,closed=True,fc='#5a5a5a',ec='k',lw=0.8,alpha=0.55,zorder=5))
    # bracket M3 counterbores (side view: 2 of 4 at z 59/99)
    for z in (59,99): ax.add_patch(Rectangle((0,z-1.7),6,3.4,fc='#aaa',ec='#555',lw=0.4,zorder=3.5)); ax.add_patch(Rectangle((3,z-3.1),3,6.2,fc='#ccc',ec='#555',lw=0.4,zorder=3.6))
    # arm (deployed): cheek hull + plate; thruster ghost
    def arm_pts(kick=0):
        cheek=chull(circ(0,0,12)+rect(-8,-6,0,6)+rect(aft-25,pz-2.5,aft+25,pz+2.5))
        plate=rect(aft-25,pz-2.5,aft+25,pz+2.5)
        duct=rect(aft-56,axis_z-pivot_z-72.27/2,aft+56,axis_z-pivot_z+72.27/2)
        frame=rect(aft-25,axis_z-pivot_z+72.27/2-2,aft+25,face_z-pivot_z)
        sh=lambda P:[(pin_x+x,pivot_z+y) for x,y in P]
        out=[sh(cheek),sh(plate),sh(duct),sh(frame)]
        if kick: out=[rot(P,pin_x,pivot_z,kick) for P in out]
        return out
    cheek,plate,duct,frame=arm_pts()
    ax.add_patch(Polygon(duct,closed=True,fc='#9fb7c9',ec='#5b7b94',lw=0.8,alpha=0.6,zorder=2))
    ax.add_patch(Polygon(frame,closed=True,fc='#9fb7c9',ec='#5b7b94',lw=0.8,alpha=0.6,zorder=2))
    ax.add_patch(Polygon(cheek,closed=True,fc='#e07b00',ec='#8a4a00',lw=0.9,alpha=0.9,zorder=4))
    ax.add_patch(Polygon(plate,closed=True,fc='#f0a040',ec='#8a4a00',lw=0.9,zorder=4.5))
    # pin, lock holes
    ax.add_patch(Circle((pin_x,pivot_z),2.65,fc='white',ec='k',lw=0.8,zorder=6))
    for a,lab in ((lock_a,'заключ. пин, спуснат'),(lock_a+100,'заключ. пин, вдигнат')):
        x=pin_x+10*math.cos(math.radians(a)); z=pivot_z+10*math.sin(math.radians(a))
        ax.add_patch(Circle((x,z),1.65,fc='white',ec='k',lw=0.6,zorder=6))
    if show_collision:
        # overlap of the cheek circle with the plate x 0..6
        ov=[p for p in circ(pin_x,pivot_z,12,360) if p[0]<=6]
        poly=[(6,pivot_z-math.sqrt(12**2-(6-pin_x)**2))]+sorted(ov,key=lambda p:-math.atan2(p[1]-pivot_z,p[0]-pin_x) if p[0]<pin_x else 0)
        # simpler: clip circle polygon to x<=6 by walking the circle
        pts=[]
        for i in range(361):
            a=math.radians(i); x=pin_x+12*math.cos(a); z=pivot_z+12*math.sin(a)
            if x<=6: pts.append((x,z))
        pts=[(6,max(p[1] for p in pts))]+pts+[(6,min(p[1] for p in pts))]
        ax.add_patch(Polygon(pts,closed=True,fc='red',ec='red',lw=1.2,hatch='xx',alpha=0.8,zorder=7))
        ax.annotate('главината (r 12) влиза\n4 mm в плочата на стойката',xy=(4,pivot_z-6),xytext=(40,10),fontsize=8,color='red',ha='left',
                    arrowprops=dict(arrowstyle='->',color='red',lw=1.2),bbox=dict(boxstyle='round,pad=0.3',fc='white',ec='red'))
    if show_stowed:
        c2,p2,d2,f2=arm_pts(kick=100)
        for P,fc in ((d2,'#9fb7c9'),(f2,'#9fb7c9'),(c2,'#e07b00'),(p2,'#f0a040')):
            ax.add_patch(Polygon(P,closed=True,fc=fc,ec='#555',lw=0.6,alpha=0.25,ls='--',zorder=1.8))
        ax.text(pin_x+30,185,'вдигнат на брега (+100°):\nдюзата над корпуса',fontsize=7.5,color='#666',ha='center')
        ax.annotate('',xy=(pin_x+40,pivot_z+40),xytext=(pin_x+40,pivot_z-10),arrowprops=dict(arrowstyle='->',color='#666',lw=1,connectionstyle='arc3,rad=-0.5'))
    # dimensions
    def dim(x1,y1,x2,y2,text,color='#1b5e8a',off=(0,0),fs=7.5):
        ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='<->',mutation_scale=9,lw=1,color=color,shrinkA=0,shrinkB=0,zorder=8))
        ax.text((x1+x2)/2+off[0],(y1+y2)/2+off[1],text,color=color,fontsize=fs,ha='center',va='center',zorder=9,bbox=dict(boxstyle='round,pad=0.15',fc='white',ec='none',alpha=0.85))
    dim(0,118,pin_x,118,f'ос на {pin_x} mm от транеца','#1b5e8a',off=(0,5))
    dim(pin_x+1,pivot_z+22,pin_x+13,pivot_z+22,'r 12 главина','#8a4a00',off=(14,0),fs=7)
    dim(6,pivot_z+14,pin_x-12,pivot_z+14,f'{pin_x-12-6:.0f} mm луфт' if pin_x>18 else '4 mm припокриване','#1b5e8a' if pin_x>18 else 'red',off=(0,-5),fs=7)
    dim(-62,0,-62,pivot_z,'оста: 75 над дъното\n= 33 над водата','#1b5e8a',off=(16,0),fs=7)
    ax.text(pin_x+aft+30,pz+pivot_z+12,'плоча на ръката 50 × 30 × 5,\n4 × M4 надолу в рамката',ha='left',fontsize=6.5,color='#5a3000')
    ax.text(8,104,'стойка: плоча 6 × 50 × 64\nна пада, 4 × M3 във вложки',ha='left',va='center',fontsize=6.5,color='#222')
    ax.text(pin_x+16,pivot_z+4,'ухо r 14\n(пред бузата)',ha='left',fontsize=6.5,color='#222')
    ax.set_xlim(-70,160); ax.set_ylim(-48,200)

fig=plt.figure(figsize=(16,11),dpi=130)
ax1=fig.add_axes([0.01,0.50,0.48,0.46]); side(ax1,14,'КАКТО Е В МОДЕЛА: th_pin_dx = 14 → сблъсък',show_collision=True)
ax2=fig.add_axes([0.51,0.50,0.48,0.46]); side(ax2,19,'ПОПРАВКА: th_pin_dx = 19 → 1 mm луфт; с вдигнатото положение',show_stowed=True)

# end view (from aft): y horizontal, z vertical
ax3=fig.add_axes([0.2,0.01,0.6,0.46]); ax3.set_aspect('equal'); ax3.axis('off'); ax3.set_title('ПОГЛЕД ОТЗАД (от кърмата): сандвичът уши – бузи – плоча, всичко на една ос Ø5',fontsize=10,loc='left')
pin_x=19
ax3.add_patch(Rectangle((-60,-10),120,draft+10,fc='#cfe6f5',ec='none',zorder=0)); ax3.plot([-60,60],[draft,draft],color='#2a7fb8',lw=1,ls='--')
ax3.add_patch(Rectangle((-50,0),100,120,fc='#f1efe6',ec='#888',lw=1,zorder=1)); ax3.text(-48,30,'корпус (кърма)\n100 широк',ha='left',fontsize=7.5,color='#666')
ax3.add_patch(Rectangle((-28,44),56,70,fc='#e2dfd0',ec='#888',lw=0.8,zorder=1.5))
ax3.add_patch(Rectangle((-25,47),50,64,fc='#444',ec='k',lw=0.8,zorder=2)); ax3.text(0,108,'плоча на стойката 50 × 64',ha='center',fontsize=7,color='white')
for y in (-20,20):
    for z in (59,99): ax3.add_patch(Circle((y,z),3.1,fc='#ccc',ec='#555',lw=0.5,zorder=3)); ax3.add_patch(Circle((y,z),1.7,fc='#888',ec='#555',lw=0.3,zorder=3.1))
for s in (-1,1):
    ax3.add_patch(Rectangle((s*19-(6 if s<0 else 0),61),6,28,fc='#5a5a5a',ec='k',lw=0.8,zorder=4)); ax3.text(s*22,65,'ухо\n6',ha='center',fontsize=6.5,color='white')
    ax3.add_patch(Rectangle((s*12.5-(6 if s<0 else 0),pivot_z-12),6,24,fc='#e07b00',ec='#8a4a00',lw=0.8,zorder=4.5)); ax3.text(s*15.5,pivot_z+3,'буза\n6',ha='center',fontsize=6.5,color='white')
ax3.add_patch(Rectangle((-30,pivot_z-30.5),60,5,fc='#f0a040',ec='#8a4a00',lw=0.8,zorder=4.5)); ax3.text(33,pivot_z-28,'плоча на ръката, 30 широка',ha='left',fontsize=6.5,color='#5a3000')
ax3.add_patch(Rectangle((-30,-10),60,0.1,fc='none',ec='none'))
ax3.add_patch(Rectangle((-30,pivot_z-2.5),60,5,fc='#c0c0c0',ec='#555',lw=0.8,zorder=6)); ax3.text(33,pivot_z,'Ø5 алуминиев прът, 60 mm,\nR-клипс в отворите 1.5',ha='left',va='center',fontsize=7,color='#222')
ax3.add_patch(Circle((0,axis_z),72.27/2,fc='#9fb7c9',ec='#5b7b94',lw=0.8,alpha=0.5,zorder=1.2)); ax3.text(0,axis_z,'тръстер Ø72, долу 40 под корпуса',ha='center',va='center',fontsize=7,color='#3b5b74')
for y,t in ((-19,'0.5'),(19,'0.5')):
    ax3.annotate(f'{t} луфт',xy=(y+(0.25 if y<0 else -0.25),pivot_z+16),xytext=(y*1.9,pivot_z+30),fontsize=6.5,color='#1b5e8a',ha='center',arrowprops=dict(arrowstyle='->',color='#1b5e8a',lw=0.8))
ax3.set_xlim(-55,90); ax3.set_ylim(-42,122)
fig.text(0.5,0.975,'Kick-up стойка на тръстера: странично (вляво: грешката; вдясно: поправката) и отзад. Размери в mm, z от дъното на корпуса.',fontsize=10.5,ha='center')
fig.savefig('AR-Mini_thruster_kickup_mount.png',facecolor='white'); print('ok', lock_a, pz, axis_z, face_z)
