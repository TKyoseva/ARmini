import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle

W,H=200,134
fig=plt.figure(figsize=(20,13.4),dpi=150)
ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,W); ax.set_ylim(0,H); ax.axis("off")
ax.add_patch(Rectangle((0,0),W,H,fc="white",ec="none"))
ax.add_patch(Rectangle((0,H-1.2),W,1.2,fc="#111",ec="none"))
C={"12V":"#D62828","5V":"#F77F00","3V3":"#C2185B","GND":"#111111","SIG":"#1D4ED8","I2C":"#2E7D32","UART":"#00897B","MOT":"#E6B800"}
NAVY="#1F2A6B"

def section(x,y,w,h,title,title_color=NAVY,sub=None):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0,rounding_size=1.6",fc="white",ec="#2B2B2B",lw=1.6,zorder=1))
    ax.text(x+w/2,y+h-2.3,title,ha="center",va="center",fontsize=11,fontweight="bold",color=title_color,zorder=5)
    if sub: ax.text(x+w/2,y+h-5.2,sub,ha="center",va="center",fontsize=8.3,color=title_color,zorder=5)
def module(x,y,w,h,label,sub=None,fc="#1E3A8A",ec="#0F1F4D",tc="white",fs=7.5):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0,rounding_size=0.8",fc=fc,ec=ec,lw=1.2,zorder=2))
    ax.text(x+w/2,y+h/2+(1.3 if sub else 0),label,ha="center",va="center",fontsize=fs,fontweight="bold",color=tc,zorder=5,linespacing=1.15)
    if sub: ax.text(x+w/2,y+h/2-1.8,sub,ha="center",va="center",fontsize=6.0,color=tc,alpha=.92,zorder=5,linespacing=1.15)
def pin(xb,y,name,side,fs=6.4):
    field=len(name)*0.92+1.0
    if side=="L":
        ax.text(xb-0.8,y,name,ha="right",va="center",fontsize=fs,fontweight="bold",zorder=5)
        xs=xb-0.8-field; ax.plot([xs,xs-2.2],[y,y],color="#333",lw=1.1,zorder=4); ax.add_patch(Circle((xs-2.2,y),0.45,fc="#333",zorder=5)); return (xs-2.2,y)
    else:
        ax.text(xb+0.8,y,name,ha="left",va="center",fontsize=fs,fontweight="bold",zorder=5)
        xs=xb+0.8+field; ax.plot([xs,xs+2.2],[y,y],color="#333",lw=1.1,zorder=4); ax.add_patch(Circle((xs+2.2,y),0.45,fc="#333",zorder=5)); return (xs+2.2,y)
def pins(xb,y0,names,side,pitch=2.6,fs=6.4): return {n:pin(xb,y0-i*pitch,n,side,fs) for i,n in enumerate(names)}
def wire(pts,color,lw=1.5): ax.plot([p[0] for p in pts],[p[1] for p in pts],color=color,lw=lw,solid_joinstyle="miter",solid_capstyle="round",zorder=3)
def dot(p,color): ax.add_patch(Circle(p,0.6,fc=color,ec=color,zorder=4))
def hto(p,x): return (x,p[1])

# ================= TITLE =================
ax.add_patch(FancyBboxPatch((52,124.5),96,7,boxstyle="round,pad=0,rounding_size=1.2",fc="white",ec="#2B2B2B",lw=1.6))
ax.text(100,128,"AMPHIREACH  AR-Mini  –  HARDWARE CIRCUIT DIAGRAM",ha="center",va="center",fontsize=15,fontweight="bold")

# ================= SENSORS =================
section(2,48,38,67,"SENSORS")
module(4,100,16,9,"MLX90642-D45","thermal · forward 45°",fc="#263238")
T1=pins(20,107,["3V3","GND","SDA0","SCL0"],"R",pitch=2.4)
module(4,86,16,9,"MLX90640-110°","thermal · cradle",fc="#263238")
T2=pins(20,93,["3V3 ","GND ","SDA1","SCL1"],"R",pitch=2.4)
module(4,72,16,9,"BNO055","9-DoF IMU",fc="#1565C0")
IM=pins(20,79,["3V3  ","GND  ","SDA0 ","SCL0 "],"R",pitch=2.4)
module(4,61,16,7,"LEAK PROBE","2 bare wires · hull floor",fc="#455A64")
LK=pins(20,65.5,["OUT","GND   "],"R",pitch=2.4)
module(4,51,16,7,"VBAT SENSE","100k / 33k divider",fc="#455A64")
VB=pins(20,55.5,["ADC","GND    "],"R",pitch=2.4)

