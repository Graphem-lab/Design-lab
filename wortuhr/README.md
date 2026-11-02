# Wortuhr HSRW – Glasscheibe 300 × 300 mm

Design für UV-Direktdruck auf Glas. Motiv: **Höhenlinien-Karte der Region Rhein-Waal** mit dem Rhein als Leitlinie
(fließt wie in echt von Südost nach Nordwest), Kartenrahmen mit Skalenstrichen und den Koordinaten der beiden
Standorte **Kleve** (51°47′N 6°08′E) und **Kamp-Lintfort** (51°30′N 6°32′E).

Die 110 Buchstaben sind *Fenster* in einer dunklen Fläche. Im Ruhezustand verschwinden sie in den Höhenlinien,
mit Licht von hinten leuchten sie klar.

**Raster = deine Frontplatte:** Maße und Buchstaben stammen aus `Buchstaben in Kästchen(glas Engrave)_aktuell.svg`
und `Wordclock_v3/matrix.cpp` (11 × 10 Kästchen à 12 × 14 mm, Abstand 16,7 × 18,7 mm, 4 Minuten-LEDs Ø 6 mm in einer
Reihe unter dem Raster). `out/check_zellen.png` legt deine Kästchen (rot) über das Design: alle Buchstaben passen.

## Dateien (`out/`)

| Datei | Zweck |
|---|---|
| `hsrw_wortuhr_master.svg` | Master mit 3 benannten Ebenen (Inkscape/Illustrator), Ansicht von **vorne** |
| `layer_1_farbe.svg` / `.pdf` | Ebene 1: Farbe |
| `layer_2_weiss_schwarz.svg` / `.pdf` | Ebene 2+3: Maske für **Weiß** und **Schwarz** (identisch) |
| `preview_aus.png` / `preview_an.png` / `preview_alle.png` | Simulation: Uhr aus, 09:27 Uhr, alle Buchstaben an |
| `check_zellen.png` | Kontrolle: Kästchen aus deinem SVG (rot) über dem Design |

Alle Schrift ist in Pfade umgewandelt (Inter SemiBold, SIL OFL) – keine Schriften nötig. Maße sind 1:1 in mm.

## Druckaufbau (Vorschlag – bitte mit der Druckerei abstimmen)

Druck von **hinten** auf die Rückseite des Glases, Datei im RIP **spiegeln**. Reihenfolge:

1. **Farbe** (`layer_1_farbe`) – wird durch das Glas gesehen, deshalb zuerst
2. **Weiß** (`layer_2_weiss_schwarz`) – ggf. 2× für Deckkraft
3. **Schwarz/Blocker** (`layer_2_weiss_schwarz`) – damit das Licht nur durch die Buchstaben tritt

In den Buchstaben und Punkten steht weder Weiß noch Schwarz. Die Buchstaben-Fenster tragen in der Farbebene nur eine
**35 %-Tönung** in der Hintergrundfarbe (`WINDOW_TINT`) – das ist die „Tarnung“. Sie kostet etwa ein Drittel der
Helligkeit; bei zu dunklem Licht auf 0.2–0.25 reduzieren, bei zu sichtbaren Buchstaben auf 0.4–0.5 erhöhen.
Die Tönung ist als Transparenz (`fill-opacity`) angelegt, das RIP muss daraus ein Raster rechnen.

**Passer:** UV-Drucker haben ~0.1 mm Versatz zwischen den Ebenen. Wenn ein heller Rand um die Buchstaben auftaucht,
die Weiß-/Schwarz-Maske im RIP um ca. 0.1 mm „spreizen“ (Fenster werden minimal enger).

## Wichtige Hinweise

* Buchstaben sind Inter SemiBold, **8 mm Versalhöhe** (automatisch so gewählt, dass W/M/Ü mit 0,6 mm Rand ins
  Kästchen passen). Dein SVG nutzt Arial; ich habe die Schrift bewusst gewechselt, sag Bescheid falls es Arial sein soll.
* Minutenpunkte sind Fenster Ø 6 mm wie im SVG. Für kleinere Punkte `DOT_R` in `generate.py` ändern.
* Das Easter Egg „HSRW“ aus dem ersten Entwurf entfällt: in deinem Layout gibt es keine 4 zusammenhängenden Füllbuchstaben.
* Alles Wichtige liegt **12 mm** innerhalb der Kante (Kartenrahmen), falls der Uhrenrahmen die Ränder überdeckt.
  Die Seitenränder (je ~60 mm) tragen die Koordinaten von Kleve und Kamp-Lintfort senkrecht.
* Die Farben (Petrol/Teal) sind eine **Wasser-Anspielung, nicht die offiziellen HSRW-Corporate-Farben**; das Logo ist
  nicht enthalten. Hex-Werte oben in `generate.py` (RGB am Bildschirm, im RIP nach CMYK wandeln).
* Die Vorschau ist eine Simulation. **Vor dem Druck der ganzen Scheibe unbedingt einen Teststreifen drucken**
  (Tarnung vs. Helligkeit hängt von LED, Abstand und Farbe der Uhren-Rückseite ab; eine dunkelblaugraue statt
  tiefschwarzer Rückwand macht die Buchstaben im Ruhezustand noch unauffälliger).
* `Wordclock/Wordclock_Matrix.dxf` enthält keine Geometrie (leerer Export) und wurde nicht verwendet.

## Neu erzeugen

```bash
pip install fonttools scikit-image shapely scipy numpy
python3 generate.py
NODE_PATH=$(npm root -g) node render.js   # PNG/PDF (benötigt Playwright)
```

`SEED` ändert das Gelände, `RIVER_PTS` den Flussverlauf, `ROWS_TEXT` die Buchstaben.
