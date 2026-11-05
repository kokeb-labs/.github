#!/usr/bin/env python3
"""Generate the Kokeb Labs logo concepts and every asset derived from them.

Every mark is drawn from a few numbers in CONCEPTS, so the same command always produces the same files, and a
variant is a parameter change, not a redraw. Colours come from PALETTE only.

  python3 brand/generate.py                  # all concepts -> brand/out/<concept>/
  python3 brand/generate.py --only die-star  # one concept

Per concept it writes: mark.svg (for light backgrounds), mark-dark.svg (for dark), mark-mono.svg (one colour,
currentColor), avatar.svg and avatar-500.png (organization avatar, safe inside GitHub's circle crop),
favicon-16/32/64.png, social.svg and social.png (1280x640 repository preview). PNGs need `rsvg-convert` (librsvg);
without it only SVGs are written. brand/out/index.html shows every concept side by side.
"""

from __future__ import annotations

import argparse
import math
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"

PALETTE = {
    "night": "#0E1726",   # deep navy: backgrounds, text on light
    "ink": "#1B2A41",     # secondary dark
    "star": "#F4B942",    # warm gold: the star
    "copper": "#D9773B",  # PCB copper accent
    "teal": "#2BB3A3",    # signal accent
    "paper": "#FAF7F0",   # light background
    "mist": "#C9D3E0",    # light lines on dark
}

WORDMARK_FONT = "'Space Grotesk', 'Avenir Next', 'Helvetica Neue', Arial, sans-serif"
C = 256.0  # every mark is drawn in a 512 x 512 box centred here


def f(x: float) -> str:
    return f"{x:.2f}".rstrip("0").rstrip(".")


def polar(r: float, a: float) -> tuple[float, float]:
    return C + r * math.cos(a), C + r * math.sin(a)


# --------------------------------------------------------------------------------------------------------------
# Concepts. Each takes (params, colours) and returns SVG elements for the 512 x 512 box.
# colours: {"fg": main, "accent": accent, "bg": background behind the mark}
# --------------------------------------------------------------------------------------------------------------

def twinkle(p: dict, col: dict) -> str:
    """Four-point star with concave sides; a round hole marks pin 1, as on a chip package."""
    R, pinch = p["radius"], p["pinch"]
    pts = [polar(R, math.radians(-90 + 90 * i)) for i in range(4)]
    d = f"M{f(pts[0][0])},{f(pts[0][1])}"
    for i in range(4):
        a_mid = math.radians(-45 + 90 * i)
        cx, cy = polar(pinch, a_mid)
        nx, ny = pts[(i + 1) % 4]
        d += f" Q{f(cx)},{f(cy)} {f(nx)},{f(ny)}"
    d += " Z"
    hx, hy = polar(p["hole_offset"], math.radians(-135))
    small = ""
    if p.get("companion"):
        sx, sy = C + p["companion"][0], C + p["companion"][1]
        s = p["companion"][2]
        small = (f'<path d="M{f(sx)},{f(sy - s)} Q{f(sx + s * .18)},{f(sy - s * .18)} {f(sx + s)},{f(sy)} '
                 f'Q{f(sx + s * .18)},{f(sy + s * .18)} {f(sx)},{f(sy + s)} Q{f(sx - s * .18)},{f(sy + s * .18)} '
                 f'{f(sx - s)},{f(sy)} Q{f(sx - s * .18)},{f(sy - s * .18)} {f(sx)},{f(sy - s)} Z" '
                 f'fill="{col["accent"]}"/>')
    return (f'<path d="{d}" fill="{col["fg"]}"/>'
            f'<circle cx="{f(hx)}" cy="{f(hy)}" r="{f(p["hole_r"])}" fill="{col["bg"]}"/>{small}')


def trace_star(p: dict, col: dict) -> str:
    """Eight PCB traces leave a centre pad, jog 45 degrees and end in vias: a star drawn as copper."""
    out = []
    w = p["trace"]
    for i in range(8):
        a = math.radians(-90 + 45 * i)
        long_ray = i % 2 == 0
        r0, r1 = p["pad"] * 0.9, p["knee_long"] if long_ray else p["knee_short"]
        r2 = p["tip_long"] if long_ray else p["tip_short"]
        jog = math.radians(p["jog_deg"]) * (1 if i % 4 < 2 else -1) * (0 if long_ray else 1)
        x0, y0 = polar(r0, a)
        x1, y1 = polar(r1, a)
        x2, y2 = polar(r2, a + jog)
        color = col["fg"] if long_ray else col["accent"]
        out.append(f'<polyline points="{f(x0)},{f(y0)} {f(x1)},{f(y1)} {f(x2)},{f(y2)}" fill="none" '
                   f'stroke="{color}" stroke-width="{f(w)}" stroke-linecap="round" stroke-linejoin="round"/>')
        out.append(f'<circle cx="{f(x2)}" cy="{f(y2)}" r="{f(p["via"])}" fill="{col["bg"]}" stroke="{color}" '
                   f'stroke-width="{f(w * 0.8)}"/>')
    s = p["pad"]
    out.append(f'<rect x="{f(C - s)}" y="{f(C - s)}" width="{f(2 * s)}" height="{f(2 * s)}" rx="{f(s * 0.28)}" '
               f'transform="rotate(45 {f(C)} {f(C)})" fill="{col["fg"]}"/>')
    return "".join(out)


def die_star(p: dict, col: dict) -> str:
    """A chip die whose package pads grow into an eight-point starburst."""
    out = []
    n, die = p["pads"], p["die"]
    for i in range(n):
        a = 2 * math.pi * i / n - math.pi / 2
        env = abs(math.cos(4 * (a + math.pi / 2))) ** p["sharpness"]
        length = p["pad_min"] + (p["pad_max"] - p["pad_min"]) * env
        r0 = p["gap"]
        x0, y0 = polar(r0, a)
        x1, y1 = polar(r0 + length, a)
        color = col["fg"] if env > 0.55 else col["accent"]
        out.append(f'<line x1="{f(x0)}" y1="{f(y0)}" x2="{f(x1)}" y2="{f(y1)}" stroke="{color}" '
                   f'stroke-width="{f(p["pad_w"])}" stroke-linecap="round"/>')
    out.append(f'<rect x="{f(C - die)}" y="{f(C - die)}" width="{f(2 * die)}" height="{f(2 * die)}" '
               f'rx="{f(die * 0.22)}" fill="{col["fg"]}"/>')
    dx, dy = C - die * 0.52, C - die * 0.52
    out.append(f'<circle cx="{f(dx)}" cy="{f(dy)}" r="{f(die * 0.16)}" fill="{col["bg"]}"/>')
    return "".join(out)


def phase_star(p: dict, col: dict) -> str:
    """Three sine-edged stars, 120 degrees apart in phase: a star drawn by three-phase signals."""
    out = []
    colours = [col["fg"], col["accent"], col["accent2"]]
    for k in range(3):
        pts = []
        phase = 2 * math.pi * k / 3
        for j in range(721):
            t = 2 * math.pi * j / 720
            r = p["r0"] - p["shrink"] * k + p["amp"] * math.sin(p["lobes"] * (t + phase / p["lobes"] * p["twist"]))
            pts.append(polar(r, t - math.pi / 2))
        d = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts) + " Z"
        out.append(f'<path d="{d}" fill="none" stroke="{colours[k]}" stroke-width="{f(p["stroke"])}" '
                   f'stroke-linejoin="round" opacity="{p["opacity"][k]}"/>')
    out.append(f'<circle cx="{f(C)}" cy="{f(C)}" r="{f(p["core"])}" fill="{col["fg"]}"/>')
    return "".join(out)


def constellation(p: dict, col: dict) -> str:
    """The letter K as a constellation; its brightest star sits where the arms meet."""
    nodes = {k: (C + x, C + y) for k, (x, y) in p["nodes"].items()}
    out = []
    for a, b in p["edges"]:
        (x1, y1), (x2, y2) = nodes[a], nodes[b]
        out.append(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" stroke="{col["line"]}" '
                   f'stroke-width="{f(p["line_w"])}" stroke-linecap="round"/>')
    for k, (x, y) in nodes.items():
        r = p["sizes"].get(k, p["node_r"])
        if k == p["bright"]:
            s = r * 2.6
            out.append(f'<path d="M{f(x)},{f(y - s)} Q{f(x + s * .16)},{f(y - s * .16)} {f(x + s)},{f(y)} '
                       f'Q{f(x + s * .16)},{f(y + s * .16)} {f(x)},{f(y + s)} Q{f(x - s * .16)},{f(y + s * .16)} '
                       f'{f(x - s)},{f(y)} Q{f(x - s * .16)},{f(y - s * .16)} {f(x)},{f(y - s)} Z" '
                       f'fill="{col["accent"]}"/>')
        else:
            out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{col["fg"]}"/>')
    return "".join(out)


def eight_point(p: dict, col: dict) -> str:
    """A filled eight-point star of two overlapping squares with a ring cut into the centre, after the
    eight-pointed stars of Ethiopian textile and window patterns, kept geometric so it stays a mark."""
    s, rc = p["half"], p["corner"]
    sq = "".join(f'<rect x="{f(C - s)}" y="{f(C - s)}" width="{f(2 * s)}" height="{f(2 * s)}" rx="{f(rc)}" '
                 f'transform="rotate({rot} {f(C)} {f(C)})" fill="{col["fg"]}"/>' for rot in (0, 45))
    return (sq + f'<circle cx="{f(C)}" cy="{f(C)}" r="{f(p["ring"])}" fill="{col["bg"]}"/>'
            f'<circle cx="{f(C)}" cy="{f(C)}" r="{f(p["core"])}" fill="{col["accent"]}"/>')


