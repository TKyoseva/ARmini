// ============================================================
//  AmphiReach  AR-Mini  v2.0  (kick-up thruster mount + measured ROB0154 plate, 9.10)  —  parametric CAD (OpenSCAD)
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
//   cam_pan_mount x1              upside down (servo face on the bed), no supports (slide onto the arch tube first)
//   cam_plate x1                  flat, tab prints at 75 deg without supports. NOT YET for the MG90S: hole pattern is the TD disc, needs the MG90S horn measured
//   Pesho (dummy)                 → cad/pesho/pesho.py (body red PLA, head + lid white PETG)
//   power_box x1, power_lid x1    PETG, 4 perimeters; sits ON the two cross-beams (v1.9), holds fuse block + 2x BTS7960 + bus bars
//                                 4 x M3x30 + washers: box floor slot -> beam tube (match-drilled on assembly) -> ROB0154 plate slot -> nut
//   thruster_bracket x2           PETG; bolts to the transom pad above the waterline (4 x M3), carries the hinge pin
//   thruster_arm x2               PETG, 6 perimeters; 4 x M4 into the thruster's brass inserts, swings on a 5 mm rod
//   thruster_coupon x1            PLA, 20 min; L005: do all 4 M4 screws go in by hand at 35.0 x 15.9?
//
//  v2.0 (9.10, from L001 + L003): ROB0154 plate measured 151.82 x 134.8, its two transverse slots are 11.3 / 26.4 mm from the
//   plate edges (octagonal hole forward) -> ch_x 290 -> 300 puts the slots under the beams (385 / 500). Power-box beam holes became
//   3.4 x 7 slots along x. Thruster measured: duct 72.27 OD x 112, face 47.10 above the axis, M4 at 35 x 15.6 -> a 72 mm duct cannot sit
//   under a 42 mm waterline on a flat stern pad, so the pad below the waterline is gone: kick-up hinge on the transom, pin 33 mm above the
//   waterline, thruster folds up on shore. No holes below the waterline.
// ============================================================

part = "assembly";   // assembly | hull_fore | hull_aft | plate_check | beam_bracket | arch_post | pivot_bracket | arm_drive | arm_idler | coupler | cam_pan_mount | cam_plate | power_box | power_lid | thruster_bracket | thruster_arm | thruster_coupon
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
draft   = 42;                     // predicted waterline at ~4.7 kg total mass (L003: 8.9 mm/kg; chassis kit alone 1175 g measured -> 41.8)

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
plate_L = 151.82; plate_W = 134.8; plate_t = 2; // the aluminium top plate, MEASURED 8.10 (L003); CAD v1.9 had 152.2
plate_slot = [11.3, plate_L - 26.4];            // MEASURED L003: the two transverse M3 slots, centres from the plate's FORWARD edge (octagonal hole forward)
plate_slot_w = 3.2;                             // slot width (M3 passes); length not measured -> drawn 100
plate_slot_len = 100;                           // VERIFY (L004)
ch_x = 300;                                     // front of the track footprint. v2.0: 290 -> 300 so the plate slots land under the beams (decision L003)
plate_x = ch_x + (ch_L - plate_L)/2;            // plate centred on the footprint -> 374.1..525.9 (ASSUMED centred: measure track front -> plate edge, L004)
beam_bot = hull_H + 6;                          // tube underside when sitting in the rim brackets (126)
chassis_raise = 0;                              // 0 = tracks flush with the hull bottom (beach together). Raise if drag is a problem.
plate_gap = beam_bot - (chassis_raise + ch_H);  // plate hangs this far under the beams -> washers (1.4 mm)
motor_axis = 62;                                // MEASURED 2.10: track bottom -> drive sprocket axis
echo(str("Track bottom z=", chassis_raise, "; plate hangs ", plate_gap, " mm under the beams; motor axis z=", chassis_raise + motor_axis, " vs waterline ", draft, " (margin ", chassis_raise + motor_axis - draft, " mm)"));
echo(str("Plate slots at x=", plate_x + plate_slot[0], " / ", plate_x + plate_slot[1], " vs beams ", beam_x[0], " / ", beam_x[1], " (offsets ", plate_x + plate_slot[0] - beam_x[0], " / ", plate_x + plate_slot[1] - beam_x[1], " mm; box slots allow +/-1.8)"));
echo(str("Tracks x ", ch_x, "..", ch_x + ch_L, " (hull ends at ", hull_L, "); stowed cradle ends at x=", pivot_x + arm_len*cos(stow_a), " -> ", ch_x - (pivot_x + arm_len*cos(stow_a)), " mm clear"));

