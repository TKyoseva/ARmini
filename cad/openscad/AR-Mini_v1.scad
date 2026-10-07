// ============================================================
//  AmphiReach  AR-Mini  v1.9  (power box seated on the cross-beams, 6.10)  —  parametric CAD (OpenSCAD)
//  Scale demonstrator: catamaran hull + ROB0154 tracks + cradle lift
//  Units: mm.   Printer: Creality K2 Pro (300 x 300 x 300).
//
//  HOW TO USE
//   1. Set `part` (below) to the piece you want, press F6, File > Export STL.
//   2. part = "assembly" shows everything in place. Ghosted shapes are
//      references only (chassis, water, dome, dummy, cradle rod).
//   3. Left-side parts are modelled. For the right side set side = -1.
//   4. Everything marked MEASURE must be checked against the real part
//      before printing (ROB0154 tray, ST3215 servo, thruster bolt pattern).
//   5. part = "plate_check" shows the aft hull section on the 300x300 bed
//      (it goes on diagonally).
//
//  PRINT LIST (PETG or ASA, 0.2 mm, 4 perimeters)
//   hull_fore  x2 (one mirrored)   bottom down, no supports
//   hull_aft   x2 (one mirrored)   bottom down, no supports
//   beam_bracket x4               as modelled
//   (chassis_hanger no longer needed: the ROB0154 top plate bolts directly onto the two beams with M4 through its slots)
//   arch_post x2                  lying on its side
//   pivot_bracket x2 (one mirrored)  as modelled (pocket faces up, no supports)
//   arm_drive x2, arm_idler x2    flat
//   coupler x2                    plate flat
//   cam_pan_mount x1              as modelled (slide onto the arch tube first)
//   cam_plate x1                  flat, tab prints at 75 deg without supports
//   dummy_head x1, dummy_lid x1   PLA; "Pesho" — hollow head with hand-warmer pocket and air vents
//   power_box x1, power_lid x1    PETG, 4 perimeters; sits ON the two cross-beams (v1.9), holds fuse block + 2x BTS7960 + bus bars
//                                 4 x M3x30 + washers: box floor -> beam tube -> ROB0154 plate slot -> nut (one bolt stack per hole)
// ============================================================

part = "assembly";   // assembly | hull_fore | hull_aft | plate_check | beam_bracket | arch_post | pivot_bracket | arm_drive | arm_idler | coupler | cam_pan_mount | cam_plate | dummy_head | dummy_lid | power_box | power_lid
side = 1;            // 1 = left (port), -1 = right (mirrored)
pose = "deployed";   // deployed | stowed   (assembly only)

$fn = 64;

// ---------------- hull ----------------
hull_L  = 610;
hull_W  = 100;
hull_H  = 120;
bow_len = 150;        // parabolic bow taper
tip_r   = 6;          // rounding of the bow tip
wall    = 1.8;        // 4 perimeters @ 0.42
floor_t = 2.0;        // 10 layers @ 0.2
cut_x   = 305;        // split into two 305 mm sections
bulk_t  = 3;          // bulkhead at the joint, one per section
rib_t   = 3;
rib_x   = [100, 200, 420, 520];   // full-height ribs -> watertight compartments
rim_h   = 10;                     // ribs stop this far below the rim (cable notch)
draft   = 42;                     // predicted waterline at ~4.7 kg total mass

// joint bolts through both bulkheads: ABOVE the waterline only
joint_bolt_z = [75, 105];
joint_bolt_y = 32;
bolt_d   = 3.4;
insert_d = 4.0;       // hole for M3 heat-set inserts

// ---------------- catamaran layout ----------------
gap    = 250;         // clear width between the hulls (ROB0154 measured over tracks: needs >= width + 10)
beam   = 15;          // square aluminium tube
beam_x = [385, 500];  // hull-to-hull beams under the ROB0154 top plate (plate 364..516)
boss_x = [165, 200, 385, 500];   // rim bosses on the inner side: arch, pivot, beams
boss_w = 24;          // boss depth inward from the wall
boss_l = 30;
boss_h = 20;
boss_pitch = 16;      // insert spacing along x

