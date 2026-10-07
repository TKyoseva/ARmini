# Структура на repo-то

```
ARmini/
├── README.md                 какво е, статус, снимка, таблица на подсистемите
├── CONTRIBUTORS.md           кой какво прави (честно: и приятелите, и менторът)
├── LICENSE                   (виж docs/decisions/0001-license.md)
├── .gitattributes            line endings; бинарните файлове са маркирани binary (без LFS засега)
├── .gitignore                .pio/, build/, secrets.h, *.bak, .DS_Store
│
├── docs/
│   ├── LOG.md                дневник: дата · какво пробвах · какво стана · какво променям (3 реда/ден)
│   ├── STRUCTURE.md          този файл
│   ├── timeline/TIMELINE.md  хронология от 9/2025 с РЕАЛНИТЕ дати (вкл. неща отпреди repo-то)
│   ├── bom/                  AR_BOM_<дата>.xlsx + bom.csv (git-friendly копие за diff) + визуален BOM
│   ├── FAILS_AND_FIXES.md    всяка грешка и как е оправена (номерирани, с дати)
│   ├── diagrams/             хардуерна схема (py + png + A3 pdf), блок-схеми
│   ├── decisions/            кратки "защо": 0001-license, 0002-chassis-on-beams, …
│   └── portfolio/            избраните 25 файла + описанията им (от декември)
│
├── cad/
│   ├── openscad/             AR-Mini_v1.scad — целият робот + всички печатани части
│   ├── fusion/               AR_Mini_hull.py (скрипт) + .f3d архиви по milestone + .step
│   ├── 3d/                   3D изгледи (PNG) + интерактивен модел (HTML) + src/ (Python, който ги прави)
│   └── stl/                  само "пуснати" STL-и, по версия: stl/v1.7/arm_drive.stl …
│
├── pcb/
│   ├── xiao-breakout-rev0/   .kicad_pcb, README, preview, gerbers/ след поръчка
│   └── carrier-revA/         SPEC.md, mockup, KiCad проектът, когато Е го направи
│
├── firmware/
│   ├── xiao/                 PlatformIO проект (platformio.ini, src/, lib/, include/secrets.example.h)
│   └── mega/                 Arduino sketch-ове: thrust-rig/, teleop/
│
├── sim/                      симулацията от статията (кодът, който вече съществува) — импорт
├── software/pi/              v2: ROS 2 пакети, launch файлове
│
├── data/
│   ├── logs/2026-10-18_bathtub-lift/*.csv      всяка сесия в своя папка с дата
│   ├── thrust-test/          таблица тяга/ток + снимка на стенда
│   ├── buoyancy/             газене, баласт, ЦТ/ЦП
│   ├── missions/             20-те мисии: missions.csv + по една папка на мисия
│   └── scripts/              Python, който прави графиките от CSV-тата
│
├── media/
│   ├── photos/2026-10-05_first-prints/*.jpg    избрани снимки, ≤ 2 MB, LFS
│   └── video-index/VIDEOS.md                   списък на видеата с линк към Drive (видеото НЕ е в git)
│
└── hardware/
    ├── datasheets/           ST3215, MLX90642, BTS7960, ROB0154 (pdf)
    └── wiring/               пинове, цветове на кабелите, конектори
```

## Правила
- **Един commit = една промяна с глагол:** `cad: move arch to x=165`, `fw: add ADC ladder for leak+kill`, `data: bathtub lift session 18.10`.
- **Папки с дата** `YYYY-MM-DD_тема` за data/ и media/ — сортират се сами.
- **Без Git LFS засега** — всеки файл е под 5 MB. Снимки ≤ 2 MB (JPG, не HEIC). Видео — не в git, в OneDrive, индексирано в media/video-index.
- **Никакви пароли** в кода: `include/secrets.h` е в .gitignore; `secrets.example.h` показва формата.
- **Branch-ове:** main е винаги работещ; приятелите работят в `feat/<име>` и правят Pull Request; ти преглеждаш. Това е и доказателство кой какво е направил.
- **Tag на всеки milestone:** `v0.1-hull-floats`, `v0.2-first-lift`, `v0.3-first-swim`, `v0.4-autonomous`, `v1.0-portfolio`.
- **Issues + Projects board** за задачите по фази: колони Фаза 1…6, една карта на задача, assignee = човекът.
