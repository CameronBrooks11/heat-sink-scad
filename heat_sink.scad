// Parametric straight-fin heat sink: a base plate with evenly spaced rectangular fins standing on
// it. The fins run along y; x is across them. MIT licence; see LICENSE.

/* [Heat sink] */

// Along the fins, mm
length = 40;

// Across the fins, mm
width = 40;

// Overall, base plate included, mm
height = 20;

// Thickness of the base plate, mm
base_height = 3.2;

// Gap between neighbouring fins, mm
gap_width = 2.2;

// Number of fins
num_fins = 11;

/* [Hidden] */

// Width of each fin: what is left of the width once the gaps are taken out, shared evenly.
function heat_sink_fin_width(width, gap_width, num_fins) = (width - gap_width * (num_fins - 1)) / num_fins;

// A heat sink with its base plate on z = 0, from the origin: width along x, length along y.
module heat_sink(length, width, height, base_height, gap_width, num_fins) {
    fin = heat_sink_fin_width(width, gap_width, num_fins);
    assert(length > 0 && width > 0, "heat_sink: length and width have to be more than 0");
    assert(base_height > 0 && height > base_height, "heat_sink: height has to be more than base_height, and base_height more than 0");
    assert(num_fins >= 1 && num_fins == floor(num_fins), str("heat_sink: num_fins has to be a whole number, 1 or more, not ", num_fins));
    assert(gap_width >= 0, "heat_sink: gap_width can't be negative");
    assert(fin > 0, str("heat_sink: ", num_fins, " fins with ", gap_width, " mm gaps leave no room for the fins in ", width, " mm"));
    echo(fin_width=fin);

    cube([width, length, base_height]);
    for (i = [0:num_fins - 1])
        translate([i * (fin + gap_width), 0, 0])
            cube([fin, length, height]);
}

heat_sink(length, width, height, base_height, gap_width, num_fins);
