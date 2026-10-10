# Test data · naming rule for CSV logs

Every measurement file carries the **same loop id as the card on the AR-Mini Board** (C001, C002, …), the same id
as the iCloud photo folder (`media/LINKS.md`) and the commit message. One id everywhere.

```
data/logs/<YYYY-MM-DD>_<C###>_<name>.csv
data/logs/2026-10-10_C005_bts-bench.csv
data/logs/2026-10-10_C005_bts-bench_2.csv      # second run the same day: the logger adds _2, _3, … — never overwrites
```

- `YYYY-MM-DD` = the real date of the measurement (the day the card was run, not the day it was committed).
- `C###` = card id from the board; `C000` only for files that belong to no card (script tests).
- `<name>` = lowercase letters, digits, dashes: `<module>-<what>`, e.g. `bts-bench`, `st3215-step`, `ladder-vbat`, `mlx-wall`.
- Written by `scripts/bench_log.py --card C005 --name bts-bench` (see `python3 scripts/bench_log.py --help`).
- Photos never go here (iCloud only); a CSV may be committed together with the card's docs entry.

## File contents

Exactly what the sketch printed, plus one first line written by the logger:

```
# bench_log 2026-10-10T09:12:03 card=C005 name=bts-bench source=/dev/tty.usbmodem1101 @ 115200
# AR-Mini bench · bts7960 · build Oct 10 2026 08:55:12
t_ms,cmd,pwm_r,pwm_l,is_r_mV,is_l_mV,kill
1234,0.000,0,0,-1,-1,0
# > s 0.3
1334,0.300,13,0,-1,-1,0
…
# DEADMAN
```

- `#` lines are messages (banner, `# > …` = command typed into the logger, `# DEADMAN`, `# WARN …`, MLX heat maps, `# RAW …`).
- The first line without `#` is the CSV header; `t_ms` (ms since boot) is always the first column; units are in the
  header names (`is_r_mV`, `volt_V`), never in the values.

## Reading

```python
import pandas as pd
df = pd.read_csv("data/logs/2026-10-10_C005_bts-bench.csv", comment="#")
df["t_s"] = (df.t_ms - df.t_ms.iloc[0]) / 1000
```

MLX90640 raw frames (`raw 1`): `grep '^# RAW' file.csv | cut -d' ' -f3-` → one line per frame, `t_ms` then 768 values
(row-major, 32 × 24, index = y·32 + x).