def _vec(a: float) -> tuple[float, float]:
    return math.cos(a), math.sin(a)


def _spike(a: float, r0: float, r1: float, w: float) -> str:
    """A straight-sided spike from radius r0 (half-width w) to a point at r1, along angle a."""
    ux, uy = _vec(a)
    vx, vy = -uy, ux
    bx, by = C + r0 * ux, C + r0 * uy
    tx, ty = C + r1 * ux, C + r1 * uy
    return f"M{f(bx + w * vx)},{f(by + w * vy)} L{f(tx)},{f(ty)} L{f(bx - w * vx)},{f(by - w * vy)} Z"


def _via(x: float, y: float, r: float, hole: float, col: str, bg: str) -> str:
    return (f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{col}"/>'
            f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(hole)}" fill="{bg}"/>')


def _diamond(s: float, col: str) -> str:
    return (f'<rect x="{f(C - s)}" y="{f(C - s)}" width="{f(2 * s)}" height="{f(2 * s)}" rx="{f(s * .18)}" '
            f'transform="rotate(45 {f(C)} {f(C)})" fill="{col}"/>')


def routed_star(p: dict, col: dict) -> str:
    """A four-point star with straight, chamfered sides, as a PCB router would draw it, each point ending in a via.
    Straight edges and vias keep it clearly apart from the curved 'sparkle' used for AI products."""
    R, rin, ch = p["radius"], p["inner"], math.radians(p["chamfer_deg"])
    pts = []
    for i in range(4):
        a = math.radians(-90 + 90 * i)
        pts.append(polar(R, a))
        mid = a + math.radians(45)
        pts.append(polar(rin, mid - ch))
        pts.append(polar(rin, mid + ch))
    d = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts) + " Z"
    out = [f'<path d="{d}" fill="{col["fg"]}" stroke="{col["fg"]}" stroke-width="{f(p["round"])}" '
           f'stroke-linejoin="round"/>']
    for i in range(4):
        x, y = polar(R, math.radians(-90 + 90 * i))
        out.append(_via(x, y, p["via"], p["via_hole"], col["fg"], col["bg"]))
    out.append(_diamond(p["pad_hole"], col["bg"]))
    out.append(_diamond(p["pad_hole"] * 0.5, col["accent"]))
    return "".join(out)


def trace_twinkle(p: dict, col: dict) -> str:
    """Four long spikes for the star, four short copper traces on the diagonals that jog and end in vias."""
    out = []
    for i in range(4):
        a = math.radians(-90 + 90 * i)
        out.append(f'<path d="{_spike(a, 0, p["radius"], p["spike_w"])}" fill="{col["fg"]}"/>')
    w = p["trace"]
    for i in range(4):
        a = math.radians(-45 + 90 * i)
        jog = math.radians(p["jog_deg"]) * (1 if i % 2 == 0 else -1)
        x0, y0 = polar(p["pad"] * 1.2, a)
        x1, y1 = polar(p["knee"], a)
        x2, y2 = polar(p["tip"], a + jog)
        out.append(f'<polyline points="{f(x0)},{f(y0)} {f(x1)},{f(y1)} {f(x2)},{f(y2)}" fill="none" '
                   f'stroke="{col["accent"]}" stroke-width="{f(w)}" stroke-linecap="round" stroke-linejoin="round"/>')
        out.append(_via(x2, y2, p["via"], p["via"] * 0.45, col["accent"], col["bg"]))
    out.append(_diamond(p["pad"], col["fg"]))
    out.append(f'<circle cx="{f(C)}" cy="{f(C)}" r="{f(p["pad"] * 0.42)}" fill="{col["bg"]}"/>')
    return "".join(out)


def split_star(p: dict, col: dict) -> str:
    """Four straight spikes that stop short of a centre pad, like traces running into a chip: a star with gaps."""
    out = [f'<path d="{_spike(math.radians(-90 + 90 * i), p["gap"], p["radius"], p["spike_w"])}" '
           f'fill="{col["fg"]}"/>' for i in range(4)]
    if p.get("diag"):
        out += [f'<path d="{_spike(math.radians(-45 + 90 * i), p["gap"], p["diag"], p["spike_w"] * 0.55)}" '
                f'fill="{col["accent"]}"/>' for i in range(4)]
    s = p["pad"]
    out.append(f'<rect x="{f(C - s)}" y="{f(C - s)}" width="{f(2 * s)}" height="{f(2 * s)}" rx="{f(s * .25)}" '
               f'fill="{col["accent"] if not p.get("diag") else col["fg"]}"/>')
    hx, hy = C - s * 0.45, C - s * 0.45
    out.append(f'<circle cx="{f(hx)}" cy="{f(hy)}" r="{f(s * 0.2)}" fill="{col["bg"]}"/>')
    return "".join(out)


def phase_twinkle(p: dict, col: dict) -> str:
    """Three filled four-point stars, each turned by a phase step and layered: Twinkle drawn as three phases."""
    out = []
    layers = [col["accent2"], col["accent"], col["fg"]]
    for k, colour in enumerate(layers):
        rot = math.radians(p["step_deg"] * (1 - k))
        d = "".join(_spike(math.radians(-90 + 90 * j) + rot, 0, p["radius"] - p["shrink"] * (2 - k), p["spike_w"])
                    for j in range(4))
        out.append(f'<path d="{d}" fill="{colour}"/>')
    out.append(f'<circle cx="{f(C)}" cy="{f(C)}" r="{f(p["core"])}" fill="{col["bg"]}"/>')
    return "".join(out)


def signal_twinkle(p: dict, col: dict) -> str:
    """Four straight points for the star; on the diagonals, short copper waves that settle into vias."""
    out = [f'<path d="{_spike(math.radians(-90 + 90 * i), 0, p["radius"], p["spike_w"])}" fill="{col["fg"]}"/>'
           for i in range(4)]
    for i in range(4):
        a = math.radians(-45 + 90 * i)
        ux, uy = _vec(a)
        vx, vy = -uy, ux
        pts = []
        for j in range(81):
            t = j / 80
            r = p["r0"] + (p["tip"] - p["r0"]) * t
            off = p["amp"] * (1 - t) ** 1.2 * math.sin(2 * math.pi * p["cycles"] * t)
            pts.append((C + r * ux + off * vx, C + r * uy + off * vy))
        d = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts)
        out.append(f'<path d="{d}" fill="none" stroke="{col["accent"]}" stroke-width="{f(p["stroke"])}" '
                   f'stroke-linecap="round" stroke-linejoin="round"/>')
        x, y = pts[-1]
        out.append(_via(x, y, p["via"], p["via"] * 0.45, col["accent"], col["bg"]))
    out.append(f'<circle cx="{f(C)}" cy="{f(C)}" r="{f(p["core"])}" fill="{col["bg"]}"/>')
    return "".join(out)


def wave_star(p: dict, col: dict) -> str:
    """Four rays drawn as sine waves that calm down towards the tips, around a solid core: a star made of signal."""
    out = []
    colours = [col["fg"], col["accent"], col["fg"], col["accent"]] if p.get("alternate") else [col["fg"]] * 4
    for i in range(4):
        a = math.radians(-90 + 90 * i)
        ux, uy = _vec(a)
        vx, vy = -uy, ux
        pts = []
        for j in range(121):
            t = j / 120
            r = p["r0"] + (p["radius"] - p["r0"]) * t
            amp = p["amp"] * (1 - t) ** 1.4
            off = amp * math.sin(2 * math.pi * p["cycles"] * t)
            pts.append((C + r * ux + off * vx, C + r * uy + off * vy))
        d = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts)
        out.append(f'<path d="{d}" fill="none" stroke="{colours[i]}" stroke-width="{f(p["stroke"])}" '
                   f'stroke-linecap="round" stroke-linejoin="round"/>')
    if p.get("diag"):
        for i in range(4):
            a = math.radians(-45 + 90 * i)
            x0, y0 = polar(p["r0"], a)
            x1, y1 = polar(p["diag"], a)
            out.append(f'<line x1="{f(x0)}" y1="{f(y0)}" x2="{f(x1)}" y2="{f(y1)}" stroke="{col["accent2"]}" '
                       f'stroke-width="{f(p["stroke"] * 0.7)}" stroke-linecap="round"/>')
    out.append(f'<circle cx="{f(C)}" cy="{f(C)}" r="{f(p["core"])}" fill="{col["fg"]}"/>')
    out.append(f'<circle cx="{f(C)}" cy="{f(C)}" r="{f(p["core"] * 0.42)}" fill="{col["bg"]}"/>')
    return "".join(out)


def phase_trace(p: dict, col: dict) -> str:
    """The trace star with a three-phase rosette at its heart instead of a pad."""
    inner = trace_star(p, col)
    inner = inner[:inner.rfind("<rect")]  # drop the square pad
    ring = phase_star({"r0": p["rose_r"], "shrink": 0, "amp": p["rose_amp"], "lobes": 4, "twist": 1,
                       "stroke": p["rose_stroke"], "core": p["rose_core"], "opacity": [1, 1, 1]}, col)
    disc = f'<circle cx="{f(C)}" cy="{f(C)}" r="{f(p["rose_r"] + p["rose_amp"] + 10)}" fill="{col["bg"]}"/>'
    return inner + disc + ring


