"""Sheet 1 — motor & servo bench on the Mega 2560 (what is on the table on 7.10, no soldering)."""
import bb
from bb import *
I3 = '/home/claude/bom_img3'
img, d = bb.new()

title('AR-Mini  ·  Breadboard 1  ·  стенд за мотор и серво', 'Първата електроника: Arduino Mega 2560 (Joy-IT кита) + BTS7960 + един мотор на ROB0154 + TD-8120MG. Без запояване. Всичко е на масата на 07.10.2026.')

# ---------- drawing area ----------
section((60, 250, 3640, 3440), 'Свързване')
# breadboard
B = Breadboard(1230, 420, cols=63, P=30); B.draw()
d.text((B.x + B.w / 2, B.y + B.h + 30), 'Breadboard 830 (от Freenove / Joy-IT кита) — горните релси = серво захранване 5–6 V, долните = 5 V на Mega-та. Двете маси (−) са свързани с един черен джъмпер.', font=f_small, fill=GREY, anchor='mm')

# ---------- Mega 2560 ----------
MX, MY, MW, MH = 180, 1500, 1180, 620
d.rounded_rectangle([MX, MY, MX + MW, MY + MH], radius=22, fill=PCB_BLUE, outline=(20, 20, 20), width=3)
d.text((MX + MW / 2, MY + MH / 2 - 10), 'Arduino Mega 2560', font=f_hdr, fill=WHITE, anchor='mm')
d.text((MX + MW / 2, MY + MH / 2 + 40), 'от Joy-IT ARD-Set01 · USB към лаптопа · 5 V от USB-то', font=f_small, fill=WHITE, anchor='mm')
# USB jack
d.rectangle([MX - 30, MY + 60, MX + 40, MY + 150], fill=(200, 200, 205), outline=(20, 20, 20), width=2); d.text((MX + 5, MY + 105), 'USB', font=f_pin_s, fill=INK, anchor='mm')
d.rectangle([MX - 30, MY + 200, MX + 40, MY + 280], fill=(40, 40, 42), outline=(20, 20, 20), width=2); d.text((MX + 5, MY + 240), 'DC', font=f_pin_s, fill=WHITE, anchor='mm')
# top header (digital) — labels right-to-left like the real board
MP = {}
top_names = ['SCL', 'SDA', 'AREF', 'GND', '13', '12', '11', '10', '9', '8', '', '7', '6', '5', '4', '3', '2', '1', '0']
for i, nm in enumerate(top_names):
    x = MX + 170 + i * 44
    if nm == '': continue
    d.rectangle([x - 12, MY - 10, x + 12, MY + 22], fill=(40, 40, 42), outline=(20, 20, 20), width=2)
    d.rectangle([x - 5, MY - 3, x + 5, MY + 15], fill=(200, 200, 200))
    t = Image.new('RGBA', (70, 26), (0, 0, 0, 0)); ImageDraw.Draw(t).text((0, 0), nm, font=f_pin_s, fill=WHITE); t = t.rotate(-90, expand=True)
    img.paste(t, (int(x - 13), int(MY + 30)), t)
    MP['D' + nm if nm.isdigit() else nm] = (x, MY - 10)
# bottom-left power header
pw_names = ['IOREF', 'RESET', '3V3', '5V', 'GND', 'GND', 'VIN']
for i, nm in enumerate(pw_names):
    x = MX + 300 + i * 44
    d.rectangle([x - 12, MY + MH - 22, x + 12, MY + MH + 10], fill=(40, 40, 42), outline=(20, 20, 20), width=2)
    d.rectangle([x - 5, MY + MH - 15, x + 5, MY + MH + 3], fill=(200, 200, 200))
    t = Image.new('RGBA', (90, 26), (0, 0, 0, 0)); ImageDraw.Draw(t).text((0, 0), nm, font=f_pin_s, fill=WHITE); t = t.rotate(90, expand=True)
    img.paste(t, (int(x - 13), int(MY + MH - 40 - 90)), t)
    MP[nm + ('_' + str(i) if nm == 'GND' else '')] = (x, MY + MH + 10)
d.text((MX + 300 + 3 * 44, MY + MH - 150), 'POWER', font=f_pin_s, fill=WHITE, anchor='mm')
# analog header
for i in range(8):
    x = MX + 680 + i * 44; nm = f'A{i}'
    d.rectangle([x - 12, MY + MH - 22, x + 12, MY + MH + 10], fill=(40, 40, 42), outline=(20, 20, 20), width=2)
    d.rectangle([x - 5, MY + MH - 15, x + 5, MY + MH + 3], fill=(200, 200, 200))
    d.text((x, MY + MH - 42), nm, font=f_pin_s, fill=WHITE, anchor='mm'); MP[nm] = (x, MY + MH + 10)
