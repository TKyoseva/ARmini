from PIL import Image, ImageDraw, ImageFont
import trimesh
exec(open('parts.py').read())
F='/usr/share/fonts/truetype/dejavu/'
def f(sz,b=False): return ImageFont.truetype(F+('DejaVuSans-Bold.ttf' if b else 'DejaVuSans.ttf'),sz)
info={p[0]:p for p in P}
ORDER=['hull_fore','arm_drive','arm_idler','coupler','hull_aft','pivot_bracket','arch_post','pesho','pesho_lid',
 'thruster_bracket','thruster_arm','beam_bracket','cam_fixed_mount','beam_leg','rudder_mount','rudder_blade','rudder_hub','rudder_frame']
W=2400; PAD=40; BG='#eef2f6'
COLS=6; TW=(W-PAD*(COLS+1))//COLS; TH=300; TXT=150
def ext(n):
    if n=='pesho': return '155 × 84 × 186'
    e=trimesh.load('out/stl/'+n+'.stl').extents
    return ' × '.join(f'{v:.0f}' for v in e)
def label(n):
    if n=='pesho': return ('Pesho body + head ×1','C039 · red PLA + white PETG','4 h 44 · 143 g (body)')
    nm,_,q,card,mat,_,note=info[n]
    return (f'{nm} ×{q}',f'{card} · {mat}',note)
HERO_H=860
rows=(len(ORDER)+COLS-1)//COLS
Ht=100+30+HERO_H+30+rows*(TH+TXT+20)+20+150
can=Image.new('RGB',(W,Ht),'white'); d=ImageDraw.Draw(can)
d.rectangle([0,0,W,100],fill='#16324f'); d.text((PAD,26),'P26  Every part I printed',fill='white',font=f(44,True))
st='COMPLETE'; tw=d.textlength(st,font=f(30,True)); d.rectangle([W-PAD-tw-30,24,W-PAD,76],fill='#2e7d32'); d.text((W-PAD-tw-15,32),st,fill='white',font=f(30,True))
# hero
y=130; HW=1440
d.rounded_rectangle([PAD,y,PAD+HW,y+HERO_H],18,fill=BG)
h=Image.open('r/_hero.png').convert('RGBA'); s=min((HW-20)/h.width,(HERO_H-20)/h.height); h=h.resize((int(h.width*s),int(h.height*s)),Image.LANCZOS)
can.paste(h,(PAD+(HW-h.width)//2,y+(HERO_H-h.height)//2),h)
d.text((PAD+24,y+20),'All 19 models, laid out as in the Fusion 360 file (615 × 431 mm)',fill='#445',font=f(26))
# stats panel
x0=PAD*2+HW; xw=W-PAD-x0
stats=[('19','different models'),('36','parts off the bed'),('15','print jobs, 10.10 → 29.10.2026'),('≈ 55 h','of printing'),('2.39 kg','PLA + PETG, with supports')]
yy=y+10
for big,small in stats:
    d.text((x0+10,yy),big,fill='#16324f',font=f(78,True)); bw=d.textlength(big,font=f(78,True))
    d.text((x0+24+bw,yy+38),small,fill='#333',font=f(30)); yy+=118
yy+=12; d.line([x0+10,yy,x0+xw,yy],fill='#bbb',width=2); yy+=20
for txt in ['PLA for dry fit parts and brackets','PETG (240–250 °C) for anything that gets wet','One Creality K2 Pro, one spool at a time','Colours in the renders = the filament used']:
    d.ellipse([x0+18,yy+14,x0+30,yy+26],fill='#16324f'); d.text((x0+48,yy),txt,fill='#222',font=f(28)); yy+=46
# grid
y0=y+HERO_H+30
for i,n in enumerate(ORDER):
    r,c=divmod(i,COLS); x=PAD+c*(TW+PAD); yt=y0+r*(TH+TXT+20)
    d.rounded_rectangle([x,yt,x+TW,yt+TH],14,fill=BG)
    im=Image.open(f'r/{n}.png').convert('RGBA'); s=min((TW-16)/im.width,(TH-16)/im.height); im=im.resize((int(im.width*s),int(im.height*s)),Image.LANCZOS)
    can.paste(im,(x+(TW-im.width)//2,yt+(TH-im.height)//2),im)
    a,b,cc=label(n); ty=yt+TH+10
    d.text((x+4,ty),a,fill='#111',font=f(26,True)); ty+=36
    d.text((x+4,ty),b,fill='#333',font=f(22)); ty+=30
    d.text((x+4,ty),ext(n)+' mm',fill='#333',font=f(22)); ty+=30
    d.text((x+4,ty),cc,fill='#555',font=f(20))
yy=y0+rows*(TH+TXT+20)+4
d.line([PAD,yy,W-PAD,yy],fill='#bbb',width=2); yy+=14
foot=('Every part was modelled in OpenSCAD (parametric, with AI help) from my caliper measurements, then printed, cleaned, fitted and tested by me. '
      'Times and grams are read from the printer-screen photos and include supports and brim. Right-hand hulls and brackets are the same file mirrored. '
      'thruster_coupon was designed but skipped; rudder_mount failed to fit and was replaced by rudder_frame. Cards C008–C057.')
import textwrap
def wrap(t,font,mw):
    out=[];line=''
    for w in t.split(' '):
        tt=(line+' '+w).strip()
        if d.textlength(tt,font=font)<=mw: line=tt
        else: out.append(line); line=w
    return out+[line]
for l in wrap(foot,f(30),W-2*PAD): d.text((PAD,yy),l,fill='#333',font=f(30)); yy+=42
can=can.crop((0,0,W,yy+30))
can.save('P26_every-part-i-printed.jpg',quality=90); print(can.size)