// ---------------- bow arch (mast for the thermal camera) ----------------
arch_x = 165;         // on the straight part of the hull, just ahead of the pivot boss
arch_z = 235;         // underside of the arch tube; clears the cradle sweep (min 19 mm)
post_w = 20;

// ---------------- thruster: Cuifati 12 V, kick-up mount on the transom (v2.0, MEASURED 8.10 / L001) ----------------
th_duct_d   = 72.27;  // duct OD (box drawing said 77)
th_duct_L   = 112;
th_face_z   = 47.10;  // thruster mounting face above the prop axis
th_frame_t  = 9.68;   // frame thickness (brass inserts in it)
th_pitch    = [35.0, 15.9];   // M4 inserts c-c [along the duct, across]. MEASURED 10.10 (inner/outer edges): along 31.17/38.86 -> 35.02, across 12.25/19.50 -> 15.88 (8.10 guess 15.6). Coupon C005 confirms
th_screw_d  = 4.5;    // clearance holes for the M4 screws (thread 3.93 measured; screw length 28.4 -> VERIFY vs 5 mm plate + 9.68 frame)
th_mass     = 206;    // g each with cable and screws (the other one 201)
th_frame_dx = 0;      // frame centre along the duct, from the duct centre.  MEASURE (L005)
th_submerge = 10;     // duct top this far under the waterline when deployed
th_axis_z   = draft - th_submerge - th_duct_d/2;   // prop axis -> -4.1: duct bottom 40 mm BELOW the hull. On shore the kick-up folds it away.
th_pivot_z  = 75;     // hinge pin above the hull bottom = 33 mm above the waterline. Nothing is drilled below the waterline.
th_pin_dx   = 19;     // pin aft of the transom pad face. Was 14: the arm boss (r 12) reached x = 2, inside the 6 mm bracket plate (FAILS 151). Now boss front at x = 7, 1 mm clear
th_aft      = 47;     // duct centre aft of the pin (deployed): duct nose 5 mm aft of the pad and clears it through the whole swing
th_kick     = 0;      // assembly only: 0 = deployed, 100 = kicked up on shore
th_pin_d    = 5.3;    // the hinge pin is the same 5 mm aluminium rod as the cradle, 60 mm, R-clips in 1.5 mm cross holes
th_lock_d   = 3.3;    // M3 lock pin: 2 holes in the lug (deployed / stowed), 1 in the arm cheek. Deployed lock = reverse thrust allowed.
th_lock_r   = 10;     // lock-pin radius from the hinge
tp_w = 56; tp_h = 70; tp_t = 6;   // transom pad: printed with the hull, 4 x M3 blind inserts, ALL above the waterline
tp_z = 79;            // pad centre -> z 44..114
tp_pitch = 40;        // insert pattern (y +/-20, z 59 / 99)
th_plate = [50, 30, 5];               // arm plate on the thruster face (same as the coupon)
assert(th_pin_dx - 6 >= 12 + 1, "thruster arm boss hits the bracket plate");   // 6 = bracket plate thickness, 12 = arm boss radius, 1 = clearance


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
servo           = servo_sel == "TD8120" ? [40.7, 20.4, 28.8] : [45.5, 25.5, 35.5];   // POCKET L (x), W (z, shaft face), depth bottom→ear plane (y). TD MEASURED 10.10 (C017): body 40.40 x 20.17 x 40.85, bottom→ear plane 28.51 (5.10 said 40.3 x 20.14, 28.0)
servo_shaft_off = servo_sel == "TD8120" ? 10.4 : 11;      // shaft centre from the servo's forward end (TD MEASURED 10.4)
servo_ear_dx    = servo_sel == "TD8120" ? 3.78 : 5;       // ear holes beyond the pocket end: span = servo[0] + 2*dx. TD MEASURED 10.10: hole c-c 48.26 along the body (inner edges 44.35, outer 52.16; the 5.10 "50" was wrong)
servo_ear_dz    = servo_sel == "TD8120" ? 4.825 : 8;      // ear holes +/- from the shaft axis (TD MEASURED 10.10: 9.65 apart, hole d4.05 -> M3)
servo_top       = servo_sel == "TD8120" ? 12.34 : 0;      // case top past the ear plane (TD MEASURED 10.10: 40.85 - 28.51)
servo_disc_h    = servo_sel == "TD8120" ? 8.84 : 4;       // case top -> disc top face, disc pushed fully onto the spline (TD MEASURED 10.10: 14.84 to the arm top - arm_t 6). ST3215: MEASURE
disc_r = 8; disc_n = 4; disc_d = 2.4;   // servo disc bolt circle. TD FITTED 10.10 (C017): black plastic 25T disc from the bag, ring c-c ~16 (inner edges 13.75); the bag screws bite in the disc

