# Tar en bild av en figur.  Kör: Blender -b fil.blend --python blender/bild.py -- bild.png
import bpy, sys
from mathutils import Vector
s = bpy.context.scene
s.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
s.render.resolution_x, s.render.resolution_y = 900, 900
s.world = s.world or bpy.data.worlds.new("v")
s.world.use_nodes = True
s.world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.75, 0.95, 1)
bpy.ops.object.light_add(type="SUN", location=(2, -3, 4)); bpy.context.active_object.data.energy = 4
bpy.context.active_object.rotation_euler = (0.8, 0.2, 0.5)
bpy.ops.object.light_add(type="AREA", location=(-2, -2, 2)); bpy.context.active_object.data.energy = 150
def kamera(plats, mal, lins):
    bpy.ops.object.camera_add(location=plats)
    k = bpy.context.active_object
    k.rotation_euler = (Vector(mal) - Vector(plats)).to_track_quat("-Z", "Y").to_euler()
    k.data.lens = lins
    s.camera = k
ut = sys.argv[-1]
kamera((1.6, -3.2, 1.4), (0, 0, 0.95), 50); s.render.filepath = ut.replace(".png", "_hel.png"); bpy.ops.render.render(write_still=True)
kamera((0.45, -0.75, 1.75), (0, 0, 1.68), 50); s.render.filepath = ut.replace(".png", "_huvud.png"); bpy.ops.render.render(write_still=True)