# --- Twinkle family: the curved four-point star, made ours with hardware details ------------------------------

def tw(radii: tuple, pinch: float, rot: float = 0.0, cx: float = C, cy: float = C) -> str:
    """Curved four-point star path. radii = (up, right, down, left) tip distances; pinch = control-point radius."""
    pts = [(cx + r * math.cos(math.radians(-90 + 90 * i) + rot), cy + r * math.sin(math.radians(-90 + 90 * i) + rot))
           for i, r in enumerate(radii)]
    d = f"M{f(pts[0][0])},{f(pts[0][1])}"
    for i in range(4):
        a = math.radians(-45 + 90 * i) + rot
        qx, qy = cx + pinch * math.cos(a), cy + pinch * math.sin(a)
        nx, ny = pts[(i + 1) % 4]
        d += f" Q{f(qx)},{f(qy)} {f(nx)},{f(ny)}"
    return d + " Z"


def _astroid_r(theta: float, R: float, p: float) -> float:
    return R / (abs(math.cos(theta)) ** p + abs(math.sin(theta)) ** p) ** (1 / p)


def via_twinkle(p: dict, col: dict) -> str:
    """Twinkle whose four points run into vias, with a pin-1 hole at its heart."""
    R = p["radius"]
    out = [f'<path d="{tw((R,) * 4, p["pinch"])}" fill="{col["fg"]}"/>']
    for i in range(4):
        x, y = polar(R, math.radians(-90 + 90 * i))
        out.append(_via(x, y, p["via"], p["via_hole"], col["accent"] if p.get("copper_vias") else col["fg"],
                        col["bg"]))
    out.append(f'<circle cx="{f(C)}" cy="{f(C)}" r="{f(p["hole"])}" fill="{col["bg"]}"/>')
    return "".join(out)


def contour_twinkle(p: dict, col: dict) -> str:
    """Twinkle drawn as isolation-routing contours, the way a PCB mill cuts around copper."""
    out = []
    for k, s in enumerate(p["scales"]):
        colour = col["fg"] if k % 2 == 0 else col["accent"]
        out.append(f'<path d="{tw((p["radius"] * s,) * 4, p["pinch"] * s)}" fill="none" stroke="{colour}" '
                   f'stroke-width="{f(p["stroke"])}" stroke-linejoin="round"/>')
    out.append(f'<circle cx="{f(C)}" cy="{f(C)}" r="{f(p["core"])}" fill="{col["fg"]}"/>')
    return "".join(out)


def die_twinkle(p: dict, col: dict) -> str:
    """Twinkle with a die window cut in the middle and the pin-1 dot inside it."""
    out = [f'<path d="{tw((p["radius"],) * 4, p["pinch"])}" fill="{col["fg"]}"/>', _diamond(p["window"], col["bg"])]
    s = p["window"] * 0.62
    out.append(f'<rect x="{f(C - s)}" y="{f(C - s)}" width="{f(2 * s)}" height="{f(2 * s)}" rx="{f(s * .2)}" '
               f'transform="rotate(45 {f(C)} {f(C)})" fill="{col["accent"]}"/>')
    dx, dy = polar(s * 0.75, math.radians(-90))
    out.append(f'<circle cx="{f(dx)}" cy="{f(dy)}" r="{f(s * 0.2)}" fill="{col["bg"]}"/>')
    return "".join(out)


def pad_star(p: dict, col: dict) -> str:
    """Four round pads in a square; the twinkle is the copper left between them."""
    R, r = p["half"], p["pad_r"]
    out = [f'<rect x="{f(C - R)}" y="{f(C - R)}" width="{f(2 * R)}" height="{f(2 * R)}" fill="{col["fg"]}"/>']
    for sx in (-1, 1):
        for sy in (-1, 1):
            out.append(f'<circle cx="{f(C + sx * R)}" cy="{f(C + sy * R)}" r="{f(r)}" fill="{col["bg"]}"/>')
            out.append(f'<circle cx="{f(C + sx * R)}" cy="{f(C + sy * R)}" r="{f(r - p["ring_gap"])}" '
                       f'fill="{col["accent"]}"/>')
            out.append(f'<circle cx="{f(C + sx * R)}" cy="{f(C + sy * R)}" r="{f(p["drill"])}" fill="{col["bg"]}"/>')
    out.append(f'<circle cx="{f(C)}" cy="{f(C)}" r="{f(p["core"])}" fill="{col["bg"]}"/>')
    return "".join(out)


def north_twinkle(p: dict, col: dict) -> str:
    """A tall, asymmetric twinkle like a guiding north star, with a copper companion."""
    out = [f'<path d="{tw(tuple(p["radii"]), p["pinch"], cy=C + p["shift"])}" fill="{col["fg"]}"/>']
    cx, cy, r = C + p["comp"][0], C + p["comp"][1], p["comp"][2]
    out.append(f'<path d="{tw((r, r * .8, r, r * .8), r * .22, cx=cx, cy=cy)}" fill="{col["accent"]}"/>')
    out.append(f'<circle cx="{f(C)}" cy="{f(C + p["shift"])}" r="{f(p["hole"])}" fill="{col["bg"]}"/>')
    return "".join(out)


def wave_twinkle(p: dict, col: dict) -> str:
    """Twinkle whose curved sides carry a sine ripple: the star drawn by a signal."""
    R, q = p["radius"], p["pinch"]
    tips = [polar(R, math.radians(-90 + 90 * i)) for i in range(4)]
    pts = []
    for i in range(4):
        (x0, y0), (x2, y2) = tips[i], tips[(i + 1) % 4]
        x1, y1 = polar(q, math.radians(-45 + 90 * i))
        for j in range(60):
            t = j / 60
            bx = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * x1 + t * t * x2
            by = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * y1 + t * t * y2
            tx = 2 * (1 - t) * (x1 - x0) + 2 * t * (x2 - x1)
            ty = 2 * (1 - t) * (y1 - y0) + 2 * t * (y2 - y1)
            n = math.hypot(tx, ty) or 1
            off = p["amp"] * math.sin(math.pi * t) * math.sin(2 * math.pi * p["cycles"] * t)
            pts.append((bx - ty / n * off, by + tx / n * off))
    d = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts) + " Z"
    return (f'<path d="{d}" fill="{col["fg"]}"/>'
            f'<circle cx="{f(C)}" cy="{f(C)}" r="{f(p["hole"])}" fill="{col["bg"]}"/>')


def faceted_twinkle(p: dict, col: dict) -> str:
    """Twinkle cut along its axes into two tones, like a faceted gem or a lit and shaded relief."""
    R, q = p["radius"], p["pinch"]
    out = [f'<path d="{tw((R,) * 4, q)}" fill="{col["fg"]}"/>']
    for i in range(4):
        a0 = math.radians(-90 + 90 * i)
        tx, ty = polar(R, a0)
        qx, qy = polar(q, a0 + math.radians(45))
        nx, ny = polar(R, a0 + math.radians(90))
        out.append(f'<path d="M{f(C)},{f(C)} L{f(tx)},{f(ty)} Q{f(qx)},{f(qy)} {f(nx)},{f(ny)} Z" '
                   f'fill="{col["accent"]}" opacity="{p["shade"]}"/>' if i % 2 == 0 else "")
    out.append(f'<circle cx="{f(C)}" cy="{f(C)}" r="{f(p["hole"])}" fill="{col["bg"]}"/>')
    return "".join(out)


def pixel_twinkle(p: dict, col: dict) -> str:
    """Twinkle lit on an LED matrix: every cell inside the star is on."""
    n, R = p["grid"], p["radius"]
    step = 2 * R / (n - 1)
    out = []
    for iy in range(n):
        for ix in range(n):
            x, y = -R + ix * step, -R + iy * step
            rr, th = math.hypot(x, y), math.atan2(y, x)
            on = rr <= _astroid_r(th, R * 1.02, p["shape"])
            centre = ix == iy == n // 2
            if centre:
                fill = col["accent"]
            elif on:
                fill = col["fg"]
            else:
                fill = col["line"]
            op = "1" if on or centre else f'{p["off_opacity"]}'
            out.append(f'<rect x="{f(C + x - p["dot"])}" y="{f(C + y - p["dot"])}" width="{f(2 * p["dot"])}" '
                       f'height="{f(2 * p["dot"])}" rx="{f(p["dot"] * p["round"])}" fill="{fill}" opacity="{op}"/>')
    return "".join(out)


def binary_twinkle(p: dict, col: dict) -> str:
    """Two twinkles, a large one and a copper one overlapping it, cut apart by a thin gap."""
    big = tw((p["r1"],) * 4, p["r1"] * p["pinch"], cx=C + p["o1"][0], cy=C + p["o1"][1])
    r2 = p["r2"]
    small = tw((r2,) * 4, r2 * p["pinch"], cx=C + p["o2"][0], cy=C + p["o2"][1])
    return (f'<path d="{big}" fill="{col["fg"]}"/>'
            f'<path d="{small}" fill="{col["bg"]}" stroke="{col["bg"]}" stroke-width="{f(p["gap"] * 2)}" '
            f'stroke-linejoin="round"/><path d="{small}" fill="{col["accent"]}"/>')