# ================= MAIN CONTROLLER =================
section(60,56,60,60,"MAIN CONTROLLER",sub="(XIAO ESP32S3 SENSE)")
module(84,68,12,34,"XIAO\nESP32S3\nSENSE","OV2640 ▲\nmicroSD ▼\nWiFi",fc="#0D47A1",fs=8.5)
L=pins(84,99,["5V","GND","3V3","A0  VBAT","A1  LEAK/KILL","D2  SDA1","D3  SCL1","D4  SDA0","D5  SCL0"],"L",pitch=3.3)
R=pins(96,99,["D6  TX1","D7  RX1","USB-C","D8–D10  SPI→SD","GPIO21  SD CS"],"R",pitch=3.3)
ax.text(90,60,"FreeRTOS · core 0: perception (thermal blobs, pan loop) · core 1: control (state machine, motors, CSV log)",ha="center",fontsize=6.4,color=NAVY,style="italic")

# ================= PWM DRIVER =================
section(126,88,42,30,"PWM DRIVER",sub="(PCA9685 · I2C 0x40 · 16 ch)")
module(144,92,14,17,"PCA9685","12-bit PWM",fc="#1B5E20")
Lp=pins(144,106,["3V3","GND","SDA","SCL","OE"],"L",pitch=3.0)
Rp=pins(158,107,["CH0","CH1","CH2","CH3","CH4","CH5","CH6","CH7–9"],"R",pitch=2.05)

# ================= THRUSTERS =================
section(170,96,27,22,"THRUSTERS")
module(172,108,15,6.5,"ESC L · CCW","bi-dir · potted",fc="#B71C1C",fs=6.8)
module(172,99,15,6.5,"ESC R · CW","bi-dir · potted",fc="#B71C1C",fs=6.8)
ax.text(183.5,97.6,"Cuifati 1.2 kg · 12 V · 8 A",ha="center",fontsize=5.8,color="#555")

# ================= TRACK DRIVERS =================
section(170,56,27,38,"TRACK DRIVERS",sub="(BTS7960 ×2 · 43 A)")
module(172,76,15,8,"BTS7960 L","RPWM LPWM EN",fc="#E65100",fs=7)
module(172,63,15,8,"BTS7960 R","RPWM LPWM EN",fc="#E65100",fs=7)
ax.text(183.5,59.3,"M+ M− → ROB0154 motors 12 V 160 rpm",ha="center",fontsize=5.6,color="#555")

# ================= INDICATORS =================
section(126,64,42,22,"INDICATORS & SAFETY")
module(129,67,12,9,"BUZZER","NPN BC337",fc="#37474F",fs=7)
module(144,67,12,9,"LED ×3","state · arm · fault",fc="#37474F",fs=7)
module(158,67,8,9,"KILL\nSW","logic",fc="#B71C1C",fs=6.5)

# ================= SERVO BUS =================
section(60,20,60,32,"SERVO BUS",sub="(Waveshare Serial Bus Servo Driver · UART 1 Mbps)")
module(64,36,16,9,"BUS DRIVER","12 V in · TTL↔bus",fc="#4A148C",fs=7)
Pd=pins(80,43.3,["TX","RX","12V","GND"],"R",pitch=2.2)
for i,(nm,fn) in enumerate([("ID1","cradle L"),("ID2","cradle R"),("ID3","cam pan"),("ID4","dome v2")]):
    module(64+i*14,23,12,8,f"ST3215 {nm}",fn,fc="#6A1B9A",fs=6.6)
    if i<3: wire([(76+i*14,27),(78+i*14,27)],C["UART"],2.2)
wire([(68,36),(68,31)],C["UART"],2.2)
ax.text(110,34,"5264-3P daisy chain\n30 cm + 90 cm",ha="center",fontsize=6.0,color="#555")

