"""Sheet 3 — the v1 controller on the Olimex ESP32-S3-DevKit-Lipo: no PCA9685, no ADC ladder (enough pins)."""
import bb
from bb import *
I3 = '/home/claude/bom_img3'
img, d = bb.new()

title('AR-Mini  ·  Breadboard 2b  ·  контролер на ESP32-S3-DevKit-Lipo', 'Същият робот, но с Olimex DevKit-Lipo вместо XIAO: 36 свободни GPIO → без PCA9685 и без ADC стълбица. Пиновете по Olimex User Manual rev 2.0 (EXT1 / EXT2 = DevKitC-1 съвместими).')
section((60, 250, 3640, 3440), 'Свързване')

B = Breadboard(900, 1470, cols=63, P=30); B.draw()
BY1 = B.y + B.h
d.text((1330, B.y - 36), 'Релси: (+) = 3V3 (EXT1 пин 1), (−) = GND (пин 22).  5 V от buck-а → EXT1 пин 21.', font=f_small, fill=GREY, anchor='lm')

# ---------- DevKit-Lipo on the board: USB-C to the left, EXT1 (J1) along the top row b, EXT2 (J3) along the bottom row i ----------
C0 = 6   # first column (pin 22 of each header, the USB end)
J1 = ['3V3', '3V3', 'EN', '4', '5', '6', '7', '15', '16', '17', '18', '8', '3', '46', '9', '10', '11', '12', '13', '14', '+5V', 'GND']      # pins 1..22
J3 = ['GND', '43', '44', '1', '2', '42', '41', '40', '39', '38', '37', '36', '35', '0', '45', '48', '47', '21', '20', '19', 'NC', 'GND']   # pins 1..22
def col_of(pin): return C0 + (22 - pin)   # pin 22 at C0, pin 1 at C0 + 21
x0 = B.col_x(C0) - 30; x1 = B.col_x(C0 + 21) + 30; y0 = B.rows['b'] - 26; y1 = B.rows['i'] + 26
d.rounded_rectangle([x0, y0, x1, y1], radius=14, fill=(190, 30, 40), outline=(10, 10, 10), width=3)
for yy in ((y0 + y1) / 2 - 70, (y0 + y1) / 2 + 70):
    d.rounded_rectangle([x0 - 40, yy - 20, x0 + 10, yy + 20], radius=8, fill=(200, 200, 205), outline=(10, 10, 10), width=2)
d.text((x0 - 15, (y0 + y1) / 2 - 70), 'OTG', font=f_pin_s, fill=INK, anchor='mm'); d.text((x0 - 15, (y0 + y1) / 2 + 70), 'UART', font=f_pin_s, fill=INK, anchor='mm')
d.rounded_rectangle([x1 - 260, (y0 + y1) / 2 - 90, x1 - 30, (y0 + y1) / 2 + 90], radius=8, fill=(200, 200, 205), outline=(60, 60, 60), width=2)
d.text((x1 - 145, (y0 + y1) / 2), 'ESP32-S3\nWROOM-1\nN8R8', font=f_pin_s, fill=INK, anchor='mm', align='center')
d.text((x0 + 240, (y0 + y1) / 2 - 30), 'Olimex ESP32-S3-DevKit-Lipo', font=f_pin, fill=WHITE, anchor='mm')
d.text((x0 + 240, (y0 + y1) / 2 + 8), 'EXT1 ↑ (пин 22 … 1) · EXT2 ↓', font=f_pin_s, fill=WHITE, anchor='mm')
d.rounded_rectangle([x0 + 140, (y0 + y1) / 2 + 36, x0 + 200, (y0 + y1) / 2 + 62], radius=4, fill=(230, 230, 230)); d.text((x0 + 170, (y0 + y1) / 2 + 49), 'LiPo', font=f_pin_s, fill=INK, anchor='mm')
XP = {}
def vlabel(x, y, t, up=True, col=INK):
    tt = Image.new('RGBA', (int(f_pin_s.getlength(t)) + 8, 28), (0, 0, 0, 0)); ImageDraw.Draw(tt).text((4, 2), t, font=f_pin_s, fill=col); tt = tt.rotate(90, expand=True)
    img.paste(tt, (int(x - tt.width / 2), int(y - tt.height if up else y)), tt)
