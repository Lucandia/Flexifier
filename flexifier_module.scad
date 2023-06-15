$fn=50;

module uni_hinge(height, hinge_h_thick=5, vert_tolerance=0.8, break=4, hor_tolerance=0.4, chamfer=2){
hinge_pin_diam = (height-vert_tolerance)/3;
// external hinge
translate([0,0,height/2]) rotate([90,0,0])
linear_extrude(hinge_h_thick)
difference(){
// external circle
union(){
circle(d=height);
// squared cornern hing
translate([0,-height/2,0])
square([(hinge_pin_diam+vert_tolerance)/2+chamfer*sqrt(2), height]);};
// internal hole + tolerance
circle(d=hinge_pin_diam+vert_tolerance);};
// internal pin
translate([0,hinge_h_thick/2+hor_tolerance,height/2]) rotate([90,0,0])
cylinder(h=(hinge_h_thick+hor_tolerance)*2, d=hinge_pin_diam);
};

module diff_hinge(height, hinge_h_thick=5, hor_tolerance=0.4, vert_tolerance=0.8, break=4, chamfer=2, break_len=200){
hinge_pin_diam = (height-vert_tolerance)/3;
hinge_v_thick = (height-hinge_pin_diam-vert_tolerance)/2;
// line break
linear_extrude(height)
translate([(hinge_pin_diam+vert_tolerance)/2,-break_len/2-hinge_h_thick/2,0])
square([break/2, break_len]);
//chamfer bottom and top
for (i=[0, height]){
translate([(hinge_pin_diam+vert_tolerance)/2+break/4,-break_len/2-hinge_h_thick/2,i])
translate([-chamfer*sqrt(2)/2,0,0])
rotate([0, 45, 0])
linear_extrude(chamfer)
square([chamfer, break_len]);};
// square for difference
translate([-hor_tolerance/2-hinge_v_thick/2,+hor_tolerance,height/2]) rotate([90,0,0])
linear_extrude(hinge_h_thick+hor_tolerance*2)
square([height+hor_tolerance-hinge_v_thick, height], center=true);
};
