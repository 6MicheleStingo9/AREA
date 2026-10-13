"""
The Kindynos logo files, drawn from the Fraunces outlines (see README.md in this folder).

The wordmark is "kindÿnos": the y transliterates the Greek upsilon of κίνδυνος, and ϋ is the upsilon
with a diaeresis. Its two dots carry the two main values of the causal "entity" axis, AI and human,
in the colours of the owl mascot. The text is shaped with HarfBuzz (kerning) and written as paths,
so the SVGs need no font to render.

Writes, next to this script unless an output folder is given:
- kindynos-mark.svg: the square mark (ÿ on a navy tile);
- kindynos-wordmark-light.svg and kindynos-wordmark-dark.svg: the wordmark for light and dark
  backgrounds;
- kindynos-tagline-dark.svg: the tagline for social.html, which composes the social preview.

Usage (pip install fonttools uharfbuzz; the variable Fraunces font from github.com/google/fonts,
ofl/fraunces, saved as Fraunces.ttf; see README.md):
    python make_brand.py Fraunces.ttf [output folder]
"""

import sys
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

WORD = "kindÿnos"
TAGLINE = ("AI risk assessment with the taxonomies", "of the MIT AI Risk Repository")
WORD_AXES = {"wght": 600, "opsz": 72, "SOFT": 50, "WONK": 0}
TAGLINE_AXES = {"wght": 400, "opsz": 24, "SOFT": 50, "WONK": 0}
# The owl's navy, gold and cream; the AI dot is a lighter tint of the navy
NAVY, GOLD, CREAM = "#132747", "#EDAA26", "#FAE5B9"
THEMES = {
    "light": {"ink": NAVY, "ai": "#4B70B8", "human": GOLD},
    "dark": {"ink": CREAM, "ai": "#8EAEE3", "human": GOLD},
}
MARK = {"tile": NAVY, "ink": CREAM, "ai": "#8EAEE3", "human": GOLD}


def num(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


class Face:
    """One instance of the variable font: HarfBuzz for the layout, fontTools for the outlines."""

    def __init__(self, path: str, axes: dict):
        self.hb = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
        self.hb.set_variations(axes)
        font = instantiateVariableFont(TTFont(path), axes)
        self.gs, self.cmap, self.order = font.getGlyphSet(), font.getBestCmap(), font.getGlyphOrder()

    def shape(self, text: str):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"kern": True, "liga": False})
        return [(self.order[i.codepoint], p.x_advance, p.x_offset, p.y_offset) for i, p in zip(buf.glyph_infos, buf.glyph_positions)]

    def contours(self, name: str):
        pen = DecomposingRecordingPen(self.gs)
        self.gs[name].draw(pen)
        out, cur = [], []
        for op, args in pen.value:
            cur.append((op, args))
            if op in ("closePath", "endPath"):
                out.append(cur)
                cur = []
        return out

    def dots(self, scale: float = 1.0, gap: float = 0.8):
        """(cx, cy, r) of the two dots of ÿ: centred where the font puts its diaeresis, sized and raised
        like the dot of the i, and `gap` radii apart so they stay two dots at small sizes."""
        y_top = max(_bounds(c)[3] for c in self.contours(self.cmap[ord("y")]))
        native = [b for b in map(_bounds, self.contours(self.cmap[0xFF])) if b[1] > y_top]
        assert len(native) == 2, native
        mid = sum((b[0] + b[2]) / 2 for b in native) / 2
        x0, y0, x1, y1 = max(map(_bounds, self.contours(self.cmap[ord("i")])), key=lambda b: b[1])
        r, cy = scale * max(x1 - x0, y1 - y0) / 2, (y0 + y1) / 2
        d = (2 + gap) * r
        return [(mid - d / 2, cy, r), (mid + d / 2, cy, r)]

    def line(self, text: str, y: float = 0.0, dot_scale: float = 1.0):
        """The text as ("glyph", name, x, y) and ("dot", role, cx, cy, r), in font units."""
        parts, x = [], 0
        for name, adv, xo, yo in self.shape(text):
            if name == self.cmap[0xFF]:
                parts.append(("glyph", self.cmap[ord("y")], x + xo, y + yo))
                for (cx, cy, r), role in zip(self.dots(dot_scale), ("ai", "human")):
                    parts.append(("dot", role, x + xo + cx, y + yo + cy, r))
            else:
                parts.append(("glyph", name, x + xo, y + yo))
            x += adv
        return parts

    def bbox(self, parts):
        boxes = []
        for p in parts:
            if p[0] == "glyph":
                pen = BoundsPen(self.gs)
                self.gs[p[1]].draw(pen)
                if pen.bounds:
                    x0, y0, x1, y1 = pen.bounds
                    boxes.append((x0 + p[2], y0 + p[3], x1 + p[2], y1 + p[3]))
            else:
                _, _, cx, cy, r = p
                boxes.append((cx - r, cy - r, cx + r, cy + r))
        return min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)

    def svg_elements(self, parts, colors, s, tx, ty):
        """Paths and circles, font units scaled by s and moved to (tx, ty), y pointing down."""
        d = []
        for p in parts:
            if p[0] == "glyph":
                pen = SVGPathPen(self.gs, ntos=num)
                self.gs[p[1]].draw(TransformPen(pen, (s, 0, 0, -s, tx + s * p[2], ty - s * p[3])))
                d.append(pen.getCommands())
        out = [f'<path fill="{colors["ink"]}" d="{" ".join(d)}"/>']
        for p in parts:
            if p[0] == "dot":
                _, role, cx, cy, r = p
                out.append(f'<circle fill="{colors[role]}" cx="{num(tx + s * cx)}" cy="{num(ty - s * cy)}" r="{num(s * r)}"/>')
        return out


