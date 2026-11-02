#!/usr/bin/env python3
"""
Wortuhr-Glasscheibe "HSRW" (Hochschule Rhein-Waal) – 300 x 300 mm, UV-Direktdruck.

Erzeugt aus einem Parametersatz:
  out/hsrw_wortuhr_master.svg        Master mit 3 Ebenen (Ansicht von VORNE)
  out/layer_1_farbe.svg              Ebene Farbe
  out/layer_2_weiss_schwarz.svg      Maske für Weiß- UND Blocker-Ebene (identisch)
  out/preview_aus.svg / _an.svg / _alle.svg   Simulationen (Uhr aus / an / alle Buchstaben)

Alle Schrift ist in Pfade umgewandelt (Inter SemiBold, SIL OFL) – keine Schriftdateien nötig.
Aufruf:  python3 generate.py
"""
import math
import pathlib

import numpy as np
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from scipy.ndimage import distance_transform_edt, gaussian_filter
from shapely.geometry import LineString, box
from skimage import measure

OUT = pathlib.Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)

# ----------------------------------------------------------------------------
# PARAMETER  (alles in mm, Ursprung links oben, Ansicht von vorne)
# ----------------------------------------------------------------------------
SIZE = 300.0

# Buchstabenraster – HIER an die eigene Uhr anpassen (Mittelpunkte der Buchstaben)
COLS, ROWS = 11, 10
PITCH_X, PITCH_Y = 22.0, 22.0          # Abstand Buchstabe zu Buchstabe
GRID_CX, GRID_CY = 150.0, 150.0        # Mitte des Rasters auf der Scheibe
CAP_H = 12.0                           # Höhe der Großbuchstaben
FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
FONT_MEDIUM = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"

# Minuten-Punkte (Fenster in den Ecken)
DOT_R = 1.7                            # Radius des Lichtfensters
DOT_INSET = 24.0                       # Abstand der Punktmitte vom Scheibenrand

# Kartenrahmen: nichts Wichtiges außerhalb, falls der Rahmen der Uhr die Kante überdeckt
FRAME_INSET = 12.0

# Farben (so wie sie von vorne aussehen sollen)
BASE = "#08151d"       # sehr dunkles Petrol – bewusst fast schwarz
LINE_MINOR = "#143f4a"
LINE_MAJOR = "#1f6573"
RIVER = "#2f8e9d"
TEXT = "#2c7381"
LED = "#fff1d6"        # LED-Lichtfarbe nur für die Vorschau
INTERIOR = "#03080b"   # dunkle Rückseite der Uhr (Vorschau)

# Tarnung: feine Tönung (Rasterfläche in der Hintergrundfarbe) in den Buchstaben-Fenstern.
# 0 = Fenster komplett klar (max. Helligkeit, Buchstaben im Ruhezustand sichtbarer)
# 0.35 = Buchstaben fast unsichtbar, kostet ca. 1/3 der Helligkeit
WINDOW_TINT = 0.35

# Reihe 4 enthält 4 Füllbuchstaben (sonst "FUNK") -> hier steckt das Kürzel der Hochschule
ROWS_TEXT = [
    "ESKISTAFÜNF",
    "ZEHNZWANZIG",
    "DREIVIERTEL",
    "VORHSRWNACH",
    "HALBAELFÜNF",
    "EINSXAMZWEI",
    "DREIPMJVIER",
    "SECHSNLACHT",
    "SIEBENZWÖLF",
    "ZEHNEUNKUHR",
]