// ---------------- ROB0154 chassis (MEASURED 2.10) ----------------
// Tank-style: flat TOP plate, side plates hang down, DRIVE SPROCKETS AT THE FRONT TOP -> motors sit high (~85 mm), dry.
ch_L = 300;  ch_W = 230;  ch_H = 124.6;        // footprint over tracks (MEASURE width: needs gap >= ch_W + 10), track bottom -> top of plate
plate_L = 152.2; plate_W = 134.8; plate_t = 2;  // the aluminium top plate (slots for M3/M4)
ch_x = 290;                                     // front of the track footprint; keeps the cradle sweep clear
plate_x = ch_x + (ch_L - plate_L)/2;            // plate centred on the footprint -> 364..516
beam_bot = hull_H + 6;                          // tube underside when sitting in the rim brackets (126)
chassis_raise = 0;                              // 0 = tracks flush with the hull bottom (beach together). Raise if drag is a problem.
plate_gap = beam_bot - (chassis_raise + ch_H);  // plate hangs this far under the beams -> washers (1.4 mm)
motor_axis = 62;                                // MEASURED 2.10: track bottom -> drive sprocket axis
echo(str("Track bottom z=", chassis_raise, "; plate hangs ", plate_gap, " mm under the beams; motor axis z=", chassis_raise + motor_axis, " vs waterline ", draft, " (margin ", chassis_raise + motor_axis - draft, " mm)"));

// ---------------- bow arch (mast for the thermal camera) ----------------
arch_x = 165;         // on the straight part of the hull, just ahead of the pivot boss
arch_z = 235;         // underside of the arch tube; clears the cradle sweep (min 19 mm)
post_w = 20;

// ---------------- thruster pad (stern, below waterline) ----------------
tp_w = 44; tp_h = 44; tp_t = 6;
tp_z = 25;            // pad centre above the bottom
tp_pitch = 20;        // MEASURE: your thruster's bolt pattern


// ---------------- power box (printed, on the ROB0154 top plate) ----------------
pb_L = 152; pb_W = 135; pb_H = 66;      // outer footprint = the plate; inner height clears BTS7960 (43 + 6 standoffs) and the fuse block cover
pb_wall = 2.4; pb_floor = 2.4;
pb_lid_t = 3; pb_lip = 2.5;             // lid thickness; lip height of the box edge (gasket sits inside the lip)
pb_gland = 12.5;                        // PG7 cable gland hole
pb_gland_n = 6;                         // on the aft wall: battery in, thruster L/R, track L/R, 12V out to logic/servo
pb_toggle = 12.4;                       // 50 A toggle on the front wall
// v1.9: in v1.8 the box stood on the ROB0154 plate (z 124.6) and the two beams (z 126-141) ran THROUGH it.
// Now the floor sits on top of the beams; the plate still hangs 1.4 mm under them. Same bolt clamps box + beam + plate.
pb_z      = hull_H + 6 + beam;          // box floor underside = beam top (141)
pb_beam_y = 30;                         // bolt holes along each beam at +/- y (MEASURE: must land on the plate slots under the beam)
pb_rail   = 3;                          // locating rails under the floor, either side of each beam (stop the box sliding in x)
pb_boss_h = 6;                          // printed standoff bosses with M3 heat-set inserts (no through-holes: the beams block screws from below)
pb_fuse_x = 55;                         // fuse block tab bosses at +/- x (MEASURE the fuse block tab spacing)