for p in range(1, 23):
    c = col_of(p)
    xt, yt = B.hole(c, 'b'); d.rectangle([xt - 9, yt - 9, xt + 9, yt + 9], fill=(220, 200, 120), outline=(60, 50, 20), width=2); XP['J1.' + J1[p - 1] if J1[p - 1] in ('3V3', 'GND') else 'J1.' + J1[p - 1]] = (xt, yt)
    if J1[p - 1] == '3V3': XP['J1.3V3.' + str(p)] = (xt, yt)
    vlabel(xt, yt + 14, J1[p - 1], up=False, col=WHITE)
    xb, yb = B.hole(c, 'i'); d.rectangle([xb - 9, yb - 9, xb + 9, yb + 9], fill=(220, 200, 120), outline=(60, 50, 20), width=2); XP['J3.' + J3[p - 1]] = (xb, yb)
    vlabel(xb, yb - 14, J3[p - 1], up=True, col=WHITE)
num_badge(B.x - 50, B.rows['b'] - 60, 2)
def J1h(name, row): return B.hole(col_of(J1.index(name) + 1), row)
def J3h(name, row): return B.hole(col_of(J3.index(name) + 1), row)

# ---------- modules ----------
d45 = Module(520, 430, 460, 320, 'MLX90642-D45', 'напред · I²C-0 · 0x33', color=PCB_GREEN, pins={'bottom': [('3V3', W_RED), ('GND', W_BLK), ('SDA', W_GRN), ('SCL', W_CYN)]}, pitch=70, photo_path=f'{I3}/r073.png', photo_box=(190, 120), photo_pos='tl', pin_font=f_pin_s); d45.draw()
bno = Module(1060, 430, 460, 320, 'BNO055', 'IMU · I²C-0 · 0x28', color=PCB_BLUE, pins={'bottom': [('VIN', W_RED), ('GND', W_BLK), ('SDA', W_GRN), ('SCL', W_CYN)]}, pitch=70, photo_path=f'{I3}/r075.png', photo_box=(160, 120), photo_pos='tl', pin_font=f_pin_s); bno.draw()
m640 = Module(1600, 430, 460, 320, 'MLX90640 110°', 'люлка · I²C-1 · 0x33', color=PCB_BLUE, pins={'bottom': [('VIN', W_RED), ('GND', W_BLK), ('SDA', W_GRN), ('SCL', W_CYN)]}, pitch=70, photo_path=f'{I3}/r074.png', photo_box=(190, 110), photo_pos='tl', pin_font=f_pin_s); m640.draw()
num_badge(480, 410, 3); num_badge(1560, 410, 4)

# pin-map box where the PCA9685 used to be
PMX, PMY = 2180, 400
d.rounded_rectangle([PMX, PMY, PMX + 1000, PMY + 560], radius=14, fill=(248, 248, 246), outline=LINE, width=3)
d.rectangle([PMX, PMY, PMX + 1000, PMY + 56], fill=(120, 120, 120)); d.text((PMX + 500, PMY + 28), 'Пинове на AR-Mini върху DevKit-Lipo', font=f_pin, fill=WHITE, anchor='mm')
rows = [('I²C-0 (Wire)', 'SDA GPIO48 · SCL GPIO47', 'D45, BNO055 — същите като pUEXT'), ('I²C-1 (Wire1)', 'SDA GPIO8 · SCL GPIO9', 'MLX90640 110°'),
        ('UART1', 'TX GPIO17 · RX GPIO18', 'bus servo adapter'), ('UART2 (v2)', 'TX GPIO15 · RX GPIO16', 'Raspberry Pi 5'),
        ('ESC L / R', 'GPIO1 · GPIO2 (LEDC 50 Hz)', 'thruster-и — не на този стенд'), ('BTS7960 L / R', 'GPIO39/40 · GPIO41/42', 'вериги — не на този стенд'),
        ('ADC', 'VBAT GPIO4 · LEAK GPIO7', 'делител 100 k / 33 k · 10 k pull-up'), ('KILL', 'GPIO14 (pull-up, rocker → GND)', 'софтуерен kill + главен ключ 50 A'),
        ('заети на борда', 'GPIO5 PWR · 6 BAT · 38 LED · 0 BUT', 'не се ползват'), ('не пипай', '35–37 (PSRAM) · 3/45/46 (strap) · 19/20 (USB)', '')]
