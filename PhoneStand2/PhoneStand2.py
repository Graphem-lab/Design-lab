import adsk.core, adsk.fusion, traceback, math

# ---- Parameter (alles in mm) -------------------------------------------
PHONE_W   = 80.0   # Breite des Schlitzes in X-Richtung (Handy + Hülle)
SLOT_T    = 14.0   # Schlitzdicke (Handy + Hülle)
WALL      = 12.0   # Wandstärke zwischen/neben den Handys
DEPTH     = 90.0   # Tiefe des Ständers (Y)
HEIGHT    = 38.0   # Höhe des Ständers (Z)
FLOOR     = 10.0   # Boden unter dem Schlitz
LIP_H     = 18.0   # Höhe der vorderen Lippe
FRONT     = 12.0   # Abstand Schlitz-Vorderkante zur Vorderseite
TILT_DEG  = 20.0   # Neigung nach hinten (0 = senkrecht)
CABLE_W   = 20.0   # Breite des Kabelkanals
CORNER_R  = 8.0    # Rundung der senkrechten Kanten
# ------------------------------------------------------------------------

MM = 0.1  # Fusion rechnet intern in cm


def offset_plane(root, z):
    inp = root.constructionPlanes.createInput()
    inp.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(z * MM))
    return root.constructionPlanes.add(inp)


def rect_sketch(root, plane, x0, y0, x1, y1):
    sk = root.sketches.add(plane)
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(x0 * MM, y0 * MM, 0),
        adsk.core.Point3D.create(x1 * MM, y1 * MM, 0))
    return sk


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent
        ext = root.features.extrudeFeatures
        dist = lambda v: adsk.core.ValueInput.createByReal(v * MM)

        width = 2 * PHONE_W + 3 * WALL

        # 1) Grundkörper
        sk = rect_sketch(root, root.xYConstructionPlane, 0, 0, width, DEPTH)
        base = ext.addSimple(sk.profiles.item(0), dist(HEIGHT),
                             adsk.fusion.FeatureOperations.NewBodyFeatureOperation).bodies.item(0)
        base.name = "Handyständer"

        # 2) senkrechte Kanten runden
        edges = adsk.core.ObjectCollection.create()
        for e in base.edges:
            a, b = e.startVertex.geometry, e.endVertex.geometry
            if abs(a.x - b.x) < 1e-6 and abs(a.y - b.y) < 1e-6:
                edges.add(e)
        fil = root.features.filletFeatures
        fi = fil.createInput()
        fi.addConstantRadiusEdgeSet(edges, dist(CORNER_R), True)
        fil.add(fi)

        # 3) Schlitz-Werkzeugkörper (geneigt) für beide Handys
        floor_plane = offset_plane(root, FLOOR)
        tools = adsk.core.ObjectCollection.create()
        for i in range(2):
            x0 = WALL + i * (PHONE_W + WALL)
            s = rect_sketch(root, floor_plane, x0, FRONT, x0 + PHONE_W, FRONT + SLOT_T)
            tool = ext.addSimple(s.profiles.item(0), dist(HEIGHT * 2),
                                 adsk.fusion.FeatureOperations.NewBodyFeatureOperation).bodies.item(0)
            m = adsk.core.Matrix3D.create()
            # negativer Winkel um X: Oberkante kippt nach hinten (+Y)
            m.setToRotation(-math.radians(TILT_DEG),
                            adsk.core.Vector3D.create(1, 0, 0),
                            adsk.core.Point3D.create(0, FRONT * MM, FLOOR * MM))
            col = adsk.core.ObjectCollection.create()
            col.add(tool)
            mi = root.features.moveFeatures.createInput2(col)
            mi.defineAsFreeMove(m)
            root.features.moveFeatures.add(mi)
            tools.add(tool)

            # Kabelkanal nach hinten
            cx = x0 + PHONE_W / 2
            c = rect_sketch(root, offset_plane(root, 2), cx - CABLE_W / 2, FRONT + 3,
                            cx + CABLE_W / 2, DEPTH + 1)
            tools.add(ext.addSimple(c.profiles.item(0), dist(FLOOR - 2),
                      adsk.fusion.FeatureOperations.NewBodyFeatureOperation).bodies.item(0))

        comb = root.features.combineFeatures
        ci = comb.createInput(base, tools)
        ci.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
        comb.add(ci)

        # 4) Vordere Lippe auf LIP_H absenken
        lp = offset_plane(root, LIP_H)
        s = rect_sketch(root, lp, -1, -1, width + 1, FRONT + SLOT_T)
        ext.addSimple(s.profiles.item(0), dist(HEIGHT - LIP_H + 1),
                      adsk.fusion.FeatureOperations.CutFeatureOperation)

        app.activeViewport.fit()
        ui.messageBox("Doppel-Handyständer erstellt (%.0f x %.0f x %.0f mm)." % (width, DEPTH, HEIGHT))
    except:
        if ui:
            ui.messageBox("Fehler:\n{}".format(traceback.format_exc()))
