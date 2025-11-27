// Parametric heat sink

$fn = $preview ? 64 : 128;

length_ex = 40;
width_ex = 40;
height_ex = 20;
base_height_ex = 3.2;
gap_width_ex = 2.2;
num_fins_ex = 11;

heat_sink(length_ex, width_ex, height_ex, base_height_ex, gap_width_ex, num_fins_ex);

module heat_sink(length, width, height, base_height, gap_width, num_fins) {
  blade_width = (width - gap_width * (num_fins - 1)) / num_fins;
  echo("blade width = ", blade_width);

  rotate([0, 0, 0])
    translate([0, 0, 0])
      cube([width, length, base_height]);

  for (i = [0:num_fins - 1]) {
    translate([i * (gap_width + blade_width), 0, 0])
      cube([blade_width, length, height]);
  }
}
