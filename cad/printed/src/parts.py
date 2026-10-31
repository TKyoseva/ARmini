U='/mnt/user-data/uploads/ARmini/'
V=U+'cad/stl/v1/'; B=U+'build/'
WHITE='#e8e6df'; ORANGE='#f28a1e'; BLACK='#3b3e44'; RED='#c62828'
# name, file, qty, card, material, color, print note
P=[
 ('hull_fore',V+'hull_fore.stl',2,'C008 · C022','white PLA',WHITE,'6 h 16 / 6 h 17 · 345 g each'),
 ('hull_aft',V+'hull_aft.stl',2,'C034','white PETG',WHITE,'7 h 30 / 7 h 34 · 410 g each'),
 ('pivot_bracket',V+'pivot_bracket.stl',2,'C037','black PLA',BLACK,'+ arch_post: 5 h 45 · 176 g'),
 ('arch_post',V+'arch_post.stl',2,'C037','black PLA',BLACK,'plate with pivot_bracket'),
 ('arm_drive',V+'arm_drive.stl',2,'C017 · C011','orange PLA',ORANGE,'first good print: 0 h 20 · 13 g'),
 ('arm_idler',V+'arm_idler.stl',2,'C011','orange PLA',ORANGE,'plate: 1 h 12 · 41 g'),
 ('coupler',V+'coupler.stl',2,'C011','orange PLA',ORANGE,'plate with the arms'),
 ('thruster_bracket',V+'thruster_bracket.stl',3,'C041 · C057','white + black PETG',WHITE,'+ thruster_arm: 2 h 52 · 96 g'),
 ('thruster_arm',V+'thruster_arm.stl',2,'C041','white PETG',WHITE,'plate with thruster_bracket'),
 ('beam_bracket',B+'beam_bracket.stl',8,'C045','black PLA',BLACK,'plate of 8: 1 h 14 · 39 g'),
 ('cam_fixed_mount',B+'cam_fixed_mount.stl',1,'C047','black',BLACK,'1 h 24 · 39 g with supports'),
 ('pesho_head',B+'pesho_head.stl',1,'C039','white PETG',WHITE,'with lid ~1 h 40 (no screen photo)'),
 ('pesho_lid',B+'pesho_lid.stl',1,'C039','white PETG',WHITE,'plate with the head'),
 ('pesho_body',B+'pesho_body.stl',1,'C039','red PLA',RED,'4 h 44 · 143 g'),
 ('beam_leg',V+'beam_leg.stl',1,'C056','black PETG',BLACK,'2 h 37 · 123 g'),
 ('rudder_mount',V+'rudder_mount.stl',1,'C057','black PETG',BLACK,'plate: 3 h 09 · 103 g (superseded)'),
 ('rudder_blade',V+'rudder_blade.stl',1,'C057','black PETG',BLACK,'NACA 0015, same plate'),
 ('rudder_hub',V+'rudder_hub.stl',1,'C057','black PETG',BLACK,'same plate'),
 ('rudder_frame',V+'rudder_frame.stl',1,'C057','black PETG',BLACK,'2 h 27 · 104 g'),
]
# print jobs (minutes, grams) from the printer screen photos; None = no screen photo
JOBS=[('C008 hull_fore L',376,345),('C022 hull_fore R',377,345),('C034 hull_aft L',450,410),('C034 hull_aft R',454,410),
 ('C017 arm_drive',20,13),('C011 orange plate',72,41),('C037 black plate',345,176),('C039 Pesho head+lid',100,None),
 ('C039 Pesho body',284,143),('C041 thruster mounts',172,96),('C045 beam brackets',74,39),('C047 camera mount',84,39),
 ('C056 beam_leg',157,123),('C057 rudder plate',189,103),('C057 rudder_frame',147,104)]
