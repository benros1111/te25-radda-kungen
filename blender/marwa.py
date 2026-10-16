# Prinsessan Marwa – byggs i Blender med kod. Version 2: mer verklig och mänsklig.
# Kör:  /Applications/Blender.app/Contents/MacOS/Blender -b --python blender/marwa.py -- modeller/marwa.glb
#
# Stil (önskad av TE25): mörkblå hijab med en liten guldtiara, svart sweater,
# gråa jeans och svarta skor.
#
# Så blir hon mer mänsklig:
# - Riktiga proportioner: huvudet är ungefär 1/7 av längden.
# - Kropp, armar och ben byggs av "ringar" (loft) som följer en riktig kroppsform,
#   och sedan rundas allt av med Subdivision Surface.
# - Ansiktet har mandelformade ögon med brun iris, ögonlock, ögonfransar, läppar och näsa.
import bpy
import bmesh
import os
import sys
from math import radians, sin, cos, pi
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)

# ===== Färger (så som de ska synas i spelet) =====
FARGER = {
    "hud":       (0.72, 0.5, 0.37),
    "hijab":     (0.06, 0.12, 0.38),   # mörkblå
    "hijabVeck": (0.045, 0.09, 0.3),
    "sweater":   (0.05, 0.05, 0.06),
    "ribb":      (0.11, 0.11, 0.12),
    "jeans":     (0.45, 0.47, 0.5),
    "som":       (0.62, 0.63, 0.66),
    "sko":       (0.04, 0.04, 0.04),
    "sula":      (0.85, 0.85, 0.85),
    "guld":      (1.0, 0.75, 0.12),
    "juvel":     (0.2, 0.55, 1.0),
    "ogonvita":  (0.95, 0.94, 0.92),
    "iris":      (0.28, 0.14, 0.06),
    "svart":     (0.02, 0.02, 0.02),
    "bryn":      (0.08, 0.05, 0.03),
    "lappar":    (0.66, 0.32, 0.32),
    "glans":     (1.0, 1.0, 1.0),
}
MATERIAL = {}
for namn, rgb in FARGER.items():
    m = bpy.data.materials.new(namn)
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*rgb, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.7
    MATERIAL[namn] = m


def ny(objekt_typ, farg, plats, skala=(1, 1, 1), rotation=(0, 0, 0), mjuk=True, **kw):
    """Lägg till en form, ge den färg och returnera den."""
    getattr(bpy.ops.mesh, "primitive_" + objekt_typ + "_add")(location=plats, rotation=rotation, **kw)
    o = bpy.context.active_object
    o.scale = skala
    o.data.materials.append(MATERIAL[farg])
    if mjuk:
        bpy.ops.object.shade_smooth()
    return o


def avrunda(o, niva=2):
    """Gör formen mjuk och rund (Subdivision Surface) och lås fast det."""
    bpy.context.view_layer.objects.active = o
    mod = o.modifiers.new("mjuk", "SUBSURF")
    mod.levels = niva
    mod.render_levels = niva
    bpy.ops.object.modifier_apply(modifier="mjuk")
    bpy.ops.object.shade_smooth()
    return o