for i, (a, b_, c) in enumerate(rows):
    yy = PMY + 80 + i * 48
    d.text((PMX + 20, yy), a, font=f_pin, fill=RED_DK); d.text((PMX + 220, yy), b_, font=f_pin, fill=INK); d.text((PMX + 600, yy), c, font=f_pin_s, fill=GREY)
num_badge(PMX - 40, PMY, 5)

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
lp = lipo_icon(3080, 1000); num_badge(3040, 960, 9)
fz = fuse_icon(3260, 1230, value='30 A')
tg = toggle_icon(3330, 1410)
FBX, FBY = 3150, 1680
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
# --- power pins to the rails (free holes: row a above EXT1, row j below EXT2)
wire([J1h('3V3', 'a'), (J1h('3V3', 'a')[0], B.rows['T+'])], W_RED)
wire([J1h('GND', 'a'), (J1h('GND', 'a')[0], B.rows['T-'])], W_BLK)
wire([B.hole(63, 'T+'), (B.x + B.w + 50, B.rows['T+']), (B.x + B.w + 50, B.rows['B+']), B.hole(63, 'B+')], W_RED)
wire([B.hole(63, 'T-'), (B.x + B.w + 90, B.rows['T-']), (B.x + B.w + 90, B.rows['B-']), B.hole(63, 'B-')], W_BLK)
tag(B.x + B.w + 70, B.rows['e'] + 24, '3V3 / GND', W_RED)
# --- I2C-0 taps on the top block (GPIO48 / 47 are on EXT2, bottom row)
SDA0, SCL0 = 33, 36
arc_wire(J3h('48', 'j'), B.hole(SDA0, 'a'), -120, W_GRN, w=7)
arc_wire(J3h('47', 'j'), B.hole(SCL0, 'a'), -160, W_CYN, w=7)
tag(B.col_x(SDA0), B.rows['a'] - 46, 'SDA0 = GPIO48', W_GRN, font=f_pin_s); tag(B.col_x(SCL0) + 60, B.rows['a'] - 86, 'SCL0 = GPIO47', W_CYN, font=f_pin_s)
# --- sensors (above) -> taps and rails
P = d45.P
wire([P['3V3'], (P['3V3'][0], 1000), (B.col_x(3), 1000), B.hole(3, 'T+')], W_RED)
wire([P['GND'], (P['GND'][0], 1030), (B.col_x(4), 1030), B.hole(4, 'T-')], W_BLK)
wire([P['SDA'], (P['SDA'][0], 1300), (B.col_x(SDA0) - 30, 1300), (B.col_x(SDA0) - 30, B.rows['b'] - 6), B.hole(SDA0, 'b')], W_GRN)
wire([P['SCL'], (P['SCL'][0], 1330), (B.col_x(SCL0) - 30, 1330), (B.col_x(SCL0) - 30, B.rows['b'] - 6), B.hole(SCL0, 'b')], W_CYN)
P = bno.P
wire([P['VIN'], (P['VIN'][0], 1060), (B.col_x(30), 1060), B.hole(30, 'T+')], W_RED)
wire([P['GND'], (P['GND'][0], 1090), (B.col_x(31), 1090), B.hole(31, 'T-')], W_BLK)
wire([P['SDA'], (P['SDA'][0], 1240), (B.col_x(SDA0), 1240), B.hole(SDA0, 'c')], W_GRN)
wire([P['SCL'], (P['SCL'][0], 1270), (B.col_x(SCL0), 1270), B.hole(SCL0, 'c')], W_CYN)
# --- I2C-1 straight from EXT1 free holes (GPIO8 SDA, GPIO9 SCL)
P = m640.P
wire([P['VIN'], (P['VIN'][0], 1120), (B.col_x(40), 1120), B.hole(40, 'T+')], W_RED)
wire([P['GND'], (P['GND'][0], 1150), (B.col_x(41), 1150), B.hole(41, 'T-')], W_BLK)
wire([P['SDA'], (P['SDA'][0], 1180), (J1h('8', 'a')[0] + 8, 1180), (J1h('8', 'a')[0] + 8, B.rows['T-'] - 70), (J1h('8', 'a')[0], B.rows['T-'] - 70), J1h('8', 'a')], W_GRN)
wire([P['SCL'], (P['SCL'][0], 1210), (J1h('9', 'a')[0] - 8, 1210), (J1h('9', 'a')[0] - 8, B.rows['T-'] - 100), (J1h('9', 'a')[0], B.rows['T-'] - 100), J1h('9', 'a')], W_CYN)
tag(1990, 1180, 'I²C-1: GPIO8 SDA · GPIO9 SCL', W_GRN, anchor='l')
# --- VBAT divider: GPIO4 (EXT1) -> col 40 bottom block ; LEAK: GPIO7 -> col 48 ; KILL: GPIO14 -> col 58
A0C, VBC, G33, LKN, K10, LKC, KLN, KP = 40, 46, 43, 48, 52, 55, 58, 61
arc_wire(J1h('4', 'a'), B.hole(A0C, 'j'), 190, W_YEL, w=7)
arc_wire(J1h('7', 'a'), B.hole(LKN, 'j'), 240, W_PUR, w=7)
arc_wire(J1h('14', 'a'), B.hole(KLN, 'j'), 290, W_PUR, w=7)
resistor(B.hole(A0C, 'i'), B.hole(VBC, 'i'), '100 k')
resistor(B.hole(A0C, 'g'), B.hole(G33, 'g'), '33 k')
wire([B.hole(G33, 'j'), B.hole(G33, 'B-')], W_BLK, w=7)
resistor(B.hole(LKN, 'g'), B.hole(K10, 'g'), '10 k')
wire([B.hole(K10, 'j'), B.hole(K10, 'B+')], W_RED, w=7)
resistor(B.hole(LKN, 'h'), B.hole(LKC, 'h'), '4.7 k')
resistor(B.hole(KLN, 'g'), B.hole(KP, 'g'), '10 k')
wire([B.hole(KP, 'j'), B.hole(KP, 'B+')], W_RED, w=7)
tag(B.col_x(A0C) - 120, BY1 + 90, 'GPIO4 ← VBAT ÷ 4 (100 k / 33 k)', W_YEL)
tag(B.col_x(LKN) + 80, BY1 + 135, 'GPIO7 ← 10 k към 3V3 · 4.7 k → leak probe → GND', W_PUR)
tag(B.col_x(KLN) + 140, BY1 + 180, 'GPIO14 ← 10 k към 3V3 · rocker → GND', W_PUR)
wire([FB['F4'], (3020, FB['F4'][1]), (3020, BY1 + 230), (B.col_x(VBC), BY1 + 230), B.hole(VBC, 'j')], W_RED, w=9)
tag(2650, BY1 + 230, 'VBAT 12 V (F4) → 100 k', W_RED)
wire([B.hole(LKC, 'j'), (B.col_x(LKC), BY1 + 275), (1300, BY1 + 275), (1300, lk['1'][1]), lk['1']], W_RED)
wire([lk['2'], (1260, lk['2'][1]), (1260, BY1 + 300), (B.col_x(2), BY1 + 300), (B.col_x(2), B.rows['B-'] + 10), B.hole(2, 'B-')], W_BLK)
# rocker: C -> GPIO14 node (col 58 i), KILL side -> GND, RUN side open
wire([rk['C'], (rk['C'][0], 2840), (B.col_x(KLN) - 40, 2840), (B.col_x(KLN) - 40, BY1 + 60), (B.col_x(KLN), BY1 + 60), B.hole(KLN, 'i')], W_PUR)
wire([rk['2'], (rk['2'][0], 2880), (1420, 2880), (1420, BY1 + 330), (B.col_x(4), BY1 + 330), (B.col_x(4), B.rows['B-'] + 20), B.hole(4, 'B-')], W_BLK)
tag(2000, 2840, 'C → GPIO14', W_PUR, anchor='l'); tag(1480, 2880, 'KILL → GND · RUN = свободен', W_BLK, anchor='r')
# --- UART1 to the servo adapter: GPIO17 TX -> RX, GPIO18 RX -> TX (both on EXT1, free holes in row a)
wire([J1h('17', 'a'), (J1h('17', 'a')[0], B.y - 70), (B.x - 60, B.y - 70), (B.x - 60, BY1 + 380), (adp.P['RX'][0] - 70, BY1 + 380), (adp.P['RX'][0] - 70, adp.P['RX'][1]), adp.P['RX']], W_ORG)
wire([J1h('18', 'a'), (J1h('18', 'a')[0], B.y - 100), (B.x - 100, B.y - 100), (B.x - 100, BY1 + 410), (adp.P['TX'][0] - 110, BY1 + 410), (adp.P['TX'][0] - 110, adp.P['TX'][1]), adp.P['TX']], W_YEL)
wire([adp.P['GND'], (adp.P['GND'][0] - 150, adp.P['GND'][1]), (adp.P['GND'][0] - 150, 3120), (1200, 3120), (1200, BY1 + 360), (B.col_x(6), BY1 + 360), (B.col_x(6), B.rows['B-'] + 30), B.hole(6, 'B-')], W_BLK)
tag(1150, BY1 + 380 + 40, 'GPIO17 TX → RX на адаптера · GPIO18 RX ← TX', W_ORG, anchor='l')
wire([adp.P['SRV'], (2940, adp.P['SRV'][1]), (2940, 2910), (2980, 2910)], W_YEL, w=8)
wire([(3220, 2910), (3340, 2910)], W_YEL, w=8)
# --- ESC / BTS labels on the EXT2 free holes
for nm, t in (('1', 'ESC L'), ('2', 'ESC R'), ('39', 'BTS L'), ('41', 'BTS R')):
    x, y = J3h(nm, 'j'); d.ellipse([x - 7, y - 7, x + 7, y + 7], outline=W_BLU, width=3)