def package_twinkle(p: dict, col: dict) -> str:
    """Twinkle printed on a chip package, with pins on all four sides and the pin-1 dot."""
    s, out = p["body"], []
    for side in range(4):
        for k in range(p["pins"]):
            t = -s + (k + 1) * 2 * s / (p["pins"] + 1)
            x0, y0, x1, y1 = {0: (t, -s, t, -s - p["pin_len"]), 1: (s, t, s + p["pin_len"], t),
                              2: (t, s, t, s + p["pin_len"]), 3: (-s, t, -s - p["pin_len"], t)}[side]
            out.append(f'<line x1="{f(C + x0)}" y1="{f(C + y0)}" x2="{f(C + x1)}" y2="{f(C + y1)}" '
                       f'stroke="{col["accent"]}" stroke-width="{f(p["pin_w"])}" stroke-linecap="round"/>')
    out.append(f'<rect x="{f(C - s)}" y="{f(C - s)}" width="{f(2 * s)}" height="{f(2 * s)}" rx="{f(p["corner"])}" '
               f'fill="{col["fg"]}"/>')
    out.append(f'<path d="{tw((p["star"],) * 4, p["star"] * 0.22)}" fill="{col["bg"]}"/>')
    out.append(f'<circle cx="{f(C - s * .72)}" cy="{f(C - s * .72)}" r="{f(s * .09)}" fill="{col["bg"]}"/>')
    return "".join(out)


def nested_twinkle(p: dict, col: dict) -> str:
    """A twinkle outline traced like a copper trace, with a solid copper twinkle inside it."""
    R = p["radius"]
    return (f'<path d="{tw((R,) * 4, R * p["pinch"])}" fill="none" stroke="{col["fg"]}" '
            f'stroke-width="{f(p["stroke"])}" stroke-linejoin="round"/>'
            f'<path d="{tw((R * p["inner"],) * 4, R * p["inner"] * p["pinch"])}" fill="{col["accent"]}"/>')


def tri_twinkle(p: dict, col: dict) -> str:
    """Three curved twinkles, each turned by a phase step and layered."""
    out = []
    for k, colour in enumerate([col["accent2"], col["accent"], col["fg"]]):
        R = p["radius"] - p["shrink"] * (2 - k)
        out.append(f'<path d="{tw((R,) * 4, R * p["pinch"], math.radians(p["step_deg"] * (1 - k)))}" '
                   f'fill="{colour}"/>')
    out.append(f'<circle cx="{f(C)}" cy="{f(C)}" r="{f(p["hole"])}" fill="{col["bg"]}"/>')
    return "".join(out)


def ray_twinkle(p: dict, col: dict) -> str:
    """Twinkle drawn as rays whose lengths follow the star's outline, around a solid core."""
    out = []
    for i in range(p["rays"]):
        a = 2 * math.pi * i / p["rays"]
        r1 = _astroid_r(a, p["radius"], p["shape"])
        if r1 < p["gap"] + 6:
            continue
        x0, y0 = polar(p["gap"], a)
        x1, y1 = polar(r1, a)
        main = min(abs(math.cos(a)), abs(math.sin(a))) < 0.2
        out.append(f'<line x1="{f(x0)}" y1="{f(y0)}" x2="{f(x1)}" y2="{f(y1)}" '
                   f'stroke="{col["fg"] if main else col["accent"]}" stroke-width="{f(p["w"])}" '
                   f'stroke-linecap="round"/>')
    out.append(f'<circle cx="{f(C)}" cy="{f(C)}" r="{f(p["core"])}" fill="{col["fg"]}"/>')
    return "".join(out)