d.text((MX + 680 + 3.5 * 44, MY + MH - 150), 'ANALOG IN', font=f_pin_s, fill=WHITE, anchor='mm')
p = photo('/home/claude/bom_img/row05.png', 230, 170); d.rectangle([MX + MW - p.width - 20, MY + 110, MX + MW - 12, MY + 118 + p.height], fill=WHITE); img.paste(p, (MX + MW - p.width - 16, MY + 114))

# ---------- servo ----------
sv_exit = servo_icon(300, 700, label='', photo_path=f'{I3}/r031.png')
d.text((460, 560), 'Серво TD-8120MG (20 kg)', font=f_mod, fill=INK, anchor='mm')
d.text((430, 900), 'кафяво = GND · червено = + · оранжево = сигнал', font=f_small, fill=GREY, anchor='mm')
num_badge(170, 560, 4)

# ---------- power bank for the servo ----------
d.rounded_rectangle([880, 400, 1120, 560], radius=14, fill=(60, 60, 64), outline=(20, 20, 20), width=3)
d.text((1000, 440), 'USB power bank', font=f_pin, fill=WHITE, anchor='mm'); d.text((1000, 480), '5 V · ≥ 2 A', font=f_pin, fill=WHITE, anchor='mm'); d.text((1000, 525), '(или MZHOU buck, 7–9.10)', font=f_pin_s, fill=(220, 220, 220), anchor='mm')
d.text((1000, 585), 'стар USB кабел с оголени краища', font=f_pin_s, fill=GREY, anchor='mm')
num_badge(850, 400, 8)

# ---------- BTS7960 ----------
bts = Module(2700, 1560, 520, 420, 'BTS7960', '43 A H-bridge', color=PCB_BLUE,
             pins={'left': [('RPWM', W_BLU), ('LPWM', W_BLU), ('R_EN', W_PUR), ('L_EN', W_PUR), ('R_IS', None), ('L_IS', None), ('VCC', W_RED), ('GND', W_BLK)]},
             pitch=46, photo_path=f'{I3}/r071.png', photo_box=(200, 160), photo_pos='tr'); bts.draw()
st = screw_terminal(3300, 1600, ['B+', 'B−', 'M+', 'M−'], pitch=60, horizontal=False, color=(40, 140, 60))
d.text((2960, 2020), 'винтови клеми: B = батерия, M = мотор', font=f_small, fill=GREY, anchor='mm')

# ---------- motor ----------
mot = motor_icon(3380, 2200, '')
d.text((3455, 2090), 'ROB0154 · ляв мотор', font=f_pin, fill=INK, anchor='mm')
num_badge(3250, 2090, 6)
# ---------- battery chain ----------
lp = lipo_icon(1500, 2850)
num_badge(1460, 2810, 9)
fz = fuse_icon(2080, 2885, value='10 A')
tg = toggle_icon(2420, 2855)
# ---------- rocker ----------
rk = rocker_icon(2380, 1640, label='')
d.text((2435, 1600), 'Rocker ON-ON', font=f_pin, fill=INK, anchor='mm')

# ---------- pot ----------
pot = pot_on_board(B, 50, 'g')

