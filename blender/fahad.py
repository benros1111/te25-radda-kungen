# Prins Fahad – byggs i Blender med kod.
# Kör:  /Applications/Blender.app/Contents/MacOS/Blender -b --python blender/fahad.py -- modeller/fahad.glb
#
# Stil (önskad av TE25): liten guldkrona, vita AirPods, fotbollströja i blått och rödbrunt
# (Barcelonas färger, utan logga), svarta byxor, slides, kort svart fluffigt hår och röd mantel.
import bpy
import os
import sys
import random
from math import radians, sin, cos, pi
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
random.seed(10)  # samma fluffiga hår varje gång

# ===== Färger (så som de ska synas i spelet) =====
FARGER = {
    "hud":     (0.62, 0.42, 0.27),
    "har":     (0.03, 0.03, 0.03),
    "bla":     (0.0, 0.2, 0.55),     # blå rand
    "rod":     (0.55, 0.04, 0.17),   # rödbrun rand
    "gul":     (1.0, 0.8, 0.1),      # detaljer och nummer
    "byxor":   (0.04, 0.04, 0.05),
    "slide":   (0.06, 0.06, 0.07),
    "slideBand": (0.95, 0.95, 0.95),
    "guld":    (1.0, 0.72, 0.08),
    "juvel":   (0.85, 0.05, 0.1),
    "airpods": (0.97, 0.97, 0.97),
    "vit":     (0.97, 0.97, 0.97),
    "svart":   (0.02, 0.02, 0.02),
    "mun":     (0.45, 0.18, 0.15),
    "mantel":  (0.75, 0.05, 0.08),
    "mantelKant": (1.0, 0.8, 0.1),
}
MATERIAL = {}
for namn, rgb in FARGER.items():
    m = bpy.data.materials.new(namn)
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*rgb, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
    MATERIAL[namn] = m


def ny(objekt_typ, farg, plats, skala=(1, 1, 1), rotation=(0, 0, 0), mjuk=False, **kw):
    """Lägg till en form, ge den färg och returnera den."""
    getattr(bpy.ops.mesh, "primitive_" + objekt_typ + "_add")(location=plats, rotation=rotation, **kw)
    o = bpy.context.active_object
    o.scale = skala
    o.data.materials.append(MATERIAL[farg])
    if mjuk:
        bpy.ops.object.shade_smooth()
    return o


def text(innehall, farg, plats, storlek, rotation):
    """Text som blir 3D-form (t.ex. ett tröjnummer)."""
    bpy.ops.object.text_add(location=plats, rotation=rotation)
    o = bpy.context.active_object
    o.data.body = innehall
    o.data.size = storlek
    o.data.extrude = 0.003
    o.data.align_x = "CENTER"
    o.data.align_y = "CENTER"
    o.data.materials.append(MATERIAL[farg])
    bpy.ops.object.convert(target="MESH")
    return bpy.context.active_object


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


def rundad(o, bredd=0.03):
    """Runda av kanterna på en låda."""
    mod = o.modifiers.new("runda", "BEVEL")
    mod.width = bredd
    mod.segments = 3
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier="runda")
    return o


# Figuren tittar mot -Y (framifrån i Blender). Vänster sida på figuren = +X.
# ===== Ben: svarta byxor, bara anklar och slides. Leden sitter i höften. =====
for s, namn in ((1, "BenV"), (-1, "BenH")):
    x = 0.1 * s
    delar = [
        ny("cylinder", "byxor", (x, 0, 0.52), (0.085, 0.085, 0.34), vertices=12, mjuk=True),
        ny("cylinder", "byxor", (x, 0, 0.83), (0.1, 0.1, 0.06), vertices=12, mjuk=True),
        ny("cylinder", "hud", (x, 0, 0.13), (0.045, 0.045, 0.06), vertices=10, mjuk=True),           # ankel
        ny("uv_sphere", "hud", (x, -0.06, 0.06), (0.06, 0.11, 0.035), segments=12, ring_count=6, mjuk=True),  # fot
        rundad(ny("cube", "slide", (x, -0.05, 0.018), (0.075, 0.15, 0.018)), 0.012),                 # sula
        rundad(ny("cube", "slideBand", (x, -0.08, 0.07), (0.072, 0.055, 0.03)), 0.012),              # bandet
    ]
    sla_ihop(delar, namn, (x, 0, 0.86))

# ===== Kropp: randig fotbollströja =====
kropp = [
    rundad(ny("cube", "rod", (0, 0, 1.12), (0.2, 0.135, 0.28)), 0.05),       # tröjan (rödbrun botten)
    ny("cylinder", "byxor", (0, 0, 0.86), (0.19, 0.13, 0.05), vertices=16),  # byxlinning
]
# Blå ränder fram och bak
for i, x in enumerate((-0.12, -0.04, 0.04, 0.12)):
    if i % 2 == 0:
        for y in (-0.136, 0.136):
            kropp.append(ny("cube", "bla", (x + 0.04, y, 1.12), (0.04, 0.003, 0.255)))
kropp += [
    ny("cylinder", "gul", (0, 0, 1.4), (0.085, 0.075, 0.015), vertices=16),          # gul krage
    ny("cylinder", "hud", (0, 0, 1.45), (0.065, 0.065, 0.06), vertices=10, mjuk=True),  # hals
    text("10", "gul", (-0.1, -0.141, 1.27), 0.09, (radians(90), 0, 0)),              # nummer på bröstet (manteln täcker ryggen)
]

