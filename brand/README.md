# Brand

The Kokeb Labs mark is **K1**: a four-point star drawn as three nested stars (navy line, copper line, solid core),
with a small copper companion star. The layers stand for the stack: driver, core, board. The finished files are in
[`mark/`](mark); use those, not anything in `out/`.

![Kokeb Labs mark](mark/mark-1024.png)

The mark is generated, not drawn by hand. [`generate.py`](generate.py) draws it from a few numbers (the `k1-arcs`
entry in `K_FINAL`) and writes every asset GitHub and the docs need, so a change of size, weight or colour is a
parameter edit and a re-run.

```bash
python3 brand/generate.py --only k1-arcs   # -> brand/out/k1-arcs/
cp brand/out/k1-arcs/* brand/mark/         # after checking the result
python3 brand/generate.py                  # every concept ever tried -> brand/out/, with out/index.html to compare
```

PNGs need `rsvg-convert` (librsvg: `brew install librsvg`, `apt install librsvg2-bin`).

## Using the mark

- Below 64 px (favicons, avatars, the docs header) use the small version, `mark-small.svg`: the solid star and its
  companion, without the inner lines, which blur at that size.
- On dark backgrounds use `mark-dark.svg` (gold, copper, gold). For one colour, `mark-mono.svg` takes `currentColor`.
- Keep clear space of at least the companion star's width on every side. Don't recolour, stretch, rotate or outline
  it, and don't add effects.
- `wordmark.svg` is the mark with "Kokeb Labs" beside it, as used in the docs theme.

## Concepts tried

| Key | Idea |
| --- | --- |
| `twinkle` | A four-point star with a pin-1 hole, as printed on a chip package, and a small companion star |
| `die-star` | A chip die whose package pads grow into a starburst |
| `trace-star` | Eight copper traces leave a centre pad, jog 45 degrees and end in vias |
| `phase-star` | Three sine-edged stars 120 degrees apart: the three phases that drive a motor |
| `constellation-k` | The K of Kokeb as a constellation, its brightest star where the arms meet |
| `eight-point` | A filled eight-point star with a ring at its centre, after the eight-pointed stars of Ethiopian textiles |

Later rounds (Twinkle variants, binary, contour, via and pad stars, the finalists) are in `TWINKLE_FAMILY`,
`SHORTLIST`, `FINAL` and `K_FINAL` in `generate.py`. K1 combined the contour layers with the binary star's calm
shape, without vias.

## Files

| File | Use |
| --- | --- |
| `mark.svg`, `mark-1024.png` | On light backgrounds |
| `mark-dark.svg`, `mark-dark-1024.png` | On dark backgrounds |
| `mark-mono.svg` | One colour (`currentColor`): engraving, silkscreen, single-colour print |
| `mark-small.svg` | Below 64 px |
| `avatar.svg`, `avatar-500.png` | Organization avatar; the mark stays inside GitHub's circle crop |
| `favicon.svg`, `favicon-16/32/64.png` | Browser tabs and docs sites |
| `social.svg`, `social.png` | Repository social preview, 1280 x 640 |
| `wordmark.svg` | Mark and name, for headers |

## Colour tokens

| Token | Hex | Use |
| --- | --- | --- |
| `night` | `#0E1726` | Dark backgrounds, text on light |
| `ink` | `#1B2A41` | Secondary dark |
| `star` | `#F4B942` | The star; the mark on dark |
| `copper` | `#D9773B` | Accent: copper, traces |
| `teal` | `#2BB3A3` | Signal accent |
| `paper` | `#FAF7F0` | Light backgrounds |
| `mist` | `#C9D3E0` | Light lines and secondary text on dark |

`wordmark.svg` uses the reader's system sans-serif (Inter where installed), with "Labs" in `#9A4A17` on light and
`star` on dark. For print or the store, set it in Space Grotesk (SIL Open Font License) and convert the text to
outlines so the file doesn't depend on an installed font.

## Before the mark goes on products

Run a trademark search for the name and a similar-mark check for the mark in the countries you sell in.