// ---------------- cradle lift ----------------
pivot_x  = 200;       // servo shaft x (on rim boss #2)
shaft_z  = 105;       // servo shaft height above the hull bottom
arm_len  = 110;
arm_w    = 12;
arm_t    = 6;
arm_gap  = 22;        // parallelogram: idler pivot this far below the shaft
pin_d    = 3.3;       // M3 pins
rod_d    = 5.3;       // 5 mm aluminium rod
deploy_a = 215;       // arm polar angle in the x-z plane, deployed (forward & 35 deg down)
stow_a   = 45;        // stowed (aft & 45 deg up)
cradle_L = 220;
// Servo preset: "TD8120" = the TD-8120MG you have now (bathtub test), "ST3215" = final (arrives 9.10 — MEASURE then)
servo_sel       = "TD8120";
servo           = servo_sel == "TD8120" ? [40.5, 20.4, 28.0] : [45.5, 25.5, 35.5];   // L (x), W (z, shaft face), depth bottom→ear plane (y). TD MEASURED 5.10: 40.3 x 20.14, ear plane 28.0
servo_shaft_off = servo_sel == "TD8120" ? 10.4 : 11;      // shaft centre from the servo's forward end (TD MEASURED 10.4)
servo_ear_dx    = servo_sel == "TD8120" ? 4.85 : 5;       // ear holes beyond the body end (TD: 50 mm hole span measured)
servo_ear_dz    = servo_sel == "TD8120" ? 5    : 8;       // ear holes +/- from the shaft axis (TD MEASURED: 10 mm apart, hole 4.34)
servo_top       = servo_sel == "TD8120" ? 12.7 : 0;       // shaft face past the ear plane (TD total 40.7 measured - 28 ear plane)
disc_r = 8; disc_n = 4; disc_d = 2.4;   // servo disc bolt circle.              MEASURE

// ---------------- thermal camera pan (4th servo, on top of the arch tube) ----------------
cam_tilt    = 15;     // camera looks this far below horizontal
cam_hole_dx = 20;     // MLX90640 board hole spacing (board 28 x 16 mm, 2 mm holes).  MEASURE

// ---------------- derived ----------------
boss_y    = gap/2 + wall + boss_w/2;              // global y of the boss holes (left hull)
vp        = 6;                                    // pivot bracket plate thickness
blk_y0    = -vp - 3 - servo[2];                   // servo block front face, bracket-local y
arm_y     = gap/2 + blk_y0 - servo_top - 4;       // drive arm face (global, left): past the servo top/disc
coupler_y = arm_y - arm_t - 4;                    // coupler centre plane
idler_y   = coupler_y - 4;                        // idler arm face
alpha     = (pose == "deployed") ? deploy_a : stow_a;
cx        = pivot_x + arm_len * cos(alpha);       // coupler upper pivot
cz        = shaft_z + arm_len * sin(alpha);
rod_z     = cz - arm_gap - 12;

echo(str("Beam tube length: ", 2*(boss_y + 13), " mm"));
echo(str("Power box (v1.9): floor on the beams at z=", pb_z, ", lid top z=", pb_z + pb_H + pb_lid_t, "; beam centres in box coords x=", beam_x[0] - (plate_x + plate_L/2), " / ", beam_x[1] - (plate_x + plate_L/2)));
echo(str("Cradle width (rod centres): ", 2*coupler_y, " mm   [servo preset: ", servo_sel, "]"));
echo(str("Pose ", pose, ": cradle rod at z=", rod_z, " (", rod_z - draft, " mm vs waterline), x from ", cx - cradle_L, " to ", cx));

// ============================================================
//  HULL
// ============================================================
function bow_side(n, s) = [ for (i = [1:n]) let(t = i/n) [bow_len*t, s*(hull_W/2)*sqrt(t)] ];

module outline2d() {
    offset(r = tip_r) offset(r = -tip_r)
    polygon(concat(
        [[0, 0]],
        bow_side(24, 1),
        [[hull_L, hull_W/2], [hull_L, -hull_W/2]],
        [ for (i = [24:-1:1]) let(t = i/24) [bow_len*t, -(hull_W/2)*sqrt(t)] ]
    ));
}

module hull_solid()  linear_extrude(hull_H) outline2d();
module hull_cavity() translate([0, 0, floor_t]) linear_extrude(hull_H) offset(delta = -wall) outline2d();

module rib(x) intersection() {
    hull_solid();
    translate([x - rib_t/2, -hull_W, 0]) cube([rib_t, 2*hull_W, hull_H - rim_h]);
}

module bulkhead(x0) intersection() {
    hull_solid();
    translate([x0, -hull_W, 0]) cube([bulk_t, 2*hull_W, hull_H]);
}

module joint_holes(x0) {
    for (z = joint_bolt_z, s = [-1, 1])
        translate([x0 - 1, s*joint_bolt_y, z]) rotate([0, 90, 0]) cylinder(d = bolt_d, h = bulk_t + 2);
}