# ================= WIRES =================
# Mega 5V / GND -> bottom rails
wire([MP['5V'], (MP['5V'][0], 2230), (1420, 2230), (1420, 1230), (B.col_x(3), 1230), B.hole(3, 'B+')], W_RED)
wire([MP['GND_4'], (MP['GND_4'][0], 2270), (1460, 2270), (1460, 1260), (B.col_x(2), 1260), B.hole(2, 'B-')], W_BLK)
num_badge(120, 1460, 2)
# tie the two GND rails (common ground)
wire([B.hole(63, 'B-'), (B.hole(63, 'B-')[0] + 60, B.rows['B-']), (B.hole(63, 'B-')[0] + 60, B.rows['T-']), B.hole(63, 'T-')], W_BLK)
tag(B.x + B.w + 160, (B.rows['B-'] + B.rows['T-']) / 2 + 60, 'обща маса', W_BLK)
# power bank -> top rails
wire([(1120, 440), (1200, 440), (1200, B.rows['T+']), B.hole(2, 'T+')], W_RED)
wire([(1120, 500), (1170, 500), (1170, B.rows['T-']), B.hole(1, 'T-')], W_BLK)
# servo cable -> top rails and D9 via column 8
sx, sy = sv_exit
wire([(sx, sy), (sx + 60, sy), (sx + 60, 1120), (B.col_x(6), 1120), B.hole(6, 'T-')], W_BRN)
wire([(sx, sy + 14), (sx + 90, sy + 14), (sx + 90, 1150), (B.col_x(7), 1150), B.hole(7, 'T+')], W_RED)
wire([(sx, sy + 28), (sx + 120, sy + 28), (sx + 120, 1180), (B.col_x(10), 1180), B.hole(10, 'a')], W_ORG)
wire([B.hole(10, 'e'), (B.col_x(10), 1440), (MP['D9'][0], 1440), MP['D9']], W_ORG)
tag(B.col_x(10) + 60, 1440, 'D9 → серво сигнал', W_ORG, anchor='l')
# pot: 1 -> B+, 3 -> B-, W -> A0
wire([pot['1'], (pot['1'][0], B.rows['B+'])], W_RED)
wire([pot['3'], (pot['3'][0], B.rows['B-'])], W_BLK)
wire([B.hole(51, 'j'), (B.col_x(51), 1330), (1500, 1330), (1500, 2310), (MP['A0'][0], 2310), MP['A0']], W_YEL)
tag(1700, 1330, 'A0 ← потенциометър (скорост + посока)', W_YEL, anchor='l')
num_badge(B.col_x(51) - 230, B.rows['g'] - 170, 3)
# BTS header -> Mega / rails
P = bts.P
wire([P['RPWM'], (2500, P['RPWM'][1]), (2500, 1400), (MP['D5'][0], 1400), MP['D5']], W_BLU)
wire([P['LPWM'], (2530, P['LPWM'][1]), (2530, 1370), (MP['D6'][0], 1370), MP['D6']], W_BLU)
tag(1900, 1400, 'D5 → RPWM · D6 → LPWM', W_BLU)
# R_EN + L_EN -> rocker C (via column 40 a-e)
wire([P['R_EN'], (2560, P['R_EN'][1]), (2560, 1240), (B.col_x(40), 1240), B.hole(40, 'j')], W_PUR)
wire([P['L_EN'], (2590, P['L_EN'][1]), (2590, 1270), (B.col_x(41), 1270), B.hole(41, 'j')], W_PUR)
wire([B.hole(40, 'f'), B.hole(41, 'f')], W_PUR, w=7)
wire([B.hole(40, 'i'), (B.col_x(40), 1300), (2300, 1300), (2300, 1920), (rk['C'][0], 1920), rk['C']], W_PUR)
wire([rk['1'], (rk['1'][0], 1960), (2260, 1960), (2260, 1210), (B.col_x(36), 1210), B.hole(36, 'B+')], W_RED)
wire([rk['2'], (rk['2'][0], 1990), (2340, 1990), (2340, 1330), (B.col_x(44), 1330), B.hole(44, 'B-')], W_BLK)
tag(1890, 1240, 'колона 40: R_EN + L_EN → C', W_PUR, anchor='l'); tag(2220, 1960, 'RUN = 5 V', W_RED, anchor='r'); tag(2560, 1990, 'KILL = GND', W_BLK, anchor='l')
num_badge(2200, 1560, 5)
# VCC / GND
wire([P['VCC'], (2620, P['VCC'][1]), (2620, 1160), (B.col_x(47), 1160), B.hole(47, 'B+')], W_RED)
wire([P['GND'], (2650, P['GND'][1]), (2650, 1190), (B.col_x(48), 1190), B.hole(48, 'B-')], W_BLK)
num_badge(2660, 1520, 5)
# battery chain
wire([lp['+'], (1990, lp['+'][1]), (1990, fz['1'][1]), fz['1']], W_RED, w=13)
wire([fz['2'], tg['1']], W_RED, w=13)
wire([tg['2'], (2620, tg['2'][1]), (2620, 2500), (3240, 2500), (3240, st['B+'][1]), st['B+']], W_RED, w=13)
wire([lp['-'], (1960, lp['-'][1]), (1960, 3120), (3200, 3120), (3200, st['B−'][1]), st['B−']], W_BLK, w=13)
# motor
wire([st['M+'], (3300, st['M+'][1]), (3300, 2520), (mot['1'][0], 2520), mot['1']], W_YEL, w=11)
wire([st['M−'], (3270, st['M−'][1]), (3270, 2560), (mot['2'][0], 2560), mot['2']], W_YEL, w=11)
d.text((2500, 2740), 'B− е свързано с GND на модула → масата на батерията е общата маса', font=f_small, fill=GREY, anchor='mm')
d.text((1500, 3080), 'LiPo се включва ПОСЛЕДНА и само с бушон 10 A; за проба без мотор — въобще не я включвай', font=f_small, fill=RED_DK)

