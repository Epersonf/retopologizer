# tools/06-rig/autorig — humanoid auto-rig, Mixamo style

```
"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe" -b --factory-startup ^
    --python tools/06-rig/autorig/cli.py -- modelo.fbx saida.fbx [--blend saida.blend] [--name Rig] [--asym] [--textures]
```

- **Input:** .fbx .obj .glb .gltf or .blend. Uses all meshes in the scene; the old armature and animations are discarded.
- **Expected pose:** the model standing on +Z, in T-pose or A-pose, facing -Y. If it faces +Y, it is rotated.
- **Output:**
  - FBX with `mixamorig:*` bones: 65 with 5 fingers, plus whichever fingers exist and a tail chain if there is one.
  - Bone heat weights, with at most 4 per vertex.
  - Prints `AUTORIG_QA: {...}` with bones, digits, tail, unweighted vertices and empty deforming bones.

| file | what it does |
|---|---|
| cli.py | entry point: imports, runs the auto-rig, exports FBX (and .blend), prints the QA |
| rig.py | armature (tools/06-rig/rig_mixamo.py), skin, nearest-bone fallback, empty bone gets half the weight of the nearest ring |
| detect.py | joins the rules: legs, arms, hands, spine, tail; mirrors a missing limb and symmetrizes |
| body.py | height H, symmetry plane, horizontal slices (cached), extremities (head, hands, feet, tail), front ±Y |
| legs.py | hip (crotch + 0.045 H), knee (52.5% hip→ankle), ankle (where the foot widens), toes |
| arms.py | wrist (1st slice after the palm as thin as the forearm), shoulder (vertical slices at the armpit curve), elbow (46.5%) |
| spine.py | Hips, Spine×3 (0.20 / 0.435 / 0.70 up to the neck), Neck, Head (chin), HeadTop (10° forward), clavicles |
| hands.py | fingers: geodesic tips from the wrist, walk back to the palm; thumb = the one that starts much closer to the wrist |
| rings.py | low-poly: finger joints move to vertex rings when a bone would end up without vertices |
| tail.py | tail: walk from the tip to the body, 5 equal bones |
| sections.py, tube.py, geodesic.py | exact mesh slices, walk along a tube, Dijkstra + persistent peaks |
| load.py | mesh in world space (numpy) and test bench cases |

The constants were calibrated against Mixamo skeletons in `projects/autorig-bench`. Mean error of the body
joints: 0.6–0.9% of height on the Mixamo cases (T-pose, bind pose and A-pose); fingers ~0.9%.

Limits:
- Needs a T-pose or A-pose. Arms stuck to the body and "I-pose" do not work.
- Mitten fingers become 1 digit.
- The tail stays on the symmetry plane.
- The rig comes out symmetric (`--asym` keeps each side as found).