// rim boss on the inner side (local -y) with two vertical insert holes
module boss(x) difference() {
    intersection() {
        hull_solid();
        translate([x - boss_l/2, -hull_W/2, hull_H - boss_h]) cube([boss_l, wall + boss_w, boss_h]);
    }
    for (dx = [-boss_pitch/2, boss_pitch/2])
        translate([x + dx, -hull_W/2 + wall + boss_w/2, hull_H - boss_h + 3]) cylinder(d = insert_d, h = boss_h);
}

module hull_full() {
    difference() {
        union() {
            hull_solid();
            translate([hull_L, -tp_w/2, tp_z - tp_h/2]) cube([tp_t, tp_w, tp_h]);   // thruster pad
        }
        hull_cavity();
        for (dy = [-tp_pitch/2, tp_pitch/2], dz = [-tp_pitch/2, tp_pitch/2])       // blind insert holes
            translate([hull_L + tp_t - 5, dy, tp_z + dz]) rotate([0, 90, 0]) cylinder(d = insert_d, h = 6);
    }
    for (x = rib_x)  rib(x);
    for (x = boss_x) boss(x);
}

module hull_fore() {
    intersection() { hull_full(); translate([-1, -hull_W, -1]) cube([cut_x + 1, 2*hull_W, hull_H + 2]); }
    difference() { bulkhead(cut_x - bulk_t); joint_holes(cut_x - bulk_t); }
}

module hull_aft() {
    intersection() { hull_full(); translate([cut_x, -hull_W, -1]) cube([hull_L - cut_x + tp_t + 1, 2*hull_W, hull_H + 2]); }
    difference() { bulkhead(cut_x); joint_holes(cut_x); }
}

// ============================================================
//  BRACKETS
// ============================================================
// Saddle on a rim boss; the square tube lies across (along y). Origin = boss hole centre, rim top.
module beam_bracket() {
    w = boss_l; d = 26; fl = 6; h = fl + beam + 4;
    difference() {
        translate([-w/2, -d/2, 0]) cube([w, d, h]);
        translate([-beam/2 - 0.2, -d, fl]) cube([beam + 0.4, 2*d, h]);          // channel, open top
        for (dx = [-boss_pitch/2, boss_pitch/2]) {
            translate([dx, 0, -1]) cylinder(d = bolt_d, h = fl + 2);
            translate([dx, 0, fl - 3.4]) cylinder(d = 6.2, h = 4);                // counterbore for M3 head
        }
        translate([-w, 0, fl + beam/2]) rotate([0, 90, 0]) cylinder(d = bolt_d, h = 2*w);   // clamp bolt through tube
    }
}

// Clamps round the beam, drops to the ROB0154 tray floor. Origin = beam centre. Slide on from the tube end.
module chassis_hanger() {
    cw = 30; c = beam/2 + 5; bot = -c - chassis_drop;
    difference() {
        union() {
            translate([-c, -cw/2, -c]) cube([2*c, cw, 2*c]);                     // clamp block
            translate([-4, -cw/2, bot]) cube([8, cw, chassis_drop + 1]);          // drop plate
            translate([-25, -cw/2, bot - 4]) cube([50, cw, 4]);                   // foot
        }
        cube([beam + 0.4, cw + 2, beam + 0.4], center = true);                    // tube channel along y
        translate([0, 0, 0]) cylinder(d = 2.6, h = c + 1);                        // set screw from top (tap M3)
        for (dy = [-9, 9]) hull() for (dx = [-12, 12])
            translate([dx, dy, bot - 5]) cylinder(d = 3.4, h = 6);                // foot slots
    }
}

// Post on the bow boss with a saddle for the arch tube on top. Origin = boss hole centre, rim top.
module arch_post() {
    h = arch_z - hull_H; H = h + beam + 4;
    difference() {
        union() {
            translate([-post_w/2, -13, 0]) cube([post_w, 26, H]);
            translate([-boss_l/2, -13, 0]) cube([boss_l, 26, 8]);                 // base flange
        }
        for (dx = [-boss_pitch/2, boss_pitch/2]) {
            translate([dx, 0, -1]) cylinder(d = bolt_d, h = 10);
            translate([dx, 0, 4]) cylinder(d = 6.2, h = 10);
        }
        translate([-beam/2 - 0.2, -20, h]) cube([beam + 0.4, 40, beam + 6]);       // saddle, open top
        translate([-post_w, 0, h + beam/2]) rotate([0, 90, 0]) cylinder(d = bolt_d, h = 2*post_w);
    }
}

