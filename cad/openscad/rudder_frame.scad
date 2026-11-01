// AR-Mini · rudder_frame (29.10.2026 evening): one-piece rudder support bolted to the beam_leg, NO collar on the duct.
// Replaces rudder_mount (the collar could not go on the duct, IMG_2680). Reuses rudder_blade, rudder_hub and the Ø5 stock.
// Global coords as beam_leg.scad: x from the bow (aft +), z from the hull bottom, y across. Print lying on the -y side, supports none.
// The 6 mm plate sits BETWEEN the beam_leg pad and the thruster_bracket (rows 29/69 go through both, M3 x 20),
// plus 2 x M3 x 12 into the free row 89. Everything aft of the pad (thruster, rudder) moves 6 mm aft.
$fn = 48;
pad_x   = 513.7;          // beam_leg aft pad face
t       = 6;              // frame plate thickness
W       = 50;             // = beam_leg / thruster_bracket width
exit_x  = pad_x + t + 19 + 47 + 112/2;   // duct exit face: pin 19 aft of the bracket face, duct centre 47 aft of the pin, duct 112 long
stock_x = exit_x + 52.5;  // same as rudder.scad: blade LE 40 aft of the rim (tail cone 34.7)
// heights (global) unchanged from rudder.scad, so blade, hub and the 110 mm stock still fit
brg_z   = [6, 14];        // bearing arm (hole Ø5.3)
P       = 60;             // MG90S ear plane = seat top
sv      = [23.6, 12.6]; sv_shaft = 6.1; ear_dx = 2.05; ear_d = 1.6;
half_w  = 15;
boom_z  = [96, 112];
boom_y  = -9;             // boom + gusset run on the -y side (y -25..-9): the thruster cable stays free on +y
post_x  = [exit_x - 8, exit_x];
plate_z = [17, 120];
rows    = [29, 69, 89];   // 29/69 = thruster_bracket bolts pass through, 89 = frame only
y0      = -W/2;           // print bed face; every member starts here so nothing overhangs

module frame() difference() {
    union() {
        translate([pad_x, -W/2, plate_z[0]]) cube([t, W, plate_z[1] - plate_z[0]]);                       // plate on the pad
        translate([pad_x, y0, boom_z[0]]) cube([post_x[1] - pad_x, boom_y - y0, boom_z[1] - boom_z[0]]);        // boom over the thruster
        hull() {                                                                                          // gusset plate -> boom (clears the lugs, top z 59)
            translate([pad_x + t - 1, y0, 86]) cube([1, boom_y - y0, 10]);
            translate([pad_x + 60, y0, boom_z[0] - 1]) cube([10, boom_y - y0, 1]);
        }
        translate([post_x[0], y0, brg_z[0]]) cube([8, half_w - y0, boom_z[1] - brg_z[0]]);               // post down to the bearing
        translate([post_x[0], y0, brg_z[0]]) cube([stock_x + 8 - post_x[0], 8 - y0, brg_z[1] - brg_z[0]]); // bearing arm
        translate([post_x[0], y0, P - 4]) cube([stock_x - sv_shaft + sv[0] + ear_dx + 5 - post_x[0], half_w - y0, 4]);   // servo seat
        hull() {                                                                                          // -y web bearing arm -> seat, forward of the hub
            translate([post_x[0], y0, brg_z[0]]) cube([8, -12 - y0, P - brg_z[0]]);
            translate([stock_x - 16, y0, brg_z[1] - 1]) cube([1, -12 - y0, 1]);
            translate([stock_x - 16, y0, P - 4]) cube([1, -12 - y0, 4]);
        }
        hull() {                                                                                          // +y wall post -> seat
            translate([post_x[0], 12, brg_z[0]]) cube([8, 3, P - brg_z[0]]);
            translate([stock_x - 16, 12, P - 6]) cube([1, 3, 6]);
        }
    }
    for (z = rows, y = [-20, 20]) translate([pad_x - 1, y, z]) rotate([0, 90, 0]) cylinder(d = 3.4, h = t + 2);
    translate([stock_x, 0, brg_z[0] - 1]) cylinder(d = 5.3, h = brg_z[1] - brg_z[0] + 2);                 // bearing
    translate([stock_x - sv_shaft, -sv[1]/2, P - 5]) cube([sv[0], sv[1], 6]);                              // servo body drops in from the top, shaft down
    for (x = [stock_x - sv_shaft - ear_dx, stock_x - sv_shaft + sv[0] + ear_dx]) translate([x, 0, P - 5]) cylinder(d = ear_d, h = 6);
}

part = "print";   // print | assembly
if (part == "print") rotate([90, 0, 0]) translate([-pad_x, -y0, 0]) frame();   // -y face on the bed
else {
    color("steelblue") frame();
    %translate([exit_x - 112, 0, -34]) rotate([0, 90, 0]) cylinder(d = 72.27, h = 112);                    // duct
    %translate([exit_x, 0, -34]) rotate([0, 90, 0]) cylinder(d1 = 32.2, d2 = 2, h = 34.7);                  // tail cone
    %translate([stock_x - 12.5, -4, -72]) cube([50, 8, 75]);                                               // blade
    %translate([stock_x - sv_shaft, -sv[1]/2, P]) cube([sv[0], sv[1], 16.3]);                              // servo body
    color("silver") translate([stock_x, 0, -70]) cylinder(d = 5, h = 110);
    %translate([pad_x + t, -25, 17]) cube([6, 50, 64]);                                                    // thruster_bracket plate
}
echo(str("exit x ", exit_x, ", stock x ", stock_x, ", frame x ", pad_x, "..", stock_x - sv_shaft + sv[0] + ear_dx + 5, " (", stock_x - sv_shaft + sv[0] + ear_dx + 5 - pad_x, " long)"));
