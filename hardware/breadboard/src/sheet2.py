"""Sheet 2 — the v1 controller on a breadboard: XIAO ESP32-S3 Sense + PCA9685 + sensors + servo bus + power."""
import bb
from bb import *
I3 = '/home/claude/bom_img3'
img, d = bb.new()

title('AR-Mini  ·  Breadboard 2  ·  контролер v1 на XIAO', 'Същите връзки като на rev 0 breakout платката и carrier rev A, само че на breadboard. Трябват запоени хедъри на XIAO (HS-03) и пратката от 7–9.10: ST3215, buck, MLX90640, BNO055.')
section((60, 250, 3640, 3440), 'Свързване')

B = Breadboard(900, 1470, cols=63, P=30); B.draw()
BY1 = B.y + B.h
d.text((B.x + 20, BY1 + 30), 'Релси: (+) = 3V3 от XIAO, (−) = GND.  5 V от buck-а отива САМО в пин 5V на XIAO и във V+ на PCA9685.', font=f_small, fill=GREY, anchor='lm')

# ---------- XIAO on the board ----------
XC0 = 8
top_row = ['5V', 'GND', '3V3', 'D10', 'D9', 'D8', 'D7']; bot_row = ['D0', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6']
XP = {}
x0 = B.col_x(XC0) - 34; x1 = B.col_x(XC0 + 6) + 34; y0 = B.rows['d'] - 30; y1 = B.rows['h'] + 30
d.rounded_rectangle([x0, y0, x1, y1], radius=14, fill=PCB_BLACK, outline=(10, 10, 10), width=3)
d.rounded_rectangle([x0 - 40, (y0 + y1) / 2 - 22, x0 + 10, (y0 + y1) / 2 + 22], radius=10, fill=(200, 200, 205), outline=(10, 10, 10), width=2)
d.text((x0 - 15, (y0 + y1) / 2), 'USB', font=f_pin_s, fill=INK, anchor='mm')
d.rounded_rectangle([x0 + 60, (y0 + y1) / 2 - 50, x0 + 170, (y0 + y1) / 2 + 50], radius=8, fill=(20, 20, 22), outline=(70, 70, 70), width=2)
d.ellipse([x0 + 90, (y0 + y1) / 2 - 24, x0 + 140, (y0 + y1) / 2 + 26], fill=(10, 10, 30), outline=(120, 120, 120), width=3)
d.text((x1 - 62, (y0 + y1) / 2), 'XIAO\nESP32-S3\nSense', font=f_pin_s, fill=WHITE, anchor='mm', align='center')
for i, nm in enumerate(top_row):
    x, y = B.hole(XC0 + i, 'd'); d.rectangle([x - 9, y - 9, x + 9, y + 9], fill=(220, 200, 120), outline=(60, 50, 20), width=2); XP[nm] = (x, y)
    d.text((x, y0 - 20), nm, font=f_pin_s, fill=INK, anchor='mm')
for i, nm in enumerate(bot_row):
    x, y = B.hole(XC0 + i, 'h'); d.rectangle([x - 9, y - 9, x + 9, y + 9], fill=(220, 200, 120), outline=(60, 50, 20), width=2); XP[nm] = (x, y)
    d.text((x, y1 + 20), nm, font=f_pin_s, fill=INK, anchor='mm')
num_badge(B.x - 50, B.rows['d'] - 60, 2)

# ---------- modules ----------
d45 = Module(520, 430, 460, 320, 'MLX90642-D45', 'напред · I²C-0 · 0x33', color=PCB_GREEN, pins={'bottom': [('3V3', W_RED), ('GND', W_BLK), ('SDA', W_GRN), ('SCL', W_CYN)]}, pitch=70, photo_path=f'{I3}/r073.png', photo_box=(190, 120), photo_pos='tl', pin_font=f_pin_s); d45.draw()
bno = Module(1060, 430, 460, 320, 'BNO055', 'IMU · I²C-0 · 0x28', color=PCB_BLUE, pins={'bottom': [('VIN', W_RED), ('GND', W_BLK), ('SDA', W_GRN), ('SCL', W_CYN)]}, pitch=70, photo_path=f'{I3}/r075.png', photo_box=(160, 120), photo_pos='tl', pin_font=f_pin_s); bno.draw()
m640 = Module(1600, 430, 460, 320, 'MLX90640 110°', 'люлка · I²C-1 · 0x33', color=PCB_BLUE, pins={'bottom': [('VIN', W_RED), ('GND', W_BLK), ('SDA', W_GRN), ('SCL', W_CYN)]}, pitch=70, photo_path=f'{I3}/r074.png', photo_box=(190, 110), photo_pos='tl', pin_font=f_pin_s); m640.draw()
pca = Module(2200, 430, 820, 400, 'PCA9685', '16-ch PWM · I²C-0 · 0x40', color=PCB_BLUE,
             pins={'left': [('GND', W_BLK), ('OE', W_PUR), ('SCL', W_CYN), ('SDA', W_GRN), ('VCC', W_RED), ('V+', None)],
                   'bottom': [('CH0', W_BLU), ('CH1', W_BLU), ('CH2', W_BLU), ('CH3', W_BLU), ('CH4', W_BLU), ('CH5', W_BLU)]},
             pitch=50, photo_path=f'{I3}/r069.png', photo_box=(260, 110), photo_pos='tr', pin_font=f_pin_s); pca.draw()
pca_t = screw_terminal(2860, 480, ['V+', 'GND'], pitch=56, horizontal=True)
d.text((2760, 920), 'CH0 / CH1 → ESC ляв / десен · CH2–CH5 → BTS7960 L / R — не са на този стенд', font=f_small, fill=GREY, anchor='mm')
num_badge(2160, 410, 5); num_badge(480, 410, 3); num_badge(1560, 410, 4)

buck = Module(230, 2700, 460, 260, 'MZHOU buck', '12 → 5 V · 3 A', color=PCB_RED, pins={'left': [('IN+', W_RED), ('IN−', W_BLK)], 'right': [('OUT+', W_RED), ('OUT−', W_BLK)]}, pitch=70, photo_path=f'{I3}/r076.png', photo_box=(150, 100), photo_pos='tr', pin_font=f_pin_s); buck.draw()
num_badge(190, 2680, 7)
adp = Module(2250, 2700, 640, 360, 'Bus Servo Adapter (A)', 'Waveshare · UART → ST3215', color=PCB_BLACK,
             pins={'left': [('RX', W_ORG), ('TX', W_YEL), ('GND', W_BLK)], 'right': [('SRV', None)]}, pitch=60, photo_path=f'{I3}/r072.png', photo_box=(200, 130), photo_pos='tl', pin_font=f_pin_s); adp.draw()
adp_t = screw_terminal(2560, 2755, ['12V+', '12V−'], pitch=66, horizontal=True)
num_badge(2210, 2680, 6)
s1 = servo_icon(2980, 2800, w=240, h=140, label='', photo_path=f'{I3}/r030.png'); d.text((3100, 2985), 'ST3215 · ID 1', font=f_pin, fill=INK, anchor='mm')
s2 = servo_icon(3340, 2800, w=240, h=140, label='', photo_path=f'{I3}/r030.png'); d.text((3460, 2985), 'ST3215 · ID 2', font=f_pin, fill=INK, anchor='mm')
d.text((2960, 3060), '5264 кабели: adapter → ID 1 → ID 2 (→ 3, 4).', font=f_small, fill=GREY, anchor='lm')
d.text((2960, 3094), 'ID-тата се задават през USB-C на адаптера.', font=f_small, fill=GREY, anchor='lm')

rk = rocker_icon(1560, 2560, label='')
d.text((1535, 2610), 'Rocker ON-ON · kill', font=f_pin, fill=INK, anchor='rm')
lk = leak_probe(900, 2620)
num_badge(850, 2560, 8)

# ---------- power chain (right) ----------
lp = lipo_icon(3080, 420); num_badge(3040, 380, 9)
fz = fuse_icon(3260, 650, value='30 A')
tg = toggle_icon(3330, 830)
FBX, FBY = 3150, 1100
d.rounded_rectangle([FBX, FBY, FBX + 430, FBY + 460], radius=14, fill=(40, 40, 42), outline=(10, 10, 10), width=3)
d.text((FBX + 215, FBY + 36), 'Бушонен блок · 6 гнезда', font=f_pin, fill=WHITE, anchor='mm')
FB = {}
for i, (nm, use, on) in enumerate([('F1 20 A', 'ESC ×2', False), ('F2 15 A', 'серво шина', True), ('F3 10 A', 'BTS7960 ×2', False), ('F4 5 A', 'логика (buck + VBAT)', True), ('F5 5 A', 'Pi buck (v2)', False), ('—', 'резерва', False)]):
    y = FBY + 90 + i * 60
    d.rounded_rectangle([FBX + 30, y - 18, FBX + 110, y + 18], radius=5, fill=(230, 60, 60) if on else (120, 120, 120), outline=(10, 10, 10), width=2)
    d.text((FBX + 70, y), nm.split()[0], font=f_pin_s, fill=WHITE, anchor='mm')
    d.text((FBX + 125, y), nm[3:] + ' · ' + use, font=f_pin_s, fill=WHITE if on else (170, 170, 170), anchor='lm')
    d.ellipse([FBX - 14, y - 14, FBX + 14, y + 14], fill=(200, 200, 200), outline=(20, 20, 20), width=2); FB[nm.split()[0]] = (FBX - 14, y)
d.text((FBX + 215, FBY + 440), 'общ вход 12 V от ключа', font=f_pin_s, fill=(200, 200, 200), anchor='mm')
d.text((FBX + 215, FBY + 500), 'сиво = не се ползва на този стенд', font=f_small, fill=GREY, anchor='mm')

# ================= WIRES =================
# --- XIAO power pins to the rails
wire([B.hole(10, 'a'), B.hole(10, 'T+')], W_RED)
wire([B.hole(9, 'a'), B.hole(9, 'T-')], W_BLK)
wire([B.hole(63, 'T+'), (B.x + B.w + 50, B.rows['T+']), (B.x + B.w + 50, B.rows['B+']), B.hole(63, 'B+')], W_RED)
wire([B.hole(63, 'T-'), (B.x + B.w + 90, B.rows['T-']), (B.x + B.w + 90, B.rows['B-']), B.hole(63, 'B-')], W_BLK)
tag(B.x + B.w + 70, B.rows['e'] + 24, '3V3 / GND', W_RED)
# --- I2C taps on the top block (straight jumpers from the XIAO pins)
SDA0, SCL0, SCL1, SDA1 = 17, 20, 27, 30
wire([B.hole(12, 'j'), B.hole(SDA0, 'a')], W_GRN, w=7)
wire([B.hole(13, 'j'), B.hole(SCL0, 'a')], W_CYN, w=7)
wire([B.hole(10, 'j'), B.hole(SCL1, 'a')], W_CYN, w=7)
wire([B.hole(11, 'j'), B.hole(SDA1, 'a')], W_GRN, w=7)
for c, t, col in ((SDA0, 'SDA0', W_GRN), (SCL0, 'SCL0', W_CYN), (SCL1, 'SCL1', W_CYN), (SDA1, 'SDA1', W_GRN)):
    tag(B.col_x(c), B.rows['a'] - 46, t, col, font=f_pin_s)
# --- sensors (above) -> taps and top rails
P = d45.P
wire([P['3V3'], (P['3V3'][0], 1000), (B.col_x(3), 1000), B.hole(3, 'T+')], W_RED)
wire([P['GND'], (P['GND'][0], 1030), (B.col_x(4), 1030), B.hole(4, 'T-')], W_BLK)
wire([P['SDA'], (P['SDA'][0], 1300), (B.col_x(SDA0) - 30, 1300), (B.col_x(SDA0) - 30, B.rows['b'] - 6), B.hole(SDA0, 'b')], W_GRN)
wire([P['SCL'], (P['SCL'][0], 1330), (B.col_x(SCL0) - 30, 1330), (B.col_x(SCL0) - 30, B.rows['b'] - 6), B.hole(SCL0, 'b')], W_CYN)
P = bno.P
wire([P['VIN'], (P['VIN'][0], 1060), (B.col_x(13), 1060), B.hole(13, 'T+')], W_RED)
wire([P['GND'], (P['GND'][0], 1090), (B.col_x(14), 1090), B.hole(14, 'T-')], W_BLK)
wire([P['SDA'], (P['SDA'][0], 1240), (B.col_x(SDA0), 1240), B.hole(SDA0, 'c')], W_GRN)
wire([P['SCL'], (P['SCL'][0], 1270), (B.col_x(SCL0), 1270), B.hole(SCL0, 'c')], W_CYN)
P = m640.P
wire([P['VIN'], (P['VIN'][0], 1120), (B.col_x(25), 1120), B.hole(25, 'T+')], W_RED)
wire([P['GND'], (P['GND'][0], 1150), (B.col_x(26), 1150), B.hole(26, 'T-')], W_BLK)
wire([P['SDA'], (P['SDA'][0], 1180), (B.col_x(SDA1), 1180), B.hole(SDA1, 'b')], W_GRN)
wire([P['SCL'], (P['SCL'][0], 1210), (B.col_x(SCL1), 1210), B.hole(SCL1, 'b')], W_CYN)
# --- PCA9685 -> taps / rails / OE
P = pca.P
wire([P['SDA'], (2140, P['SDA'][1]), (2140, 1360), (B.col_x(SDA0) + 30, 1360), (B.col_x(SDA0) + 30, B.rows['d'] - 6), B.hole(SDA0, 'd')], W_GRN)
wire([P['SCL'], (2110, P['SCL'][1]), (2110, 1390), (B.col_x(SCL0) + 30, 1390), (B.col_x(SCL0) + 30, B.rows['d'] - 6), B.hole(SCL0, 'd')], W_CYN)
wire([P['VCC'], (2080, P['VCC'][1]), (2080, 1420), (B.col_x(40), 1420), B.hole(40, 'T+')], W_RED)
wire([P['GND'], (2050, P['GND'][1]), (2050, 1450), (B.col_x(41), 1450), B.hole(41, 'T-')], W_BLK)
OE_COL = 61
wire([P['OE'], (2170, P['OE'][1]), (2170, 1330), (2900, 1330), (2900, BY1 + 150), (B.col_x(OE_COL), BY1 + 150), B.hole(OE_COL, 'i')], W_PUR)
tag(2900, 1800, 'OE', W_PUR)
# --- ladder on the bottom block (right half)
A0C, VBC, G33, A1C, K10, LKC, KLC = 40, 46, 43, 48, 52, 55, 58
arc_wire(B.hole(8, 'j'), B.hole(A0C, 'j'), 90, W_YEL, w=7)
arc_wire(B.hole(9, 'j'), B.hole(A1C, 'j'), 140, W_PUR, w=7)
resistor(B.hole(A0C, 'i'), B.hole(VBC, 'i'), '100 k')
resistor(B.hole(A0C, 'g'), B.hole(G33, 'g'), '33 k')
wire([B.hole(G33, 'j'), B.hole(G33, 'B-')], W_BLK, w=7)
resistor(B.hole(A1C, 'g'), B.hole(K10, 'g'), '')
wire([B.hole(K10, 'j'), B.hole(K10, 'B+')], W_RED, w=7)
resistor(B.hole(A1C, 'h'), B.hole(LKC, 'h'), '')
resistor(B.hole(A1C, 'i'), B.hole(KLC, 'i'), '')
resistor(B.hole(OE_COL, 'f'), B.hole(OE_COL, 'B+'), '2.2 k')
# tags under the board, aligned to the columns
tag(B.col_x(A0C) - 120, BY1 + 90, 'A0 ← D0: VBAT ÷ 4 (100 k / 33 k)', W_YEL)
tag(B.col_x(A1C) + 60, BY1 + 135, 'A1 ← D1 (колона 48), отгоре надолу: 10 k → 3V3 · 4.7 k → leak · 1 k → KILL', W_PUR)
tag(B.col_x(63) + 20, BY1 + 40, 'колона 61 = OE · 2.2 k към 3V3', W_PUR, anchor='r')
# VBAT (F4) -> col 46 j
wire([FB['F4'], (3020, FB['F4'][1]), (3020, BY1 + 230), (B.col_x(VBC), BY1 + 230), B.hole(VBC, 'j')], W_RED, w=9)
tag(2650, BY1 + 230, 'VBAT 12 V (F4) → 100 k', W_RED)
# leak probe -> col 55 j and GND rail
wire([B.hole(LKC, 'j'), (B.col_x(LKC), BY1 + 190), (1300, BY1 + 190), (1300, lk['1'][1]), lk['1']], W_RED)
wire([lk['2'], (1260, lk['2'][1]), (1260, BY1 + 270), (B.col_x(2), BY1 + 270), (B.col_x(2), B.rows['B-'] + 10), B.hole(2, 'B-')], W_BLK)
# rocker: C -> GND ; 1 RUN -> OE col ; 2 KILL -> col 58
wire([rk['C'], (rk['C'][0], 2840), (1420, 2840), (1420, BY1 + 300), (B.col_x(4), BY1 + 300), (B.col_x(4), B.rows['B-'] + 20), B.hole(4, 'B-')], W_BLK)
wire([rk['1'], (rk['1'][0], 2810), (B.col_x(OE_COL) + 70, 2810), (B.col_x(OE_COL) + 70, BY1 + 110), (B.col_x(OE_COL), BY1 + 110), B.hole(OE_COL, 'j')], W_PUR)
wire([rk['2'], (rk['2'][0], 2870), (B.col_x(KLC) - 40, 2870), (B.col_x(KLC) - 40, BY1 + 60), (B.col_x(KLC), BY1 + 60), B.hole(KLC, 'j')], W_PUR)
tag(2000, 2810, 'RUN → OE на GND', W_PUR, anchor='l'); tag(2000, 2870, 'KILL → A1 през 1 k', W_PUR, anchor='l'); tag(1480, 2840, 'C → GND', W_BLK, anchor='r')
# --- UART to the servo adapter
wire([B.hole(14, 'j'), (B.col_x(14), BY1 + 40), (B.col_x(14) + 160, BY1 + 40), (B.col_x(14) + 160, 2990), (adp.P['RX'][0] - 70, 2990), (adp.P['RX'][0] - 70, adp.P['RX'][1]), adp.P['RX']], W_ORG)
wire([B.hole(14, 'a'), (B.col_x(14), B.y - 70), (B.x - 60, B.y - 70), (B.x - 60, BY1 + 350), (adp.P['TX'][0] - 110, BY1 + 350), (adp.P['TX'][0] - 110, adp.P['TX'][1]), adp.P['TX']], W_YEL)
wire([adp.P['GND'], (adp.P['GND'][0] - 150, adp.P['GND'][1]), (adp.P['GND'][0] - 150, 3120), (1200, 3120), (1200, BY1 + 330), (B.col_x(6), BY1 + 330), (B.col_x(6), B.rows['B-'] + 30), B.hole(6, 'B-')], W_BLK)
tag(1150, 2990, 'D6 TX → RX на адаптера', W_ORG, anchor='l'); tag(1150, BY1 + 350 + 40, 'D7 RX ← TX на адаптера', W_YEL, anchor='l')
wire([adp.P['SRV'], (2940, adp.P['SRV'][1]), (2940, 2910), (2980, 2910)], W_YEL, w=8)
wire([(3220, 2910), (3300, 2910), (3300, 2910), (3340, 2910)], W_YEL, w=8)
# --- power
wire([lp['+'], (3590, lp['+'][1]), (3590, 690), fz['2']], W_RED, w=13, end=False)
wire([fz['1'], (3200, fz['1'][1]), (3200, 890), tg['1']], W_RED, w=13)
wire([tg['2'], (3500, tg['2'][1]), (3500, FBY + 490), (FBX + 215, FBY + 490), (FBX + 215, FBY + 460)], W_RED, w=13)
wire([lp['-'], (3620, lp['-'][1]), (3620, 3200), (120, 3200), (120, buck.P['IN−'][1]), buck.P['IN−']], W_BLK, w=11)
wire([(3620, 3200), (3620, 3230)], W_BLK, w=11, start=False, end=False)
wire([(adp_t['12V−'][0], adp_t['12V−'][1]), (adp_t['12V−'][0], 2640), (3040, 2640), (3040, 3200)], W_BLK, w=11, end=False)
tag(3300, 3200, 'обща маса от LiPo −', W_BLK)
wire([FB['F2'], (3080, FB['F2'][1]), (3080, 2620), (adp_t['12V+'][0], 2620), (adp_t['12V+'][0], adp_t['12V+'][1])], W_RED, w=11)
tag(3330, 2400, 'F2 15 A → серво шина', W_RED)
wire([FB['F4'], (3020, FB['F4'][1])], W_RED, w=9, end=False)
wire([(3020, BY1 + 230), (3020, 3160), (160, 3160), (160, buck.P['IN+'][1]), buck.P['IN+']], W_RED, w=9, start=False)
tag(1700, 3160, 'F4 5 A → buck IN+', W_RED)
# buck OUT+ -> XIAO 5V (col 8 a) + PCA V+ ; OUT- -> rail
wire([buck.P['OUT+'], (790, buck.P['OUT+'][1]), (790, BY1 + 400), (B.x - 120, BY1 + 400), (B.x - 120, B.rows['a'] - 10), B.hole(8, 'a')], W_RED, w=9)
wire([(790, BY1 + 400), (790, BY1 + 470), (2960, BY1 + 470), (2960, 1000), (pca_t['V+'][0], 1000), pca_t['V+']], W_RED, w=9, start=False)
wire([buck.P['OUT−'], (760, buck.P['OUT−'][1]), (760, BY1 + 430), (B.x - 90, BY1 + 430), (B.x - 90, B.rows['T-'] - 30), B.hole(1, 'T-')], W_BLK, w=9)
wire([pca_t['GND'], (pca_t['GND'][0], 1030), (B.col_x(52), 1030), B.hole(52, 'T-')], W_BLK, w=7)
tag(1900, BY1 + 470, '5 V от buck-а → V+ на PCA9685', W_RED); tag(B.x - 120, BY1 + 400 - 40, '5 V → пин 5V на XIAO', W_RED, anchor='l')
num_badge(B.col_x(8) - 110, B.rows['a'] - 90, 1)

# ---------- right column ----------
RX = 3700
section((RX, 250, 4900, 3440), 'Стъпки')
y = steps(RX + 30, 350, [
    'Запои хедърите на XIAO (сандвич: мъжки в женски в платка, една ъглова спойка, провери, после останалите). Сложи го на breadboard-а с USB-C наляво, пинове в редове d и h.',
    'Релси: 3V3 (ред a, колона 10) → (+), GND (колона 9) → (−). Свържи релсите отдясно с два джъмпера.',
    'I²C-0: D4 → колона 17 (SDA0), D5 → колона 20 (SCL0). На тях: MLX90642-D45, BNO055, PCA9685 (SDA, SCL; VCC = 3V3, GND).',
    'I²C-1: D2 → колона 27 (SCL1), D3 → колона 30 (SDA1) → MLX90640. Двете MLX са на адрес 0x33 — затова са на два отделни буса.',
    'PCA9685: OE → колона 61 (2.2 k към 3V3). V+ и GND на клемата → от buck-а (5 V). CH0–5 остават свободни на този стенд.',
    'Bus Servo Adapter: XIAO D6 → RX, D7 → TX, GND → (−). 12V клема: + от F2, − от LiPo −. ST3215 на 5264 кабел; ID през USB-C на адаптера.',
    'Buck MZHOU: IN от F4 и маса; OUT+ → пин 5V на XIAO и клемата V+ на PCA9685. Премери OUT: 4.9–5.2 V, преди да го свържеш.',
    'Стълбица: D0 → колона 40 (100 k / 33 k към 12 V и GND); D1 → колона 48 (10 k към 3V3, 4.7 k → leak probe → GND, 1 k → rocker KILL). Rocker C → GND, RUN → колона 61. Нямаш ли 100 k / 33 k: 10 k / 3.3 k от кита е същото ÷ 4.',
    'Първо USB в XIAO БЕЗ LiPo: I²C скенер в Serial трябва да намери 0x28, 0x33, 0x40 (Wire) и 0x33 (Wire1). Чак после: бушони 30 / 15 / 5 A, ключът, LiPo.',
], 1150)
d.line([(RX + 30, y + 10), (4870, y + 10)], fill=(200, 200, 200), width=3); y += 40
d.text((RX + 30, y), 'Какво трябва да видиш', font=f_txt_b, fill=INK); y += 46
y = para(RX + 30, y, '• I²C скенер: 0x28 · 0x33 · 0x40 на Wire, 0x33 на Wire1.  • A0 ≈ VBAT ÷ 4 (12.4 V → 3.1 V).  • A1: 3.3 V; с мокри жила 1.06 V; rocker на KILL → 0.3 V и всички PCA9685 канали гаснат.  • ST3215 ID 1 отговаря на ping през адаптера.', f_small, 1130, GREY)
y += 20; d.text((RX + 30, y), 'Защо така', font=f_txt_b, fill=INK); y += 46
y = para(RX + 30, y, 'Това е 1:1 схемата на rev 0 breakout-а + carrier rev A: същите пинове, същите стойности. Заработи ли на breadboard, платката е проверена. Една разлика от spec-а §5: R10 е pull-up 2.2 k към 3V3 (не 10 k към GND) и rocker-ът дърпа OE към GND в RUN — падне ли му кабелът, моторите спират сами. 2.2 k, защото модулът има 10 k pull-down на OE.', f_small, 1130, GREY)
y += 20; d.text((RX + 30, y), 'Не е на този стенд', font=f_txt_b, fill=INK); y += 46
y = para(RX + 30, y, 'ESC-тата и thruster-ите (CH0/1), BTS7960 (CH2–5 — виж Breadboard 1), Pi 5 и QIQIAZI buck-ът (v2), камерата OV3660 (на самото XIAO). Моторите се добавят последни, когато стълбицата и kill-ът вече работят.', f_small, 1130, GREY)
y += 30
legend(RX + 30, y, [(W_RED, '3V3 / 5 V / 12 V'), (W_BLK, 'GND'), (W_GRN, 'SDA'), (W_CYN, 'SCL'), (W_PUR, 'OE / стълбица A1'), (W_YEL, 'A0 / UART TX'), (W_ORG, 'UART RX'), (W_BLU, 'PWM канали')], cols=2, colw=560)

d.text((60, H - 60), 'AmphiReach · AR-Mini · Breadboard 2 · 07.10.2026 · T. Kyoseva.  Стойности от AR-Mini_carrier_revA_spec.md §5; пинове от PINOUT.md.', font=f_small, fill=GREY)
img.save('sheet2.png', dpi=(300, 300))
img.resize((W // 3, H // 3), Image.LANCZOS).save('sheet2_prev.png')
print('ok')
