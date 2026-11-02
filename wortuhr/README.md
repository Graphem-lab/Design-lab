# Wortuhr HSRW – Glasscheibe 300 × 300 mm

Design für UV-Direktdruck auf Glas. Motiv: **Höhenlinien-Karte der Region Rhein-Waal** mit dem Rhein als Leitlinie
(fließt wie in echt von Südost nach Nordwest), Kartenrahmen mit Skalenstrichen und den Koordinaten der beiden
Standorte **Kleve** (51°47′N 6°08′E) und **Kamp-Lintfort** (51°30′N 6°32′E).

Die 110 Buchstaben sind *Fenster* in einer dunklen Fläche. Im Ruhezustand verschwinden sie in den Höhenlinien,
mit Licht von hinten leuchten sie klar. Easter Egg: Die vier Füllbuchstaben in „VOR ▢▢▢▢ NACH“ sind **HSRW**.

## Dateien (`out/`)

| Datei | Zweck |
|---|---|
| `hsrw_wortuhr_master.svg` | Master mit 3 benannten Ebenen (Inkscape/Illustrator), Ansicht von **vorne** |
| `layer_1_farbe.svg` / `.pdf` | Ebene 1: Farbe |
| `layer_2_weiss_schwarz.svg` / `.pdf` | Ebene 2+3: Maske für **Weiß** und **Schwarz** (identisch) |
| `preview_aus.png` / `preview_an.png` / `preview_alle.png` | Simulation: Uhr aus, 09:25 Uhr, alle Buchstaben an |

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

## Wichtige Annahmen – bitte gegen die eigene Uhr prüfen

* Standard-Layout **11 × 10 Buchstaben + 4 Minutenpunkte** (ES IST … UHR).
* Raster-Abstand **22 × 22 mm**, Buchstabenhöhe **12 mm**, Raster mittig auf der Scheibe.
  Wenn die Löcher/Kammern der Uhr anders liegen, in `generate.py` oben `PITCH_X/Y`, `GRID_CX/CY`, `CAP_H` ändern.
* Minutenpunkte als Fenster (Ø 3.4 mm) **24 mm** von den Kanten.
* Alles Wichtige liegt **12 mm** innerhalb der Kante (Kartenrahmen), falls der Uhrenrahmen die Ränder überdeckt.
* Die Farben (Petrol/Teal) sind eine **Wasser-Anspielung, nicht die offiziellen HSRW-Corporate-Farben**, und das
  Logo ist bewusst nicht enthalten. Die Hex-Werte stehen oben in `generate.py` (RGB am Bildschirm, im RIP nach CMYK
  wandeln; sehr dunkle Töne sehen im Druck oft anders aus).
* Die Vorschau ist eine Simulation. **Vor dem Druck der ganzen Scheibe unbedingt einen Teststreifen drucken**
  (Tarnung vs. Helligkeit hängt von LED, Abstand und Farbe der Uhren-Rückseite ab; eine dunkelblaugraue statt
  tiefschwarzer Rückwand macht die Buchstaben im Ruhezustand noch unauffälliger).

## Neu erzeugen

```bash
pip install fonttools scikit-image shapely scipy numpy
python3 generate.py
NODE_PATH=$(npm root -g) node render.js   # PNG/PDF (benötigt Playwright)
```

`SEED` ändert das Gelände, `RIVER_PTS` den Flussverlauf, `ROWS_TEXT` die Buchstaben (z. B. Füllbuchstaben).
