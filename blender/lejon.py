# Lejonet Husein – byggs i Blender med kod. Version 2: så verkligt som möjligt.
# Kör:  /Applications/Blender.app/Contents/MacOS/Blender -b --python blender/lejon.py -- modeller/lejon.glb
#
# Önskat av TE25: ett jätterealistiskt lejon som går på fyra ben och är en skurk i spelet.
# Förebild: ett riktigt afrikanskt lejon (som de verklighetstrogna djuren i nya Lejonkungen).
#
# Så blir det verkligt:
# - Pälsens färg varierar mjukt: mörkare rygg, ljus mage, ljus nos, mörka örons baksidor.
#   Det görs med "vertex colors": varje punkt i modellen får sin egen färg.
# - Manen är mörkbrun längst bak och gyllene närmast ansiktet, byggd av hundratals tofsar.
# - Musklerna syns: skulderblad och höftben buktar ut.
# - Benen är egna delar (BenFV, BenFH, BenBV, BenBH) med leden i axeln/höften,
#   så att spelet kan få lejonet att gå. Svansen (Svans) kan svänga.
import bpy
import bmesh
import os
import sys
import random
from math import radians, sin, cos, pi
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
random.seed(7)
V = Vector


def blanda(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(x + (y - x) * t for x, y in zip(a, b))


# ===== Färger (sRGB, så som de ska synas) =====
PALS = (0.76, 0.56, 0.31)
RYGG = (0.6, 0.42, 0.22)
MAGE = (0.9, 0.8, 0.62)
NOS = (0.86, 0.75, 0.58)
MAN_MORK = (0.24, 0.13, 0.06)
MAN_MELLAN = (0.46, 0.27, 0.11)
MAN_GULD = (0.72, 0.5, 0.24)
SVART = (0.04, 0.03, 0.025)
NOSTIPP = (0.42, 0.24, 0.2)
OGA = (0.82, 0.56, 0.1)
VIT = (1.0, 1.0, 1.0)
KLO = (0.88, 0.85, 0.78)

# Ett enda material som visar varje punkts egen färg (bra för spelets prestanda också)
MAT = bpy.data.materials.new("lejon")
MAT.use_nodes = True
noder = MAT.node_tree.nodes
attr = noder.new("ShaderNodeVertexColor")
attr.layer_name = "Col"
MAT.node_tree.links.new(attr.outputs["Color"], noder["Principled BSDF"].inputs["Base Color"])
noder["Principled BSDF"].inputs["Roughness"].default_value = 0.9


def linjar(c):
    """Från sRGB till linjär färg (så lagras färger i 3D-filer)."""
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def farga(o, farg):
    """Ge varje punkt en färg. farg = en färg, eller en funktion av punktens plats i världen."""
    mesh = o.data
    if "Col" in mesh.color_attributes:
        mesh.color_attributes.remove(mesh.color_attributes["Col"])
    lager = mesh.color_attributes.new(name="Col", type="FLOAT_COLOR", domain="POINT")
    mw = o.matrix_world
    for i, v in enumerate(mesh.vertices):
        c = farg(mw @ v.co) if callable(farg) else farg
        lager.data[i].color = (*linjar(c), 1.0)
    if not mesh.materials:
        mesh.materials.append(MAT)
    return o


def ny(objekt_typ, farg, plats, skala=(1, 1, 1), rotation=(0, 0, 0), mjuk=True, **kw):
    getattr(bpy.ops.mesh, "primitive_" + objekt_typ + "_add")(location=plats, rotation=rotation, **kw)
    o = bpy.context.active_object
    o.scale = skala
    bpy.context.view_layer.update()
    if mjuk:
        bpy.ops.object.shade_smooth()
    return farga(o, farg)


def avrunda(o, niva=2):
    bpy.context.view_layer.objects.active = o
    mod = o.modifiers.new("mjuk", "SUBSURF")
    mod.levels = niva
    mod.render_levels = niva
    bpy.ops.object.modifier_apply(modifier="mjuk")
    bpy.ops.object.shade_smooth()
    return o


def loft(namn, farg, ringar, axel="z", segment=16, niva=2):
    """Bygg en form av ringar längs en axel. Ring = (mittpunkt, radie1, radie2)."""
    bm = bmesh.new()
    lager = []
    for mitt, r1, r2 in ringar:
        ring = []
        for i in range(segment):
            a = i / segment * 2 * pi
            if axel == "z":
                p = (mitt[0] + r1 * cos(a), mitt[1] + r2 * sin(a), mitt[2])
            else:
                p = (mitt[0] + r1 * cos(a), mitt[1], mitt[2] + r2 * sin(a))
            ring.append(bm.verts.new(p))
        lager.append(ring)
    for a, b in zip(lager, lager[1:]):
        for i in range(segment):
            bm.faces.new((a[i], a[(i + 1) % segment], b[(i + 1) % segment], b[i]))
    bm.faces.new(list(reversed(lager[0])))
    bm.faces.new(lager[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(namn)
    bm.to_mesh(mesh)
    bm.free()
    o = bpy.data.objects.new(namn, mesh)
    bpy.context.collection.objects.link(o)
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    avrunda(o, niva)
    return farga(o, farg)


def tofs(farg, start, riktning, langd, bredd):
    """En mjuk hårtofs: avlång och rundad, som en hårslinga."""
    riktning = riktning.normalized()
    rot = V((0, 0, 1)).rotation_difference(riktning).to_euler()
    if bredd < 0.01:  # morrhår: ett tunt strå
        return ny("cone", farg, start + riktning * langd * 0.5, (bredd, bredd, langd / 2),
                  rotation=rot, vertices=4, radius1=1, radius2=0.2, depth=2, mjuk=False)
    return ny("uv_sphere", farg, start + riktning * langd * 0.5, (bredd, bredd * 0.65, langd / 2),
              rotation=rot, segments=8, ring_count=6)


def sla_ihop(delar, namn, led):
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


# ===== Pälsens färg beroende på var på kroppen punkten sitter =====
def kroppsfarg(p):
    c = PALS
    c = blanda(c, RYGG, (p.z - 0.86) / 0.22)           # mörkare upp mot ryggen
    c = blanda(c, MAGE, (0.68 - p.z) / 0.14)           # ljus mage och insida
    return c


def benfarg(p):
    c = blanda(PALS, MAGE, (0.35 - p.z) / 0.3)         # ljusare ner mot tassarna
    return blanda(c, RYGG, (p.z - 0.75) / 0.2)


# Lejonet tittar mot -Y (framifrån i Blender). Huvudet vid -Y, svansen vid +Y.
# Längd cirka 2 m (utan svans), mankhöjd cirka 1 m.

# ===== Kropp: lång, låg och muskulös med djup bröstkorg =====
kropp = [
    loft("bal", kroppsfarg, [
        (V((0, 0.88, 0.8)), 0.08, 0.09),
        (V((0, 0.8, 0.82)), 0.2, 0.22),
        (V((0, 0.56, 0.83)), 0.25, 0.25),    # höfter
        (V((0, 0.25, 0.83)), 0.21, 0.22),    # midja
        (V((0, -0.05, 0.8)), 0.25, 0.29),    # revben
        (V((0, -0.32, 0.82)), 0.27, 0.33),   # djup bröstkorg
        (V((0, -0.5, 0.88)), 0.22, 0.28),
        (V((0, -0.58, 0.93)), 0.1, 0.12),
    ], axel="y", segment=20),
    loft("hals", kroppsfarg, [
        (V((0, -0.45, 0.94)), 0.2, 0.22),
        (V((0, -0.62, 1.0)), 0.17, 0.19),
        (V((0, -0.76, 1.04)), 0.14, 0.15),
    ], axel="y"),
]
# Musklerna: skulderblad och höftben som buktar ut
for s in (1, -1):
    kropp += [
        ny("uv_sphere", kroppsfarg, (0.15 * s, -0.36, 1.03), (0.1, 0.16, 0.09), segments=16, ring_count=10),
        ny("uv_sphere", kroppsfarg, (0.16 * s, 0.6, 0.9), (0.09, 0.12, 0.06), segments=16, ring_count=10),
    ]

# ===== Huvud: brett, med kraftigt nosparti =====
H = V((0, -0.88, 1.06))


def huvudfarg(p):
    r = p - H
    c = blanda(PALS, RYGG, (r.z - 0.08) / 0.1)          # mörkare panna
    c = blanda(c, NOS, (-r.y - 0.15) / 0.06)            # ljust nosparti
    c = blanda(c, NOS, (-r.z - 0.07) / 0.05)            # ljus haka
    return c


huvud = ny("uv_sphere", huvudfarg, H, (0.17, 0.2, 0.16), segments=28, ring_count=18)
kropp.append(huvud)
kropp += [
    ny("uv_sphere", huvudfarg, H + V((0, -0.17, -0.05)), (0.115, 0.12, 0.09), segments=20, ring_count=12),       # nosparti
    ny("uv_sphere", NOS, H + V((0.05, -0.25, -0.06)), (0.06, 0.05, 0.05), segments=14, ring_count=10),          # morrhårskuddar
    ny("uv_sphere", NOS, H + V((-0.05, -0.25, -0.06)), (0.06, 0.05, 0.05), segments=14, ring_count=10),
    ny("uv_sphere", NOS, H + V((0, -0.2, -0.13)), (0.07, 0.075, 0.045), segments=14, ring_count=10),             # haka
    ny("uv_sphere", huvudfarg, H + V((0, -0.12, 0.03)), (0.08, 0.13, 0.06), segments=14, ring_count=10),         # näsrygg
    ny("uv_sphere", NOSTIPP, H + V((0, -0.295, -0.02)), (0.045, 0.022, 0.03), segments=14, ring_count=8),         # nos
    ny("cube", SVART, H + V((0, -0.285, -0.085)), (0.045, 0.006, 0.004), mjuk=False),                            # mun
    ny("cube", SVART, H + V((0, -0.292, -0.055)), (0.003, 0.004, 0.02), mjuk=False),                             # linje under nosen
]
for s in (1, -1):
    oga = H + V((0.072 * s, -0.16, 0.06))
    kropp += [
        ny("uv_sphere", SVART, oga, (0.034, 0.018, 0.022), segments=14, ring_count=8),
        ny("uv_sphere", OGA, oga + V((0, -0.008, 0)), (0.026, 0.012, 0.018), segments=14, ring_count=8),
        ny("uv_sphere", SVART, oga + V((0, -0.015, 0)), (0.009, 0.005, 0.012), segments=10, ring_count=6),
        ny("uv_sphere", VIT, oga + V((0.006 * s, -0.017, 0.006)), (0.004, 0.003, 0.004), segments=6, ring_count=4),
        ny("uv_sphere", NOS, oga + V((0, -0.006, -0.026)), (0.03, 0.012, 0.01), segments=10, ring_count=6),          # ljus fläck under ögat
        ny("uv_sphere", RYGG, oga + V((0.0, -0.006, 0.026)), (0.045, 0.022, 0.012), rotation=(0, radians(-22 * s), 0), segments=12, ring_count=6),  # arg panna
        ny("uv_sphere", SVART, H + V((0.125 * s, 0.0, 0.14)), (0.045, 0.022, 0.05), segments=12, ring_count=8),     # örats svarta baksida
        ny("uv_sphere", PALS, H + V((0.125 * s, -0.012, 0.14)), (0.038, 0.014, 0.042), segments=12, ring_count=8),  # örats framsida
    ]
    for i in range(4):  # morrhår
        start = H + V((0.06 * s, -0.27, -0.055 - i * 0.01))
        kropp.append(tofs(KLO, start, V((s * 1, -0.3, 0.06 - i * 0.07)), 0.17, 0.0025))


# ===== Manen: hundratals tofsar. Mörk längst bak, gyllene närmast ansiktet. =====
MANCENTER = H + V((0, 0.16, -0.02))


def manfarg(start, d):
    bak = (d.y + 1) / 2                              # 0 = fram vid ansiktet, 1 = bak
    c = blanda(MAN_GULD, MAN_MELLAN, bak * 1.6)
    c = blanda(c, MAN_MORK, bak * 1.6 - 0.6)
    variation = random.uniform(-0.05, 0.05)
    return tuple(max(0, x + variation) for x in c)


inre = ny("uv_sphere", MAN_MELLAN, MANCENTER, (0.26, 0.3, 0.31), segments=24, ring_count=16)
kropp.append(inre)
for lager, (antal, radie, langd, bredd) in enumerate(((260, 0.21, (0.22, 0.32), (0.055, 0.075)),
                                                      (200, 0.26, (0.26, 0.4), (0.05, 0.07)))):
    for i in range(antal):
        u = random.uniform(-1, 1)
        v = random.uniform(0, 2 * pi)
        r = (1 - u * u) ** 0.5
        d = V((r * cos(v), u, r * sin(v)))
        if d.y < -0.3 and abs(d.x) < 0.68 and -0.7 < d.z < 0.62:
            continue   # lämna ansiktet fritt
        start = MANCENTER + V((d.x * radie, d.y * radie * 1.1, d.z * radie * 1.15))
        riktning = d + V((0, 0.85, -0.8))    # håret faller bakåt och neråt
        l = random.uniform(*langd) * (1.25 if d.z < 0 else 1.0)
        kropp.append(tofs(manfarg(start, d), start, riktning, l, random.uniform(*bredd)))
# Kort, gyllene krans runt ansiktet
for i in range(48):
    v = i / 48 * 2 * pi
    start = H + V((cos(v) * 0.17, -0.07, sin(v) * 0.17))
    kropp.append(tofs(blanda(MAN_GULD, MAN_MELLAN, random.random() * 0.5), start, V((cos(v), 0.35, sin(v) - 0.2)),
                      random.uniform(0.1, 0.16), 0.045))
# Lång man som hänger ner över bröstet och mellan frambenen
for i in range(110):
    x = random.uniform(-0.2, 0.2)
    y = random.uniform(-0.7, -0.28)
    z = random.uniform(0.78, 1.05)
    kropp.append(tofs(blanda(MAN_MELLAN, MAN_MORK, random.random()), V((x, y, z)),
                      V((x * 0.6, random.uniform(0.1, 0.35), -1)), random.uniform(0.24, 0.4), random.uniform(0.055, 0.075)))

sla_ihop(kropp, "Kropp", (0, 0, 0))


# ===== Ben: kraftiga med böjda leder och stora tassar. Leden sitter i axeln/höften. =====
def ben(namn, x, y, fram):
    if fram:
        ringar = [
            (V((x, y - 0.02, 0.07)), 0.06, 0.065),
            (V((x, y - 0.01, 0.16)), 0.06, 0.065),    # handled
            (V((x, y, 0.32)), 0.07, 0.078),
            (V((x, y + 0.012, 0.5)), 0.09, 0.1),      # armbåge
            (V((x, y - 0.01, 0.68)), 0.125, 0.14),    # kraftig överarm
            (V((x * 0.9, y, 0.86)), 0.14, 0.16),
        ]
        led = V((x * 0.9, y, 0.86))
    else:
        ringar = [
            (V((x, y - 0.03, 0.07)), 0.058, 0.062),
            (V((x, y + 0.02, 0.17)), 0.055, 0.06),
            (V((x, y + 0.11, 0.32)), 0.06, 0.072),     # hasled (bakåtböjd)
            (V((x, y + 0.04, 0.48)), 0.095, 0.11),
            (V((x * 1.05, y - 0.06, 0.64)), 0.145, 0.17),  # kraftigt lår
            (V((x * 0.95, y - 0.02, 0.84)), 0.15, 0.18),
        ]
        led = V((x * 0.95, y - 0.02, 0.84))
    delar = [
        loft(namn, benfarg, ringar),
        ny("uv_sphere", MAGE, (x, y - 0.06, 0.045), (0.08, 0.105, 0.05), segments=16, ring_count=10),  # tass
    ]
    for t in (-1.5, -0.5, 0.5, 1.5):   # tår och klor
        delar.append(ny("uv_sphere", MAGE, (x + t * 0.032, y - 0.14, 0.035), (0.024, 0.03, 0.03), segments=10, ring_count=6))
        delar.append(ny("cone", KLO, (x + t * 0.032, y - 0.172, 0.02), (0.008, 0.008, 0.018), rotation=(radians(100), 0, 0), vertices=6))
    return sla_ihop(delar, namn, led)


ben("BenFV", 0.16, -0.36, True)    # fram vänster
ben("BenFH", -0.16, -0.36, True)   # fram höger
ben("BenBV", 0.16, 0.58, False)    # bak vänster
ben("BenBH", -0.16, 0.58, False)   # bak höger

# ===== Svans med mörk tofs =====
svans = [loft("svans", PALS, [
    (V((0, 0.84, 0.82)), 0.035, 0.035),
    (V((0, 1.0, 0.75)), 0.03, 0.03),
    (V((0, 1.16, 0.58)), 0.025, 0.025),
    (V((0, 1.26, 0.45)), 0.022, 0.022),
    (V((0, 1.33, 0.4)), 0.02, 0.02),
], axel="y", segment=10)]
for i in range(20):
    d = V((random.uniform(-1, 1), random.uniform(0.2, 1), random.uniform(-1, 0.3)))
    svans.append(tofs(MAN_MORK, V((0, 1.33, 0.4)), d, random.uniform(0.08, 0.12), 0.022))
sla_ihop(svans, "Svans", (0, 0.84, 0.82))

# ===== Exportera till spelet =====
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=sys.argv[-1], export_format="GLB", use_selection=True,
    export_yup=True, export_apply=True, export_animations=False,
)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(os.path.abspath(__file__)), "lejon.blend"))
print("KLAR: Lejonet Husein")