# (Reihe, Startspalte, Länge) – für die Vorschau "Uhr an"
WORDS = {
    "ES": (0, 0, 2), "IST": (0, 3, 3), "FÜNF_M": (0, 7, 4), "ZEHN_M": (1, 0, 4),
    "ZWANZIG": (1, 4, 7), "DREIVIERTEL": (2, 0, 11), "VIERTEL": (2, 4, 7),
    "VOR": (3, 0, 3), "NACH": (3, 8, 3), "HALB": (4, 0, 4), "ELF": (4, 5, 3),
    "FÜNF_H": (4, 7, 4), "EINS": (5, 0, 4), "ZWEI": (5, 7, 4), "DREI": (6, 0, 4),
    "VIER": (6, 7, 4), "SECHS": (7, 0, 5), "ACHT": (7, 7, 4), "SIEBEN": (8, 0, 6),
    "ZWÖLF": (8, 6, 5), "ZEHN_H": (9, 0, 4), "NEUN": (9, 3, 4), "UHR": (9, 8, 3),
}
WORDS["NACH"] = (3, 7, 4)
# 09:25 Uhr  ->  "ES IST FÜNF VOR HALB ZEHN"
DEMO_WORDS = ["ES", "IST", "FÜNF_M", "VOR", "HALB", "ZEHN_H"]
DEMO_DOTS = 0

# Höhenlinien / Rhein
SEED = 11
GRID_N = 1000                          # Auflösung des Geländemodells
LEVEL_STEP = 0.21
MAJOR_EVERY = 5
RIVER_PTS = [  # SO -> NW, wie der echte Rhein bei Kleve / Kamp-Lintfort
    (310, 235), (258, 226), (214, 196), (194, 150), (164, 116),
    (112, 100), (72, 116), (44, 86), (12, 58), (-10, 52),
]


