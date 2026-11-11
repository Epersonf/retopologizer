# Stylized Treasure Chest — Low Poly, Hand-Painted, Game-Ready

A clean, game-ready **stylized treasure chest** with an openable lid. Only **813 triangles** and a single **2048×2048 hand-painted albedo** texture: one material, one draw call, drop-in for mobile, VR and stylized PC/console projects.

## What you get
- `stylized-chest.fbx` — 2 meshes: `chest_base` and `chest_lid`
- `chest_basecolor.png` — 2048×2048 albedo (sRGB), hand-painted look with the lighting baked into the paint
- 1 material (`chest_mat`) using the albedo only

## Technical details
| | |
|---|---|
| Triangles | **813** total (base 473 + lid 340) |
| Meshes | 2 (base + lid, separate so you can animate the lid) |
| Materials | 1 |
| Textures | 1 × 2048×2048 PNG (albedo) |
| UVs | Single non-overlapping atlas (UV0), 8 px padding, all UVs inside 0–1 |
| Size | about 0.69 m wide × 0.71 m deep, 0.80 m tall with the lid open at 50° |
| Pivot | Lid pivot sits on the hinge; rotate the lid on its local X axis (open pose is -50°) |
| Format | FBX, Y-up, -Z forward |

## Quality checks
- No exposed back faces (checked from every direction, interior included)
- No overlapping UVs and no coplanar overlapping faces (no z-fighting)
- Clean, closed geometry with consistent normals
- Bake artifacts detected and repaired before painting

## Good to know
- Albedo only: there are no normal, roughness, metallic or AO maps. The painted detail is in the albedo, so it looks right with simple unlit or lightly lit stylized shaders. Add your own roughness/metallic values in the engine if you need them.
- Lid and base are separate objects; the chest is shown open in the previews, and you can close it by setting the lid rotation to 0.
- Interior of the base and lid is modeled and textured.

## AI disclosure
The shape was started from an AI-generated mesh and then fully **retopologized by hand-guided workflow** into the low-poly meshes you get here; the texture was baked and then painted over by the author. (Check this wording against the current Fab generative-AI disclosure rules before publishing and tick the matching option on the listing.)

## Tags
chest, treasure, stylized, low poly, game ready, hand painted, prop, fantasy, loot, RPG, medieval, mobile, VR
