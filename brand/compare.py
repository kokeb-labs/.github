#!/usr/bin/env python3
"""Put chosen concepts through the same real-use tests on one self-contained page.

  python3 brand/compare.py final-a final-b final-c -o finalists.html

Tests: light, dark, the GitHub avatar circle, white silkscreen on a green board, one colour, 16-32 px, a browser
tab, the organization header and the wordmark. Run generate.py first.
"""
from __future__ import annotations

import argparse
import base64
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("generate", HERE / "generate.py")
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
P = g.PALETTE


def uri(svg_text: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg_text.encode()).decode()


def card(key: str) -> str:
    c = g.CONCEPTS[key]
    small = dict(c, params=c["small"]) if "small" in c else c
    mk = lambda conc, scheme, s=1, dx=0, dy=0: g.mark(conc, scheme, s, dx, dy)  # noqa: E731
    light, dark = uri(g.svg(mk(c, "light"))), uri(g.svg(mk(c, "dark")))
    small_light = uri(g.svg(mk(small, "light")))
    av = uri(g.svg(f'<rect width="512" height="512" fill="{P["night"]}"/>' + mk(c, "dark", 0.72, 71.7, 71.7)))
    fav = uri(g.svg(f'<rect width="512" height="512" rx="112" fill="{P["night"]}"/>' + mk(small, "dark", 0.82, 46, 46)))
    silk = mk(c, "mono").replace("currentColor", "#F2F2EA").replace('"#fff"', '"#1F5E3A"')
    pcb = uri(g.svg('<rect width="512" height="512" fill="#1F5E3A"/>' + silk))
    stamp = uri(g.svg(mk(c, "mono").replace("currentColor", P["night"]).replace('"#fff"', f'"{P["paper"]}"')))
    return f'''<section class="card"><h2>{c["title"]}</h2><p>{c["story"]}</p>
<div class="tests">
<figure><div class="t light"><img src="{light}" alt=""></div><figcaption>Light</figcaption></figure>
<figure><div class="t dark"><img src="{dark}" alt=""></div><figcaption>Dark</figcaption></figure>
<figure><div class="t"><img class="circle" src="{av}" alt=""></div><figcaption>GitHub avatar</figcaption></figure>
<figure><div class="t pcb"><img src="{pcb}" alt=""></div><figcaption>Silkscreen on a board</figcaption></figure>
<figure><div class="t light"><img src="{stamp}" alt=""></div><figcaption>One colour</figcaption></figure>
<figure><div class="t light"><img src="{small_light}" alt=""></div><figcaption>Small-size version</figcaption></figure>
<figure><div class="t small"><img src="{fav}" width="16" height="16" alt=""><img src="{fav}" width="24" height="24" alt="">
<img src="{fav}" width="32" height="32" alt=""><img src="{small_light}" width="20" height="20" alt=""></div>
<figcaption>16, 24, 32 px and inline</figcaption></figure>
</div>
<div class="tab"><img src="{fav}" width="16" height="16" alt=""><span>kokeb-labs/driver-pcal95555</span></div>
<div class="hdr"><img class="circle" src="{av}" width="72" height="72" alt=""><div><b>Kokeb Labs</b>
<span>Open drivers and a portable core for real hardware</span></div></div>
<div class="lock"><img src="{light}" width="64" height="64" alt=""><span>Kokeb Labs</span></div>
</section>'''


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("keys", nargs="+", choices=sorted(g.CONCEPTS))
    ap.add_argument("-o", "--out", default=str(g.OUT / "compare.html"))
    ap.add_argument("--title", default="Logo finalists")
    args = ap.parse_args()
    css = f''':root{{--bg:{P["paper"]};--fg:{P["night"]};--card:#fff;--line:#e6e1d6;--mut:#5d6675}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#0a111d;--fg:#eef1f5;--card:#121c2c;--line:#22324a;--mut:#9aa6b8}}}}
:root[data-theme="dark"]{{--bg:#0a111d;--fg:#eef1f5;--card:#121c2c;--line:#22324a;--mut:#9aa6b8}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}}
main{{max-width:1100px;margin:0 auto;padding:28px 16px 60px}}h1,h2{{font-family:'Space Grotesk',sans-serif}}h1{{margin:0 0 6px}}
.sub{{color:var(--mut)}}.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;margin:18px 0}}
.card h2{{margin:0}}.card>p{{margin:4px 0 12px;color:var(--mut)}}
.tests{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px}}figure{{margin:0}}
figcaption{{font-size:12px;color:var(--mut);margin-top:4px;text-align:center}}
.t{{aspect-ratio:1;border-radius:10px;display:flex;align-items:center;justify-content:center;padding:10px;gap:8px;flex-wrap:wrap}}
.t img{{width:100%;height:100%}}.light{{background:{P["paper"]};border:1px solid #e6e1d6}}.dark{{background:{P["night"]}}}
.pcb{{background:#1F5E3A}}.small{{background:#fff;border:1px solid #e6e1d6}}.small img{{width:auto;height:auto}}.circle{{border-radius:50%}}
.tab{{display:inline-flex;align-items:center;gap:8px;margin:12px 8px 0 0;padding:7px 14px;border-radius:9px 9px 0 0;background:#dee1e6;color:#1f1f1f;font-size:13px}}
.hdr{{display:flex;align-items:center;gap:14px;margin-top:12px;padding:14px;border:1px solid var(--line);border-radius:10px}}
.hdr b{{display:block;font-size:22px}}.hdr span{{color:var(--mut);font-size:14px}}
.lock{{display:flex;align-items:center;gap:12px;margin-top:12px;padding:12px;border-radius:10px;background:{P["paper"]};color:{P["night"]}}}
.lock span{{font:700 34px 'Space Grotesk',sans-serif}}'''
    html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Kokeb Labs Logo Finalists</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
<style>{css}</style></head><body><main><h1>{args.title}</h1>
<p class="sub">Each candidate through the same tests. Marks with fine lines switch to a small-size version (solid star,
same vias and companion) at favicon sizes, the way large brands keep detail where there's room and drop it where
there isn't.</p>
{"".join(card(k) for k in args.keys)}</main></body></html>'''
    Path(args.out).write_text(html)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
