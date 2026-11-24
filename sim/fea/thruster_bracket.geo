// AR-Mini · thruster_bracket for FEA (card C083). Same numbers as module thruster_bracket() in
// cad/openscad/AR-Mini_v1.scad. Bracket coordinates: x aft from the pad face, y across, z from the hull bottom
// (on the beam_leg deep rows the whole bracket sits 30 mm lower; that does not change the stresses). Units mm.
SetFactory("OpenCASCADE");
DefineConstant[ h = 2 ];
tp_z = 79; tp_pitch = 40; bolt_d = 3.4; pivot_z = 75; pin_dx = 19; pin_d = 5.3; lock_d = 3.3; lock_r = 10;
th_aft = 47; plate_dz = -29.5; lock_a = Atan2(plate_dz, th_aft);

Box(1) = {0, -25, tp_z - 32, 6, 50, 64};                          // plate z 47..111
For s In {0:1}
  y0 = (s == 0) ? -25 : 19;                                       // lugs |y| 19..25
  Box(2 + 2*s) = {0, y0, pivot_z - 14, pin_dx, 6, 28};
  Cylinder(3 + 2*s) = {pin_dx, y0, pivot_z, 0, 6, 0, 14};
EndFor
BooleanUnion(10) = { Volume{1}; Delete; }{ Volume{2:5}; Delete; };
n = 11;
For t In {0:1}
  For r In {0:1}
    yy = -tp_pitch/2 + tp_pitch*t; zz = tp_z - tp_pitch/2 + tp_pitch*r;
    Cylinder(n) = {-1, yy, zz, 8, 0, 0, bolt_d/2}; n++;           // M3 clearance
    Cylinder(n) = {3, yy, zz, 4, 0, 0, 3.1}; n++;                 // head counterbore Ø6.2 from x 3
  EndFor
EndFor
Cylinder(n) = {pin_dx, -40, pivot_z, 0, 80, 0, pin_d/2}; n++;     // hinge pin
For k In {0:1}
  a = lock_a + k*100*Pi/180;                                      // lock pin: deployed / stowed
  Cylinder(n) = {pin_dx + lock_r*Cos(a), -40, pivot_z + lock_r*Sin(a), 0, 80, 0, lock_d/2}; n++;
EndFor
BooleanDifference(100) = { Volume{10}; Delete; }{ Volume{11:n-1}; Delete; };

e = 0.05;
fix[] = {};                                                       // FIXED: the back face on the pad (x = 0)
fix[] += Surface In BoundingBox{-e, -26, 0, e, 26, 200};
pin[] = {}; lock[] = {};
For s In {0:1}
  y0 = (s == 0) ? -25 : 19;
  pin[] += Surface In BoundingBox{pin_dx - pin_d/2 - e, y0 - e, pivot_z - pin_d/2 - e, pin_dx + pin_d/2 + e, y0 + 6 + e, pivot_z + pin_d/2 + e};
  lx = pin_dx + lock_r*Cos(lock_a); lz = pivot_z + lock_r*Sin(lock_a);
  lock[] += Surface In BoundingBox{lx - lock_d/2 - e, y0 - e, lz - lock_d/2 - e, lx + lock_d/2 + e, y0 + 6 + e, lz + lock_d/2 + e};
EndFor
Physical Volume("BODY") = {100};
Physical Surface("FIX") = {fix[]};
Physical Surface("PIN") = {pin[]};
Physical Surface("LOCK") = {lock[]};
Mesh.CharacteristicLengthMax = h; Mesh.CharacteristicLengthMin = h/3;
Mesh.MeshSizeFromCurvature = 8; Mesh.ElementOrder = 2;
Mesh.SaveGroupsOfNodes = 1; Mesh.Algorithm3D = 1;