// ---------------- thermal camera pan (4th servo, on top of the arch tube) ----------------
cam_tilt    = 15;     // camera looks this far below horizontal
cam_hole_dx = 20;     // MLX90640 board hole spacing (board 28 x 16 mm, 2 mm holes).  MEASURE
// Camera pan servo: MG90S (chosen 20.10), not the TD-8120MG of the pivot brackets. Values = catalogue drawing + clearance.
cam_servo     = [22.8, 12.4, 16.3];   // pocket L (x), W (y), depth bottom→ear plane (z). Catalogue 22.4 x 12 x 16 + 0.4 / 0.4 / 0.3. MEASURE
cam_ear_dx    = 2.45;    // ear hole centre beyond the pocket end: c-c = 22.8 + 2*2.45 = 27.7 (catalogue). One hole per ear, on the axis. MEASURE
cam_ear_d     = 1.6;     // M2 self-tapping screw (M2 kit), no inserts in a 20 mm block
cam_shaft_off = 5.9;     // shaft centre from the pocket end, -x (not on the drawing). MEASURE
cam_horn_h    = 16;      // ear plane → horn top face (catalogue 32 - 16). MEASURE
cam_cable_w   = 7;       // cable window at the bottom of both end walls (outlet side not known yet); the 3-pin plug (7.6 x 2.6) threads through on edge
cam_cable_h   = 8;       // window height from the pocket floor; its top is 8.3 below the ear face, the 6 mm deep M2 holes end 2.3 above it

// ---------------- derived ----------------
boss_y    = gap/2 + wall + boss_w/2;              // global y of the boss holes (left hull)
vp        = 6;                                    // pivot bracket plate thickness
blk_y0    = -vp - 3 - servo[2];                   // servo block front face, bracket-local y
arm_y     = gap/2 + blk_y0 - servo_top - servo_disc_h;   // drive arm face (global, left): on the disc top
idler_boss_L = servo_top + servo_disc_h - 0.7;     // was a fixed 16 (= 12.7 + 4 - 0.7); TD now 20.48
coupler_y = arm_y - arm_t - 4;                    // coupler centre plane
idler_y   = coupler_y - 4;                        // idler arm face
alpha     = (pose == "deployed") ? deploy_a : stow_a;
cx        = pivot_x + arm_len * cos(alpha);       // coupler upper pivot
cz        = shaft_z + arm_len * sin(alpha);
rod_z     = cz - arm_gap - 12;
th_plate_dz = th_axis_z + th_face_z + th_plate[2]/2 - th_pivot_z;   // arm plate centre below the pin (-29.5)
th_lock_a   = atan2(th_plate_dz, th_aft);                           // direction pin -> plate centre, deployed (-32 deg)

