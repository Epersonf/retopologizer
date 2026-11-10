"""Write the lean, committable .blend (no reference mesh, baked images packed).
Run inside Blender (MCP): exec(open(...).read()); make_lean_blend(["chest_base","chest_lid"], "chest_mat", out_path)
Then link the collection into a scene so it opens normally (done here via a headless pass)."""
import bpy, os, subprocess

BLENDER = r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe"
_FIX = ("import bpy\nsc=bpy.context.scene\n"
        "for c in bpy.data.collections:\n"
        "    if c.name not in sc.collection.children: sc.collection.children.link(c)\n"
        "bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, compress=True)\n")


def make_lean_blend(names, mat_name, out_path, collection="LOWPOLY"):
    mat = bpy.data.materials[mat_name]
    imgs = [i for i in bpy.data.images if i.name.startswith("bake_")]
    for i in imgs:
        if i.is_dirty:
            i.save()
        i.pack(); i.use_fake_user = True   # AO is not wired in the material: keep it alive
    objs = [bpy.data.objects[n] for n in names]
    bpy.data.libraries.write(out_path, {bpy.data.collections[collection], *objs, mat, *imgs}, fake_user=True, compress=True)
    fix = out_path + ".fix.py"
    open(fix, "w").write(_FIX)
    subprocess.run([BLENDER, "--background", out_path, "--python", fix], check=True, capture_output=True)
    os.remove(fix)
    return round(os.path.getsize(out_path) / 1e6, 2)
