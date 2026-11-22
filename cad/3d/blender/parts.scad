// AR-Mini · parts for the Blender scene (C086). Every solid comes from the repo CAD:
//   AR-Mini_v1.scad (hulls, brackets, lift), beam_leg.scad, rudder.scad.
// Simplified at measured size (not CAD): thruster duct, the two IP65 boxes, the cradle rod.
// One group per run:  openscad -D 'grp="hull_l"' -o parts/hull_l.stl parts.scad
// World coordinates as in AR-Mini_v1.scad: x from the bow, y to port, z from the hull bottom, mm.
include <../../openscad/AR-Mini_v1.scad>
use <../../openscad/beam_leg.scad>
use <../../openscad/rudder.scad>
part = "none";          // switches off the selector of AR-Mini_v1.scad
grp  = "hull_l";

leg_dz  = beam_bot - 130;         // beam_leg was drawn for the measured beam height 130; the v1 CAD has 126
leg_x1  = 500 + 15.4/2 + 6;       // aft face of the beam_leg pad (513.7)
th_dz   = -30 + leg_dz;           // bracket on the deep rows 29 / 69 instead of the transom rows 59 / 99
duct_cx = leg_x1 + th_pin_dx + th_aft;          // duct centre x
duct_z  = th_axis_z + th_dz;                    // prop axis z
exit_x  = duct_cx + th_duct_L/2;                // duct exit face = rudder origin

module side(s) mirror([0, s < 0 ? 1 : 0, 0]) children();
module hull_one() translate([0, gap/2 + hull_W/2, 0]) { hull_fore(); hull_aft(); }
module brackets_one() {
    for (bx = beam_x) translate([bx, boss_y, hull_H]) beam_bracket();
    translate([arch_x, boss_y, hull_H]) arch_post();
    translate([pivot_x, gap/2, hull_H]) pivot_bracket();
}
module thruster_simple() translate([duct_cx, 0, duct_z]) {
    rotate([0, 90, 0]) difference() { cylinder(d = th_duct_d, h = th_duct_L, center = true); cylinder(d = th_duct_d - 5, h = th_duct_L + 2, center = true); }
    rotate([0, 90, 0]) cylinder(d = 32.2, h = th_duct_L - 10, center = true);                    // motor pod
    for (a = [0, 120, 240]) rotate([a, 0, 0]) translate([-3, -1.5, 0]) cube([6, 3, th_duct_d/2 - 1]);   // struts
    translate([-25, -15, th_duct_d/2 - 2]) cube([50, 30, th_face_z - th_duct_d/2 + 2]);          // frame up to the mounting face
}

if (grp == "hull_l")      side(1)  hull_one();
if (grp == "hull_r")      side(-1) hull_one();
if (grp == "brackets")  { side(1) brackets_one(); side(-1) brackets_one(); translate([arch_x, 0, arch_z + beam/2]) cam_fixed_mount(); }
if (grp == "beams")     { for (bx = beam_x) translate([bx, 0, hull_H + 6 + beam/2]) cube([beam, 2*(boss_y + 13), beam], center = true);
                          translate([arch_x, 0, arch_z + beam/2]) cube([beam, 2*(boss_y + 13), beam], center = true); }
if (grp == "leg")         translate([0, 0, leg_dz]) beam_leg();
if (grp == "th_mount")    translate([leg_x1, 0, th_dz]) { thruster_bracket(); translate([th_pin_dx, 0, th_pivot_z]) thruster_arm(); }
if (grp == "thruster")    thruster_simple();
if (grp == "rudder_mount") translate([exit_x, 0, duct_z]) rudder_mount();
// blade + hub + stock turn together: exported with the stock axis on the origin
if (grp == "rudder_blade") translate([-52.5, 0, 0]) { rudder_blade(); translate([52.5, 0, 94 - 16]) rudder_hub(); translate([52.5, 0, -36]) cylinder(d = 5, h = 112); }
// lift arms at alpha = 0, pivot on the origin (x, z); y is global
if (grp == "arm_drive_l") translate([0, arm_y, 0])   rotate([90, 0, 0]) arm(true);
if (grp == "arm_drive_r") mirror([0, 1, 0]) translate([0, arm_y, 0])   rotate([90, 0, 0]) arm(true);
if (grp == "arm_idler_l") translate([0, idler_y, 0]) rotate([90, 0, 0]) arm(false);
if (grp == "arm_idler_r") mirror([0, 1, 0]) translate([0, idler_y, 0]) rotate([90, 0, 0]) arm(false);
// couplers + cradle U, the coupler upper pivot on the origin (x, z)
if (grp == "couplers")    for (s = [1, -1]) side(s) translate([0, coupler_y, 0]) coupler();
if (grp == "cradle") {
    for (s = [-1, 1]) translate([-cradle_L, s*coupler_y, -arm_gap - 12]) rotate([0, 90, 0]) cylinder(d = 5, h = cradle_L + 8);
    translate([-cradle_L, -coupler_y, -arm_gap - 12]) rotate([-90, 0, 0]) cylinder(d = 5, h = 2*coupler_y);
}
// planned C072 boxes on the two beams (plain blocks at the catalogue size)
if (grp == "box_power")   translate([442.5 - 100, -125, pb_z]) cube([200, 100, 70]);
if (grp == "box_logic")   translate([442.5 - 75, 15, pb_z]) cube([150, 110, 70]);

echo(str("KIN pivot_x=", pivot_x, " shaft_z=", shaft_z, " arm_len=", arm_len, " arm_gap=", arm_gap, " deploy_a=", deploy_a, " stow_a=", stow_a,
         " draft=", draft, " rudder_x=", exit_x + 52.5, " rudder_z=", duct_z, " coupler_y=", coupler_y, " cradle_L=", cradle_L, " duct_z=", duct_z));
