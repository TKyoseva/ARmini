// AR-Mini C085 · the wetted part of one hull as a double body (mirrored at the waterline), in metres.
// Outline copied from module outline2d() in cad/openscad/AR-Mini_v1.scad. x from the bow, waterline at z = 0.
hull_L = 610; hull_W = 100; bow_len = 150; tip_r = 6;
draft = 23;   // mm at 2.5 kg. SOURCE: C063 mass 2.5 kg × 9.1 mm/kg (C007 measured waterplane)
$fn = 64;
function bow_side(n, s) = [ for (i = [1:n]) let(t = i/n) [bow_len*t, s*(hull_W/2)*sqrt(t)] ];
module outline2d() offset(r = tip_r) offset(r = -tip_r) polygon(concat([[0, 0]], bow_side(24, 1),
    [[hull_L, hull_W/2], [hull_L, -hull_W/2]], [ for (i = [24:-1:1]) let(t = i/24) [bow_len*t, -(hull_W/2)*sqrt(t)] ]));
scale(0.001) translate([0, 0, -draft]) linear_extrude(2*draft) outline2d();
