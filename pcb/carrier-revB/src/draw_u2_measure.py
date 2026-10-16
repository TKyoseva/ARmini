import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch, FancyBboxPatch
import matplotlib.font_manager as fm

fig = plt.figure(figsize=(13, 9.2), dpi=150)
ax = fig.add_axes([0.03, 0.30, 0.94, 0.66])
ax.set_aspect('equal'); ax.axis('off')
# board 62 x 25.4 (typical Adafruit-style layout, drawn schematically)
L, W = 62.0, 25.4
ax.add_patch(FancyBboxPatch((0, 0), L, W, boxstyle="round,pad=0,rounding_size=1.5", fc='#2d6cdf', ec='#1b3f84', lw=1.5))
# mounting holes
holes = [(2.6, 2.6), (L-2.6, 2.6), (2.6, W-2.6), (L-2.6, W-2.6)]
for x, y in holes:
    ax.add_patch(Circle((x, y), 1.3, fc='white', ec='#9aa', lw=0.8)); ax.add_patch(Circle((x, y), 0.9, fc='#2d6cdf', ec='none'))
# end headers 1x6 (vertical columns) — pins at x = hx and L-hx
hx = 4.2; pitch = 2.54; y0 = W/2 - 2.5*pitch
labels = ['GND', 'OE', 'SCL', 'SDA', 'VCC', 'V+']
for side, x in (('L', hx), ('R', L-hx)):
    ax.add_patch(Rectangle((x-1.3, y0-1.3), 2.6, 5*pitch+2.6, fc='#111', ec='k', lw=0.5))
    for i in range(6):
        y = y0 + i*pitch
        ax.add_patch(Rectangle((x-0.8, y-0.8), 1.6, 1.6, fc='#e6c15a', ec='#7a5c10', lw=0.4))
        ax.text(x + (2.0 if side=='L' else -2.0), y, labels[i], fontsize=7, color='white', ha='left' if side=='L' else 'right', va='center', family='DejaVu Sans')
    ax.text(x, -0.4, 'пин 1?', fontsize=6.5, color='#444', ha='center', va='top', style='italic')
# servo field 16 x 3
sx0 = 13.0; sy0 = 5.0
for c in range(16):
    for r in range(3):
        ax.add_patch(Rectangle((sx0 + c*pitch - 0.7, sy0 + r*pitch - 0.7), 1.4, 1.4, fc='#e6c15a' if r else '#222', ec='#7a5c10', lw=0.3))
ax.text(sx0 + 7.5*pitch, sy0 + 2*pitch + 2.0, 'поле 16 × 3 за серво кабели (сочи НАГОРЕ)', fontsize=7, color='white', ha='center')
# screw terminal V+ on top edge, cap
ax.add_patch(Rectangle((40.0, W-8.0), 7.0, 7.0, fc='#2f8f4e', ec='#1a5a2e', lw=0.8))
ax.text(43.5, W-4.5, 'V+\nклема', fontsize=6.5, color='white', ha='center', va='center')
ax.add_patch(Circle((50.0, 20.5), 2.4, fc='#333', ec='#111')); ax.text(50.0, 20.5, 'C', fontsize=7, color='white', ha='center', va='center')
# chip
ax.add_patch(Rectangle((26, 15.5), 10, 6, fc='#222', ec='k')); ax.text(31, 18.5, 'PCA9685', fontsize=6.5, color='white', ha='center', va='center')

