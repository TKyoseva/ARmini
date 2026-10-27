# AR-Mini · system architecture v2, pictorial: same topology as AR-Mini_architecture_v2, with the BOM product photos.
import os
from PIL import Image, ImageDraw, ImageFont
H=os.environ['HOME']; IMG=H+'/work/bomimg/'; OUT=H+'/mnt/ARmini/docs/diagrams/AR-Mini_architecture_v2_pictorial.png'
F='/usr/share/fonts/truetype/dejavu/'
def f(s,b=False): return ImageFont.truetype(F+('DejaVuSans-Bold.ttf' if b else 'DejaVuSans.ttf'),s)
S=2  # scale
W,Hh=1720*S,1060*S
im=Image.new('RGB',(W,Hh),'#fbfaf7'); d=ImageDraw.Draw(im)
INK='#1d1d1b'; MUT='#6b6b66'; PLAN='#9a6b00'; P12='#c2410c'; P5='#b7791f'; EN='#7c3aed'; OKF='#ffffff'; PLF='#fff8e6'
def photo(n):
    for e in ('jpeg','png','jpg'):
        p=f'{IMG}n{n:03d}.{e}'
        if os.path.exists(p): return Image.open(p).convert('RGBA')
    return None
def fitimg(pic,w,h):
    sc=min(w/pic.width,h/pic.height); pic=pic.resize((int(pic.width*sc),int(pic.height*sc)),Image.LANCZOS)
    bg=Image.new('RGBA',pic.size,(255,255,255,255)); bg.alpha_composite(pic); return bg.convert('RGB')
