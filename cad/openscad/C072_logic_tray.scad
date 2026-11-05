// AR-Mini C072 · LOGIC box tray (LANUCN IP65 150 x 110 x 70, BOM 26)
// Origin = centre of the box floor (the small centre pin). X = across (+ starboard), Y = along (+ bow).
// Boss positions are read from Teddy's photos 05.11.2026, calibrated with the caliper
// (63.80 mm between the two boss rows). Expect ±3 mm -> print the FIT template first.
// part = "tray" | "fit"
// layout = "carrier": one 100 x 80 board on the rev B hole grid 93 x 73 (perfboard now, rev B PCB later, same holes)
// layout = "split":   P1 + P2 + P4 perfboards and the standing PCA9685 wall (04.11 plan)
part = "tray";
layout = "carrier";
$fn = 48;

// ---- box floor (measure-and-edit block) ----
PLATE   = [96, 134];     // tray outline (floor ≈ 100 x 140)
NOTCH   = 10;            // corner cut for the lid-screw pillars (pillar ≈ 12 mm from the walls)
T       = 3;             // plate thickness
LIFT    = 12;            // floor -> underside of the plate (clears the 4 floor rings)
BOSS_H  = 5;             // boss height above the floor (guess, recess covers up to 6.5)
SCREW   = [[-32, 23], [32, 23], [-41, 0], [41, 0]];   // bosses used (M3 x 20 into the boss)
SLOT    = 3;             // ± slot length along Y for position tolerance
FEET    = [[0, 60], [0, -60]];                        // plain feet resting on the floor
RINGS   = [[-33.5, 53], [33.5, 53], [-33.5, -53], [33.5, -53]]; // floor knockouts: never open

// ---- rev B carrier (SPEC.md §1): 100 x 80, 4 x M3 on 93 x 73, 3.5 mm from the edges ----
CAR = [80, 100];          // X across (DevKit spans the 80 side: antenna -> starboard, USB-C -> port), Y along
CAR_C = [0, 6];           // centre of the board on the plate
CAR_GRID = [73, 93];
CAR_SO_H = 8; CAR_SO_D = 7.5; INSERT = 4.0;   // ruthex M3 insert (BOM 18), Ø4.0 x 5.7

// ---- boards on the plate ----
SO_H = 6; SO_D = 5; PILOT = 1.7;   // M2 self-tapping into PETG (BOM 17)
INSET = 2.2;                         // perfboard corner-hole inset (measure)
// [x0, y0, size_x, size_y]
P1 = [-35,  -3, 70, 50];   // MCU, DevKit-Lipo; USB-C to port (-X), antenna to starboard
P2 = [-35, -35, 70, 30];   // I/O, 74HCT125
P4 = [-35, -66.5, 70, 30];   // BNO055, arrow to bow
BOARDS = [P1, P2, P4];
// PCA9685 standing bracket (board 62.5 x 25.4, holes 55.9 x 19.05, M2.5)
PCA_Y = 56; PCA_W = 66; PCA_H = 30;  // wall stern face at Y = PCA_Y, PCA board at Y ≈ 50.4

TIES = [[-45, -45], [45, -45], [-45, 15], [45, 15], [-45, 45], [45, 45]]; // zip-tie slots
LEAK_SLOT = [-41, -38];   // wires of P5 (lying on the floor under the plate)

module outline2d() {
    difference() {
        square(PLATE, center = true);
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx * PLATE[0] / 2, sy * PLATE[1] / 2]) square(2 * NOTCH, center = true);
    }
}
module slot2d(d) { hull() for (dy = [-SLOT, SLOT]) translate([0, dy]) circle(d = d); }