# ================= RASPBERRY PI =================
section(128,20,68,40,"RASPBERRY PI 5  (v2: ROS 2 bridge · telemetry)")
module(146,30,24,18,"RASPBERRY PI 5","8 GB · active cooler · 64 GB",fc="#C62828",fs=8.5)
Pp=pins(146,44,["USB-C PWR","USB-A"],"L",pitch=3.4)
module(172,41,22,10,"BUCK 12→5 V 5 A","USB-C out · 25 W",fc="#F57C00",fs=6.8)
ax.text(162,24.5,"XIAO ↔ Pi over USB (serial)  ·  Pi records ROS 2 bags, hosts WiFi dashboard",ha="center",fontsize=6.0,color="#555")

# ================= POWER SUPPLY =================
section(2,4,54,40,"POWER SUPPLY",title_color="#B71C1C")
module(5,26,14,10,"LiPo 3S\n2200 mAh","XT60 · 40C",fc="#1565C0",fs=7.5)
module(23,28,10,6.5,"KILL SW","50 A DC",fc="#263238",fs=6.6)
module(37,22,13,16,"FUSE\nBLOCK","6-slot blade",fc="#263238",fs=7.5)
Fo=pins(50,36,["20 A  thrusters","15 A  servo bus","10 A  tracks","5 A  logic","5 A  Pi"],"R",pitch=3.0,fs=6.0)
module(23,8,16,9,"BUCK 12→5 V","3 A · logic rail",fc="#F57C00",fs=7)
ax.text(10,6.3,"GND common",fontsize=6.3,color=C["GND"],fontweight="bold")
wire([(19,32),(23,32)],C["12V"],2.2); wire([(33,32),(37,32)],C["12V"],2.2)
wire([(19,29),(21,29),(21,17.5),(60,17.5)],C["GND"],2.0)
wire([Fo["5 A  logic"],hto(Fo["5 A  logic"],58),(58,15),(31,15),(31,12.5)],C["12V"],1.6)   # 5A logic -> buck
ax.text(27,19.5,"12 V in",fontsize=5.5,color=C["12V"])

# ================= LEGEND =================
section(160,4,36,14,"LEGEND",title_color="#111")
leg=[("+12 V","12V"),("+5 V","5V"),("3V3","3V3"),("GND","GND"),("PWM / signal","SIG"),("I2C","I2C"),("UART / bus","UART"),("Motor out","MOT")]
for i,(n,k) in enumerate(leg):
    col=i//4; row=i%4; x=163+col*17; y=13.6-row*2.6
    ax.plot([x,x+4],[y,y],color=C[k],lw=2.4); ax.text(x+5,y,n,va="center",fontsize=6.5)