tag(B.col_x(col_of(J3.index('2') + 1)) - 80, BY1 + 45, 'GPIO1/2 → ESC · GPIO39–42 → BTS7960 (по-късно)', W_BLU, font=f_pin_s)
# --- power
wire([lp['+'], (3590, lp['+'][1]), (3590, 1270), fz['2']], W_RED, w=13, end=False)
wire([fz['1'], (3200, fz['1'][1]), (3200, 1470), tg['1']], W_RED, w=13)
wire([tg['2'], (3500, tg['2'][1]), (3500, FBY + 490), (FBX + 215, FBY + 490), (FBX + 215, FBY + 460)], W_RED, w=13)
wire([lp['-'], (3620, lp['-'][1]), (3620, 3200), (120, 3200), (120, buck.P['IN−'][1]), buck.P['IN−']], W_BLK, w=11)
wire([(adp_t['12V−'][0], adp_t['12V−'][1]), (adp_t['12V−'][0], 2640), (3040, 2640), (3040, 3200)], W_BLK, w=11, end=False)
tag(3300, 3200, 'обща маса от LiPo −', W_BLK)
wire([FB['F2'], (3080, FB['F2'][1]), (3080, 2620), (adp_t['12V+'][0], 2620), (adp_t['12V+'][0], adp_t['12V+'][1])], W_RED, w=11)
tag(3330, 2400, 'F2 15 A → серво шина', W_RED)
wire([(3020, BY1 + 230), (3020, 3160), (160, 3160), (160, buck.P['IN+'][1]), buck.P['IN+']], W_RED, w=9, start=False)
tag(1700, 3160, 'F4 5 A → buck IN+', W_RED)
# buck OUT+ -> EXT1 +5V (row a) ; OUT- -> rail
wire([buck.P['OUT+'], (790, buck.P['OUT+'][1]), (790, BY1 + 440), (B.x - 140, BY1 + 440), (B.x - 140, B.rows['a'] - 10), J1h('+5V', 'a')], W_RED, w=9)
wire([buck.P['OUT−'], (760, buck.P['OUT−'][1]), (760, BY1 + 470), (B.x - 170, BY1 + 470), (B.x - 170, B.rows['T-'] - 30), B.hole(1, 'T-')], W_BLK, w=9)
tag(B.x - 140, BY1 + 440 - 40, '5 V → EXT1 пин 21 (+5V)', W_RED, anchor='l')
num_badge(B.col_x(C0) - 110, B.rows['a'] - 90, 1)

