# Humanoid rigging (Mixamo style)

Two paths, same output: armature with `mixamorig:*` bones, weights with at most 4 bones per vertex, FBX.
1. **Auto-rig** (`tools/06-rig/autorig`): finds the joints from the mesh. Try it first.
2. **Joints by hand** (`tools/06-rig/rig_mixamo.py`): when the auto-rig does not fit (non-standard pose or anatomy).
   Example: `examples/cuca-rig/cuca_rig.py`.

## Before rigging
- Topology with loops at the joints (3 at the elbow and knee, one ring per finger joint): `docs/02-retopology/topology.md`.
- Standing on +Z, facing −Y (character's left = +X), in meters, T-pose or A-pose (tested down to arms 40°
  below horizontal), fingers separated.
- Old armatures and animations are discarded by the auto-rig; transforms are applied to the mesh.

## Auto-rig
```
"<blender.exe>" -b --factory-startup --python tools/06-rig/autorig/cli.py -- modelo.fbx saida.fbx [--blend saida.blend] [--name Nome_Rig] [--asym] [--textures]
```
- Input .fbx, .obj, .glb, .gltf or .blend; uses all meshes (body and clothes); if the model faces +Y, it is rotated.
- Prints `AUTORIG_QA: {...}`: bones, digits found, tail, unweighted vertices, empty deforming bones.
- Inside Blender: `rig, qa = autorig([corpo, roupa], "Nome_Rig")` (`tools/06-rig/autorig/rig.py`).
- Accuracy against Mixamo skeletons: body joints within 0.6–0.9% of height; fingers ~0.9%. 1–2 s per character.
- Limits: arms stuck to the body ("I-pose") do not work; mitten fingers become 1 digit; the tail stays on the
  symmetry plane; the rig comes out symmetric (`--asym` keeps each side as found). Modules and calibration: `tools/06-rig/autorig/README.md`.

## Where the joints go (auto-rig rules, H = height)
| joint | position |
|---|---|
| UpLeg (hip) | 0.045 H above the crotch, at the center of the thigh cross-section |
| Hips | on the symmetry plane, 0.028 H above the hip joints |
| Leg (knee) | 52.5% of the way hip → ankle |
| Foot (ankle) | where the foot starts to widen (1.25× the thinnest shin); ToeBase at 64% from the ankle to the tip |
| Spine, Spine1, Spine2 | in a straight line, at 0.20 / 0.435 / 0.70 from Hips to Neck |
| Neck | 0.027 H above the shoulder joints |
| Head | at the chin (the cross-section grows again above the neck); HeadTop_End tilted 10° forward |
| Shoulder (clavicle) | from the neck toward the shoulder (x at 0.33 of the shoulder) |
| Arm (shoulder) | where the vertical slices start to climb the armpit curve |
| ForeArm (elbow) | 46.5% from the shoulder to the wrist |
| Hand (wrist) | first slice after the palm as thin as the forearm |
| fingers 1–4 | 1 at the knuckle (thumb deep in the palm, near the wrist), 2 and 3 at 39% and 74% of the way to the tip, 4 at the tip |

The joints sit at the **center of the cross-section** of the limb. In low-poly, the joint goes to the nearest **vertex ring**:
the bone bends where the mesh has a loop (`tools/06-rig/autorig/rings.py`).

## Weights (skin)
- Blender's bone heat (`ARMATURE_AUTO`), then, per vertex, the 4 largest weights ≥ 0.01, normalized.
- Vertex the heat left empty (non-manifold mesh, loose shells): weight 1 on the nearest bone.
- A short bone between two rings that ended up empty gets half the weight of the nearest ring.
- Tip bones (`*_End`) do not deform.

## Non-standard tail and fingers
- Chain `Tail1..Tail5` + `Tail_End` hanging from Hips: `chain(TAIL, "Hips")`, `sideways=TAIL`.
- The tail bends between rigid segments (Cuca: in the gaps between scales, each scale on a single bone).
- Fewer fingers: `bones(("Thumb", "Index", "Middle", "Ring"))`; the auto-rig creates only the fingers it found.

## Hand rig (`rig_mixamo.py`)
```python
J = {"Hips": (0, -0.02, 0.48), ..., "LeftHand": (...), "LeftHandIndex1": (...)}   # meters, left side only (+X)
J = mirror_left(J)
rig = build("Body", "Nome_Rig", J, bones(dedos) + chain(TAIL, "Hips"), sideways=TAIL)
qa = skin("Body", rig)
export_fbx(path, rig, "Body", textures=False)
```
Measure the joints on the low-poly itself: `retopo.centred` on the limb cross-section, elbow and knee at the middle ring, wrist at the
thinnest ring.

## Checking
- Skin QA: 0 unweighted vertices and no empty deforming bone, except where there is no mesh (the leg the Saci does not have).
- Test pose: bend elbows, knees, shoulders, fingers and tail and render (`examples/autorig-bench/pose_test.py`).
  Look for volume at the elbow and knee, armpit without tearing, fingers not dragging the palm.

## Export
`export_fbx`: selected armature + mesh, no leaf bones, `FBX_SCALE_UNITS`, `bake_space_transform`, no animation;
`textures=True` copies the images. Godot and where to put the FBX in the game: `docs/05-delivery/delivery.md`.
