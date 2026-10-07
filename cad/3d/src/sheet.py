import time, armesh as A
from views import shot
from PIL import Image, ImageDraw, ImageFont
FD='/usr/share/fonts/opentype/inter/'
def F(n,s): return ImageFont.truetype(FD+n,s)
t=time.time()
hero_full = shot(A.deploy_a, (-560, 700, 720), (280, 0, 70), 2400, 1500, fov=31, side=-0.45); hero_full.save('hero_deployed.png')
hero = hero_full.resize((2380, 1488), Image.LANCZOS)
rear = shot(A.stow_a, (1300, -760, 640), (320, 0, 95), 1180, 730, fov=30, side=-0.45, dummy=False)
top  = shot(A.deploy_a, (292, 0.01, 3000), (292, 0, 0), 1180, 740, ortho=560, side=0.2)
side = shot(A.deploy_a, (292, 3000, 150), (292, 0, 150), 2380, 980, ortho=390, side=-0.3)
bow  = shot(A.stow_a, (-3000, 0.01, 150), (300, 0, 150), 1180, 980, ortho=560, side=0.3, dummy=False)
print('renders', time.time()-t)
W, H = 3600, 2770
S = Image.new('RGB', (W, H), (255, 255, 255)); d = ImageDraw.Draw(S)
RED = (181, 18, 27); INK = (26, 26, 26); GREY = (105, 105, 105)
d.text((20, 30), 'AR-Mini  ·  3D model', font=F('InterDisplay-Bold.otf', 88), fill=INK)
d.rectangle([20, 138, 20 + F('InterDisplay-Bold.otf', 88).getlength('AR-Mini  ·  3D model'), 145], fill=RED)
d.text((1060, 70), '1:9 demonstrator of AmphiReach  ·  geometry from AR-Mini_v1.scad v1.9 (TD-8120MG preset)  ·  water at the 42 mm design draft  ·  dimensions in mm',
       font=F('Inter-Regular.otf', 34), fill=GREY)
y1 = 170
S.paste(hero, (0, y1)); S.paste(rear, (2400, y1)); S.paste(top, (2400, y1 + 750))
y2 = y1 + 1488 + 20
S.paste(side, (0, y2)); S.paste(bow, (2400, y2))
def cap(x, y, t, sub):
    f1 = F('Inter-Bold.otf', 34); f2 = F('Inter-Regular.otf', 28)
    w = max(f1.getlength(t), f2.getlength(sub)) + 36
    d.rounded_rectangle([x, y, x + w, y + 92], radius=12, fill=(255, 255, 255), outline=(210, 214, 220), width=2)
    d.rectangle([x, y + 10, x + 6, y + 82], fill=RED)
    d.text((x + 20, y + 10), t, font=f1, fill=INK); d.text((x + 20, y + 52), sub, font=f2, fill=GREY)
cap(30, y1 + 24, 'Deployed, Pesho on the cradle', 'arms at 215°, Ø5 rod 34 mm under the waterline')
cap(2420, y1 + 18, 'Stowed, 3/4 rear', 'arms at 45° · thrusters on the transom pads')
cap(2420, y1 + 768, 'Top', 'hull gap 250 · beams at x 385 / 500 · power box on the beams')
cap(30, y2 + 20, 'Side, port', 'draft 42 at 4.7 kg · track bottom flush with the hull bottom')
cap(2420, y2 + 20, 'Bow, stowed', 'width 450 over the hulls')
d.text((20, H - 66), 'Colours: white = PETG hull · black = structure (PLA) · orange = moving parts (PLA) · blue = power box · red = Pesho · silver = aluminium 15 × 15 tube and Ø5 rod.   '
       'ROB0154, thrusters, servos and boxes are stand-ins at measured size.   T. Kyoseva · 06.10.2026', font=F('Inter-Regular.otf', 28), fill=GREY)
S.save('../AR-Mini_3D_renders.png', dpi=(300, 300))
hero_full = Image.open('hero_deployed.png'); hero_full.save('../AR-Mini_3D_hero.png', dpi=(300, 300))
S.resize((W // 3, H // 3), Image.LANCZOS).save('sheet_prev.png')
print('done', time.time()-t)