def dashed_rect(x,y,w,h,col,r=8,wd=3,dash=14,gap=8):
    # approximate: draw full rounded rect in bg then dashes along edges
    pts=[(x,y),(x+w,y),(x+w,y+h),(x,y+h),(x,y)]
    for (x0,y0),(x1,y1) in zip(pts,pts[1:]):
        L=((x1-x0)**2+(y1-y0)**2)**.5; n=int(L//(dash+gap)); ux,uy=(x1-x0)/L,(y1-y0)/L
        for i in range(n+1):
            s=i*(dash+gap); e=min(s+dash,L); d.line([(x0+ux*s,y0+uy*s),(x0+ux*e,y0+uy*e)],fill=col,width=wd)
def box(x,y,w,h,title,lines,st='ok',tag='',pic=None,picw=120,indent=None):
    x,y,w,h=x*S,y*S,w*S,h*S
    d.rounded_rectangle([x,y,x+w,y+h],radius=8*S,fill=OKF if st=='ok' else PLF,outline=None)
    if st=='ok': d.rounded_rectangle([x,y,x+w,y+h],radius=8*S,outline=INK,width=3)
    else: dashed_rect(x,y,w,h,PLAN)
    tx=x+12*S
    if pic is not None:
        p=fitimg(pic,picw*S,h-16*S); im.paste(p,(x+8*S,y+(h-p.height)//2)); tx=x+(picw+16)*S
    if indent: tx=x+indent*S
    d.text((tx,y+9*S),title,fill=INK,font=f(14*S,True))
    if tag:
        tw=d.textlength(tag,font=f(11*S,True)); d.text((x+w-10*S-tw,y+h-17*S),tag,fill=PLAN if st!='ok' else MUT,font=f(11*S,True))
    for i,l in enumerate(lines): d.text((tx,y+(32+17*i)*S),l,fill=INK,font=f(12.5*S))
def sec(x,y,t): d.text((x*S,y*S),t,fill=MUT,font=f(12*S,True))
def wire(pts,col=INK,w=1.6,label=None,lx=0,ly=0,arrow=True,dash=False):
    pts=[(a*S,b*S) for a,b in pts]
    if dash:
        for (x0,y0),(x1,y1) in zip(pts,pts[1:]):
            L=((x1-x0)**2+(y1-y0)**2)**.5; n=int(L//(10*S)); ux,uy=(x1-x0)/L,(y1-y0)/L
            for i in range(n+1):
                s=i*10*S; e=min(s+6*S,L); d.line([(x0+ux*s,y0+uy*s),(x0+ux*e,y0+uy*e)],fill=col,width=int(w*S))
    else: d.line(pts,fill=col,width=int(w*S),joint='curve')
    if arrow:
        (x0,y0),(x1,y1)=pts[-2],pts[-1]; L=((x1-x0)**2+(y1-y0)**2)**.5; ux,uy=(x1-x0)/L,(y1-y0)/L; a=8*S
        d.polygon([(x1,y1),(x1-ux*a-uy*a*.5,y1-uy*a+ux*a*.5),(x1-ux*a+uy*a*.5,y1-uy*a-ux*a*.5)],fill=col)
    if label: d.text((lx*S,ly*S),label,fill=col if col!=INK else MUT,font=f(12*S,col!=INK))
d.text((30*S,22*S),'AR-Mini · system architecture v2 · the parts',fill=INK,font=f(24*S,True))
d.text((30*S,50*S),'same connections as the block diagram, drawn with the real parts · 27.10.2026',fill=MUT,font=f(14*S))
sec(30,66,'POWER'); sec(400,66,'SENSING'); sec(400,286,'SAFETY INPUTS'); sec(880,286,'CONTROLLER'); sec(1130,286,'ACTUATION'); sec(400,866,'OPERATOR')
box(400,82,290,100,'MLX90642-D45 · 45°',['32 × 24 px, 45°, front search','Pesho 39.8 °C at 1.3 m'],'ok','C048',photo(76),90)
box(710,82,290,100,'MLX90640 · 110°',['32 × 24 px, wide, on the arch','orientation to check'],'ok','C029',photo(77),90)
box(1020,82,250,100,'BNO055 IMU',['heading for homing','not wired yet'],'plan','PLAN',photo(78),80)
box(1290,82,400,100,'XIAO ESP32-S3 + OV3660',['own 5 V USB-C, own WiFi "AR-Mini-cam"','MJPEG stream + microSD recording'],'ok','C049',photo(63),100)
box(720,302,340,440,'Olimex ESP32-S3-DevKit-Lipo',['','','','','','ESP32-S3-WROOM-1, 8 MB / 8 MB','WiFi AP "AR-Mini", page 192.168.4.1','PlatformIO envs: remote, esc, pca9685,','bts7960, thermal, ladder, bno055','','now: breadboard, pins frozen (C030)','next: carrier PCB rev B 100 × 80 (C032)','','state machine + safety layer:','KILL, LEAK, battery, heartbeat → SAFE','every motor output to neutral'],'ok','IN USE')
p=fitimg(photo(61),300*S,88*S); im.paste(p,((720+170)*S-p.width//2,(302+36)*S))
box(400,302,250,91,'KILL rocker (SPDT)',['RUN: EN high · KILL: EN low','GPIO14 reads the EN node'],'ok','C025 C050',photo(82),60)
box(400,412,250,74,'LEAK probe',['two bare wires in the bilge','10 k to 3V3, probe pulls low'],'ok','C027')
box(400,505,250,74,'Battery sense',['divider 100 k / 30 k → ADC1','±0.02 V from 10 to 12.6 V'],'ok','C027')
box(1130,302,540,100,'Left thruster · Cuifati 560 KV',['GPIO1 → S8050 level shifter → 5 V signal','1600 µs 0.22 A · 1650 µs 0.58 A at 12 V','moved the floating robot (C028)'],'ok','C025 C028',photo(28),110)
box(1130,412,540,100,'Right channel (GPIO2)',['right Cuifati faulty, out (FAILS 173)','interim: MG90S rudder, 5 V, signal direct','next: 2 × Blue Robotics T200 (on order)'],'plan','REPLACING',photo(31),110)
box(1130,522,540,100,'PCA9685 16-ch PWM · I2C-0',['CH10/11 → 2 × TD-8120MG, mirrored','lifts Pesho at ~0.24 A · V+ 6.0 V','OE ← EN · CH6–9 buzzer, LEDs'],'ok','C023',photo(72),110)
p=fitimg(photo(30),70*S,60*S); im.paste(p,((1670-80)*S,(522+10)*S))
box(1130,632,540,100,'2 × BTS7960 → ROB0154 tracks',['L GPIO39/40 · R GPIO41/42 · 10 k pull-downs','VCC 3V3 · R_EN / L_EN ← EN','left track 0.34 A at 80 % · right open'],'ok','LEFT C050',photo(74),110)
p=fitimg(photo(27),80*S,64*S); im.paste(p,((1670-90)*S,(632+8)*S))
box(30,82,320,100,'Bench supply 30 V / 10 A',['all tests so far: tethered, 12 V','servo rail 6.0 V, 3 A limit'],'ok','IN USE',photo(108),80)
box(30,192,320,74,'3S LiPo 2200 mAh 40C',['11.1 V nominal, 12.6 V full'],'plan','',photo(53),80)
box(30,276,320,74,'Fuse 30 A → switch 50 A',['master switch cuts everything'],'plan','',photo(83),52,indent=126)
p=fitimg(photo(81),50*S,50*S); im.paste(p,((30+66)*S,(276+12)*S))
box(30,360,320,74,'Fuse block',['ESCs 20 A · BTS 10 A · logic 5 A'],'plan','C026',photo(84),80)
box(30,560,320,100,'Buck 12 → 5 V, 3 A',['into the DevKit OTG USB-C','now: laptop USB instead'],'plan','',photo(79),90)
box(30,670,320,74,'Servo rails',['TD-8120MG 6.0 V on PCA9685 V+','MG90S rudder 5 V, never 12 V'],'plan','')
# wires (same routes as v2)
wire([(190,266),(190,274)],P12,3); wire([(190,350),(190,358)],P12,3)
wire([(190,434),(190,558)],P12,3,'12 V',200,490)
wire([(350,400),(365,400),(365,820),(1700,820),(1700,350),(1674,350)],P12,3,'12 V bus: thrusters 20 A, tracks 10 A, buck',380,826)
wire([(1700,690),(1674,690)],P12,3); wire([(1700,460),(1674,460)],P12,3)
wire([(350,600),(380,600),(380,640),(716,640)],P5,2.4,'5 V → USB-C',560,620)
wire([(545,182),(545,240),(780,240),(780,298)],INK,1.6,'I2C-0 · GPIO48 / 47',552,224)
wire([(855,182),(855,298)],INK,1.6,'I2C-1 · GPIO8 / 9',862,224)
wire([(1145,182),(1145,262),(1020,262),(1020,298)],PLAN,1.6,'I2C-0',1152,248,dash=True)
wire([(650,350),(716,350)],INK,1.6,'GPIO14',656,334); wire([(650,450),(716,450)],INK,1.6,'GPIO7',656,434); wire([(650,543),(716,543)],INK,1.6,'GPIO4',656,527)
wire([(400,330),(388,330),(388,790),(1110,790),(1110,580),(1126,580)],EN,2.2,'EN: hardware stop, no firmware in the loop',420,795,dash=True)
wire([(1110,690),(1126,690)],EN,2.2,dash=True)
wire([(1060,345),(1126,345)],INK,1.6,'GPIO1',1066,331); wire([(1060,455),(1126,455)],PLAN,1.6,'GPIO2',1066,441,dash=True)
wire([(1060,560),(1126,560)],INK,1.6,'I2C-0',1066,546); wire([(1060,670),(1126,670)],INK,1.6,'GPIO39–42',1066,650)
box(400,882,340,74,'Phone browser → AR-Mini',['ARM · thrust stick · STOP','heartbeat 500 ms → SAFE if lost'],'ok','C028')
box(760,882,330,57,'Phone → AR-Mini-cam',['live view from the arch (OV3660)'],'ok','C049')
box(1110,882,280,57,'Laptop · USB serial',['bench commands, CSV logs, flashing'],'ok','')
box(1410,882,280,74,'v2 (2027)',['Pi 5 + ROS 2 · UART GPIO15/16','4 × ST3215 bus servos'],'plan','v2',photo(64),60)
wire([(570,882),(570,850),(800,850),(800,744)],INK,1.6,'WiFi · WebSocket',578,853)
wire([(1250,882),(1250,850),(960,850),(960,744)],INK,1.6,'USB-C',1258,853)
# legend
ly=1030
d.rounded_rectangle([30*S,(ly-13)*S,56*S,(ly+3)*S],radius=3*S,outline=INK,width=3,fill=OKF); d.text((64*S,(ly-10)*S),'tested on hardware (card)',fill=INK,font=f(12*S))
dashed_rect(260*S,(ly-13)*S,26*S,16*S,PLAN); d.text((294*S,(ly-10)*S),'designed / on order',fill=INK,font=f(12*S))
for i,(c,t) in enumerate([(P12,'12 V'),(P5,'5 V'),(EN,'EN hardware stop'),(INK,'signal / data')]):
    x=480+i*170; d.line([(x*S,(ly-5)*S),((x+34)*S,(ly-5)*S)],fill=c,width=3*S if c!=INK else 2*S); d.text(((x+42)*S,(ly-10)*S),t,fill=INK,font=f(12*S))
d.text((1260*S,(ly-10)*S),'photos: the BOM (docs/bom)',fill=MUT,font=f(12*S))
im.save(OUT,quality=92); print(OUT,im.size)
