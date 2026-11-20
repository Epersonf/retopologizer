"""Cycles on the GPU (Blender, any mode). ALWAYS call before a bake or a Cycles render: on the CPU a 2048 bake takes
many times longer. Only scene.cycles.device = 'GPU' is not enough (above all in background/worker mode): the compute
type has to be set in the preferences and the devices turned on.
  exec(open(r"C:/Users/epers/Desktop/retopologizer/tools/general/cycles_gpu.py").read()); use_gpu()   # -> "OPTIX: RTX ..."
Returns what is in use; "CPU (no GPU found)" when the PC has none (then it says so instead of failing)."""
import bpy


def use_gpu(scene=None, order=("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI")):
    sc = scene or bpy.context.scene; sc.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in order:
        try:
            prefs.compute_device_type = kind
        except TypeError:                       # this build does not know the type
            continue
        prefs.refresh_devices()
        gpus = [d for d in prefs.devices if d.type == kind]
        if gpus:
            for d in prefs.devices:
                d.use = d.type == kind
            sc.cycles.device = 'GPU'
            return kind + ": " + ", ".join(d.name for d in gpus)
    prefs.compute_device_type = 'NONE'; sc.cycles.device = 'CPU'
    return "CPU (no GPU found)"
