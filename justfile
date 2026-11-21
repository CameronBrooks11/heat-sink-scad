default:
    @just --list

# Render heat sinks and check their size, their fins and the refusals
test:
    python3 tests/test_heat_sink.py

# Everything CI runs, bar the tests
check: fmt-check

# Format the .scad sources with topiary (.topiary/languages.ncl)
fmt:
    git ls-files -z '*.scad' | xargs -0 -r topiary format

# Check the .scad sources are formatted, without changing them
fmt-check:
    git ls-files -z '*.scad' | xargs -0 -r -n1 topiary format --check

# Render the README picture into assets/
images:
    @mkdir -p assets
    openscad --camera=20,20,8,55,0,30,140 --imgsize=800,480 --colorscheme=Tomorrow -o assets/heat-sink.png heat_sink.scad