// Pivot bracket for the cradle lift. Local frame: origin at (pivot_x, inner wall, rim top);
// +y goes into the hull over the boss, -y into the gap. Holds the ST3215 with its shaft along -y.
module pivot_bracket() {
    pt = 6;
    zs = shaft_z - hull_H;
    x0 = -servo_shaft_off - servo_ear_dx - 5;
    x1 = servo[0] - servo_shaft_off + servo_ear_dx + 5;
    z0 = zs - arm_gap - 8;
    difference() {
        union() {
            translate([-boss_l/2, 0, 0]) cube([boss_l, wall + boss_w, pt]);                 // top plate on the boss
            translate([-boss_l/2, -vp, z0]) cube([boss_l, vp, -z0 + pt]);                   // plate down the inner face
            translate([x0, blk_y0, z0]) cube([x1 - x0, servo[2] + 3, -z0]);                 // servo block
            translate([0, blk_y0 + 0.01, zs - arm_gap]) rotate([90, 0, 0]) cylinder(d = 9, h = 16);   // idler boss
        }
        for (dx = [-boss_pitch/2, boss_pitch/2]) {
            translate([dx, wall + boss_w/2, -1]) cylinder(d = bolt_d, h = pt + 2);
            translate([dx, wall + boss_w/2, 3]) cylinder(d = 6.2, h = pt);
        }
        translate([-servo_shaft_off, blk_y0 - 1, zs - servo[1]/2]) cube([servo[0], servo[2] + 1, servo[1]]);   // pocket
        for (xe = [-servo_shaft_off - servo_ear_dx, servo[0] - servo_shaft_off + servo_ear_dx], dz = [-servo_ear_dz, servo_ear_dz])
            translate([xe, blk_y0 - 1, zs + dz]) rotate([-90, 0, 0]) cylinder(d = insert_d, h = 9);   // ear inserts
        translate([0, blk_y0 - 17, zs - arm_gap]) rotate([-90, 0, 0]) cylinder(d = 2.6, h = servo[2] + 18);   // idler pin (tap M3)
    }
}

// ============================================================
//  LIFT LINKAGE
// ============================================================
module arm(drive = false) {
    r0 = drive ? 14 : arm_w/2;
    difference() {
        linear_extrude(arm_t) hull() { circle(r = r0); translate([arm_len, 0]) circle(d = arm_w); }
        translate([arm_len, 0, -1]) cylinder(d = pin_d, h = arm_t + 2);
        translate([0, 0, -1]) cylinder(d = drive ? 6.5 : pin_d, h = arm_t + 2);
        if (drive) for (i = [0:disc_n - 1]) rotate(i*360/disc_n)
            translate([disc_r, 0, -1]) cylinder(d = disc_d, h = arm_t + 2);
    }
}

// Joins both arm ends and clamps the cradle rod. Plate in the x-z plane, pivots along y.
module coupler() {
    difference() {
        union() {
            rotate([90, 0, 0]) translate([0, 0, -4]) linear_extrude(8) hull() { circle(d = 14); translate([0, -arm_gap]) circle(d = 14); }
            translate([-8, -7, -arm_gap - 19]) cube([16, 14, 14]);                              // rod boss
        }
        for (z = [0, -arm_gap]) translate([0, 10, z]) rotate([90, 0, 0]) cylinder(d = pin_d, h = 20);
        translate([-10, 0, -arm_gap - 12]) rotate([0, 90, 0]) cylinder(d = rod_d, h = 20);      // rod along x
        translate([0, -10, -arm_gap - 12]) rotate([-90, 0, 0]) cylinder(d = 2.6, h = 8);       // set screw (tap M3)
    }
}