def loft(namn, farg, ringar, segment=16, topp=True, botten=True, niva=2):
    """Bygg en form av ringar. Varje ring = (mittpunkt, bredd, djup)."""
    bm = bmesh.new()
    lager = []
    for mitt, rx, ry in ringar:
        lager.append([bm.verts.new((mitt[0] + rx * cos(a), mitt[1] + ry * sin(a), mitt[2]))
                      for a in [i / segment * 2 * pi for i in range(segment)]])
    for a, b in zip(lager, lager[1:]):
        for i in range(segment):
            bm.faces.new((a[i], a[(i + 1) % segment], b[(i + 1) % segment], b[i]))
    if botten:
        bm.faces.new(list(reversed(lager[0])))
    if topp:
        bm.faces.new(lager[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(namn)
    bm.to_mesh(mesh)
    bm.free()
    o = bpy.data.objects.new(namn, mesh)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(MATERIAL[farg])
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    return avrunda(o, niva)


def ta_bort(o, villkor):
    """Ta bort de punkter i en form där villkor(punkt) är sant."""
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for v in o.data.vertices:
        v.select = villkor(v.co)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.mode_set(mode="OBJECT")
    return o


def sla_ihop(delar, namn, led):
    """Sätt ihop delar till ett objekt och lägg leden (origin) på rätt ställe."""
    bpy.ops.object.select_all(action="DESELECT")
    for d in delar:
        d.select_set(True)
    bpy.context.view_layer.objects.active = delar[0]
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    if len(delar) > 1:
        bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = namn
    bpy.context.scene.cursor.location = led
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    return o


V = Vector
# Figuren tittar mot -Y (framifrån i Blender). Vänster sida på figuren = +X.
# Längd: 1,65 m. Huvudet är cirka 0,23 m högt.

# ===== Ben: gråa jeans med söm, uppvikt kant och svarta sneakers. Leden sitter i höften. =====
for s, namn in ((1, "BenV"), (-1, "BenH")):
    x = 0.085 * s
    ben = loft("jeans" + namn, "jeans", [
        (V((x, 0, 0.08)), 0.043, 0.048),
        (V((x, 0, 0.16)), 0.046, 0.05),
        (V((x, 0.004, 0.32)), 0.055, 0.06),    # vad
        (V((x, 0, 0.47)), 0.052, 0.056),       # knä
        (V((x * 1.05, -0.004, 0.62)), 0.066, 0.072),
        (V((x * 1.1, 0, 0.78)), 0.082, 0.088), # lår
        (V((x * 1.1, 0, 0.9)), 0.088, 0.095),
    ])
    delar = [
        ben,
        loft("kant" + namn, "jeans", [(V((x, 0, 0.075)), 0.049, 0.054), (V((x, 0, 0.11)), 0.05, 0.055)], niva=1),
        ny("cube", "som", (x + 0.056 * s, 0, 0.47), (0.002, 0.004, 0.36), mjuk=False),
    ]
    # Sneaker: en mjuk form som är platt under
    sko = ny("uv_sphere", "sko", (x, -0.035, 0.055), (0.048, 0.115, 0.048), segments=16, ring_count=10)
    for v in sko.data.vertices:
        if v.co.z < -0.35:
            v.co.z = -0.35
    delar += [sko, ny("cube", "sula", (x, -0.035, 0.012), (0.05, 0.115, 0.012), mjuk=False)]
    sla_ihop(delar, namn, (x * 1.1, 0, 0.9))

# ===== Kropp: svart sweater som följer kroppens form =====
kropp = [
    loft("sweater", "sweater", [
        (V((0, 0, 0.84)), 0.165, 0.112),   # höfter
        (V((0, 0, 0.93)), 0.158, 0.106),
        (V((0, 0.004, 1.02)), 0.14, 0.096),  # midja
        (V((0, 0, 1.12)), 0.148, 0.104),
        (V((0, -0.006, 1.21)), 0.163, 0.116),  # bröst
        (V((0, 0, 1.29)), 0.172, 0.108),
        (V((0, 0.006, 1.35)), 0.168, 0.088),  # axlar
        (V((0, 0.006, 1.385)), 0.11, 0.065),
        (V((0, 0.006, 1.40)), 0.055, 0.048),
    ]),
    loft("ribb", "ribb", [(V((0, 0, 0.82)), 0.168, 0.115), (V((0, 0, 0.87)), 0.168, 0.115)], niva=1),
    loft("hals", "hud", [(V((0, 0.008, 1.37)), 0.045, 0.042), (V((0, 0.006, 1.47)), 0.043, 0.04)], niva=1),
]

# ===== Huvud: äggform med smalare haka =====
HUVUD = V((0, 0, 1.535))
HX, HY, HZ = 0.093, 0.105, 0.118
huvud = ny("uv_sphere", "hud", HUVUD, (HX, HY, HZ), segments=32, ring_count=20)
for v in huvud.data.vertices:
    if v.co.z < 0:  # käken blir smalare mot hakan
        v.co.x *= 1 - 0.28 * (-v.co.z) ** 1.5
        if v.co.y < 0:
            v.co.y *= 1 - 0.1 * (-v.co.z)
kropp.append(huvud)


def pa_ansiktet(x, z, ut=0.0):
    """En punkt precis på ansiktets yta (framsidan)."""
    t = 1 - (x / HX) ** 2 - (z / HZ) ** 2
    y = -HY * max(t, 0.0) ** 0.5
    return HUVUD + V((x, y - ut, z))


# Ögon: ögonvita, brun iris, pupill, glans, ögonlock och fransar
for s in (1, -1):
    x = 0.034 * s
    oga = pa_ansiktet(x, 0.014)
    kropp += [
        ny("uv_sphere", "ogonvita", oga + V((0, 0.003, 0)), (0.016, 0.006, 0.0095), segments=16, ring_count=8),
        ny("uv_sphere", "iris", oga + V((0, -0.0025, 0)), (0.0085, 0.003, 0.0085), segments=12, ring_count=8),
        ny("uv_sphere", "svart", oga + V((0, -0.0045, 0)), (0.0042, 0.002, 0.0042), segments=8, ring_count=6),
        ny("uv_sphere", "glans", oga + V((0.0025 * s, -0.0058, 0.0028)), (0.0018, 0.001, 0.0018), segments=6, ring_count=4),
        # Övre ögonlock med fransar (en tunn mörk båge)
        ny("uv_sphere", "svart", oga + V((0, -0.001, 0.0085)), (0.0175, 0.0045, 0.0028), rotation=(0, radians(-6 * s), 0), segments=12, ring_count=6),
        ny("uv_sphere", "svart", oga + V((0.016 * s, -0.001, 0.009)), (0.004, 0.003, 0.0016), rotation=(0, radians(-30 * s), 0), segments=6, ring_count=4),
        # Ögonbryn: smalt och lite böjt
        ny("uv_sphere", "bryn", pa_ansiktet(0.036 * s, 0.04, 0.002), (0.02, 0.003, 0.0035), rotation=(0, radians(-10 * s), 0), segments=10, ring_count=6),
    ]

# Näsa: smal näsrygg och en liten rund spets
nasa = ny("uv_sphere", "hud", pa_ansiktet(0, -0.01, -0.004), (0.012, 0.016, 0.026), segments=16, ring_count=12)
for v in nasa.data.vertices:
    # Smal upptill (näsrygg), bredare och rundare nertill (näsvingar)
    v.co.x *= 0.55 + 0.45 * (1 - v.co.z) / 2
    if v.co.y < 0:
        v.co.y *= 0.6 + 0.4 * (1 - v.co.z) / 2
kropp.append(nasa)
# Läppar: överläpp och underläpp
kropp += [
    ny("uv_sphere", "lappar", pa_ansiktet(0, -0.048, 0.003), (0.019, 0.004, 0.0042), segments=12, ring_count=6),
    ny("uv_sphere", "lappar", pa_ansiktet(0, -0.057, 0.002), (0.016, 0.0045, 0.005), segments=12, ring_count=6),
]

# ===== Hijab: täcker huvud, hals och axlar men lämnar ansiktet fritt =====
hijab = ny("uv_sphere", "hijab", HUVUD + V((0, 0.01, 0.008)), (HX * 1.2, HY * 1.13, HZ * 1.16), segments=32, ring_count=20)
ta_bort(hijab, lambda p: p.y < -0.2 and (p.x / 0.6) ** 2 + ((p.z + 0.14) / 0.66) ** 2 < 1)
kropp.append(avrunda(hijab, 1))
# Tyget som går runt halsen och faller ner över axlarna och bröstet
kropp.append(loft("hijabFall", "hijab", [
    (V((0, 0.01, 1.47)), 0.088, 0.095),
    (V((0, 0.0, 1.43)), 0.105, 0.105),
    (V((0, -0.005, 1.39)), 0.15, 0.118),
    (V((0, -0.008, 1.355)), 0.188, 0.122),
    (V((0, -0.01, 1.325)), 0.196, 0.126),
], topp=False, botten=False))
# En flik som hänger ner fram på bröstet
kropp.append(loft("hijabFlik", "hijabVeck", [
    (V((-0.06, -0.112, 1.36)), 0.055, 0.012),
    (V((-0.055, -0.118, 1.27)), 0.045, 0.011),
    (V((-0.05, -0.116, 1.2)), 0.03, 0.009),
], niva=2))

# ===== Liten guldtiara som ligger an mot hijaben =====
TIARA = HUVUD + V((0, 0.012, 0.085))
RX, RY = 0.098, 0.105               # lika stor som hijaben på den höjden
tiara = ny("torus", "guld", TIARA, (RX / 0.1, RY / 0.1, 1), major_radius=0.1, minor_radius=0.005,
           major_segments=40, minor_segments=6)
ta_bort(tiara, lambda p: p.y > -0.02)  # bara den främre halvan
kropp.append(tiara)
for vinkel, hojd in ((-50, 0.012), (-25, 0.02), (0, 0.03), (25, 0.02), (50, 0.012)):
    v = radians(vinkel - 90)
    bas = TIARA + V((cos(v) * RX, sin(v) * RY, 0))
    kropp.append(ny("cone", "guld", bas + V((0, 0, hojd / 2)), (0.007, 0.007, hojd / 2), vertices=8))
    kropp.append(ny("uv_sphere", "guld", bas + V((0, 0, hojd + 0.004)), (0.0055, 0.0055, 0.0055), segments=8, ring_count=6))
kropp.append(ny("uv_sphere", "juvel", TIARA + V((0, -RY - 0.003, 0.012)), (0.011, 0.006, 0.013), segments=10, ring_count=6))

sla_ihop(kropp, "Kropp", (0, 0, 0))

# ===== Armar: svarta sweaterärmar med mudd och händer med tumme. Leden sitter i axeln. =====
for s, namn in ((1, "ArmV"), (-1, "ArmH")):
    x0, x1 = 0.19 * s, 0.225 * s
    def x(t):
        return x0 + (x1 - x0) * t
    arm = loft("arm" + namn, "sweater", [
        (V((x(1.0), -0.005, 0.84)), 0.034, 0.036),
        (V((x(0.8), -0.006, 0.95)), 0.038, 0.04),
        (V((x(0.55), -0.004, 1.09)), 0.042, 0.043),  # armbåge
        (V((x(0.3), 0, 1.21)), 0.048, 0.048),
        (V((x(0.08), 0.002, 1.32)), 0.055, 0.056),
        (V((x(-0.05), 0.004, 1.37)), 0.05, 0.05),
    ])
    delar = [
        arm,
        loft("mudd" + namn, "ribb", [(V((x(1.0), -0.005, 0.82)), 0.035, 0.037), (V((x(0.98), -0.005, 0.855)), 0.036, 0.038)], niva=1),
        ny("uv_sphere", "hud", (x(1.02), -0.006, 0.775), (0.022, 0.04, 0.05), segments=16, ring_count=10),           # handflata
        ny("uv_sphere", "hud", (x(1.02) - 0.004 * s, -0.04, 0.79), (0.012, 0.012, 0.025), rotation=(radians(-20), 0, 0), segments=10, ring_count=6),  # tumme
    ]
    sla_ihop(delar, namn, (x(-0.05), 0.004, 1.36))

# ===== Exportera till spelet =====
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=sys.argv[-1], export_format="GLB", use_selection=True,
    export_yup=True, export_apply=True, export_animations=False,
)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(os.path.abspath(__file__)), "marwa.blend"))
print("KLAR: Prinsessan Marwa")