def f2(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


# ----------------------------------------------------------------------------
# Schrift -> Pfade
# ----------------------------------------------------------------------------
class Face:
    def __init__(self, path):
        self.font = TTFont(path)
        self.gs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upm = self.font["head"].unitsPerEm
        self.cap = self.font["OS/2"].sCapHeight
        self.fmt = lambda v: f"{v:.3f}".rstrip("0").rstrip(".")

    def name(self, ch):
        return self.cmap[ord(ch)]

    def adv(self, ch):
        return self.font["hmtx"][self.name(ch)][0]

    def bbox(self, ch):
        bp = BoundsPen(self.gs)
        self.gs[self.name(ch)].draw(bp)
        return bp.bounds

    def path(self, ch, ox, oy, size):
        s = size / self.upm
        pen = SVGPathPen(self.gs, ntos=self.fmt)
        self.gs[self.name(ch)].draw(TransformPen(pen, (s, 0, 0, -s, ox, oy)))
        return pen.getCommands()

    def size_for_cap(self, cap_mm):
        return cap_mm * self.upm / self.cap


def letter_path(face, ch, cx, cy, cap_h):
    """Buchstabe optisch mittig auf (cx, cy) – horizontal nach Glyphen-BBox, vertikal nach Versalhöhe."""
    size = face.size_for_cap(cap_h)
    s = size / face.upm
    xmin, _, xmax, _ = face.bbox(ch)
    ox = cx - (xmin + xmax) / 2 * s
    oy = cy + cap_h / 2
    return face.path(ch, ox, oy, size)


def text_path(face, txt, x, y, cap_mm, tracking=0.3, anchor="start"):
    """Text als Pfad. tracking in em. y = Grundlinie."""
    size = face.size_for_cap(cap_mm)
    s = size / face.upm
    adv = [face.adv(c) * s + tracking * size for c in txt]
    total = sum(adv) - tracking * size
    ox = x - (total / 2 if anchor == "middle" else total if anchor == "end" else 0)
    d = []
    for c, a in zip(txt, adv):
        if c != " ":
            d.append(face.path(c, ox, y, size))
        ox += a
    return " ".join(d), total


# ----------------------------------------------------------------------------
# Raster, Buchstaben, Punkte
# ----------------------------------------------------------------------------
def cell_center(r, c):
    x = GRID_CX + (c - (COLS - 1) / 2) * PITCH_X
    y = GRID_CY + (r - (ROWS - 1) / 2) * PITCH_Y
    return x, y


def dot_centers():
    a, b = DOT_INSET, SIZE - DOT_INSET
    return [(a, a), (b, a), (b, b), (a, b)]


def circle_d(cx, cy, r):
    return (f"M{f2(cx - r)} {f2(cy)}a{f2(r)} {f2(r)} 0 1 0 {f2(2 * r)} 0"
            f"a{f2(r)} {f2(r)} 0 1 0 {f2(-2 * r)} 0Z")


def build_windows(face):
    """Alle Lichtfenster: Buchstaben + Minutenpunkte.  Rückgabe: Liste (Pfad, Zelle)"""
    letters = []
    for r, row in enumerate(ROWS_TEXT):
        assert len(row) == COLS, (r, row)
        for c, ch in enumerate(row):
            cx, cy = cell_center(r, c)
            letters.append((r, c, ch, letter_path(face, ch, cx, cy, CAP_H)))
    dots = [circle_d(x, y, DOT_R) for x, y in dot_centers()]
    return letters, dots


# ----------------------------------------------------------------------------
# Höhenlinien + Fluss
# ----------------------------------------------------------------------------
def catmull(points, per=40):
    p = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = (np.array(v, float) for v in p[i - 1:i + 3])
        for t in np.linspace(0, 1, per, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(np.array(points[-1], float))
    return np.array(out)


def terrain():
    rng = np.random.default_rng(SEED)
    n = GRID_N
    mm = SIZE / n
    f = np.zeros((n, n))
    for sigma, w in [(150, 1.0), (62, 0.5), (26, 0.17)]:
        z = gaussian_filter(rng.standard_normal((n, n)), sigma, mode="wrap")
        f += w * z / z.std()
    river = catmull(RIVER_PTS)
    mask = np.ones((n, n), bool)
    for (x, y) in river:
        i, j = int(round(y / mm)), int(round(x / mm))
        if 0 <= i < n and 0 <= j < n:
            mask[i, j] = False
    d = distance_transform_edt(mask) * mm            # Abstand zum Fluss in mm
    valley = 1 - np.exp(-(d / 55.0) ** 2)
    f = 0.55 * f + 3.2 * valley
    f = gaussian_filter(f, 2.0)
    return f, mm, river


def contour_paths(f, mm):
    inner = box(FRAME_INSET, FRAME_INSET, SIZE - FRAME_INSET, SIZE - FRAME_INSET)
    levels = np.arange(np.floor(f.min() / LEVEL_STEP) * LEVEL_STEP, f.max(), LEVEL_STEP)
    minor, major = [], []
    for k, lv in enumerate(levels):
        idx = int(round(lv / LEVEL_STEP))
        for c in measure.find_contours(f, lv):
            c = measure.approximate_polygon(c, 0.35)
            if len(c) < 2:
                continue
            ls = LineString([(p[1] * mm, p[0] * mm) for p in c]).intersection(inner)
            if ls.is_empty:
                continue
            geoms = getattr(ls, "geoms", [ls])
            for g in geoms:
                if g.geom_type != "LineString" or g.length < 1.0:
                    continue
                d = "M" + "L".join(f"{f2(x)} {f2(y)}" for x, y in g.coords)
                (major if idx % MAJOR_EVERY == 0 else minor).append(d)
    return minor, major, inner


def river_paths(river):
    inner = box(FRAME_INSET, FRAME_INSET, SIZE - FRAME_INSET, SIZE - FRAME_INSET)
    ls = LineString(river)
    out = []
    for off, w, col in [(0, 0.7, RIVER), (3.2, 0.28, RIVER), (-3.2, 0.28, RIVER)]:
        g = ls if off == 0 else ls.offset_curve(off)
        g = g.intersection(inner)
        for part in getattr(g, "geoms", [g]):
            if part.geom_type != "LineString" or part.length < 2:
                continue
            out.append((w, "M" + "L".join(f"{f2(x)} {f2(y)}" for x, y in part.coords)))
    return out


# ----------------------------------------------------------------------------
# Kartenrahmen + Beschriftung
# ----------------------------------------------------------------------------
def neatline():
    a, b = FRAME_INSET, SIZE - FRAME_INSET
    parts = [f'<rect x="{a}" y="{a}" width="{b - a}" height="{b - a}" fill="none" '
             f'stroke="{LINE_MAJOR}" stroke-width="0.35"/>']
    tick = []
    step = 5
    for v in range(int(a) + step, int(b), step):
        L = 2.6 if (v - a) % 25 == 0 else 1.3
        tick.append(f"M{v} {a}v{L}M{v} {b}v{-L}M{a} {v}h{L}M{b} {v}h{-L}")
    parts.append(f'<path d="{"".join(tick)}" stroke="{LINE_MAJOR}" stroke-width="0.3" fill="none"/>')
    return "\n".join(parts)


def labels(face_m):
    """(Pfad, Halo-Pfad-Stil) für alle Beschriftungen. Rückgabe: Liste von Pfadstrings."""
    ytop, ybot = DOT_INSET + 1.0, SIZE - DOT_INSET + 1.0
    x0, x1 = DOT_INSET + 12, SIZE - DOT_INSET - 12
    items = []
    d, _ = text_path(face_m, "KLEVE", x0, ytop, 1.8, 0.32, "start"); items.append(d)
    d, _ = text_path(face_m, "RHINE-WAAL UNIVERSITY OF APPLIED SCIENCES", SIZE / 2, ytop, 1.8, 0.32, "middle"); items.append(d)
    d, _ = text_path(face_m, "KAMP-LINTFORT", x1, ytop, 1.8, 0.32, "end"); items.append(d)
    d, _ = text_path(face_m, "51°47′N 6°08′E", x0, ybot, 1.8, 0.32, "start"); items.append(d)
    d, _ = text_path(face_m, "HOCHSCHULE RHEIN-WAAL", SIZE / 2, ybot, 2.5, 0.38, "middle"); items.append(d)
    d, _ = text_path(face_m, "51°30′N 6°32′E", x1, ybot, 1.8, 0.32, "end"); items.append(d)
    return items


# ----------------------------------------------------------------------------
# SVG-Bausteine
# ----------------------------------------------------------------------------
def window_cutout(letters, dots):
    """Ein Pfad: Vollfläche minus Fenster (even-odd).  Innenflächen (Punzen von A, O, Ö …) bleiben gefüllt."""
    holes = " ".join(p for *_, p in letters) + " " + " ".join(dots)
    return f"M0 0H{SIZE}V{SIZE}H0Z {holes}"


def color_layer(letters, dots, minor, major, rivers, labs):
    g = []
    g.append(f'<path d="{window_cutout(letters, dots)}" fill="{BASE}" fill-rule="evenodd"/>')
    if WINDOW_TINT > 0:
        g.append(f'<path d="{" ".join(p for *_, p in letters)}" fill="{BASE}" fill-opacity="{WINDOW_TINT}" '
                 f'id="tarnung-tint"/>')
    g.append(f'<g fill="none" stroke-linecap="round" stroke-linejoin="round">')
    g.append(f'<path d="{" ".join(minor)}" stroke="{LINE_MINOR}" stroke-width="0.24"/>')
    g.append(f'<path d="{" ".join(major)}" stroke="{LINE_MAJOR}" stroke-width="0.46"/>')
    for w, d in rivers:
        g.append(f'<path d="{d}" stroke="{RIVER}" stroke-width="{w}"/>')
    g.append("</g>")
    g.append(neatline())
    # Halos (Linien um Text/Punkte frei räumen), dann Text
    for d in labs:
        g.append(f'<path d="{d}" fill="{BASE}" stroke="{BASE}" stroke-width="1.8" stroke-linejoin="round"/>')
    for d in labs:
        g.append(f'<path d="{d}" fill="{TEXT}"/>')
    for x, y in dot_centers():
        g.append(f'<path d="{circle_d(x, y, 3.6)} {circle_d(x, y, DOT_R)}" fill="{BASE}" fill-rule="evenodd"/>')
        g.append(f'<circle cx="{x}" cy="{y}" r="2.7" fill="none" stroke="{RIVER}" stroke-width="0.28"/>')
    return "\n".join(g)


def mask_layer(letters, dots, fill):
    return f'<path d="{window_cutout(letters, dots)}" fill="{fill}" fill-rule="evenodd"/>'


def svg_doc(body, extra_defs="", bg=None, ns=True):
    bgr = f'<rect width="{SIZE}" height="{SIZE}" fill="{bg}"/>' if bg else ""
    nsd = ('xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
           'xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"') if ns else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" {nsd} width="{SIZE}mm" height="{SIZE}mm" '
            f'viewBox="0 0 {SIZE} {SIZE}">\n<defs>{extra_defs}</defs>\n{bgr}\n{body}\n</svg>\n')


def layer(id_, label, content, visible=True):
    vis = "" if visible else ' style="display:none"'
    return (f'<g id="{id_}" inkscape:groupmode="layer" inkscape:label="{label}"{vis}>\n{content}\n</g>')


def lit_letters(letters, words, dots_on):
    lit = set()
    for w in words:
        r, c0, n = WORDS[w]
        lit.update((r, c) for c in range(c0, c0 + n))
    return lit


def main():
    face = Face(FONT)
    face_m = Face(FONT_MEDIUM)
    letters, dots = build_windows(face)
    f, mm, river = terrain()
    minor, major, _ = contour_paths(f, mm)
    rivers = river_paths(river)
    labs = labels(face_m)

    col = color_layer(letters, dots, minor, major, rivers, labs)

    # --- Master (Ebenen von unten nach oben: Blocker, Weiß, Farbe) ---
    master = "\n".join([
        layer("SCHWARZ_Blocker", "3 Schwarz (Lichtsperre) – zuletzt drucken", mask_layer(letters, dots, "#000000")),
        layer("WEISS", "2 Weiß – als zweites drucken", mask_layer(letters, dots, "#ffffff")),
        layer("FARBE", "1 Farbe (CMYK) – als erstes drucken", col),
    ])
    (OUT / "hsrw_wortuhr_master.svg").write_text(svg_doc(master))
    (OUT / "layer_1_farbe.svg").write_text(svg_doc(col, ns=False))
    (OUT / "layer_2_weiss_schwarz.svg").write_text(svg_doc(mask_layer(letters, dots, "#000000"), ns=False))

    # --- Vorschauen ---
    glow = ('<filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="0.9"/></filter>'
            '<filter id="bloom" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3.2"/></filter>')
    all_lit = {(r, c) for r in range(ROWS) for c in range(COLS)}
    demo_lit = lit_letters(letters, DEMO_WORDS, DEMO_DOTS)

    def preview(lit, dots_on, unlit_dim):
        parts = [f'<rect width="{SIZE}" height="{SIZE}" fill="{INTERIOR}"/>']
        glow_src = "".join(f'<path d="{p}" fill="{LED}"/>' for r, c, ch, p in letters if (r, c) in lit)
        dots_src = "".join(f'<path d="{d}" fill="{LED}"/>' for i, d in enumerate(dots) if i < dots_on)
        if lit or dots_on:
            parts.append(f'<g filter="url(#glow)">{glow_src}{dots_src}</g>')
        parts.append(f'<g>{col}</g>')
        if unlit_dim:
            # ohne weiße Hinterlegung wirken Linien im Fenster dunkler als außen
            dim = "".join(f'<path d="{p}" fill="{INTERIOR}" opacity="0.3"/>'
                          for r, c, ch, p in letters if (r, c) not in lit)
            parts.append(f'<g>{dim}</g>')
        if lit or dots_on:
            parts.append(f'<g filter="url(#bloom)" opacity="0.45" style="mix-blend-mode:screen">{glow_src}{dots_src}</g>')
            # LED-Überstrahlung: Kern der Buchstaben hell, Linien bleiben als Textur sichtbar
            parts.append(f'<g opacity="0.7" style="mix-blend-mode:screen">{glow_src}{dots_src}</g>')
        return "\n".join(parts)

    (OUT / "preview_aus.svg").write_text(svg_doc(preview(set(), 0, True), glow, ns=False))
    (OUT / "preview_an.svg").write_text(svg_doc(preview(demo_lit, DEMO_DOTS, True), glow, ns=False))
    (OUT / "preview_alle.svg").write_text(svg_doc(preview(all_lit, 4, False), glow, ns=False))
    print("fertig:", ", ".join(sorted(p.name for p in OUT.glob("*.svg"))))


if __name__ == "__main__":
    main()