module plate() {
    translate([0, 0, LIFT]) difference() {
        linear_extrude(T) outline2d();
        for (p = SCREW) translate([p[0], p[1], -1]) linear_extrude(T + 2) slot2d(3.4);
        for (p = TIES) translate([p[0], p[1], -1]) linear_extrude(T + 2) square([3, 5], center = true);
        if (layout == "split") translate([LEAK_SLOT[0], LEAK_SLOT[1], -1]) linear_extrude(T + 2) square([6, 14], center = true);
        else translate([0, -52, -1]) linear_extrude(T + 2) square([14, 6], center = true);   // P5 wires, behind the carrier
        // labels
        translate([0, -64, T - 0.6]) linear_extrude(1) text("STERN", size = 4, halign = "center");
        translate([0, 36, T - 0.6]) linear_extrude(1) text("C072 LOGIC  BOW ^", size = 3.5, halign = "center");
    }
}
module screw_pad(p) {
    translate([p[0], p[1], 0]) difference() {
        linear_extrude(LIFT) slot2d(14);
        translate([0, 0, -1]) linear_extrude(BOSS_H + 2.5) slot2d(10);   // boss slides in here
        translate([0, 0, -1]) linear_extrude(LIFT + 2) slot2d(3.4);
    }
}
module foot(p) { translate([p[0], p[1], 0]) cylinder(d = 12, h = LIFT); }

module standoffs() {
    for (b = BOARDS) for (cx = [b[0] + INSET, b[0] + b[2] - INSET], cy = [b[1] + INSET, b[1] + b[3] - INSET])
        translate([cx, cy, LIFT + T]) difference() {
            cylinder(d = SO_D, h = SO_H);
            translate([0, 0, 1]) cylinder(d = PILOT, h = SO_H);
        }
}
module pca_bracket() {
    // wall standing on the plate; PCA9685 screws to its STERN face, servo pins up
    translate([-PCA_W / 2, PCA_Y, LIFT + T]) difference() {
        union() {
            cube([PCA_W, 3, PCA_H]);
            cube([PCA_W, 11, 3]);                                              // foot (bow side)
            for (x = [10, PCA_W / 2, PCA_W - 10]) translate([x - 1.5, 0, 0]) cube([3, 11, PCA_H * 0.6]); // gussets (bow side)
            for (hx = [-55.9 / 2, 55.9 / 2], hz = [7, 7 + 19.05])
                translate([PCA_W / 2 + hx, 0.5, hz]) rotate([90, 0, 0]) cylinder(d = 5, h = 4.5);   // standoffs (stern side)
        }
        for (hx = [-55.9 / 2, 55.9 / 2], hz = [7, 7 + 19.05])
            translate([PCA_W / 2 + hx, -5, hz]) rotate([-90, 0, 0]) cylinder(d = 2.2, h = 7);  // M2.5 self-tap
    }
}
module fit_template() {
    // 0.8 mm outline: lay it on the floor, check the 4 screw holes sit on bosses and the 4 rings are inside the circles
    difference() {
        linear_extrude(0.8) outline2d();
        for (p = SCREW) translate([p[0], p[1], -1]) cylinder(d = 4, h = 3);
        for (p = RINGS) translate([p[0], p[1], -1]) cylinder(d = 26, h = 3);
        if (layout == "split") for (b = BOARDS) for (cx = [b[0] + INSET, b[0] + b[2] - INSET], cy = [b[1] + INSET, b[1] + b[3] - INSET]) translate([cx, cy, -1]) cylinder(d = 2, h = 3);
        else for (sx = [-1, 1], sy = [-1, 1]) translate([CAR_C[0] + sx * CAR_GRID[0] / 2, CAR_C[1] + sy * CAR_GRID[1] / 2, -1]) cylinder(d = 3.2, h = 3);
        translate([0, -30, 0.4]) linear_extrude(1) text("FIT C072", size = 6, halign = "center");
        translate([0, 30, 0.4]) linear_extrude(1) text("BOW ^", size = 6, halign = "center");
        translate([0, 0, -1]) cylinder(d = 2, h = 3);   // centre pin
    }
}

if (part == "fit") fit_template();
else {
    plate(); for (p = SCREW) screw_pad(p); for (p = FEET) foot(p);
    if (layout == "split") { standoffs(); pca_bracket(); }
    else carrier_standoffs();
}
module carrier_standoffs() {
    for (sx = [-1, 1], sy = [-1, 1])
        translate([CAR_C[0] + sx * CAR_GRID[0] / 2, CAR_C[1] + sy * CAR_GRID[1] / 2, LIFT + T]) difference() {
            cylinder(d = CAR_SO_D, h = CAR_SO_H);
            translate([0, 0, CAR_SO_H - 6]) cylinder(d = INSERT, h = 7);
        }
}