def encoder_twinkle(p: dict, col: dict) -> str:
    """Twinkle inside the tick ring of a rotary encoder: the star that knows where it's pointing."""
    out = []
    for i in range(p["ticks"]):
        a = 2 * math.pi * i / p["ticks"]
        long_tick = i % (p["ticks"] // 4) == 0
        r0 = p["ring"] - (p["tick_long"] if long_tick else p["tick"])
        x0, y0 = polar(r0, a)
        x1, y1 = polar(p["ring"], a)
        out.append(f'<line x1="{f(x0)}" y1="{f(y0)}" x2="{f(x1)}" y2="{f(y1)}" stroke="{col["accent"]}" '
                   f'stroke-width="{f(p["tick_w"])}" stroke-linecap="round"/>')
    R = p["star"]
    out.append(f'<path d="{tw((R,) * 4, R * p["pinch"], math.radians(p["turn_deg"]))}" fill="{col["fg"]}"/>')
    out.append(f'<circle cx="{f(C)}" cy="{f(C)}" r="{f(p["hole"])}" fill="{col["bg"]}"/>')
    return "".join(out)


TWINKLE_FAMILY = {
    "via-twinkle": ("Via twinkle", "Twinkle whose points run into vias, with a pin-1 hole at its heart.",
                    via_twinkle, {"radius": 200, "pinch": 44, "via": 34, "via_hole": 13, "hole": 24,
                                  "copper_vias": True}),
    "contour-twinkle": ("Contour twinkle", "Twinkle drawn as isolation-routing contours, as a PCB mill cuts them.",
                        contour_twinkle, {"radius": 228, "pinch": 50, "scales": [1, 0.68, 0.38], "stroke": 18,
                                          "core": 20}),
    "die-twinkle": ("Die twinkle", "Twinkle with a die window cut in its middle and the pin-1 dot inside.",
                    die_twinkle, {"radius": 228, "pinch": 52, "window": 58}),
    "pad-star": ("Pad star", "Four round plated pads in a square; the twinkle is the copper left between them.",
                 pad_star, {"half": 128, "pad_r": 118, "ring_gap": 12, "drill": 40, "core": 16}),
    "north-twinkle": ("North twinkle", "A tall, asymmetric twinkle like a guiding north star, with a companion.",
                      north_twinkle, {"radii": [232, 132, 196, 132], "pinch": 36, "shift": 14,
                                      "comp": [128, -132, 50], "hole": 0}),
    "wave-twinkle": ("Wave twinkle", "Twinkle whose curved sides carry a sine ripple: a star drawn by a signal.",
                     wave_twinkle, {"radius": 228, "pinch": 50, "amp": 6, "cycles": 6, "hole": 24}),
    "faceted-twinkle": ("Faceted twinkle", "Twinkle cut along its axes into two tones, like a faceted gem.",
                        faceted_twinkle, {"radius": 228, "pinch": 50, "shade": 1, "hole": 0}),
    "pixel-twinkle": ("Pixel twinkle", "Twinkle lit on an LED matrix, like the addressable LEDs our drivers run.",
                      pixel_twinkle, {"grid": 9, "radius": 212, "dot": 20, "round": 0.35, "shape": 0.95,
                                      "off_opacity": 0.18}),
    "binary-twinkle": ("Binary twinkle", "Two twinkles, one copper, overlapping and cut apart by a thin gap.",
                       binary_twinkle, {"r1": 200, "o1": [-34, 34], "r2": 92, "o2": [120, -120], "pinch": 0.22,
                                        "gap": 12}),
    "package-twinkle": ("Package twinkle", "Twinkle printed on a chip package, pins on four sides, pin-1 dot.",
                        package_twinkle, {"body": 150, "pins": 5, "pin_len": 50, "pin_w": 16, "corner": 22,
                                          "star": 118}),
    "nested-twinkle": ("Nested twinkle", "A twinkle traced in outline, with a solid copper twinkle inside it.",
                       nested_twinkle, {"radius": 222, "pinch": 0.22, "stroke": 20, "inner": 0.5}),
    "tri-twinkle": ("Tri twinkle", "Three curved twinkles, each turned by a phase step, layered.",
                    tri_twinkle, {"radius": 230, "pinch": 0.21, "step_deg": 8, "shrink": 22, "hole": 20}),
    "ray-twinkle": ("Ray twinkle", "Twinkle drawn as rays whose lengths follow its outline, around a core.",
                    ray_twinkle, {"rays": 72, "radius": 230, "shape": 0.62, "gap": 54, "w": 9, "core": 34}),
    "encoder-twinkle": ("Encoder twinkle", "Twinkle inside the tick ring of a rotary encoder, turned slightly.",
                        encoder_twinkle, {"ticks": 48, "ring": 240, "tick": 16, "tick_long": 34, "tick_w": 8,
                                          "star": 172, "pinch": 0.22, "turn_deg": 0, "hole": 20}),
}


CONCEPTS = {
    "twinkle": {
        "title": "Twinkle",
        "story": "The original: a curved four-point star with a pin-1 hole. Too close to the sparkle used by Gemini and other AI products; kept for comparison.",
        "draw": twinkle,
        "params": {"radius": 222, "pinch": 48, "hole_offset": 34, "hole_r": 28, "companion": [150, -150, 46]},
        "accent": "copper",
    },
    "die-star": {
        "title": "Die star",
        "story": "A chip die whose package pads grow into a starburst: silicon and star in one shape.",
        "draw": die_star,
        "params": {"pads": 32, "die": 66, "gap": 98, "pad_min": 30, "pad_max": 150, "pad_w": 18,
                   "sharpness": 6},
        "accent": "copper",
    },
    "trace-star": {
        "title": "Trace star",
        "story": "Eight copper traces leave a centre pad, jog 45 degrees and end in vias, like a routed board.",
        "draw": trace_star,
        "params": {"pad": 44, "trace": 24, "via": 18, "knee_long": 150, "tip_long": 214,
                   "knee_short": 104, "tip_short": 150, "jog_deg": 14},
        "accent": "copper",
    },
    "phase-star": {
        "title": "Phase star",
        "story": "Three sine-edged stars, 120 degrees apart: the three phases that drive a motor, drawn as a star.",
        "draw": phase_star,
        "params": {"r0": 168, "shrink": 0, "amp": 58, "lobes": 6, "twist": 1, "stroke": 13, "core": 40,
                   "opacity": [1, 1, 1]},
        "accent": "copper",
    },
    "constellation-k": {
        "title": "Constellation K",
        "story": "The K of Kokeb as a constellation: many parts joined into one picture, a map of the ecosystem.",
        "draw": constellation,
        "params": {
            "nodes": {"top": (-92, -176), "mid": (-92, 0), "bot": (-92, 176), "join": (-30, 4),
                      "arm_up": (110, -170), "arm_dn": (128, 172), "spur": (60, -66)},
            "edges": [("top", "mid"), ("mid", "bot"), ("mid", "join"), ("join", "spur"), ("spur", "arm_up"),
                      ("join", "arm_dn")],
            "sizes": {"top": 28, "bot": 28, "arm_up": 30, "arm_dn": 30, "mid": 22, "spur": 20},
            "bright": "join", "node_r": 22, "line_w": 16,
        },
        "accent": "star",
    },
    "eight-point": {
        "title": "Eight-point",
        "story": "Two interlaced squares make an eight-point star, a shape found across Ethiopian textiles.",
        "draw": eight_point,
        "params": {"half": 160, "corner": 5, "ring": 72, "core": 40},
        "accent": "copper",
    },
    "routed-star": {
        "title": "Routed star",
        "story": "Twinkle's simplicity with straight, chamfered sides like a routed trace, and a via at every point.",
        "draw": routed_star,
        "params": {"radius": 196, "inner": 62, "chamfer_deg": 14, "round": 8, "via": 34, "via_hole": 13,
                   "pad_hole": 34},
        "accent": "copper",
    },
    "trace-twinkle": {
        "title": "Trace twinkle",
        "story": "Twinkle's four points plus Trace star's copper: short traces on the diagonals jog out to vias.",
        "draw": trace_twinkle,
        "params": {"radius": 226, "spike_w": 34, "pad": 46, "trace": 20, "knee": 112, "tip": 168,
                   "jog_deg": 16, "via": 22},
        "accent": "copper",
    },
    "split-star": {
        "title": "Split star",
        "story": "Four points that stop short of a chip pad, like traces running into a package. Simple at 16 px.",
        "draw": split_star,
        "params": {"radius": 226, "gap": 76, "spike_w": 40, "pad": 52},
        "accent": "copper",
    },
    "split-star-8": {
        "title": "Split star, eight",
        "story": "Split star with four shorter copper points on the diagonals: a compass, a chip, a star.",
        "draw": split_star,
        "params": {"radius": 226, "gap": 76, "spike_w": 40, "pad": 50, "diag": 150},
        "accent": "copper",
    },
    "phase-twinkle": {
        "title": "Phase twinkle",
        "story": "Three straight-sided four-point stars, each turned by a phase step and layered: a star in motion.",
        "draw": phase_twinkle,
        "params": {"radius": 226, "spike_w": 36, "step_deg": 11, "shrink": 14, "core": 22},
        "accent": "copper",
    },
    "signal-twinkle": {
        "title": "Signal twinkle",
        "story": "All three ideas in one: Twinkle's points, Phase star's waves and Trace star's vias on the diagonals.",
        "draw": signal_twinkle,
        "params": {"radius": 226, "spike_w": 34, "r0": 70, "tip": 172, "amp": 18, "cycles": 1.5, "stroke": 18,
                   "via": 22, "core": 22},
        "accent": "copper",
    },
    "wave-star": {
        "title": "Wave star",
        "story": "Four rays drawn as sine waves that settle into straight points: a star made of signal.",
        "draw": wave_star,
        "params": {"r0": 58, "radius": 226, "amp": 30, "cycles": 2.5, "stroke": 22, "core": 44,
                   "alternate": True},
        "accent": "copper",
    },
    "wave-star-8": {
        "title": "Wave star, eight",
        "story": "Wave star with straight teal rays on the diagonals: signal and structure together.",
        "draw": wave_star,
        "params": {"r0": 58, "radius": 226, "amp": 30, "cycles": 2.5, "stroke": 22, "core": 44,
                   "alternate": False, "diag": 140},
        "accent": "copper",
    },
    "phase-trace": {
        "title": "Phase trace",
        "story": "Trace star with a three-phase rosette at its heart: routing outside, motion inside.",
        "draw": phase_trace,
        "params": {"pad": 44, "trace": 22, "via": 18, "knee_long": 158, "tip_long": 216,
                   "knee_short": 116, "tip_short": 158, "jog_deg": 14,
                   "rose_r": 54, "rose_amp": 16, "rose_stroke": 9, "rose_core": 16},
        "accent": "copper",
    },
}

for _k, (_t, _s, _d, _p) in TWINKLE_FAMILY.items():
    CONCEPTS[_k] = {"title": _t, "story": _s, "draw": _d, "params": _p, "accent": "copper"}


# --- Shortlist: the favourites and their combinations -----------------------------------------------------------
# Every function below draws a twinkle in one of these styles, so styles combine freely:
#   solid    one colour
#   bevel    each point split along its axis, one half in a second tone (lit from one side)
#   contour  nested outlines, like isolation routing
#   pads     the star left between four round plated pads

_uid = [0]


def _id(prefix: str) -> str:
    _uid[0] += 1
    return f"{prefix}{_uid[0]}"


def tw_style(style: str, R: float, pinch: float, col: dict, tone: str, cx: float = C, cy: float = C,
             rot: float = 0.0, extra: dict | None = None) -> str:
    """Draw one twinkle of radius R in the given style. `tone` is the colour of bevels and inner contours."""
    extra = extra or {}
    if style == "solid":
        return f'<path d="{tw((R,) * 4, pinch, rot, cx, cy)}" fill="{col["fg"]}"/>'
    if style == "bevel":
        out = [f'<path d="{tw((R,) * 4, pinch, rot, cx, cy)}" fill="{col["fg"]}"/>']
        for i in range(4):
            a0 = math.radians(-90 + 90 * i) + rot
            tx, ty = cx + R * math.cos(a0), cy + R * math.sin(a0)
            qx, qy = cx + pinch * math.cos(a0 + math.pi / 4), cy + pinch * math.sin(a0 + math.pi / 4)
            nx, ny = cx + R * math.cos(a0 + math.pi / 2), cy + R * math.sin(a0 + math.pi / 2)
            mx, my = 0.25 * tx + 0.5 * qx + 0.25 * nx, 0.25 * ty + 0.5 * qy + 0.25 * ny
            hx, hy = (tx + qx) / 2, (ty + qy) / 2
            out.append(f'<path d="M{f(cx)},{f(cy)} L{f(tx)},{f(ty)} Q{f(hx)},{f(hy)} {f(mx)},{f(my)} Z" '
                       f'fill="{tone}"/>')
        return "".join(out)
    if style == "contour":
        scales = extra.get("scales", [1, 0.66, 0.34])
        sw = extra.get("stroke", 18) * R / 228
        out = []
        for k, s in enumerate(scales):
            colour = col["fg"] if k % 2 == 0 else tone
            out.append(f'<path d="{tw((R * s,) * 4, pinch * s, rot, cx, cy)}" fill="none" stroke="{colour}" '
                       f'stroke-width="{f(sw)}" stroke-linejoin="round"/>')
        if extra.get("core_star"):
            s = scales[-1] * 0.45
            out.append(f'<path d="{tw((R * s,) * 4, pinch * s, rot, cx, cy)}" fill="{tone}"/>')
        return "".join(out)
    raise ValueError(style)


def binary2(p: dict, col: dict) -> str:
    """Binary twinkle with a style per star; the companion is cut out of the big star by a thin gap."""
    tone = col[p.get("tone", "accent")] if p.get("tone", "accent") in col else PALETTE[p["tone"]]
    big = tw_style(p["big_style"], p["r1"], p["r1"] * p["pinch"], col, tone, C + p["o1"][0], C + p["o1"][1],
                   extra=p.get("extra"))
    r2, cx2, cy2 = p["r2"], C + p["o2"][0], C + p["o2"][1]
    small_path = tw((r2,) * 4, r2 * p["pinch"], 0, cx2, cy2)
    cut = (f'<path d="{small_path}" fill="{col["bg"]}" stroke="{col["bg"]}" stroke-width="{f(p["gap"] * 2)}" '
           f'stroke-linejoin="round"/>') if p["gap"] else ""
    small_col = dict(col, fg=col["accent"])
    small = tw_style(p.get("small_style", "solid"), r2, r2 * p["pinch"], small_col, col["fg"], cx2, cy2)
    hx, hy = C + p["o1"][0], C + p["o1"][1]
    if p.get("hole_offset"):
        hx += p["hole_offset"] * math.cos(math.radians(-135))
        hy += p["hole_offset"] * math.sin(math.radians(-135))
    hole = (f'<circle cx="{f(hx)}" cy="{f(hy)}" r="{f(p["hole"])}" fill="{col["bg"]}"/>' if p.get("hole") else "")
    return big + hole + cut + small


def pads2(p: dict, col: dict) -> str:
    """The star left between four round plated pads, with a choice of what fills the star."""
    h, r = p["half"], p["pad_r"]
    m = _id("padmask")
    circles = "".join(f'<circle cx="{f(C + sx * h)}" cy="{f(C + sy * h)}" r="{f(r)}" fill="black"/>'
                      for sx in (-1, 1) for sy in (-1, 1))
    mask = (f'<mask id="{m}"><rect x="{f(C - h)}" y="{f(C - h)}" width="{f(2 * h)}" height="{f(2 * h)}" '
            f'fill="white"/>{circles}</mask>')
    tone = col["accent"] if p.get("fill_tone") == "accent" else PALETTE["ink"] if col["bg"] == PALETTE["paper"] \
        else PALETTE["copper"]
    inner = f'<rect x="{f(C - h)}" y="{f(C - h)}" width="{f(2 * h)}" height="{f(2 * h)}" fill="{col["fg"]}"/>'
    if p.get("bevel"):
        tip = h  # the star's tips sit on the square's edge midpoints
        for i in range(4):
            a0 = math.radians(-90 + 90 * i)
            tx, ty = polar(tip, a0)
            ex, ey = polar(h * math.sqrt(2), a0 + math.pi / 4)
            inner += f'<path d="M{f(C)},{f(C)} L{f(tx)},{f(ty)} L{f(ex)},{f(ey)} Z" fill="{tone}"/>'
    out = [f'<defs>{mask}</defs><g mask="url(#{m})">{inner}</g>']
    ring_col = col["accent"] if not p.get("mono_pads") else col["fg"]
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = C + sx * h, C + sy * h
            out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r - p["ring_gap"])}" fill="{ring_col}"/>')
            out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(p["drill"])}" fill="{col["bg"]}"/>')
    if p.get("core"):
        out.append(f'<circle cx="{f(C)}" cy="{f(C)}" r="{f(p["core"])}" fill="{col["bg"]}"/>')
    if p.get("companion"):
        cx, cy, s = C + p["companion"][0], C + p["companion"][1], p["companion"][2]
        out.append(f'<path d="{tw((s,) * 4, s * .22, 0, cx, cy)}" fill="{col["bg"]}"/>')
    return "".join(out)