# ===== Huvud =====
HUVUD = Vector((0, 0, 1.62))
R = 0.17
kropp += [
    ny("uv_sphere", "hud", HUVUD, (R, R * 0.95, R * 1.08), segments=20, ring_count=12, mjuk=True),
    ny("uv_sphere", "hud", HUVUD + Vector((0, -0.165, -0.02)), (0.025, 0.03, 0.03), segments=8, ring_count=6, mjuk=True),  # näsa
    ny("cube", "mun", HUVUD + Vector((0, -0.158, -0.075)), (0.03, 0.005, 0.006)),        # leende
]
for s in (1, -1):
    x = 0.06 * s
    kropp += [
        ny("uv_sphere", "vit", HUVUD + Vector((x, -0.148, 0.02)), (0.03, 0.015, 0.025), segments=10, ring_count=6, mjuk=True),
        ny("uv_sphere", "svart", HUVUD + Vector((x, -0.162, 0.02)), (0.015, 0.008, 0.016), segments=8, ring_count=6, mjuk=True),
        ny("cube", "har", HUVUD + Vector((x, -0.155, 0.07)), (0.035, 0.008, 0.008)),        # ögonbryn
        ny("uv_sphere", "hud", HUVUD + Vector((0.172 * s, 0, 0)), (0.025, 0.035, 0.045), segments=8, ring_count=6, mjuk=True),  # öra
        # Vita AirPods
        ny("uv_sphere", "airpods", HUVUD + Vector((0.18 * s, -0.012, -0.005)), (0.02, 0.02, 0.02), segments=8, ring_count=6, mjuk=True),
        ny("cylinder", "airpods", HUVUD + Vector((0.185 * s, -0.018, -0.045)), (0.008, 0.008, 0.035), vertices=8, mjuk=True),
    ]

# ===== Kort, fluffigt svart hår: många små bollar över toppen och sidorna =====
for i in range(70):
    v = random.uniform(0, 2 * pi)
    hojd = random.uniform(0.25, 1.0)          # från strax ovanför öronen och uppåt
    if sin(v) < -0.5 and hojd < 0.55:          # lämna pannan och ansiktet fritt
        continue
    r = (1 - hojd * hojd) ** 0.5
    riktning = Vector((r * cos(v), r * sin(v), hojd))
    plats = HUVUD + Vector((riktning.x * R, riktning.y * R * 0.95, riktning.z * R * 1.08)) * 1.02
    storlek = random.uniform(0.045, 0.06)
    kropp.append(ny("ico_sphere", "har", plats, (storlek, storlek, storlek * 0.85), subdivisions=1))
# En hårlugg fram
for x in (-0.07, -0.02, 0.03, 0.08):
    kropp.append(ny("ico_sphere", "har", HUVUD + Vector((x, -0.12, 0.12)), (0.05, 0.045, 0.04), subdivisions=1))

# ===== Liten guldkrona, lite på sned =====
KRONA = HUVUD + Vector((0.02, 0.01, 0.235))
kropp.append(ny("cylinder", "guld", KRONA, (0.075, 0.075, 0.03), rotation=(radians(-5), radians(10), 0), vertices=10))
for i in range(5):
    v = (i / 5) * 2 * pi
    kropp.append(ny("cone", "guld", KRONA + Vector((cos(v) * 0.065, sin(v) * 0.065, 0.045)), (0.02, 0.02, 0.035),
                    rotation=(radians(-5), radians(10), 0), vertices=6))
    kropp.append(ny("uv_sphere", "guld", KRONA + Vector((cos(v) * 0.065, sin(v) * 0.065, 0.085)), (0.01, 0.01, 0.01),
                    segments=6, ring_count=4))
kropp.append(ny("uv_sphere", "juvel", KRONA + Vector((0, -0.075, 0)), (0.016, 0.01, 0.016), segments=8, ring_count=6))

sla_ihop(kropp, "Kropp", (0, 0, 0))

# ===== Armar: korta blå ärmar + bara armar. Leden sitter i axeln. =====
for s, namn in ((1, "ArmV"), (-1, "ArmH")):
    x = 0.255 * s
    delar = [
        ny("cylinder", "bla", (x, 0, 1.31), (0.068, 0.068, 0.09), rotation=(0, radians(-8 * s), 0), vertices=12, mjuk=True),  # ärm
        ny("uv_sphere", "rod", (x - 0.01 * s, 0, 1.37), (0.07, 0.07, 0.05), segments=12, ring_count=6, mjuk=True),            # axel
        ny("cylinder", "hud", (x + 0.015 * s, 0, 1.06), (0.045, 0.045, 0.18), rotation=(0, radians(-5 * s), 0), vertices=10, mjuk=True),
        ny("uv_sphere", "hud", (x + 0.03 * s, 0, 0.85), (0.05, 0.04, 0.06), segments=10, ring_count=6, mjuk=True),            # hand
    ]
    sla_ihop(delar, namn, (x - 0.01 * s, 0, 1.38))

# ===== Röd mantel med guldkant. Leden sitter vid axlarna så den kan fladdra. =====
mantel = [
    ny("cube", "mantel", (0, 0.16, 1.02), (0.22, 0.008, 0.37)),
    ny("cube", "mantelKant", (0, 0.162, 0.66), (0.22, 0.01, 0.015)),
    ny("cylinder", "guld", (0.15, 0.12, 1.37), (0.025, 0.025, 0.01), rotation=(radians(90), 0, 0), vertices=10),  # spänne
    ny("cylinder", "guld", (-0.15, 0.12, 1.37), (0.025, 0.025, 0.01), rotation=(radians(90), 0, 0), vertices=10),
]
sla_ihop(mantel, "Mantel", (0, 0.15, 1.39))

# ===== Exportera till spelet =====
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=sys.argv[-1], export_format="GLB", use_selection=True,
    export_yup=True, export_apply=True, export_animations=False,
)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(os.path.abspath(__file__)), "fahad.blend"))
print("KLAR: Prins Fahad")
