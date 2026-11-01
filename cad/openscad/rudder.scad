// AR-Mini · centre-line rudder for the beam_leg thruster (29.10.2026). After rudder-1026/RUDDER_SPEC.md,
// heights moved for beam_leg deep rows (prop axis global z -34, duct top +2, duct exit x 635.7).
// Local coords: origin = duct axis at the duct EXIT face, +x aft, +z up. Global z = local z - 34.
// Parts: rudder_mount (collar + bearing arm + MG90S seat, one print), rudder_blade (NACA 0015), rudder_hub.
// Stock: Ø5 alu rod cut to 112 mm, two flats filed 0.5 mm deep: bottom 30 mm (blade) and top 10 mm (hub grub).
$fn = 64;
part = "all";            // all | mount | blade | hub   (print orientation for single parts)

duct_d   = 72.27;
col_id   = 72.6; col_w = 12; col_t = 4;
col_r    = col_id/2 + col_t;
stock_x  = 52.5;         // LE 40 aft of the duct rim (tail cone sticks out 34.7 MEASURED 29.10 IMG_2651, Ø32.2 at the rim IMG_2652) + 25 % of chord 50
stock_d  = 5.3;          // bearing hole
P        = 94;           // ear plane (seat top) local = global 60
horn_dz  = 16;           // ear plane -> horn face (cam_horn_h, MEASURE)
sv       = [23.6, 12.6]; // MG90S pocket: body 23.14 MEASURED 29.10 (IMG_2648, catalogue 22.4) + 0.46; width catalogue 12 + 0.6
sv_shaft = 6.1;          // shaft from the pocket end (catalogue 5.9 + half the extra clearance, MEASURE)
ear_dx   = 2.05; ear_d = 1.6;   // ear tips 31.60 MEASURED (IMG_2646, catalogue 31.8), hole c-c 27.7 (catalogue) = 23.6 + 2 x 2.05; total height 32.28 (IMG_2647, catalogue 32)
brg_z    = [40, 48];     // bearing plate, sits on the collar top (global 6..14)
blade_c  = 50; blade_t = 0.15;
blade_z  = [-38, 37];    // local = global -72..+3 (jet -70..+2), 3 mm under the bearing plate
half_w   = 15;           // half width of the seat; side walls at |y| 12..15 clear a single-arm horn at +/-30°

module naca(c, t) {
    pts = [ for (i = [0:40]) let(x = i/40) [x*c, 5*t*c*(0.2969*sqrt(x) - 0.1260*x - 0.3516*x*x + 0.2843*x*x*x - 0.1036*x*x*x*x)] ];
    polygon(concat(pts, [ for (i = [40:-1:0]) [pts[i][0], -pts[i][1]] ]));
}

module rudder_mount() difference() {
    union() {
        rotate([0, 90, 0]) translate([0, 0, -col_w]) cylinder(r = col_r, h = col_w);                         // collar
        for (s = [-1, 1]) translate([-col_w, s > 0 ? 1 : -7, -col_r - 9]) cube([col_w, 6, 12]);           // clamp ears at the bottom split
        translate([-col_w, -8, 30]) cube([col_w, 16, P - 30]);                                            // post
        translate([-col_w, -8, brg_z[0]]) cube([stock_x + 8 + col_w, 16, brg_z[1] - brg_z[0]]);           // bearing arm
        translate([-col_w, -half_w, P - 4]) cube([stock_x - sv_shaft + sv[0] + ear_dx + 5 + col_w, 2*half_w, 4]);   // servo seat
        for (s = [-1, 1]) translate([-col_w, s > 0 ? half_w - 3 : -half_w, brg_z[0]])                    // side walls, forward part only
            hull() { cube([col_w + 2, 3, P - brg_z[0]]); translate([0, 0, P - 6]) cube([stock_x - 8 + col_w, 3, 6]); }
        for (s = [-1, 1]) translate([-col_w, s > 0 ? 8 : -half_w + 3 - 0.01, P - 12]) cube([col_w, half_w - 11 + 0.02, 12]);   // tie walls to post
    }
    rotate([0, 90, 0]) translate([0, 0, -col_w - 1]) cylinder(d = col_id, h = col_w + 2);               // duct bore
    translate([-col_w - 1, -1, -col_r - 10]) cube([col_w + 2, 2, col_t + 12]);                          // split
    translate([-col_w/2, 0, -col_r - 4]) rotate([90, 0, 0]) cylinder(d = 3.4, h = 20, center = true);  // M3 x 16 clamp bolt
    translate([stock_x, 0, brg_z[0] - 1]) cylinder(d = stock_d, h = 20);                               // bearing
    translate([stock_x - sv_shaft, -sv[1]/2, P - 5]) cube([sv[0], sv[1], 6]);                           // servo cut-out (body drops in from the top, shaft down)
    for (x = [stock_x - sv_shaft - ear_dx, stock_x - sv_shaft + sv[0] + ear_dx]) translate([x, 0, P - 5]) cylinder(d = ear_d, h = 6);
}

module rudder_blade() difference() {
    translate([stock_x - 12.5, 0, blade_z[0]]) linear_extrude(blade_z[1] - blade_z[0]) naca(blade_c, blade_t);
    translate([stock_x, 0, blade_z[0] + 2]) intersection() {                                           // D bore, closed bottom
        cylinder(d = 5.15, h = 100);
        translate([-3, -2.0, 0]) cube([6, 6, 100]);                                                    // flat 0.5 mm on the -y side
    }
}

module rudder_hub() difference() {                    // under the inverted MG90S horn; origin = horn face
    union() { translate([0, 0, -3]) cylinder(d = 26, h = 3); translate([0, 0, -15]) cylinder(d = 16, h = 12); }
    translate([-3, -13, -1.5]) cube([6, 26, 2]);       // slot for the single-arm horn (MEASURE arm width)
    translate([0, 0, -3.5]) cylinder(d = 7, h = 4);    // horn screw head
    translate([0, 0, -16]) cylinder(d = 5.2, h = 11);  // stock bore 10 deep
    translate([0, 0, -10]) rotate([90, 0, 0]) cylinder(d = 4.0, h = 10);   // ruthex M3 insert -> M3 grub onto the top flat
}

if (part == "all") {
    color("steelblue") rudder_mount();
    color("orange") rudder_blade();
    color("gray") translate([stock_x, 0, P - horn_dz]) rudder_hub();
    color("silver") translate([stock_x, 0, blade_z[0] + 2]) cylinder(d = 5, h = 112);
    %rotate([0, 90, 0]) translate([0, 0, -112]) cylinder(d = duct_d, h = 112);
    %translate([stock_x - sv_shaft, -sv[1]/2, P]) cube([sv[0], sv[1], 16.3]);
} else if (part == "mount") rotate([0, -90, 0]) translate([col_w, 0, 0]) rudder_mount();    // collar face on the bed, no supports
else if (part == "blade") translate([0, 0, -blade_z[0]]) rudder_blade();                     // standing, bore up
else if (part == "hub")   rotate([180, 0, 0]) translate([0, 0, 0]) rudder_hub();             // flange on the bed
echo(str("stock: hub bore bottom local ", P - horn_dz - 15, ", blade bore bottom ", blade_z[0] + 2, " -> length ", P - horn_dz - 15 + 10 - (blade_z[0] + 2)));