def kokeb_mark(p: dict, col: dict) -> str:
    """The final family: a contour star with a solid core, a copper companion, and vias.

    The big star is drawn as routed contours around a solid core (the layers), the copper companion overlaps it
    (the pair), and vias mark where things connect: in the core (offset or centred) and optionally at the tips.
    """
    R, pinch = p["r1"], p["pinch"]
    cx, cy = C + p["o1"][0], C + p["o1"][1]
    sw = p["stroke"]
    out = []
    for k, s in enumerate(p["contours"]):
        colour = col["fg"] if k % 2 == 0 else col["accent"]
        out.append(f'<path d="{tw((R * s,) * 4, R * s * pinch, 0, cx, cy)}" fill="none" stroke="{colour}" '
                   f'stroke-width="{f(sw)}" stroke-linejoin="round"/>')
    core = p["core"]
    out.append(f'<path d="{tw((R * core,) * 4, R * core * pinch, 0, cx, cy)}" fill="{col["fg"]}"/>')
    # Via in the core: "offset" (a drill toward the upper left, like pin 1) or "center" (a plated via).
    v = p.get("core_via")
    if v == "offset":
        hx = cx + p["via_offset"] * math.cos(math.radians(-135))
        hy = cy + p["via_offset"] * math.sin(math.radians(-135))
        out.append(f'<circle cx="{f(hx)}" cy="{f(hy)}" r="{f(p["drill"])}" fill="{col["bg"]}"/>')
    elif v == "center":
        out.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(p["ring"])}" fill="{col["accent"]}"/>')
        out.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(p["drill"])}" fill="{col["bg"]}"/>')
    # Vias at the outer contour's tips.
    for i in p.get("tip_vias", []):
        a = math.radians(-90 + 90 * i)
        x, y = cx + R * math.cos(a), cy + R * math.sin(a)
        out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(p["tip_via"])}" fill="{col["accent"]}"/>')
        out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(p["tip_via"] * 0.42)}" fill="{col["bg"]}"/>')
    # Companion, cut out of whatever it overlaps by a thin gap.
    r2, x2, y2 = p["r2"], C + p["o2"][0], C + p["o2"][1]
    small = tw((r2,) * 4, r2 * pinch, 0, x2, y2)
    out.append(f'<path d="{small}" fill="{col["bg"]}" stroke="{col["bg"]}" stroke-width="{f(p["gap"] * 2)}" '
               f'stroke-linejoin="round"/>')
    out.append(f'<path d="{small}" fill="{col["accent"]}"/>')
    if p.get("companion_via"):
        out.append(f'<circle cx="{f(x2)}" cy="{f(y2)}" r="{f(p["companion_via"])}" fill="{col["bg"]}"/>')
    return "".join(out)


FINAL_BASE = {"r1": 214, "o1": [-28, 28], "pinch": 0.22, "contours": [1, 0.72], "stroke": 20, "core": 0.46,
              "r2": 90, "o2": [128, -128], "gap": 12}
FINAL = {
    "final-a": ("Final A: offset via", "Contour star, solid core with an offset via like pin 1, copper companion. "
                "The quietest of the three.", kokeb_mark,
                dict(FINAL_BASE, core_via="offset", via_offset=20, drill=19)),
    "final-b": ("Final B: centred plated via", "The core carries a centred plated via: a copper ring around a drill. "
                "The via becomes the heart of the star.", kokeb_mark,
                dict(FINAL_BASE, core_via="center", ring=34, drill=14)),
    "final-c": ("Final C: connected", "Final B plus vias where the outer contour's points land, on the three points "
                "away from the companion: the star connects things.", kokeb_mark,
                dict(FINAL_BASE, r1=198, o1=[-20, 20], core_via="center", ring=32, drill=13, tip_vias=[1, 2, 3], tip_via=26)),
}
for _k, (_t, _s, _d, _p) in FINAL.items():
    # At favicon sizes contour lines blur together, so the small version is the same mark with a solid star.
    _small = dict(_p, contours=[], core=0.9, tip_vias=[], ring=_p.get("ring", 0) * 1.5,
                  drill=_p["drill"] * 1.5, via_offset=_p.get("via_offset", 0) * 2)
    CONCEPTS[_k] = {"title": _t, "story": _s, "draw": _d, "params": _p, "accent": "copper", "small": _small}


def kokeb_mark2(p: dict, col: dict) -> str:
    """The final mark with true equal-width contours.

    The big star is cut into bands of constant width, like isolation routing keeps a constant clearance: an outer
    navy line, a gap, a copper line, a gap, then the solid core. Each band is a stroke of the star's own outline,
    clipped to the star, so every gap is the same width all the way round, tips included. A copper companion
    overlaps it, cut out by a thin gap; vias can sit on chosen points.
    """
    R, pinch = p["r1"], p["pinch"]
    cx, cy = C + p["o1"][0], C + p["o1"][1]
    star = tw((R,) * 4, R * pinch, 0, cx, cy)
    cid = _id("starclip")
    w, gap = p["line"], p["space"]
    # Paint from the widest band inwards; each stroke covers everything within half its width of the outline.
    bands = [(2 * (2 * w + 2 * gap), col["bg"]), (2 * (2 * w + gap), col["accent"]),
             (2 * (w + gap), col["bg"]), (2 * w, col["fg"])]
    out = [f'<defs><clipPath id="{cid}"><path d="{star}"/></clipPath></defs>',
           f'<path d="{star}" fill="{col["fg"]}"/>', f'<g clip-path="url(#{cid})">']
    out += [f'<path d="{star}" fill="none" stroke="{c}" stroke-width="{f(sw)}" stroke-linejoin="round"/>'
            for sw, c in bands]
    out.append("</g>")
    if p.get("core_drill"):
        hx = cx + p["drill_offset"] * math.cos(math.radians(-135))
        hy = cy + p["drill_offset"] * math.sin(math.radians(-135))
        out.append(f'<circle cx="{f(hx)}" cy="{f(hy)}" r="{f(p["core_drill"])}" fill="{col["bg"]}"/>')
    for i in p.get("tip_vias", []):
        a = math.radians(-90 + 90 * i)
        x, y = cx + (R - p["via_inset"]) * math.cos(a), cy + (R - p["via_inset"]) * math.sin(a)
        out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(p["tip_via"] + p["via_gap"])}" fill="{col["bg"]}"/>')
        out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(p["tip_via"])}" fill="{col["accent"]}"/>')
        out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(p["tip_via"] * 0.42)}" fill="{col["bg"]}"/>')
    r2, x2, y2 = p["r2"], C + p["o2"][0], C + p["o2"][1]
    small = tw((r2,) * 4, r2 * pinch, 0, x2, y2)
    out.append(f'<path d="{small}" fill="{col["bg"]}" stroke="{col["bg"]}" stroke-width="{f(p["gap"] * 2)}" '
               f'stroke-linejoin="round"/>')
    out.append(f'<path d="{small}" fill="{col["accent"]}"/>')
    return "".join(out)