// ============================================================
//  THERMAL CAMERA PAN
// ============================================================
// Slides onto the arch tube before the tube goes into the posts. Servo pocket on top, shaft up.
module cam_pan_mount() {
    c  = beam/2 + 5;
    bx = servo[0] + 2*(servo_ear_dx + 5);
    by = servo[1] + 12;
    bz = servo[2] + 4;
    difference() {
        union() {
            translate([-c, -by/2, -c]) cube([2*c, by, 2*c]);                          // clamp round the tube
            translate([-bx/2, -by/2, c - 0.01]) cube([bx, by, bz]);                    // servo block on top
        }
        cube([beam + 0.4, by + 2, beam + 0.4], center = true);                         // tube channel along y
        translate([0, 0, -c - 1]) cylinder(d = 2.6, h = c);                            // set screw from below (tap M3)
        translate([-servo[0]/2, -servo[1]/2, c + bz - servo[2]]) cube([servo[0], servo[1], servo[2] + 1]);   // pocket, open top
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx*(servo[0]/2 + servo_ear_dx), sy*servo_ear_dz, c + bz - 8]) cylinder(d = insert_d, h = 9);   // ear inserts
    }
}

// Bolts to the servo disc; the MLX90640 sits on the tilted tab, lens forward (-x).
module cam_plate() {
    difference() {
        linear_extrude(4) hull() { circle(r = 14); translate([-26, 0]) circle(r = 12); }
        translate([0, 0, -1]) cylinder(d = 6.5, h = 6);
        for (i = [0:disc_n - 1]) rotate(i*360/disc_n) translate([disc_r, 0, -1]) cylinder(d = disc_d, h = 6);
    }
    translate([-30, 0, 0]) rotate([0, -cam_tilt, 0]) difference() {
        translate([0, -13, 0]) cube([3, 26, 22]);
        for (s = [-1, 1]) translate([-1, s*cam_hole_dx/2 - 1.1, 10]) cube([5, 2.2, 8]);   // slots for M2
    }
}

// ============================================================
//  TEST DUMMY HEAD ("Pesho") — hollow, hand warmer inside, vents on top, flat neck to glue on the foam torso
// ============================================================
head_d = 46; head_wall = 1.6; head_neck_d = 26; head_mouth_d = 28; head_vents = 6;
module dummy_head() {
    difference() {
        sphere(d = head_d);
        sphere(d = head_d - 2*head_wall);
        translate([0, 0, head_d/2 - 8]) cylinder(d = head_mouth_d, h = 20);            // opening for the warmer + lid
        translate([0, 0, -head_d]) cube([head_d, head_d, head_d - (head_neck_d/2) * 1.4], center = true);   // flat neck (prints flat)
        for (i = [0:head_vents - 1]) rotate([0, 0, i*360/head_vents]) translate([head_d/2 - 6, 0, head_d/2 - 12]) rotate([0, 20, 0]) cylinder(d = 3, h = 10);   // air vents
    }
}
module dummy_lid() {
    difference() {
        union() { cylinder(d = head_mouth_d - 0.4, h = 4); translate([0, 0, 4]) cylinder(d = head_mouth_d + 5, h = 1.6); }
        for (i = [0:3]) rotate([0, 0, i*90 + 45]) translate([8, 0, -1]) cylinder(d = 3, h = 8);   // vents in the lid
    }
}

