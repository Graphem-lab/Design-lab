#!/usr/bin/env python3
"""Löst die Primärvariante (invers) der HSRW-Wort-/Bildmarke aus dem CD-PDF (Seite 5) als Vektorpfad.
Aufruf: python3 extract_logo.py ../00_202406_HSRW_CD_Basics.pdf   (benötigt pdftocairo)
Ergebnis: assets/hsrw_logo_primaer_invers.json  {d, w, h}  (Einheit: pt, Ursprung links oben)"""
import json, re, subprocess, sys, tempfile, pathlib
import xml.etree.ElementTree as ET

pdf = sys.argv[1]
tmp = pathlib.Path(tempfile.mkdtemp()) / "p5.svg"
subprocess.run(["pdftocairo", "-svg", "-f", "5", "-l", "5", pdf, str(tmp)], check=True)
ns = {"s": "http://www.w3.org/2000/svg", "x": "http://www.w3.org/1999/xlink"}
root = ET.parse(tmp).getroot()
S = "{http://www.w3.org/2000/svg}"
X = "{http://www.w3.org/1999/xlink}href"

glyphs = {}
for g in root.find(S + "defs").iter(S + "g"):
    if g.get("id", "").startswith("glyph"):
        glyphs[g.get("id")] = " ".join(p.get("d") for p in g.findall(S + "path"))

# Fläche der inversen Primärvariante (dunkles Rechteck) aus der Seite
RECT = (614.9, 176.2, 805.4, 271.8)
inside = lambda x, y: RECT[0] <= x <= RECT[2] and RECT[1] <= y <= RECT[3]
WHITE = "rgb(100%, 100%, 100%)"

def shift(d, dx, dy):
    nums = iter(re.findall(r"-?\d+\.?\d*(?:e-?\d+)?|[A-Za-z]", d))
    out, cmd = [], None
    for t in nums:
        if t.isalpha():
            cmd = t; out.append(t)
        else:
            x = float(t); y = float(next(nums))
            out.append(f"{x + dx:.3f} {y + dy:.3f}")
    return " ".join(out)

parts = []
for el in root:
    if el.tag == S + "path" and el.get("fill") == WHITE:
        m = re.match(r"M ([\d.]+) ([\d.]+)", el.get("d"))
        if inside(float(m[1]), float(m[2])):
            parts.append(el.get("d"))
    elif el.tag == S + "g" and el.get("fill") == WHITE:
        for u in el.findall(S + "use"):
            x, y = float(u.get("x")), float(u.get("y"))
            if inside(x, y):
                parts.append(shift(glyphs[u.get(X)[1:]], x, y))
d = " ".join(parts)
pts = [float(v) for v in re.findall(r"-?\d+\.?\d*", d)]
xs, ys = pts[0::2], pts[1::2]
x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
d = shift(d, -x0, -y0)
out = pathlib.Path(__file__).parent / "assets" / "hsrw_logo_primaer_invers.json"
out.write_text(json.dumps({"d": d, "w": round(x1 - x0, 3), "h": round(y1 - y0, 3)}))
print(f"{len(parts)} Teile, {x1 - x0:.1f} x {y1 - y0:.1f} pt ->", out)
