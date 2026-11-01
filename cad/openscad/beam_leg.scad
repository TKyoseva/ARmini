// AR-Mini · beam_leg (29.10.2026, pool run without the ROB0154 chassis)
// Hangs the working left Cuifati on the centreline from the two cross-beams.
// The existing thruster_bracket + thruster_arm bolt to the aft face exactly as to a transom pad.
// Global coords: x from the bow, z from the hull bottom. Print lying on its side (the profile flat on the bed), PETG 245 °C.
$fn = 48;
bb      = 130;              // beam underside above the hull bottom: MEASURED 29.10 by Teddy (CAD 126)
beam    = 15;               // 15 x 15 alu tube
beam_x  = [385, 500];
c       = beam + 0.4;       // channel width
w       = 6;                // channel walls
W       = 50;               // part width across (y) = thruster_bracket plate width
floor_t = 8;
bolt_d  = 3.4;
insert_d = 4.0;             // ruthex M3 x 5.7 hole (as the transom pads)
pitch   = 40;               // thruster_bracket pattern y +/-20, rows 40 apart
rows_z  = [29, 49, 69, 89]; // rows 29/69 = deep (axis z -34), rows 49/89 = shallow (axis z -14)
pad_t   = 8;
pad_bot = 13;

bolt_z = bb + beam + 2.2;   // M3 x 30 across each channel, just above the beam: captures it, no drilling
top    = bolt_z + 4;
zb     = bb - floor_t;
x0     = beam_x[0] - c/2 - w;
x1     = beam_x[1] + c/2 + w;   // aft face of the pad = the "transom pad face"

module profile() difference() {
    union() {
        translate([x0, zb]) square([x1 - x0, top - zb]);                        // beam block
        translate([x1 - pad_t, pad_bot]) square([pad_t, top - pad_bot]);        // pad
        hull() { translate([x1 - pad_t - 4, 39]) circle(r = 4.5); translate([x0 + 28, zb + 3]) circle(r = 4.5); }   // strut
    }
    for (bx = beam_x) translate([bx - c/2, bb]) square([c, top]);              // channels, open top
    translate([beam_x[0] + c/2 + w, bb]) square([beam_x[1] - beam_x[0] - c - 2*w, top]);   // lighten between the channels
}

module beam_leg() difference() {
    rotate([90, 0, 0]) linear_extrude(W, center = true) profile();
    for (bx = beam_x, y = [-18, 18]) translate([bx - c/2 - w - 1, y, bolt_z]) rotate([0, 90, 0]) cylinder(d = bolt_d, h = c + 2*w + 2);
    for (y = [-pitch/2, pitch/2], z = rows_z) translate([x1 - pad_t - 1, y, z]) rotate([0, 90, 0]) cylinder(d = insert_d, h = pad_t + 2);
}

part = "print";   // print | assembly
if (part == "print") translate([0, 0, W/2]) rotate([90, 0, 0]) translate([-x0, 0, 0]) beam_leg();   // side down, fits a 350 bed
else beam_leg();
echo(str("x ", x0, "..", x1, " (", x1 - x0, " long), z ", pad_bot, "..", top, ", width ", W));
echo(str("deep rows: prop axis z ", 49 - 79 - 4, ", duct ", 49 - 79 - 4 - 36, "..", 49 - 79 - 4 + 36));
