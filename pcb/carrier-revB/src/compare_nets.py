#!/usr/bin/env python3
"""Compare the SPEC netlist (spec_netlist.py) with the copper (.kicad_pcb) pin by pin (card C080).

  python3 pcb/carrier-revB/src/compare_nets.py [board.kicad_pcb]

Checks, per reference and pin: same net on both routes (net NAMES and net MEMBERSHIP). Two-pin passives may be
mirrored (pin 1 ↔ 2) without counting as a difference. Prints every difference and exits 1 if there is any that is
not listed in KNOWN (a reviewed, explained difference). Pure Python, no KiCad needed.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spec_netlist import PARTS  # noqa: E402

# Reviewed differences: (ref, pin) → why it is acceptable. Each one is also in FAILS / the C080 report.
KNOWN = {}  # reviewed, explained differences: (ref, pin or "*") → reason. Empty since 18.11 (JP4 added to SPEC).

PASSIVE2 = re.compile(r"^(R|C)\d+$")


def pcb_pads(path):
    s = open(path).read()
    starts = [m.start() for m in re.finditer(r'\(footprint "', s)]
    # end of the last footprint = first top-level item after it
    tail = re.search(r'\n\t\((segment|via|zone|gr_|net |embedded_fonts)', s[starts[-1]:])
    ends = starts[1:] + [starts[-1] + (tail.start() if tail else len(s) - starts[-1])]
    out = {}
    for a, b in zip(starts, ends):
        blk = s[a:b]
        ref = (re.search(r'\(property "Reference" "([^"]+)"', blk) or re.search(r'reference "([^"]+)"', blk)).group(1)
        pins = {}
        for p in blk.split("(pad ")[1:]:
            num = re.match(r'"([^"]*)"', p).group(1)
            if num == "":
                continue  # mechanical hole
            net = re.search(r'\(net (?:\d+ )?"([^"]*)"\)', p)
            name = net.group(1) if net else None
            pins[num] = None if name and name.startswith("unconnected-") else name  # KiCad's name for a no-connect pad
        out[ref] = pins
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    board = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "AR-Mini_carrier_revB.kicad_pcb")
    pcb = pcb_pads(board)
    spec = {r: {str(k): v for k, v in pins.items()} for r, (_, pins) in PARTS.items()}
    diffs, known = [], []

    for ref in sorted(set(spec) | set(pcb)):
        if ref not in pcb:
            diffs.append(f"{ref}: in SPEC, not on the PCB")
            continue
        if ref not in spec:
            (known if (ref, "*") in KNOWN else diffs).append(
                f"{ref}: on the PCB only ({' '.join(f'{p}:{n}' for p, n in pcb[ref].items())})")
            continue
        s, p = spec[ref], pcb[ref]
        if set(s) != set(p):
            diffs.append(f"{ref}: pin sets differ SPEC {sorted(s)} PCB {sorted(p)}")
            continue
        bad = [k for k in s if s[k] != p[k]]
        if bad and PASSIVE2.match(ref) and len(s) == 2 and sorted(map(str, s.values())) == sorted(map(str, p.values())):
            bad = []  # mirrored passive
        for k in bad:
            (known if (ref, k) in KNOWN else diffs).append(f"{ref}.{k}: SPEC {s[k]} · PCB {p[k]}")

    # membership check (independent of names): every SPEC net must be exactly one PCB net
    def members(d):
        m = {}
        for r, pins in d.items():
            for k, n in pins.items():
                if n is not None:
                    m.setdefault(n, set()).add(f"{r}.{k}")
        return m
    common = {r: spec[r] for r in spec if r in pcb}
    sm = members(common)
    pm = members({r: pcb[r] for r in common})
    for n, mem in sorted(sm.items()):
        pn = {pcb[x.split('.')[0]][x.split('.')[1]] for x in mem}
        if len(pn) != 1:
            diffs.append(f"net {n}: split across PCB nets {sorted(map(str, pn))}")
        else:
            (only,) = pn
            if only is not None and pm.get(only, set()) - mem:
                extra = sorted(pm[only] - mem)
                diffs.append(f"net {n}: PCB net {only} also joins {extra}")

    print(f"SPEC parts {len(spec)} · PCB footprints {len(pcb)} · nets {len(sm)}")
    for k in known:
        print("KNOWN ", k)
    for d in diffs:
        print("DIFF  ", d)
    print("RESULT", "OK" if not diffs else f"{len(diffs)} difference(s)")
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