echo(str("Beam tube length: ", 2*(boss_y + 13), " mm"));
echo(str("Power box (v1.9): floor on the beams at z=", pb_z, ", lid top z=", pb_z + pb_H + pb_lid_t, "; beam centres in box coords x=", beam_x[0] - (plate_x + plate_L/2), " / ", beam_x[1] - (plate_x + plate_L/2)));
echo(str("Cradle width (rod centres): ", 2*coupler_y, " mm   [servo preset: ", servo_sel, "]"));
echo(str("Thruster deployed: axis z=", th_axis_z, ", duct bottom z=", th_axis_z - th_duct_d/2, ", duct top ", draft - (th_axis_z + th_duct_d/2), " mm under the waterline; arm plate z=", th_axis_z + th_face_z, "; overall length ", hull_L + tp_t + th_pin_dx + th_aft + th_duct_L/2, " mm"));
echo(str("Thruster hinge: pin z=", th_pivot_z, " (", th_pivot_z - draft, " above the waterline); lock angles deployed ", th_lock_a, " / stowed ", th_lock_a + 100, " deg"));
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
        for (dy = [-tp_pitch/2, tp_pitch/2], dz = [-tp_pitch/2, tp_pitch/2])       // blind insert holes, z 59 / 99: above the waterline
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
            translate([0, blk_y0 + 0.01, zs - arm_gap]) rotate([90, 0, 0]) cylinder(d = 9, h = idler_boss_L);   // idler boss, ends 0.7 short of the drive arm plane
        }
        for (dx = [-boss_pitch/2, boss_pitch/2]) {
            translate([dx, wall + boss_w/2, -1]) cylinder(d = bolt_d, h = pt + 2);
            translate([dx, wall + boss_w/2, 3]) cylinder(d = 6.2, h = pt);
        }
        translate([-servo_shaft_off, blk_y0 - 1, zs - servo[1]/2]) cube([servo[0], servo[2] + 1, servo[1]]);   // pocket
        for (xe = [-servo_shaft_off - servo_ear_dx, servo[0] - servo_shaft_off + servo_ear_dx], dz = [-servo_ear_dz, servo_ear_dz])
            translate([xe, blk_y0 - 1, zs + dz]) rotate([-90, 0, 0]) cylinder(d = insert_d, h = 9);   // ear inserts
        translate([0, blk_y0 - idler_boss_L - 1, zs - arm_gap]) rotate([-90, 0, 0]) cylinder(d = 2.6, h = servo[2] + idler_boss_L + 2);   // idler pin (tap M3)
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
// Slides onto the arch tube before the tube goes into the posts. MG90S pocket on top, shaft up (at -x).
module cam_pan_mount() {
    c  = beam/2 + 5;
    sv = cam_servo;
    bx = sv[0] + 2*(cam_ear_dx + 5);
    by = sv[1] + 12;
    bz = sv[2] + 4;
    difference() {
        union() {
            translate([-c, -by/2, -c]) cube([2*c, by, 2*c]);                          // clamp round the tube
            translate([-bx/2, -by/2, c - 0.01]) cube([bx, by, bz]);                    // servo block on top
        }
        cube([beam + 0.4, by + 2, beam + 0.4], center = true);                         // tube channel along y
        translate([0, 0, -c - 1]) cylinder(d = 2.6, h = c);                            // set screw from below (tap M3)
        translate([-sv[0]/2, -sv[1]/2, c + bz - sv[2]]) cube([sv[0], sv[1], sv[2] + 1]);   // pocket, open top
        for (sx = [-1, 1])
            translate([sx*(sv[0]/2 + cam_ear_dx), 0, c + bz - 6]) cylinder(d = cam_ear_d, h = 7);   // ear screws, M2 self-tapping
        for (sx = [-1, 1])
            translate([sx > 0 ? sv[0]/2 - 1 : -bx/2 - 1, -cam_cable_w/2, c + bz - sv[2]]) cube([(bx - sv[0])/2 + 2, cam_cable_w, cam_cable_h]);   // cable windows, both ends (FAILS 158)
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
//  TEST DUMMY "Pesho": moved to cad/pesho/pesho.py (v3, 12.10). Body, head and lid are generated there
//  (signed-distance fields → build/pesho_*.stl) together with the floating check, so one file holds the
//  geometry and the numbers. The assembly below still shows him as the grey 40 × 200 reference cylinder.
// ============================================================

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
        // beam bolts: floor SLOT 3.4 x 7 along x (v2.0) -> 15x15 tube (match-drilled through the plate slots on assembly) -> ROB0154 plate slot -> nyloc
        for (bx = bx_rel, sy = [-1, 1]) hull() for (dx = [-1.8, 1.8]) translate([bx + dx, sy*pb_beam_y, -pb_rail - 1]) cylinder(d = bolt_d, h = pb_floor + pb_rail + 2);
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
//  THRUSTER KICK-UP MOUNT (v2.0)   origin = transom pad face, hull centreline, hull bottom
// ============================================================
// Transom side: plate on the pad (4 x M3) + two lugs carrying the 5 mm pin. Nothing below the waterline.
module thruster_bracket() {
    lug_y = [19, 25];                     // lug faces |y|; the arm cheeks run inside them at 12.5..18.5
    difference() {
        union() {
            translate([0, -25, tp_z - 32]) cube([6, 50, 64]);                                   // plate z 47..111
            for (s = [-1, 1]) hull() {                                                           // lugs, aft to the pin
                translate([0, s*lug_y[0] - (s < 0 ? 6 : 0), th_pivot_z - 14]) cube([1, 6, 28]);
                translate([th_pin_dx, s*(lug_y[0] + 3), th_pivot_z]) rotate([90, 0, 0]) cylinder(r = 14, h = 6, center = true);
            }
        }
        for (dy = [-tp_pitch/2, tp_pitch/2], dz = [-tp_pitch/2, tp_pitch/2]) translate([-1, dy, tp_z + dz]) rotate([0, 90, 0]) { cylinder(d = bolt_d, h = 8); translate([0, 0, 4]) cylinder(d = 6.2, h = 4); }
        translate([th_pin_dx, 0, th_pivot_z]) rotate([90, 0, 0]) cylinder(d = th_pin_d, h = 80, center = true);           // hinge pin
        for (a = [th_lock_a, th_lock_a + 100])                                                                              // lock pin: deployed / stowed
            translate([th_pin_dx + th_lock_r*cos(a), 0, th_pivot_z + th_lock_r*sin(a)]) rotate([90, 0, 0]) cylinder(d = th_lock_d, h = 80, center = true);
    }
}
// Swing arm: origin = hinge pin. Plate on the thruster face aft and below; cheeks between the lugs; forward tab = stop on the bracket plate.
module thruster_arm() {
    pz = th_plate_dz;                     // plate centre below the pin
    difference() {
        union() {
            translate([th_aft - th_plate[0]/2, -th_plate[1]/2, pz - th_plate[2]/2]) cube(th_plate);
            for (s = [-1, 1]) translate([0, s*15.5, 0]) rotate([90, 0, 0]) linear_extrude(6, center = true) hull() {   // cheeks |y| 12.5..18.5
                circle(r = 12);
                translate([-8, -6]) square([8, 12]);                                                                    // stop tab against the bracket plate (x = -8)
                translate([th_aft - th_plate[0]/2, pz - th_plate[2]/2]) square([th_plate[0], th_plate[2]]);
            }
        }
        rotate([90, 0, 0]) cylinder(d = th_pin_d, h = 60, center = true);
        translate([th_lock_r*cos(th_lock_a), 0, th_lock_r*sin(th_lock_a)]) rotate([90, 0, 0]) cylinder(d = th_lock_d, h = 60, center = true);
        for (dx = [-1, 1], dy = [-1, 1]) translate([th_aft + dx*th_pitch[0]/2, dy*th_pitch[1]/2, pz - 10]) cylinder(d = th_screw_d, h = 20);   // M4 to the thruster inserts
    }
}
// Ghost of the real thruster, arm coordinates (deployed)
module thruster_ref() {
    ax = th_axis_z - th_pivot_z;
    %translate([th_aft - th_frame_dx, 0, ax]) rotate([0, 90, 0]) cylinder(d = th_duct_d, h = th_duct_L, center = true);       // duct
    %translate([th_aft - 25, -15, ax + th_duct_d/2 - 2]) cube([50, 30, th_face_z - th_duct_d/2 + 2]);                     // frame up to the mounting face
}
// L005 coupon: does the measured pattern fit the real screws?
module thruster_coupon() difference() {
    translate([-25, -15, 0]) cube([50, 30, 5]);
    for (dx = [-1, 1], dy = [-1, 1]) translate([dx*th_pitch[0]/2, dy*th_pitch[1]/2, -1]) cylinder(d = th_screw_d, h = 7);
}
module thruster_mount() {                // placed at the transom pad face of one hull
    color("dimgray") thruster_bracket();
    translate([th_pin_dx, 0, th_pivot_z]) rotate([0, -th_kick, 0]) { color("gray") thruster_arm(); thruster_ref(); }
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
    translate([hull_L + tp_t, gap/2 + hull_W/2, 0]) thruster_mount();
}

module assembly() {
    left_side();
    mirror([0, 1, 0]) left_side();
    // beams and arch tube
    for (bx = beam_x) translate([bx, 0, hull_H + 6 + beam/2]) color("silver") cube([beam, 2*(boss_y + 13), beam], center = true);
    translate([arch_x, 0, arch_z + beam/2]) color("silver") cube([beam, 2*(boss_y + 13), beam], center = true);
    translate([arch_x, 0, arch_z + beam/2]) color("dimgray") cam_pan_mount();
    translate([arch_x - cam_servo[0]/2 + cam_shaft_off, 0, arch_z + beam/2 + beam/2 + 5 + cam_servo[2] + 4 + cam_horn_h]) color("darkgoldenrod") cam_plate();
    // cradle rod (buy: 5 mm aluminium, bend the front corners)
    color("red") {
        for (s = [-1, 1]) translate([cx - cradle_L, s*coupler_y, rod_z]) rotate([0, 90, 0]) cylinder(d = 5, h = cradle_L + 8);
        translate([cx - cradle_L, -coupler_y, rod_z]) rotate([-90, 0, 0]) cylinder(d = 5, h = 2*coupler_y);
    }
    // references
    %translate([ch_x, -ch_W/2, chassis_raise]) cube([ch_L, ch_W, ch_H]);                           // ROB0154 track envelope
    color("gray") translate([plate_x, -plate_W/2, chassis_raise + ch_H - plate_t]) difference() {                      // top plate (measured), its two transverse slots shown
        cube([plate_L, plate_W, plate_t]);
        for (sx = plate_slot) translate([sx - plate_slot_w/2, (plate_W - plate_slot_len)/2, -1]) cube([plate_slot_w, plate_slot_len, plate_t + 2]);
    }
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
else if (part == "power_box")      power_box();
else if (part == "power_lid")      power_lid();
else if (part == "thruster_bracket") thruster_bracket();
else if (part == "thruster_arm")   thruster_arm();
else if (part == "thruster_coupon") thruster_coupon();