# ---------- right column ----------
RX = 3700
section((RX, 250, 4900, 3440), 'Стъпки')
y = steps(RX + 30, 350, [
    'Всичко е изключено: USB-то на Mega-та не е в лаптопа, power bank-ът е откачен, LiPo-то е в торбата.',
    'Сложи Mega-та и breadboard-а на ESD подложката. Червен джъмпер 5V → долна (+) релса, черен GND → долна (−) релса.',
    'Потенциометърът на колони 50–52, ред g: крайните пинове към + и − релсата, средният → A0.',
    'Сервото: кафяво → горна (−), червено → горна (+), оранжево → колона 10 → D9. Един черен джъмпер между двете (−) релси (обща маса!).',
    'BTS7960: VCC → долна (+), GND → долна (−), RPWM → D5, LPWM → D6. R_EN и L_EN заедно → C на rocker-а; 1 → +, 2 → −.',
    'Клемите: M+ / M− към двата проводника на левия мотор на ROB0154. B+ / B− остават празни засега.',
    'Качи bench_v1.ino. USB в лаптопа → Serial Monitor 115200. Въртиш потенциометъра → цифрите се сменят. Сервото още не мърда (няма power bank).',
    'Включи power bank-а в горните релси → сервото следва потенциометъра. Ако Mega-та се рестартира, захранването е слабо.',
    'Сложи бушон 10 A в GT4652. Верига: LiPo + → бушон → ключ → B+; LiPo − → B−. Ключът е OFF. Включи LiPo-то.',
    'Rocker на RUN, ключът ON. В средата на потенциометъра моторът стои; наляво = назад, надясно = напред. Rocker на KILL → моторът спира веднага, Mega-та работи.',
], 1150)
d.line([(RX + 30, y + 10), (4870, y + 10)], fill=(200, 200, 200), width=3); y += 40
d.text((RX + 30, y), 'Проверка с мултиметъра преди LiPo-то', font=f_txt_b, fill=INK); y += 46
y = para(RX + 30, y, '• Ω между B+ и B− на BTS7960: не трябва да е ~0 Ω.  • Ω между + и − на долната релса: не трябва да е ~0 Ω.  • V на горната релса с power bank: 4.8–5.2 V.', f_small, 1130, GREY)
y += 20; d.text((RX + 30, y), 'В bench_v1.ino', font=f_txt_b, fill=INK); y += 46
y = para(RX + 30, y, 'D9 = серво (Servo.h) · D5 = RPWM · D6 = LPWM · A0 = потенциометър. 512 ± 25 = стоп. Serial печата pot / PWM / ъгъл 10 пъти в секунда — това е първият CSV лог на проекта.', f_small, 1130, GREY)
y += 20; d.text((RX + 30, y), 'Какво НЕ е тук (идва на Breadboard 2)', font=f_txt_b, fill=INK); y += 46
y = para(RX + 30, y, 'XIAO (трябват запоени хедъри → HS-03), PCA9685, ST3215 + bus servo adapter, термокамерите, BNO055, buck-овете, thruster-ът (първо мултиметър: ESC или само мотор).', f_small, 1130, GREY)
y += 30
legend(RX + 30, y, [(W_RED, '5 V / +'), (W_BLK, 'GND / −'), (W_ORG, 'серво сигнал'), (W_BLU, 'PWM към BTS7960'), (W_PUR, 'enable (kill)'), (W_YEL, 'аналогов / мотор'), (W_BRN, 'серво GND (кафяво)'), ((214, 40, 40), 'дебело = 12 V LiPo')], cols=2, colw=560)

d.text((60, H - 60), 'AmphiReach · AR-Mini · Breadboard 1 · 07.10.2026 · T. Kyoseva.  Ако нещо се нагрее, замирише или Mega-та се рестартира: ключът OFF, после всичко останало.', font=f_small, fill=GREY)
img.save('sheet1.png', dpi=(300, 300))
img.resize((W // 3, H // 3), Image.LANCZOS).save('sheet1_prev.png')
print('ok')