def kokeb_arcs(p: dict, col: dict) -> str:
    """The Kokeb Labs mark: nested twinkles with true arcs, spaced evenly, and a copper companion.

    Each inner star is a real twinkle (four concave arcs), not an offset of the outer one, so every layer keeps the
    star's shape. Spacing is even where the eye reads it: on the diagonals, the midpoints of the arcs step in by one
    pitch (line + space) per layer; along the axes, the tips step in by `tip_step` pitches, because a sharp tip
    needs a longer step to show the same clearance. Each layer's curve depth follows from those two distances:
    an arc's midpoint sits at R*sqrt(2)/4 + q/2 from the centre, so q = 2 * (mid - R*sqrt(2)/4).
    """
    R0, q0 = p["r1"], p["r1"] * p["pinch"]
    cx, cy = C + p["o1"][0], C + p["o1"][1]
    line, space = p["line"], p["space"]
    pitch = line + space
    k = math.sqrt(2) / 4
    mid0 = R0 * k + q0 / 2
    out = []
    colours = [col["fg"], col["accent"]]
    for i in range(p["layers"]):
        R = R0 - i * p["tip_step"] * pitch
        q = 2 * ((mid0 - i * pitch) - R * k)
        out.append(f'<path d="{tw((R,) * 4, q, 0, cx, cy)}" fill="none" stroke="{colours[i % 2]}" '
                   f'stroke-width="{f(line)}" stroke-linejoin="round"/>')
    # The core: one more step in, filled, its edge a half line closer so the last gap matches the others.
    i = p["layers"]
    R = R0 - i * p["tip_step"] * pitch + line / 2 * p["tip_step"]
    q = 2 * ((mid0 - i * pitch + line / 2) - R * k)
    out.append(f'<path d="{tw((R,) * 4, q, 0, cx, cy)}" fill="{col["fg"]}"/>')
    r2, x2, y2 = p["r2"], C + p["o2"][0], C + p["o2"][1]
    small = tw((r2,) * 4, r2 * p["pinch"], 0, x2, y2)
    out.append(f'<path d="{small}" fill="{col["bg"]}" stroke="{col["bg"]}" stroke-width="{f(p["gap"] * 2)}" '
               f'stroke-linejoin="round"/>')
    out.append(f'<path d="{small}" fill="{col["accent"]}"/>')
    return "".join(out)


K_BASE = {"r1": 222, "o1": [-26, 26], "pinch": 0.22, "line": 20, "space": 14, "r2": 88, "o2": [130, -130],
          "gap": 12, "tip_via": 24, "via_gap": 8, "via_inset": 6}
K_FINAL = {
    "k-clean": ("K1: clean", "Equal-width contours around a solid core, and the copper companion. No vias: the "
                "layers and the pair carry it alone.", kokeb_mark2, dict(K_BASE)),
    "k-two-vias": ("K2: two vias", "K1 with the right and bottom points running into vias, like traces landing on "
                   "pads: two connections, balanced against the companion at the top right.", kokeb_mark2,
                   dict(K_BASE, r1=212, o1=[-22, 22], tip_vias=[1, 2], via_gap=0, via_inset=-4, tip_via=25)),
    "k-two-vias-drill": ("K3: two vias and a drill", "K2 with a small offset drill in the core, Twinkle's pin-1 "
                         "hole, instead of a centred via.", kokeb_mark2,
                         dict(K_BASE, r1=210, o1=[-22, 22], tip_vias=[1, 2], core_drill=15, drill_offset=24)),
}
K_FINAL["k1-arcs"] = ("K1 with arcs", "K1 redrawn so every inner layer is a true twinkle with concave arcs, "
                      "evenly spaced: the layers read as stars inside a star.", kokeb_arcs,
                      {"r1": 214, "o1": [-24, 24], "pinch": 0.22, "line": 19, "space": 15, "layers": 2,
                       "tip_step": 2.2, "r2": 88, "o2": [130, -130], "gap": 12})
for _k, (_t, _s, _d, _p) in K_FINAL.items():
    _small = dict(_p, line=0.001, space=0.001, tip_vias=[], core_drill=_p.get("core_drill", 0) * 1.6,
                  drill_offset=_p.get("drill_offset", 0) * 1.6, layers=0, tip_step=0)
    CONCEPTS[_k] = {"title": _t, "story": _s, "draw": _d, "params": _p, "accent": "copper", "small": _small}


def single2(p: dict, col: dict) -> str:
    """One twinkle in any style, with an optional hole and companion."""
    tone = col["accent"] if p.get("tone", "accent") == "accent" else PALETTE[p["tone"]]
    out = [tw_style(p["style"], p["radius"], p["radius"] * p["pinch"], col, tone, extra=p.get("extra"))]
    if p.get("hole"):
        out.append(f'<circle cx="{f(C)}" cy="{f(C)}" r="{f(p["hole"])}" fill="{col["bg"]}"/>')
    return "".join(out)


def pads_twinkle(p: dict, col: dict) -> str:
    """A full twinkle sitting between four plated pads at the corners, separated from them by a thin gap."""
    h, r = p["half"], p["pad_r"]
    out = []
    ring_col = col["fg"] if p.get("mono_pads") else col["accent"]
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = C + sx * h, C + sy * h
            out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{ring_col}"/>')
            out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(p["drill"])}" fill="{col["bg"]}"/>')
    R = p["radius"]
    path = tw((R,) * 4, R * p["pinch"])
    out.append(f'<path d="{path}" fill="{col["bg"]}" stroke="{col["bg"]}" stroke-width="{f(2 * p["gap"])}" '
               f'stroke-linejoin="round"/>')
    tone = col["accent"] if p.get("bevel") == "accent" else PALETTE["ink"]
    out.append(tw_style("bevel" if p.get("bevel") else "solid", R, R * p["pinch"], col, tone))
    if p.get("hole"):
        out.append(f'<circle cx="{f(C)}" cy="{f(C)}" r="{f(p["hole"])}" fill="{col["bg"]}"/>')
    return "".join(out)


SHORTLIST = {
    # Binary
    "binary-a": ("Binary A: classic", "The binary twinkle as you liked it, slightly tightened.",
                 binary2, {"big_style": "solid", "r1": 204, "o1": [-34, 34], "r2": 92, "o2": [124, -124],
                           "pinch": 0.22, "gap": 12}),
    "binary-b": ("Binary B: bevelled", "The big star bevelled in two tones, the copper companion solid.",
                 binary2, {"big_style": "bevel", "tone": "accent", "r1": 204, "o1": [-34, 34], "r2": 92,
                           "o2": [124, -124], "pinch": 0.22, "gap": 12}),
    "binary-c": ("Binary C: contour", "The big star drawn as routing contours, the copper companion solid.",
                 binary2, {"big_style": "contour", "r1": 208, "o1": [-30, 30], "r2": 92, "o2": [124, -124],
                           "pinch": 0.22, "gap": 0, "extra": {"scales": [1, 0.64, 0.3], "stroke": 20}}),
    "binary-d": ("Binary D: apart", "The companion set apart instead of overlapping: a quieter pair.",
                 binary2, {"big_style": "solid", "r1": 186, "o1": [-40, 40], "r2": 70, "o2": [150, -150],
                           "pinch": 0.22, "gap": 0, "hole": 20}),
    "binary-via": ("Binary via", "Binary A with the offset via hole: the original Twinkle's idea, refined.",
                   binary2, {"big_style": "solid", "r1": 204, "o1": [-34, 34], "r2": 92, "o2": [124, -124],
                             "pinch": 0.22, "gap": 12, "hole": 24, "hole_offset": 34}),
    # Contour
    "contour-a": ("Contour A: three lines", "Three routed contours around a solid core.",
                  single2, {"style": "contour", "radius": 228, "pinch": 0.22,
                            "extra": {"scales": [1, 0.66, 0.34], "stroke": 20}, "hole": 0}),
    "contour-b": ("Contour B: star core", "Two contours around a small solid copper twinkle.",
                  single2, {"style": "contour", "radius": 228, "pinch": 0.22,
                            "extra": {"scales": [1, 0.62], "stroke": 24, "core_star": True}}),
    "contour-c": ("Contour C: four lines", "Four thinner contours, alternating navy and copper.",
                  single2, {"style": "contour", "radius": 230, "pinch": 0.22,
                            "extra": {"scales": [1, 0.75, 0.5, 0.25], "stroke": 14}}),
    # Twinkle
    "twinkle-a": ("Twinkle A: pure", "The original curved star, nothing added. Shown for comparison.",
                  single2, {"style": "solid", "radius": 228, "pinch": 0.21, "hole": 0}),
    "twinkle-b": ("Twinkle B: bevelled", "The original star bevelled in two tones, lit from one side.",
                  single2, {"style": "bevel", "radius": 228, "pinch": 0.21, "tone": "accent", "hole": 0}),
    "twinkle-c": ("Twinkle C: bevel, one colour", "The bevel in a second navy (gold and copper on dark).",
                  single2, {"style": "bevel", "radius": 228, "pinch": 0.21, "tone": "ink", "hole": 0}),
    # Pads
    "pads-a": ("Pads A: copper pads", "The star left between four plated pads, as you liked it.",
               pads2, {"half": 128, "pad_r": 118, "ring_gap": 12, "drill": 40, "core": 16}),
    "pads-b": ("Pads B: bevelled star", "Between the pads, the star bevelled in two tones.",
               pads2, {"half": 128, "pad_r": 118, "ring_gap": 12, "drill": 40, "bevel": True,
                       "fill_tone": "accent"}),
    "pads-c": ("Pads C: one colour", "Pads and star in one colour: strong for silkscreen and engraving.",
               pads2, {"half": 128, "pad_r": 118, "ring_gap": 12, "drill": 46, "mono_pads": True, "core": 16}),
    "pads-d": ("Pads D: with a companion", "A small companion star cut into the main one, a nod to Binary.",
               pads2, {"half": 128, "pad_r": 118, "ring_gap": 12, "drill": 40,
                       "companion": [0, 0, 30]}),
    "pads-e": ("Pads E: twinkle between pads", "The full twinkle between four plated pads, cut apart by a gap.",
               pads_twinkle, {"half": 158, "pad_r": 76, "drill": 28, "radius": 232, "pinch": 0.2, "gap": 12,
                              "hole": 0}),
    "pads-f": ("Pads F: bevelled, between pads", "Pads E with the star bevelled in two tones.",
               pads_twinkle, {"half": 158, "pad_r": 76, "drill": 28, "radius": 232, "pinch": 0.2, "gap": 12,
                              "bevel": "accent"}),
    "pads-g": ("Pads G: one colour", "Pads E in one colour, for silkscreen and engraving.",
               pads_twinkle, {"half": 158, "pad_r": 76, "drill": 28, "radius": 232, "pinch": 0.2, "gap": 12,
                              "mono_pads": True, "hole": 18}),
    # Faceted
    "faceted-a": ("Faceted A: halves", "The faceted twinkle: alternate quarters in copper.",
                  faceted_twinkle, {"radius": 228, "pinch": 50, "shade": 1, "hole": 0}),
}
for _k, (_t, _s, _d, _p) in SHORTLIST.items():
    CONCEPTS[_k] = {"title": _t, "story": _s, "draw": _d, "params": _p, "accent": "copper"}