def dim(x1, y1, x2, y2, text, color, off=0.0, ha='center', va='bottom', lw=1.6, fs=10):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='<->', mutation_scale=12, lw=lw, color=color, shrinkA=0, shrinkB=0))
    mx, my = (x1+x2)/2, (y1+y2)/2
    ax.text(mx, my + off, text, fontsize=fs, color=color, ha=ha, va=va, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.25', fc='white', ec=color, lw=0.8))

RED = '#d62728'; ORG = '#e07b00'; GRN = '#1b8a3a'; PUR = '#7b2fbf'; TEAL = '#0b7f8a'
# A: pin1 to pin1 across the length
dim(hx, -3.2, L-hx, -3.2, 'A  пин 1 → пин 1 (център до център)', RED, off=-1.2, va='top')
for x in (hx, L-hx): ax.plot([x, x], [y0-0.8, -3.2], color=RED, lw=0.7, ls=':')
# B: width
dim(L+3.0, 0, L+3.0, W, 'B\nширина', ORG, off=0, ha='left', va='center')
ax.text(L+5.5, W/2, '', fontsize=1)
# C: header to board end (both ends)
dim(0, W+3.0, hx, W+3.0, 'C', GRN, off=0.6)
dim(L-hx, W+3.0, L, W+3.0, 'C′', GRN, off=0.6)
ax.plot([hx, hx], [y0+5*pitch+0.8, W+3.0], color=GRN, lw=0.7, ls=':'); ax.plot([L-hx, L-hx], [y0+5*pitch+0.8, W+3.0], color=GRN, lw=0.7, ls=':')
# D: pin order arrow next to left header
ax.annotate('', xy=(hx-2.6, y0+5*pitch), xytext=(hx-2.6, y0), arrowprops=dict(arrowstyle='->', color=PUR, lw=1.6))
ax.text(hx-3.4, W/2, 'D', fontsize=10, color=PUR, ha='right', va='center', fontweight='bold', bbox=dict(boxstyle='round,pad=0.25', fc='white', ec=PUR, lw=0.8))
# E: mounting holes c-c
dim(2.6, -8.2, L-2.6, -8.2, 'E  отвор → отвор (и Ø)', TEAL, off=-1.2, va='top')
dim(-3.0, 2.6, -3.0, W-2.6, 'E′', TEAL, off=0, ha='right', va='center')
for x, y in holes:
    ax.plot([x, x], [y, -8.2] if y < W/2 else [y, y], color=TEAL, lw=0.5, ls=':')
ax.plot([2.6, -3.0], [2.6, 2.6], color=TEAL, lw=0.5, ls=':'); ax.plot([2.6, -3.0], [W-2.6, W-2.6], color=TEAL, lw=0.5, ls=':')
# F: terminal position
ax.annotate('F  къде е клемата V+', xy=(43.5, W+0.3), xytext=(36, W+6.5), fontsize=9, color='#2f8f4e', fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='#2f8f4e', lw=1.4), bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='#2f8f4e', lw=0.8))
ax.set_xlim(-9, L+9); ax.set_ylim(-11.5, W+9)
ax.text(L/2, W+8.2, 'PCA9685 модул (U2), изглед отгоре, схематично — твоят може да се различава, затова мерим', fontsize=10.5, ha='center', va='bottom', fontweight='bold')

# bottom panel: the list + caliper method
ax2 = fig.add_axes([0.03, 0.02, 0.94, 0.27]); ax2.axis('off')
rows = [
 (RED,  'A', 'Разстоянието между двата 6-пинови реда по дължината, от център на пин 1 до център на пин 1 (това е U2_ROW; във файла е 46 = предположение).\n     Шублер: външни челюсти върху външните ръбове на двата крайни пина = A_out; вътрешни челюсти между вътрешните им ръбове = A_in; A = (A_out + A_in) / 2.'),
 (ORG,  'B', 'Ширината на платката (късата страна).'),
 (GRN,  'C, C′', 'От реда пинове до края на платката, за всеки от двата края (колко стърчи модулът извън пиновете).'),
 (PUR,  'D', 'Редът на надписите на всеки от двата реда, от единия край до другия (напр. GND, OE, SCL, SDA, VCC, V+). Еднакъв ли е при двата? Снимка на надписите.'),
 (TEAL, 'E, E′', 'Монтажни отвори: колко са, диаметър, разстояние отвор→отвор по дължина и по ширина.'),
 ('#2f8f4e', 'F', 'На коя страна е клемата V+ и колко е от края (жиците 6 V трябва да имат място).\n     Пиновете на двата реда: запоени ли са и накъде сочат? Трябва да сочат НАДОЛУ, за да влязат в женските редове на носещата платка; серво полето сочи нагоре.'),
]
y = 0.97
for col, k, t in rows:
    ax2.text(0.0, y, k, fontsize=10.5, color=col, fontweight='bold', va='top', ha='left')
    ax2.text(0.05, y, t, fontsize=8.6, va='top', ha='left', color='#222', linespacing=1.35)
    y -= 0.17 if '\n' in t else 0.12
fig.savefig('U2_PCA9685_measure.png', facecolor='white')
print('ok')