# ================= WIRING =================
ch={"3V3":44,"GND":46,"SDA0":48,"SCL0":50,"SDA1":52,"SCL1":54,"VBAT":56,"LEAK":58}
# I2C-0
wire([T1["SDA0"],hto(T1["SDA0"],ch["SDA0"]),(ch["SDA0"],L["D4  SDA0"][1]),L["D4  SDA0"]],C["I2C"])
wire([T1["SCL0"],hto(T1["SCL0"],ch["SCL0"]),(ch["SCL0"],L["D5  SCL0"][1]),L["D5  SCL0"]],C["I2C"])
wire([IM["SDA0 "],hto(IM["SDA0 "],ch["SDA0"])],C["I2C"]); dot((ch["SDA0"],IM["SDA0 "][1]),C["I2C"])
wire([IM["SCL0 "],hto(IM["SCL0 "],ch["SCL0"])],C["I2C"]); dot((ch["SCL0"],IM["SCL0 "][1]),C["I2C"])
# I2C-0 to PCA9685 over the top
wire([(ch["SDA0"],L["D4  SDA0"][1]),(ch["SDA0"],119.5),(124,119.5),(124,Lp["SDA"][1]),Lp["SDA"]],C["I2C"],1.3); dot((ch["SDA0"],L["D4  SDA0"][1]),C["I2C"])
wire([(ch["SCL0"],L["D5  SCL0"][1]),(ch["SCL0"],121.2),(125.5,121.2),(125.5,Lp["SCL"][1]),Lp["SCL"]],C["I2C"],1.3); dot((ch["SCL0"],L["D5  SCL0"][1]),C["I2C"])
# I2C-1
wire([T2["SDA1"],hto(T2["SDA1"],ch["SDA1"]),(ch["SDA1"],L["D2  SDA1"][1]),L["D2  SDA1"]],C["I2C"])
wire([T2["SCL1"],hto(T2["SCL1"],ch["SCL1"]),(ch["SCL1"],L["D3  SCL1"][1]),L["D3  SCL1"]],C["I2C"])
# analog
wire([VB["ADC"],hto(VB["ADC"],ch["VBAT"]),(ch["VBAT"],L["A0  VBAT"][1]),L["A0  VBAT"]],C["SIG"])
wire([LK["OUT"],hto(LK["OUT"],ch["LEAK"]),(ch["LEAK"],L["A1  LEAK/KILL"][1]),L["A1  LEAK/KILL"]],C["SIG"])
# 3V3 rail (XIAO -> sensors, PCA)
x3=L["3V3"]
wire([x3,hto(x3,ch["3V3"]),(ch["3V3"],T1["3V3"][1]),T1["3V3"]],C["3V3"],1.3)
for p in [T2["3V3 "],IM["3V3  "]]: wire([p,hto(p,ch["3V3"])],C["3V3"],1.3); dot((ch["3V3"],p[1]),C["3V3"])
wire([(ch["3V3"],x3[1]),(ch["3V3"],118),(122.5,118),(122.5,Lp["3V3"][1]),Lp["3V3"]],C["3V3"],1.3); dot((ch["3V3"],x3[1]),C["3V3"])
# GND rail
g=L["GND"]
wire([g,hto(g,ch["GND"]),(ch["GND"],T1["GND"][1]),T1["GND"]],C["GND"],1.3)
for p in [T2["GND "],IM["GND  "],LK["GND   "],VB["GND    "]]: wire([p,hto(p,ch["GND"])],C["GND"],1.3); dot((ch["GND"],p[1]),C["GND"])
wire([(ch["GND"],VB["GND    "][1]),(ch["GND"],17.5)],C["GND"],1.3); dot((ch["GND"],17.5),C["GND"])
wire([(ch["GND"],g[1]),(ch["GND"],116.8),(121.3,116.8),(121.3,Lp["GND"][1]),Lp["GND"]],C["GND"],1.2); dot((ch["GND"],g[1]),C["GND"])
# 5V logic rail: buck -> XIAO 5V ; -> BTS VCC/EN
wire([(31,8),(31,6.5),(59,6.5),(59,L["5V"][1]),L["5V"]],C["5V"],1.8)
wire([(59,L["5V"][1]),(59,54.5),(122,54.5),(122,61.5),(170.6,61.5),(170.6,78.5),(172,78.5)],C["5V"],1.1); dot((59,L["5V"][1]),C["5V"])
wire([(170.6,78.5),(170.6,65.5),(172,65.5)],C["5V"],1.1); dot((170.6,78.5),C["5V"])
ax.text(146,61.9,"5 V → BTS7960 VCC · R_EN · L_EN",fontsize=5.3,color=C["5V"],ha="center",va="bottom")
# UART1 -> servo driver
wire([R["D6  TX1"],hto(R["D6  TX1"],116.5),(116.5,Pd["RX"][1]),Pd["RX"]],C["UART"])
wire([R["D7  RX1"],hto(R["D7  RX1"],117.3),(117.3,Pd["TX"][1]),Pd["TX"]],C["UART"])
# USB to Pi
wire([R["USB-C"],hto(R["USB-C"],119.2),(119.2,Pp["USB-A"][1]),Pp["USB-A"]],C["UART"],1.6)
ax.text(119,66,"USB-C ↔ USB-A",fontsize=5.6,color=C["UART"],ha="left")
# PCA outputs
for k,x,y in [("CH0",169.0,111),("CH1",168.2,102)]:
    wire([Rp[k],hto(Rp[k],x),(x,y),(172,y)],C["SIG"])