# ---------- right column ----------
RX = 3700
section((RX, 250, 4900, 3440), 'Стъпки')
y = steps(RX + 30, 350, [
    'DevKit-Lipo на breadboard-а: USB-C конекторите наляво, EXT1 (3V3 … +5V/GND) в ред b, EXT2 (GND, 43, 44 …) в ред i. Остава по един свободен отвор на пин: ред a отгоре, ред j отдолу. Хедърите са запоени фабрично.',
    'Релси: EXT1 пин 1 (3V3) → (+), пин 22 (GND) → (−). Свържи релсите отдясно с два джъмпера.',
    'I²C-0: GPIO48 (SDA) → колона 33, GPIO47 (SCL) → колона 36. На тях: MLX90642-D45 и BNO055. Същите пинове са на pUEXT конектора.',
    'I²C-1: MLX90640 директно на GPIO8 (SDA) и GPIO9 (SCL) — те са на EXT1, ред a.',
    'Няма PCA9685: ESC и BTS7960 ще се карат директно от GPIO1/2 и GPIO39–42 (LEDC). На този стенд остават свободни.',
    'Bus Servo Adapter: GPIO17 (U1TXD) → RX, GPIO18 (U1RXD) → TX, GND → (−). 12V клема: + от F2, − от LiPo −.',
    'Buck MZHOU: IN от F4 и маса; OUT+ → EXT1 пин 21 (+5V, "power in/out"). Премери 4.9–5.2 V преди да го свържеш. Не го дръж включен, докато програмираш по USB.',
    'ADC: GPIO4 ← делител 100 k / 33 k от F4. GPIO7 ← 10 k към 3V3 + 4.7 k към leak probe → GND. GPIO14 ← 10 k към 3V3, rocker C → GPIO14, KILL → GND. GPIO6 е за вградената LiPo на борда — не става за 12 V.',
    'Първо USB-UART в лаптопа БЕЗ LiPo: Arduino → board "OLIMEX ESP32-S3-DevKit-Lipo", I²C скенер → 0x28, 0x33 (Wire), 0x33 (Wire1). После бушони 30 / 15 / 5 A, ключът, LiPo.',
], 1150)
d.line([(RX + 30, y + 10), (4870, y + 10)], fill=(200, 200, 200), width=3); y += 40
d.text((RX + 30, y), 'Какво трябва да видиш', font=f_txt_b, fill=INK); y += 46
y = para(RX + 30, y, '• I²C скенер: 0x28 · 0x33 на Wire(48, 47), 0x33 на Wire1(8, 9).  • GPIO4 ≈ VBAT ÷ 4.  • GPIO7: 3.3 V сухо, ~1.06 V мокро.  • GPIO14: 3.3 V в RUN, 0 V в KILL.  • Зеленият LED на борда (GPIO38, активен на 0) се управлява от скицата.  • ST3215 ID 1 отговаря на ping.', f_small, 1130, GREY)
y += 20; d.text((RX + 30, y), 'Разлики от XIAO варианта', font=f_txt_b, fill=INK); y += 46
y = para(RX + 30, y, 'Без PCA9685, без стълбица на един ADC (всеки сигнал има свой пин), без OE — kill-ът тук е софтуерен (GPIO14) плюс главният ключ 50 A. Ако искаш хардуерен kill на веригите, rocker-ът може да дърпа и R_EN/L_EN на BTS7960 както на Breadboard 1. UART0 (GPIO43/44) остава за USB-UART дебъг. Платката е 1.1" широка → на 830 breadboard пиновете са в редове b и i.', f_small, 1130, GREY)
y += 20; d.text((RX + 30, y), 'Захранване на DevKit-Lipo', font=f_txt_b, fill=INK); y += 46
y = para(RX + 30, y, 'Три входа: USB-UART, USB-OTG, +5V на EXT1 пин 21 (in/out) и собствен LiPo конектор (JST 2.0, 1S — НЕ 3S пакета!). 3V3 изход до 600 mA — стига за двете MLX и BNO055. При програмиране: само USB. При работа: само buck-ът.', f_small, 1130, GREY)
y += 30
legend(RX + 30, y, [(W_RED, '3V3 / 5 V / 12 V'), (W_BLK, 'GND'), (W_GRN, 'SDA'), (W_CYN, 'SCL'), (W_PUR, 'ADC / kill'), (W_YEL, 'VBAT ADC / UART RX'), (W_ORG, 'UART TX'), (W_BLU, 'PWM изходи (по-късно)')], cols=2, colw=560)

d.text((60, H - 60), 'AmphiReach · AR-Mini · Breadboard 2b · 07.10.2026 · T. Kyoseva.  Пинове: Olimex ESP32-S3-DevKit-LiPo User Manual rev 2.0 (GitHub OLIMEX/ESP32-S3-DevKit-Lipo), EXT1/EXT2 = DevKitC-1.', font=f_small, fill=GREY)
img.save('sheet3.png', dpi=(300, 300))
img.resize((W // 3, H // 3), Image.LANCZOS).save('sheet3_prev.png')
print('ok')