def _bounds(ops):
    pen = BoundsPen(None)
    for op, args in ops:
        getattr(pen, op)(*args)
    return pen.bounds


def _svg(w: float, h: float, label: str, body) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {num(w)} {num(h)}" width="{num(w)}" height="{num(h)}" '
            f'role="img" aria-label="{label}">' + "".join(body) + "</svg>\n")


def text_svg(face: Face, parts, colors, label: str, height: float, pad: float) -> str:
    """The parts fitted to `height` (from the lowest to the highest point), with `pad` around."""
    x0, y0, x1, y1 = face.bbox(parts)
    s = height / (y1 - y0)
    w, h = s * (x1 - x0) + 2 * pad, height + 2 * pad
    return _svg(w, h, label, face.svg_elements(parts, colors, s, pad - s * x0, pad + s * y1))


def mark_svg(face: Face, size: int = 512) -> str:
    parts = [("glyph", face.cmap[ord("y")], 0, 0)] + [
        ("dot", role, cx, cy, r) for (cx, cy, r), role in zip(face.dots(scale=1.2), ("ai", "human"))
    ]
    x0, y0, x1, y1 = face.bbox(parts)
    s = 0.62 * size / (y1 - y0)
    tx, ty = size / 2 - s * (x0 + x1) / 2, size / 2 + s * (y0 + y1) / 2
    tile = f'<rect width="{size}" height="{size}" rx="{num(0.22 * size)}" fill="{MARK["tile"]}"/>'
    return _svg(size, size, "Kindynos", [tile] + face.svg_elements(parts, MARK, s, tx, ty))


def main() -> None:
    font_path = sys.argv[1]
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent
    out.mkdir(parents=True, exist_ok=True)
    word = Face(font_path, WORD_AXES)
    word_parts = word.line(WORD)
    for theme, colors in THEMES.items():
        (out / f"kindynos-wordmark-{theme}.svg").write_text(text_svg(word, word_parts, colors, "kindÿnos", 120, 14), encoding="utf-8")
    (out / "kindynos-mark.svg").write_text(mark_svg(word), encoding="utf-8")
    tag = Face(font_path, TAGLINE_AXES)
    leading = 1.35 * tag.hb.face.upem
    tag_parts = [p for i, text in enumerate(TAGLINE) for p in tag.line(text, y=-i * leading)]
    tagline = text_svg(tag, tag_parts, {"ink": CREAM}, " ".join(TAGLINE), 70, 0)
    (out / "kindynos-tagline-dark.svg").write_text(tagline, encoding="utf-8")
    print("written to", out)


if __name__ == "__main__":
    main()