for k,x,y in [("CH2",167.4,81.5),("CH3",166.6,79.5),("CH4",165.8,68.5),("CH5",165.0,66.5)]:
    wire([Rp[k],hto(Rp[k],x),(x,y),(172,y)],C["SIG"])
wire([Rp["CH6"],hto(Rp["CH6"],164.6),(164.6,87.2),(135,87.2),(135,76)],C["SIG"],1.2)
wire([Rp["CH7–9"],hto(Rp["CH7–9"],163.8),(163.8,86.6),(150,86.6),(150,76)],C["SIG"],1.2)
# kill -> OE
wire([(162,76),(162,87.4),(138,87.4),(138,Lp["OE"][1]),Lp["OE"]],C["12V"],1.2)
ax.text(147,89.2,"KILL → OE: всички PWM изходи off, хардуерно",fontsize=5.4,color=C["12V"],ha="center",va="bottom")
# 12 V distribution (red), routed below boxes then up the x=125 corridor and the right edge
f=Fo["20 A  thrusters"]; wire([f,hto(f,61),(61,19),(125,19),(125,122.5),(191.5,122.5),(191.5,110.5),(187,110.5)],C["12V"],1.6)
wire([(191.5,110.5),(191.5,101.5),(187,101.5)],C["12V"],1.6); dot((191.5,110.5),C["12V"])
f=Fo["15 A  servo bus"]; wire([f,hto(f,59.8),(59.8,19.6),(105,19.6),(105,Pd["12V"][1]),Pd["12V"]],C["12V"],1.6)
f=Fo["10 A  tracks"]; wire([f,hto(f,61.8),(61.8,18.3),(124.2,18.3),(124.2,62.2),(191.5,62.2),(191.5,78.5),(187,78.5)],C["12V"],1.6)
wire([(191.5,78.5),(191.5,65.5),(187,65.5)],C["12V"],1.6); dot((191.5,78.5),C["12V"])
f=Fo["5 A  Pi"]; wire([f,hto(f,57.2),(57.2,15.8),(123.4,15.8),(123.4,46),(172,46)],C["12V"],1.3)
wire([(172,43.5),(140,43.5),(140,Pp["USB-C PWR"][1]),Pp["USB-C PWR"]],C["5V"],1.6)
# GND bus (bottom) -> servo driver, Pi, BTS, ESC
wire([(60,17.5),(102,17.5),(102,Pd["GND"][1]),Pd["GND"]],C["GND"],1.3)
wire([(102,17.5),(126.5,17.5),(126.5,27),(146,27)],C["GND"],1.3); dot((102,17.5),C["GND"])
wire([(126.5,17.5),(194,17.5),(194,64),(187,64)],C["GND"],1.3); dot((126.5,17.5),C["GND"])
wire([(194,64),(194,77),(187,77)],C["GND"],1.3); dot((194,64),C["GND"])
wire([(194,77),(194,100),(187,100)],C["GND"],1.3); dot((194,77),C["GND"])
wire([(194,100),(194,109),(187,109)],C["GND"],1.3); dot((194,100),C["GND"])
ax.text(149,27.6,"GND",fontsize=5.3,color="#333")
# motor outs (yellow): stubs leaving the module bottoms
for x0 in (176,182):
    wire([(x0,76),(x0,73.5)],C["MOT"],2.2); wire([(x0,63),(x0,60.8)],C["MOT"],2.2)
    wire([(x0,108),(x0,106.2)],C["MOT"],2.2); wire([(x0,99),(x0,97.3)],C["MOT"],2.2)
ax.text(188.6,74.3,"M+ M−",fontsize=5,ha="left",va="center",color="#7a6400")
ax.text(188.6,106.6,"→ prop",fontsize=5,ha="left",va="center",color="#7a6400")
ax.text(100,1.6,"Силовите вериги (thruster-и, серво шина, вериги) идват директно от бушонния блок; през XIAO и PCA9685 минават само сигнали. Обща маса за всички модули. Kill: 50 A ключ на батерията (hardware) + OE на PCA9685 (логика) + ADC стълбица към A1.",
        ha="center",fontsize=6.4,color="#333")
plt.savefig("/mnt/user-data/outputs/AR-Mini_hardware_diagram.png",dpi=150,facecolor="white")
print("saved")
