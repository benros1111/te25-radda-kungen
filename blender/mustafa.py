# Super Mustafa – byggs i Blender med kod.
# Kör:  /Applications/Blender.app/Contents/MacOS/Blender -b --python blender/mustafa.py -- modeller/mustafa.glb
#
# Stil (önskad av TE25): svart stängd jacka, svarta kostymbyxor, svarta sneakers,
# grå AirPods, taggigt mörkt hår med en riktigt hög fade.
import bpy
import sys
from math import radians, sin, cos, pi
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)

# ===== Färger (så som de ska synas i spelet) =====
FARGER = {
    "hud":      (0.78, 0.53, 0.30),
    "fade":     (0.36, 0.25, 0.17),  # kortklippt, mörkare hud = fade
    "har":      (0.05, 0.04, 0.035),
    "jacka":    (0.06, 0.06, 0.07),
    "jackaDet": (0.16, 0.16, 0.18),  # dragkedja och sömmar
    "byxor":    (0.04, 0.04, 0.05),
    "sko":      (0.05, 0.05, 0.05),
    "sula":     (0.92, 0.92, 0.92),
    "airpods":  (0.62, 0.63, 0.66),
    "vit":      (0.97, 0.97, 0.97),
    "svart":    (0.02, 0.02, 0.02),
    "mun":      (0.45, 0.18, 0.15),
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


# Figuren tittar mot -Y (framifrån i Blender). Vänster sida på figuren = +X.
# ===== Ben: kostymbyxor + sneakers. Leden sitter i höften. =====
for s, namn in ((1, "BenV"), (-1, "BenH")):
    x = 0.1 * s
    delar = [
        ny("cylinder", "byxor", (x, 0, 0.5), (0.085, 0.085, 0.37), vertices=12, mjuk=True),   # byxben
        ny("cylinder", "byxor", (x, 0, 0.83), (0.1, 0.1, 0.06), vertices=12, mjuk=True),      # höft
        ny("cube", "byxor", (x, -0.083, 0.5), (0.004, 0.004, 0.33)),                           # pressveck
        ny("cube", "sko", (x, -0.04, 0.085), (0.075, 0.14, 0.055)),                            # sko
        ny("uv_sphere", "sko", (x, -0.17, 0.08), (0.075, 0.06, 0.05), segments=12, ring_count=6, mjuk=True),  # tå
        ny("cube", "sula", (x, -0.05, 0.02), (0.08, 0.165, 0.02)),                             # vit sula
        ny("cube", "jackaDet", (x, -0.1, 0.13), (0.05, 0.002, 0.012)),                         # snören
    ]
    sla_ihop(delar, namn, (x, 0, 0.86))

# ===== Kropp: svart stängd jacka =====
kropp = [
    ny("cylinder", "jacka", (0, 0, 1.12), (0.21, 0.15, 0.3), vertices=16, mjuk=True),      # bål
    ny("uv_sphere", "jacka", (0, 0, 1.38), (0.26, 0.17, 0.09), segments=16, ring_count=8, mjuk=True),  # axlar
    ny("cylinder", "jacka", (0, 0, 0.86), (0.2, 0.14, 0.05), vertices=16, mjuk=True),      # jackans nederkant
    ny("cube", "jackaDet", (0, -0.152, 1.1), (0.008, 0.004, 0.3)),                         # dragkedja
    ny("cylinder", "jacka", (0, 0, 1.47), (0.1, 0.09, 0.05), vertices=12, mjuk=True),      # krage
    ny("cube", "jackaDet", (0.11, -0.14, 0.98), (0.055, 0.004, 0.004)),                     # ficka V
    ny("cube", "jackaDet", (-0.11, -0.14, 0.98), (0.055, 0.004, 0.004)),                    # ficka H
    ny("cylinder", "hud", (0, 0, 1.52), (0.065, 0.065, 0.05), vertices=10, mjuk=True),     # hals
]

# ===== Huvud =====
HUVUD = Vector((0, 0, 1.66))
R = 0.17
kropp += [
    ny("uv_sphere", "hud", HUVUD, (R, R * 0.95, R * 1.08), segments=20, ring_count=12, mjuk=True),
    ny("uv_sphere", "hud", HUVUD + Vector((0, -0.165, -0.02)), (0.025, 0.03, 0.03), segments=8, ring_count=6, mjuk=True),  # näsa
    ny("cube", "mun", HUVUD + Vector((0, -0.158, -0.075)), (0.035, 0.005, 0.006)),        # mun
]
for s in (1, -1):
    x = 0.06 * s
    kropp += [
        ny("uv_sphere", "vit", HUVUD + Vector((x, -0.148, 0.025)), (0.03, 0.015, 0.025), segments=10, ring_count=6, mjuk=True),
        ny("uv_sphere", "svart", HUVUD + Vector((x, -0.162, 0.025)), (0.015, 0.008, 0.016), segments=8, ring_count=6, mjuk=True),
        ny("cube", "har", HUVUD + Vector((x, -0.155, 0.075)), (0.04, 0.008, 0.009), rotation=(0, radians(-12 * s), 0)),  # ögonbryn
        ny("uv_sphere", "hud", HUVUD + Vector((0.172 * s, 0, 0)), (0.025, 0.035, 0.045), segments=8, ring_count=6, mjuk=True),  # öra
        # AirPods: en liten knopp i örat och en pinne som pekar ner
        ny("uv_sphere", "airpods", HUVUD + Vector((0.18 * s, -0.012, -0.005)), (0.02, 0.02, 0.02), segments=8, ring_count=6, mjuk=True),
        ny("cylinder", "airpods", HUVUD + Vector((0.185 * s, -0.018, -0.045)), (0.008, 0.008, 0.035), vertices=8, mjuk=True),
    ]

# ===== Hög fade: kort, mörkare hud på sidorna och håret bara högst upp =====
def bara_toppen(o, zmin, zmax=9, ta_bort_fram=False):
    """Behåll bara en del av ett klot: mellan höjd zmin och zmax (räknat från -1 till 1)."""
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")   # börja utan något markerat
    bpy.ops.object.mode_set(mode="OBJECT")
    for v in o.data.vertices:
        v.select = v.co.z < zmin or v.co.z > zmax or (ta_bort_fram and v.co.y < -0.55)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.mode_set(mode="OBJECT")

HUVUD_SKALA = Vector((R, R * 0.95, R * 1.08))
fade = ny("uv_sphere", "fade", HUVUD, HUVUD_SKALA * 1.02, segments=24, ring_count=16, mjuk=True)
bara_toppen(fade, 0.15, 0.75, ta_bort_fram=True)   # ett band högt upp på sidorna och bak
kropp.append(fade)

har = ny("uv_sphere", "har", HUVUD, HUVUD_SKALA * 1.05, segments=24, ring_count=16, mjuk=True)
bara_toppen(har, 0.6)                              # bara högst upp på huvudet
kropp.append(har)

# Taggar: flest fram och upp, som en spikig topp
TAGGAR = 26
for i in range(TAGGAR):
    v = i * 2.39996                                # gyllene vinkeln = jämnt utspridda
    t = (i + 0.5) / TAGGAR
    lutning = radians(5 + 38 * t ** 0.5)           # mitten pekar rakt upp, kanten lite utåt
    riktning = Vector((sin(lutning) * cos(v), sin(lutning) * sin(v) - 0.25 * sin(lutning), cos(lutning))).normalized()
    plats = HUVUD + Vector((riktning.x * R, riktning.y * R * 0.95, riktning.z * R * 1.08)) * 1.0
    langd = 0.1 + 0.06 * (1 - t)
    rot = Vector((0, 0, 1)).rotation_difference(riktning).to_euler()
    kropp.append(ny("cone", "har", plats + riktning * langd * 0.45, (0.032, 0.032, langd / 2), rotation=rot, vertices=6))

sla_ihop(kropp, "Kropp", (0, 0, 0))

# ===== Armar: svarta jackärmar + händer. Leden sitter i axeln. =====
for s, namn in ((1, "ArmV"), (-1, "ArmH")):
    x = 0.27 * s
    delar = [
        ny("cylinder", "jacka", (x, 0, 1.13), (0.06, 0.06, 0.24), rotation=(0, radians(-6 * s), 0), vertices=12, mjuk=True),
        ny("uv_sphere", "jacka", (x - 0.01 * s, 0, 1.37), (0.075, 0.075, 0.07), segments=12, ring_count=6, mjuk=True),
        ny("cylinder", "jackaDet", (x + 0.025 * s, 0, 0.9), (0.062, 0.062, 0.015), vertices=12, mjuk=True),  # mudd
        ny("uv_sphere", "hud", (x + 0.03 * s, 0, 0.83), (0.05, 0.04, 0.06), segments=10, ring_count=6, mjuk=True),  # hand
    ]
    sla_ihop(delar, namn, (x - 0.01 * s, 0, 1.38))

# ===== Exportera till spelet =====
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=sys.argv[-1], export_format="GLB", use_selection=True,
    export_yup=True, export_apply=True, export_animations=False,
)
import os
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(os.path.abspath(__file__)), "mustafa.blend"))
print("KLAR: Super Mustafa")
