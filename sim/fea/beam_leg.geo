// AR-Mini · beam_leg for FEA (card C083). Same numbers as cad/openscad/beam_leg.scad, assembly coordinates:
// x from the bow, y across, z from the hull bottom. Units mm. Mesh size from the command line: -setnumber h 3
SetFactory("OpenCASCADE");
DefineConstant[ h = 3 ];
bb = 130; beam = 15; bx0 = 385; bx1 = 500; c = beam + 0.4; w = 6; W = 50; floor_t = 8;
bolt_d = 3.4; insert_d = 4.0; pitch = 40; pad_t = 8; pad_bot = 13;
bolt_z = bb + beam + 2.2; top = bolt_z + 4; zb = bb - floor_t;
x0 = bx0 - c/2 - w; x1 = bx1 + c/2 + w;

Box(1) = {x0, -W/2, zb, x1 - x0, W, top - zb};                 // beam block
Box(2) = {x1 - pad_t, -W/2, pad_bot, pad_t, W, top - pad_bot}; // pad
// strut = hull of two r 4.5 circles: (x1 - pad_t - 4, 39) → (x0 + 28, zb + 3)
ax = x1 - pad_t - 4; az = 39; cx = x0 + 28; cz = zb + 3;
L = Sqrt((cx - ax)^2 + (cz - az)^2); phi = Atan2(cz - az, cx - ax);
Box(3) = {0, -W/2, -4.5, L, W, 9};
Rotate {{0, 1, 0}, {0, 0, 0}, -phi} { Volume{3}; }
Translate {ax, 0, az} { Volume{3}; }
Cylinder(4) = {ax, -W/2, az, 0, W, 0, 4.5};
Cylinder(5) = {cx, -W/2, cz, 0, W, 0, 4.5};
BooleanUnion(10) = { Volume{1}; Delete; }{ Volume{2, 3, 4, 5}; Delete; };

Box(11) = {bx0 - c/2, -W, bb, c, 2*W, 100};                    // channels, open top
Box(12) = {bx1 - c/2, -W, bb, c, 2*W, 100};
Box(13) = {bx0 + c/2 + w, -W, bb, bx1 - bx0 - c - 2*w, 2*W, 100};  // lighten between the channels
n = 14;
For s In {0:1}
  bxs = bx0 + s*(bx1 - bx0);
  For t In {0:1}
    Cylinder(n) = {bxs - c/2 - w - 1, -18 + 36*t, bolt_z, c + 2*w + 2, 0, 0, bolt_d/2}; n++;   // clamp bolts
  EndFor
EndFor
For t In {0:1}
  For r In {0:3}
    Cylinder(n) = {x1 - pad_t - 1, -pitch/2 + pitch*t, 29 + 20*r, pad_t + 2, 0, 0, insert_d/2}; n++;   // insert rows 29/49/69/89
  EndFor
EndFor
BooleanDifference(100) = { Volume{10}; Delete; }{ Volume{11:n-1}; Delete; };

e = 0.05;
// FIXED: the faces of the two channels that sit on the 15 × 15 beams (floor and both walls of each channel)
fix[] = {};
fix[] += Surface In BoundingBox{bx0 - c/2 - e, -W, bb - e, bx0 + c/2 + e, W, top + e};
fix[] += Surface In BoundingBox{bx1 - c/2 - e, -W, bb - e, bx1 + c/2 + e, W, top + e};
// LOAD: the four insert holes the bracket is bolted to (deep rows z 29 and 69)
ld[] = {};
For t In {0:1}
  For r In {0:2:2}
    yy = -pitch/2 + pitch*t; zz = 29 + 20*r;
    ld[] += Surface In BoundingBox{x1 - pad_t - e, yy - insert_d/2 - e, zz - insert_d/2 - e, x1 + e, yy + insert_d/2 + e, zz + insert_d/2 + e};
  EndFor
EndFor
Physical Volume("BODY") = {100};
Physical Surface("FIX") = {fix[]};
Physical Surface("LOAD") = {ld[]};
Mesh.CharacteristicLengthMax = h; Mesh.CharacteristicLengthMin = h/3;
Mesh.MeshSizeFromCurvature = 8; Mesh.ElementOrder = 2; Mesh.SecondOrderLinear = 0;
Mesh.SaveGroupsOfNodes = 1; Mesh.Algorithm3D = 1;
