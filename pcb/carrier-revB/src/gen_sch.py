#!/usr/bin/env python3
"""AR-Mini carrier rev B — write the schematic (.kicad_sch) from spec_netlist.py (card C080).

  python3 pcb/carrier-revB/src/gen_sch.py

The schematic is the SPEC route drawn for KiCad, so ERC can run and `kicad-cli pcb drc --schematic-parity`
can compare it with the board that gen.py wrote. One box symbol per part, every pin on a short wire with a net
label, every unused pin with a no-connect flag (KiCad names those nets
unconnected-(REF[-PINNAME]-PadN); gen.py writes the same names on the board pads, NC_PIN_NAMES there = NAMES here). File format 20230121 (KiCad 7), opened and checked by KiCad 7–10.
Footprint fields point at the board's own footprints (AR-Mini:<ref>), so the parity check matches part to part.
"""
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from spec_netlist import DNP, PARTS  # noqa: E402

OUT = os.path.join(HERE, "..", "AR-Mini_carrier_revB.kicad_sch")
PROJECT = "AR-Mini_carrier_revB"
NS = uuid.UUID("6f1d3c2e-0c80-4a5e-9b1a-2026111800c0")  # deterministic uuids → stable diffs


def U(*k):
    return str(uuid.uuid5(NS, "/".join(map(str, k))))


ROOT = U("root")


def fp_name(ref):
    """Footprint name on the board: one per reference, except the four mounting holes (all AR-Mini:M3)."""
    return "M3" if ref in ("H1", "H2", "H3", "H4") else ref
G = 2.54

# Pin names shown inside the boxes (function, not net). SOURCE: SPEC §3–§7 and the module silk.
NAMES = {
    "U1_1": {1: "3V3", 2: "3V3", 4: "GPIO4", 7: "GPIO7", 8: "GPIO15", 9: "GPIO16", 10: "GPIO17", 11: "GPIO18",
            12: "GPIO8", 15: "GPIO9", 16: "GPIO10", 17: "GPIO11", 20: "GPIO14", 21: "+5V", 22: "GND"},
    "U1_2": {1: "GND", 4: "GPIO1", 5: "GPIO2", 6: "GPIO42", 7: "GPIO41", 8: "GPIO40", 9: "GPIO39", 16: "GPIO48",
            17: "GPIO47", 22: "GND"},
    "U2_1": {1: "GND", 2: "OE", 3: "SCL", 4: "SDA", 5: "VCC", 6: "V+"},
    "U3": {1: "Vin", 2: "3Vo", 3: "GND", 4: "SDA", 5: "SCL", 6: "RST", "B1": "PS0", "B2": "PS1", "B3": "INT", "B4": "ADR"},
    "U6": {1: "1OE", 2: "1A", 3: "1Y", 4: "2OE", 5: "2A", 6: "2Y", 7: "GND", 8: "3Y", 9: "3A", 10: "3OE", 11: "4Y",
           12: "4A", 13: "4OE", 14: "VCC"},
    "Q2": {1: "E", 2: "B", 3: "C"}, "Q3": {1: "E", 2: "B", 3: "C"},
    "LED1": {1: "A", 2: "K"}, "LED2": {1: "A", 2: "K"}, "LED3": {1: "A", 2: "K"},
    "BZ1": {1: "+", 2: "-"},
}


def pin_order(pins):
    def key(p):
        s = str(p)
        return (0, int(s)) if s.isdigit() else (1, s)
    return sorted(pins, key=key)


def font(size=1.27):
    return f"(effects (font (size {size} {size})))"