def colours(scheme: str, accent: str) -> dict:
    if scheme == "light":
        return {"fg": PALETTE["night"], "accent": PALETTE[accent] if accent != "star" else PALETTE["copper"],
                "accent2": PALETTE["teal"], "bg": PALETTE["paper"], "line": PALETTE["ink"]}
    if scheme == "dark":
        return {"fg": PALETTE["star"], "accent": PALETTE[accent] if accent != "star" else PALETTE["star"],
                "accent2": PALETTE["teal"], "bg": PALETTE["night"], "line": PALETTE["mist"]}
    return {"fg": "currentColor", "accent": "currentColor", "accent2": "currentColor", "bg": "#fff",
            "line": "currentColor"}


def svg(body: str, w: int = 512, h: int = 512, view: str = "0 0 512 512", title: str = "Kokeb Labs") -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="{view}" role="img" '
            f'aria-label="{title}"><title>{title}</title>{body}</svg>\n')


def mark(concept: dict, scheme: str, scale: float = 1.0, dx: float = 0, dy: float = 0) -> str:
    col = colours(scheme, concept["accent"])
    if scheme == "light" and concept["draw"] is constellation:
        col["fg"], col["accent"] = PALETTE["night"], PALETTE["star"]
    inner = concept["draw"](concept["params"], col)
    return f'<g transform="translate({f(dx)} {f(dy)}) scale({f(scale)})">{inner}</g>'


def write_concept(key: str, concept: dict, png: bool) -> None:
    d = OUT / key
    d.mkdir(parents=True, exist_ok=True)
    (d / "mark.svg").write_text(svg(mark(concept, "light")))
    (d / "mark-dark.svg").write_text(svg(mark(concept, "dark")))
    (d / "mark-mono.svg").write_text(svg(mark(concept, "mono")))
    # Avatar: GitHub shows a circle; keep the mark within 72% of the width.
    bg = f'<rect width="512" height="512" fill="{PALETTE["night"]}"/>'
    (d / "avatar.svg").write_text(svg(bg + mark(concept, "dark", 0.72, 256 * 0.28, 256 * 0.28)))
    # Favicon source: a rounded tile so the mark survives tab bars in both themes.
    tile = f'<rect width="512" height="512" rx="112" fill="{PALETTE["night"]}"/>'
    small = dict(concept, params=concept["small"]) if "small" in concept else concept
    (d / "favicon.svg").write_text(svg(tile + mark(small, "dark", 0.82, 256 * 0.18, 256 * 0.18)))
    (d / "mark-small.svg").write_text(svg(mark(small, "light")))
    # Social preview, 1280 x 640.
    social = (f'<rect width="1280" height="640" fill="{PALETTE["night"]}"/>'
              f'{mark(concept, "dark", 0.82, 150, 110)}'
              f'<text x="620" y="300" font-family="{WORDMARK_FONT}" font-size="104" font-weight="700" '
              f'fill="{PALETTE["paper"]}" letter-spacing="2">Kokeb Labs</text>'
              f'<text x="624" y="372" font-family="{WORDMARK_FONT}" font-size="38" fill="{PALETTE["mist"]}">'
              f'Open drivers and a portable core</text>'
              f'<text x="624" y="420" font-family="{WORDMARK_FONT}" font-size="38" fill="{PALETTE["mist"]}">'
              f'for real hardware</text>')
    (d / "social.svg").write_text(svg(social, 1280, 640, "0 0 1280 640"))
    if not png:
        return
    jobs = [("avatar.svg", "avatar-500.png", 500, 500), ("favicon.svg", "favicon-16.png", 16, 16),
            ("favicon.svg", "favicon-32.png", 32, 32), ("favicon.svg", "favicon-64.png", 64, 64),
            ("social.svg", "social.png", 1280, 640), ("mark.svg", "mark-1024.png", 1024, 1024),
            ("mark-dark.svg", "mark-dark-1024.png", 1024, 1024)]
    for src, dst, w, h in jobs:
        subprocess.run(["rsvg-convert", "-w", str(w), "-h", str(h), "-o", str(d / dst), str(d / src)], check=True)


def index(keys: list[str], name: str = "index.html", heading: str = "Kokeb Labs logo concepts") -> None:
    cards = []
    for k in keys:
        c = CONCEPTS[k]
        cards.append(f"""
<section class="card">
  <h2>{c["title"]}</h2><p>{c["story"]}</p>
  <div class="row">
    <div class="tile light"><img src="{k}/mark.svg" alt="{c["title"]} on light"></div>
    <div class="tile dark"><img src="{k}/mark-dark.svg" alt="{c["title"]} on dark"></div>
    <div class="tile avatar"><img src="{k}/avatar.svg" alt="{c["title"]} avatar"></div>
    <div class="tile sizes">
      <img src="{k}/favicon.svg" width="64" height="64" alt=""><img src="{k}/favicon.svg" width="32" height="32" alt="">
      <img src="{k}/favicon.svg" width="16" height="16" alt="">
      <span class="mono"><img src="{k}/mark-mono.svg" width="40" height="40" alt=""></span>
    </div>
  </div>
  <div class="lockup"><img src="{k}/mark.svg" alt=""><span>Kokeb Labs</span></div>
  <img class="social" src="{k}/social.svg" alt="{c["title"]} social preview">
  <code>python3 brand/generate.py --only {k}</code>
</section>""")
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Kokeb Labs Logos</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
<style>
:root{{--bg:{PALETTE["paper"]};--fg:{PALETTE["night"]};--card:#fff;--line:#e6e1d6;--mut:#5d6675}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#0a111d;--fg:#eef1f5;--card:#121c2c;--line:#22324a;--mut:#9aa6b8}}}}
:root[data-theme="dark"]{{--bg:#0a111d;--fg:#eef1f5;--card:#121c2c;--line:#22324a;--mut:#9aa6b8}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}}
main{{max-width:1100px;margin:0 auto;padding:28px 16px 60px}} h1{{font-family:'Space Grotesk',sans-serif;margin:0 0 4px}}
.sub{{color:var(--mut);margin:0 0 20px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;margin:16px 0}}
.card h2{{margin:0;font-family:'Space Grotesk',sans-serif}} .card p{{margin:4px 0 12px;color:var(--mut)}}
.row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}}
.tile{{border-radius:10px;aspect-ratio:1;display:flex;align-items:center;justify-content:center;padding:12px}}
.tile img{{width:100%;height:100%}} .light{{background:{PALETTE["paper"]};border:1px solid #e6e1d6}}
.dark{{background:{PALETTE["night"]}}} .avatar img{{border-radius:50%}}
.sizes{{gap:12px;background:{PALETTE["paper"]};border:1px solid #e6e1d6;flex-wrap:wrap}} .sizes img{{width:auto;height:auto}}
.mono{{color:{PALETTE["ink"]}}}
.lockup{{display:flex;align-items:center;gap:14px;margin:14px 0;padding:14px;border-radius:10px;
background:{PALETTE["paper"]};color:{PALETTE["night"]}}}
.lockup img{{width:64px;height:64px}} .lockup span{{font:700 40px 'Space Grotesk',sans-serif;letter-spacing:.5px}}
.social{{width:100%;border-radius:10px;display:block;margin:8px 0}} code{{font-size:12px;color:var(--mut)}}
</style></head><body><main>
<h1>{heading}</h1>
<p class="sub">Every mark is drawn by <code>brand/generate.py</code> from a few numbers, so any option can be
regenerated, tuned or exported exactly. Each card shows the mark on light and dark, as the organization avatar
(GitHub crops it to a circle), at favicon sizes and in one colour, as a wordmark lockup and as a repository social
preview.</p>
{''.join(cards)}
</main></body></html>
"""
    (OUT / name).write_text(html)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", action="append", choices=sorted(CONCEPTS), default=[])
    args = ap.parse_args()
    keys = args.only or list(CONCEPTS)
    png = shutil.which("rsvg-convert") is not None
    for k in keys:
        write_concept(k, CONCEPTS[k], png)
    first = list(TWINKLE_FAMILY) + ["trace-twinkle", "signal-twinkle", "phase-twinkle", "routed-star", "split-star", "split-star-8",
             "phase-trace", "wave-star-8", "wave-star"]
    order = first + [k for k in CONCEPTS if k not in first]
    index(order if not args.only else keys)
    if not args.only:
        index(list(SHORTLIST), "shortlist.html", "Kokeb Labs logo shortlist")
    print(f"wrote {len(keys)} concept(s) to {OUT}" + ("" if png else " (SVG only: rsvg-convert not found)"))


if __name__ == "__main__":
    main()