// ============================================================
//  POWER BOX — printed enclosure on the chassis plate (fuse block, 2x BTS7960, bus bars, 50 A toggle on the front wall)
// ============================================================
module power_box() {
    cx_box = plate_x + plate_L/2;                                   // box centre x in the assembly
    bx_rel = [ for (b = beam_x) b - cx_box ];                       // beam centres in box coordinates (-55.1, 59.9)
    bts = [ for (mx = [-28, 28], sx = [-1, 1], sy = [-1, 1]) [mx + sx*20.4, -pb_W/2 + 30 + sy*20.4] ];   // BTS7960 40.8 mm pattern, -y half
    fus = [ for (sx = [-1, 1]) [sx*pb_fuse_x, pb_W/2 - 27] ];                                           // fuse block tabs, +y half
    difference() {
        union() {
            translate([-pb_L/2, -pb_W/2, 0]) cube([pb_L, pb_W, pb_H]);
            // corner bosses for the lid screws (M3 heat-set)
            for (sx = [-1, 1], sy = [-1, 1]) translate([sx*(pb_L/2 - 5), sy*(pb_W/2 - 5), 0]) cylinder(d = 9, h = pb_H);
            // locating rails under the floor, either side of each beam
            for (bx = bx_rel, s = [-1, 1]) translate([bx + s*(beam/2 + 0.3) + (s < 0 ? -3 : 0), -pb_W/2 + 8, -pb_rail]) cube([3, pb_W - 16, pb_rail + 0.01]);
            // standoff bosses (BTS7960 x2, fuse block)
            for (p = concat(bts, fus)) translate([p[0], p[1], pb_floor - 0.01]) cylinder(d = 8, h = pb_boss_h);
        }
        translate([-pb_L/2 + pb_wall, -pb_W/2 + pb_wall, pb_floor]) difference() {
            cube([pb_L - 2*pb_wall, pb_W - 2*pb_wall, pb_H]);                                          // cavity
            for (p = concat(bts, fus)) translate([p[0] + pb_L/2 - pb_wall, p[1] + pb_W/2 - pb_wall, -1]) cylinder(d = 8, h = pb_boss_h + 1);   // keep the bosses
        }
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx*(pb_L/2 - 5), sy*(pb_W/2 - 5), pb_H - 8]) cylinder(d = insert_d, h = 9);
        // insert holes in the standoff bosses (blind, from the top)
        for (p = concat(bts, fus)) translate([p[0], p[1], pb_floor + pb_boss_h - 6]) cylinder(d = insert_d, h = 7);
        // gasket groove along the top edge (2 mm wide, 1.2 deep) for silicone bead or EVA
        translate([0, 0, pb_H - 1.2]) linear_extrude(2) difference() { offset(delta = -1.2) square([pb_L, pb_W], center = true); offset(delta = -3.2) square([pb_L, pb_W], center = true); }
        // cable glands on the aft wall (+x), evenly spaced, centred at mid height
        for (i = [0:pb_gland_n - 1]) translate([pb_L/2 - pb_wall - 1, -pb_W/2 + pb_W*(i + 1)/(pb_gland_n + 1), pb_H*0.55]) rotate([0, 90, 0]) cylinder(d = pb_gland, h = pb_wall + 2);
        // 50 A toggle on the front wall (-x)
        translate([-pb_L/2 - 1, 0, pb_H*0.6]) rotate([0, 90, 0]) cylinder(d = pb_toggle, h = pb_wall + 2);
        // beam bolts: floor -> 15x15 tube -> ROB0154 plate slot (M3x30 + washers, nyloc under the plate)
        for (bx = bx_rel, sy = [-1, 1]) translate([bx, sy*pb_beam_y, -pb_rail - 1]) cylinder(d = bolt_d, h = pb_floor + pb_rail + 2);
    }
}
module power_lid() {
    difference() {
        union() {
            translate([-pb_L/2, -pb_W/2, 0]) cube([pb_L, pb_W, pb_lid_t]);
            translate([0, 0, pb_lid_t - 0.01]) linear_extrude(pb_lip) offset(delta = -pb_wall - 0.4) square([pb_L, pb_W], center = true);   // lip that drops into the box
        }
        translate([0, 0, pb_lid_t - 0.02]) linear_extrude(pb_lip + 1) offset(delta = -pb_wall - 2.8) square([pb_L, pb_W], center = true);  // hollow the lip
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx*(pb_L/2 - 5), sy*(pb_W/2 - 5), -1]) { cylinder(d = bolt_d, h = 10); translate([0, 0, 1]) cylinder(d = 6.2, h = 2.2); }
        // 4 holes for the pod dome flange, M3 (dome v2)
        for (a = [45:90:315]) rotate([0, 0, a]) translate([50, 0, -1]) cylinder(d = insert_d, h = 10);
    }
}

