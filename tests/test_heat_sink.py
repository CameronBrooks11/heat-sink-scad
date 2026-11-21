"""Render heat sinks and check their size, their fins, and the refusals.

usage: python3 tests/test_heat_sink.py [OPENSCAD]

Each case renders heat_sink() with --hardwarnings to a binary STL and checks:

- the whole: one solid, width x length x height from the origin;
- the fins: cut just above the base plate, the sink is num_fins separate
  solids, each the fin width heat_sink_fin_width() gives, spanning the width.

The refusals check that a sink that can't be made stops with its message.
"""

import os
import struct
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "heat_sink.scad")


def solids(path):
    """Bounding box of each separate solid."""
    data = open(path, "rb").read()
    (n,) = struct.unpack_from("<I", data, 80)
    tris = [struct.unpack_from("<9f", data, 84 + i * 50 + 12) for i in range(n)]
    parent = {}

    def find(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v

    for t in tris:
        corners = [t[0:3], t[3:6], t[6:9]]
        for c in corners:
            parent.setdefault(c, c)
        root = find(corners[0])
        for c in corners[1:]:
            parent[find(c)] = root
    groups = {}
    for v in parent:
        groups.setdefault(find(v), []).append(v)
    return sorted(([min(p[i] for p in g) for i in range(3)], [max(p[i] for p in g) for i in range(3)])
                  for g in groups.values())


def render(openscad, source, out, tmp):
    path = os.path.join(tmp, "probe.scad")
    with open(path, "w") as f:
        f.write(f"use <{LIB}>\n" + source)
    return subprocess.run([openscad, "--hardwarnings", "--export-format", "binstl", "-o", out, path],
                          capture_output=True, text=True)


CASES = [
    # length, width, height, base_height, gap_width, num_fins
    ("defaults", (40, 40, 20, 3.2, 2.2, 11)),
    ("one fin", (30, 10, 15, 2, 1, 1)),
    ("wide gaps", (25, 60, 12, 1.5, 6, 5)),
    ("long and thin", (120, 20, 30, 4, 1.5, 7)),
]

results = []


def check(label, ok, got):
    results.append(bool(ok))
    print(f"{'ok  ' if ok else 'FAIL'} {label}: {got}")


def close(a, b):
    return abs(a - b) <= 0.01


def main():
    openscad = sys.argv[1] if len(sys.argv) > 1 else "openscad"
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "case.stl")
        for label, (length, width, height, base, gap, fins) in CASES:
            args = f"{length}, {width}, {height}, {base}, {gap}, {fins}"
            fin = (width - gap * (fins - 1)) / fins

            r = render(openscad, f"heat_sink({args});\n", out, tmp)
            bad = [l for l in r.stderr.splitlines() if "WARNING" in l or "ERROR" in l]
            if r.returncode != 0 or bad:
                check(f"{label}: whole", False, bad[:1] or f"exit {r.returncode}")
                continue
            parts = solids(out)
            (lo, hi), = parts if len(parts) == 1 else [([1] * 3, [0] * 3)]
            size = [hi[i] - lo[i] for i in range(3)]
            check(f"{label}: whole", len(parts) == 1 and all(close(v, 0) for v in lo)
                  and [close(*p) for p in zip(size, (width, length, height))] == [True] * 3,
                  f"{len(parts)} solid(s), {' x '.join(f'{s:.2f}' for s in size)} mm")

            r = render(openscad, f"intersection() {{ heat_sink({args}); "
                       f"translate([-1, -1, {base} + 0.01]) cube([{width} + 2, {length} + 2, {height}]); }}\n", out, tmp)
            parts = solids(out) if r.returncode == 0 else []
            widths = [hi[0] - lo[0] for lo, hi in parts]
            ok = len(parts) == fins and all(close(w, fin) for w in widths) \
                and close(parts[0][0][0], 0) and close(parts[-1][1][0], width)
            check(f"{label}: fins", ok,
                  f"{len(parts)} fins (want {fins}), each {fin:.3f} mm: {', '.join(f'{w:.3f}' for w in widths[:3])}"
                  + ("..." if len(widths) > 3 else ""))

        # The example: one 25 x 25 x 10 mm sink from the origin.
        r = subprocess.run([openscad, "--hardwarnings", "--export-format", "binstl", "-o", out,
                            os.path.join(ROOT, "examples", "chip_sink.scad")], capture_output=True, text=True)
        bad = [l for l in r.stderr.splitlines() if "WARNING" in l or "ERROR" in l]
        parts = solids(out) if r.returncode == 0 and not bad else []
        ok = len(parts) == 1 and all(close(v, 0) for v in parts[0][0]) \
            and all(close(a, b) for a, b in zip(parts[0][1], (25, 25, 10)))
        check("examples/chip_sink.scad", ok, f"{len(parts)} solid(s), up to {parts[0][1]}" if parts
              else bad[:1] or f"exit {r.returncode}")

        for label, args, message in [
            ("refuses fins that don't fit", "40, 10, 20, 3, 2, 6", "leave no room for the fins"),
            ("refuses a fin count that isn't whole", "40, 40, 20, 3, 2, 2.5", "num_fins has to be a whole number"),
            ("refuses a base as tall as the sink", "40, 40, 3, 3, 2, 5", "height has to be more than base_height"),
            ("refuses a negative gap", "40, 40, 20, 3, -1, 5", "gap_width can't be negative"),
        ]:
            r = render(openscad, f"heat_sink({args});\n", out, tmp)
            errors = [l for l in r.stderr.splitlines() if "ERROR" in l]
            check(label, errors and message in errors[0], errors[0][:110] if errors else f"exit {r.returncode}")

    print(f"{sum(results)} of {len(results)} checks passed")
    sys.exit(0 if all(results) else 1)


main()