def lib_symbol(ref, value, pins):
    order = pin_order(pins)
    n = max(len(order), 1)
    names = NAMES.get(ref, {})
    w = 15.24 if names else 7.62
    body = (f'(symbol "{ref}_0_1" (rectangle (start -5.08 {G:.2f}) (end {w - 5.08:.2f} {-(n) * G:.2f}) '
            f'(stroke (width 0.254) (type default)) (fill (type background))))')
    pl = []
    for i, p in enumerate(order):
        nm = names.get(p, names.get(str(p), "~"))
        pl.append(f'(pin passive line (at -7.62 {-i * G:.2f} 0) (length 2.54) '
                  f'(name "{nm}" {font(1.0)}) (number "{p}" {font(1.0)}))')
    return (f'(symbol "armini:{ref}" (pin_names (offset 0.5)) (in_bom yes) (on_board yes)\n'
            f'  (property "Reference" "{ref}" (at 0 {G * 2:.2f} 0) {font()})\n'
            f'  (property "Value" "{value}" (at 0 {G:.2f} 0) {font()})\n'
            f'  (property "Footprint" "AR-Mini:{fp_name(ref)}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n'
            f'  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n'
            f'  {body}\n  (symbol "{ref}_1_1" {" ".join(pl)}))'), n


def main():
    libs, items = [], []
    # simple column packing on an A2 sheet
    x, y, col_w, top, bottom = 40.64, 30.48, 55.88, 30.48, 380.0
    for ref in sorted(PARTS, key=lambda r: (r.rstrip("0123456789_") or r, len(r), r)):
        value, pins = PARTS[ref]
        lib, n = lib_symbol(ref, value, pins)
        libs.append(lib)
        h = (n + 3) * G
        if y + h > bottom:
            x, y = x + col_w, top
        X, Y = x, y + 2 * G
        props = (f'(property "Reference" "{ref}" (at {X:.2f} {Y - 2 * G:.2f} 0) {font()})\n'
                 f'  (property "Value" "{value}" (at {X:.2f} {Y - G:.2f} 0) {font()})\n'
                 f'  (property "Footprint" "AR-Mini:{fp_name(ref)}" (at {X:.2f} {Y:.2f} 0) (effects (font (size 1.27 1.27)) hide))\n'
                 f'  (property "Datasheet" "" (at {X:.2f} {Y:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        dnp = "yes" if ref in DNP else "no"
        pin_uuids = " ".join(f'(pin "{p}" (uuid {U(ref, "pin", p)}))' for p in pin_order(pins))
        items.append(f'(symbol (lib_id "armini:{ref}") (at {X:.2f} {Y:.2f} 0) (unit 1) (in_bom yes) (on_board yes) '
                     f'(dnp {dnp}) (uuid {U(ref)})\n  {props}\n  {pin_uuids}\n'
                     f'  (instances (project "{PROJECT}" (path "/{ROOT}" (reference "{ref}") (unit 1)))))')
        for i, p in enumerate(pin_order(pins)):
            px, py = X - 7.62, Y + i * G
            net = pins[p]
            if net is None:
                items.append(f"(no_connect (at {px:.2f} {py:.2f}) (uuid {U(ref, 'nc', p)}))")
            else:
                lx = px - 5.08
                items.append(f"(wire (pts (xy {px:.2f} {py:.2f}) (xy {lx:.2f} {py:.2f})) "
                             f"(stroke (width 0) (type default)) (uuid {U(ref, 'w', p)}))")
                # Global labels: the net is named "GND", not "/GND", so it equals the board's net name (parity).
                items.append(f'(global_label "{net}" (shape passive) (at {lx:.2f} {py:.2f} 180) (fields_autoplaced) '
                             f'(effects (font (size 1.27 1.27)) (justify right)) (uuid {U(ref, "l", p)}) '
                             f'(property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at 0 0 0) '
                             f'(effects (font (size 1.27 1.27)) hide)))')
        y += h
    out = (f'(kicad_sch (version 20230121) (generator eeschema)\n'
           f'(uuid {ROOT})\n(paper "A2")\n'
           f'(title_block (title "AR-Mini carrier rev B — schematic from SPEC.md") (date "2026-11-18") (rev "B")\n'
           f'  (comment 1 "Written by src/gen_sch.py from src/spec_netlist.py (card C080): second route to the copper")\n'
           f'  (comment 2 "Board: gen.py. Check: src/compare_nets.py + kicad-cli pcb drc --schematic-parity"))\n'
           f'(lib_symbols\n' + "\n".join(libs) + '\n)\n' + "\n".join(items) +
           f'\n(sheet_instances (path "/" (page "1")))\n)\n')
    open(OUT, "w").write(out)
    print("wrote", os.path.normpath(OUT), len(PARTS), "symbols")


if __name__ == "__main__":
    main()