// ============================================================
//  ASSEMBLY
// ============================================================
module left_side() {
    translate([0, gap/2 + hull_W/2, 0]) { color("indianred") hull_fore(); color("firebrick") hull_aft(); }
    for (bx = beam_x) translate([bx, boss_y, hull_H]) color("gray") beam_bracket();
    translate([arch_x, boss_y, hull_H]) color("gray") arch_post();
    translate([pivot_x, gap/2, hull_H]) color("dimgray") pivot_bracket();
    translate([pivot_x, arm_y, shaft_z])            rotate([0, -alpha, 0]) rotate([90, 0, 0]) color("goldenrod") arm(true);
    translate([pivot_x, idler_y, shaft_z - arm_gap]) rotate([0, -alpha, 0]) rotate([90, 0, 0]) color("goldenrod") arm(false);
    translate([cx, coupler_y, cz]) color("darkgoldenrod") coupler();
}

module assembly() {
    left_side();
    mirror([0, 1, 0]) left_side();
    // beams and arch tube
    for (bx = beam_x) translate([bx, 0, hull_H + 6 + beam/2]) color("silver") cube([beam, 2*(boss_y + 13), beam], center = true);
    translate([arch_x, 0, arch_z + beam/2]) color("silver") cube([beam, 2*(boss_y + 13), beam], center = true);
    translate([arch_x, 0, arch_z + beam/2]) color("dimgray") cam_pan_mount();
    translate([arch_x - servo[0]/2 + servo_shaft_off, 0, arch_z + beam/2 + beam/2 + 5 + servo[2] + 4 + 3]) color("darkgoldenrod") cam_plate();
    // cradle rod (buy: 5 mm aluminium, bend the front corners)
    color("red") {
        for (s = [-1, 1]) translate([cx - cradle_L, s*coupler_y, rod_z]) rotate([0, 90, 0]) cylinder(d = 5, h = cradle_L + 8);
        translate([cx - cradle_L, -coupler_y, rod_z]) rotate([-90, 0, 0]) cylinder(d = 5, h = 2*coupler_y);
    }
    // references
    %translate([ch_x, -ch_W/2, chassis_raise]) cube([ch_L, ch_W, ch_H]);                           // ROB0154 track envelope
    color("gray") translate([plate_x, -plate_W/2, chassis_raise + ch_H - plate_t]) cube([plate_L, plate_W, plate_t]);   // top plate, bolted under the beams
    translate([plate_x + plate_L/2, 0, pb_z]) { color("slategray") power_box(); color("lightslategray") translate([0, 0, pb_H + pb_lid_t]) mirror([0, 0, 1]) power_lid(); }   // v1.9: on the beams
    %translate([plate_x + plate_L/2, 0, pb_z + pb_H + pb_lid_t]) scale([1.3, 1, 0.45]) sphere(r = 100);   // pod dome (v2) on the lid
    %color("lightblue", 0.3) translate([-300, -260, draft - 0.5]) cube([hull_L + 600, 520, 1]);   // water
    if (pose == "deployed")
        %color("gray") translate([cx - cradle_L/2, 0, draft - 12]) rotate([0, 90, 0]) cylinder(d = 40, h = 200, center = true);   // 20 cm dummy
}

// ============================================================
//  PART SELECTOR
// ============================================================
module mir() mirror([0, side < 0 ? 1 : 0, 0]) children();

if (part == "assembly")            assembly();
else if (part == "hull_fore")      mir() hull_fore();
else if (part == "hull_aft")       mir() hull_aft();
else if (part == "plate_check") {
    %square(300);
    translate([150, 150]) rotate(45) translate([-(hull_L - cut_x + tp_t)/2, -hull_W/2])
        projection() translate([-cut_x, 0, 0]) hull_aft();
}
else if (part == "beam_bracket")   beam_bracket();
else if (part == "chassis_hanger") rotate([90, 0, 0]) chassis_hanger();
else if (part == "arch_post")      rotate([90, 0, 0]) arch_post();
else if (part == "pivot_bracket")  mir() rotate([-90, 0, 0]) pivot_bracket();
else if (part == "arm_drive")      arm(true);
else if (part == "arm_idler")      arm(false);
else if (part == "coupler")        rotate([90, 0, 0]) coupler();
else if (part == "cam_pan_mount")  cam_pan_mount();
else if (part == "cam_plate")      cam_plate();
else if (part == "dummy_head")     dummy_head();
else if (part == "dummy_lid")      dummy_lid();
else if (part == "power_box")      power_box();
else if (part == "power_lid")      power_lid();
