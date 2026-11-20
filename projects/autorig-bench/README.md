# autorig-bench — calibração e teste do tools/06-rig/autorig

Casos: `male`, `female` (corpos base do Mixamo na pose da take), `male_bind`, `female_bind` (pose de bind + esqueleto
de rest), `saci`, `cuca` (rigs feitos à mão), `female_apose` (braços 40° para baixo). `input/` e `output/` são gerados
(fora do git).

| arquivo | para quê |
|---|---|
| prep_cases.py | `input/<caso>.blend` (só a malha "Body") e `<caso>_gt.json` (juntas de referência) |
| make_apose.py | caso `female_apose`, a partir do rig automático da `female` |
| measure.py | perfil horizontal cru, caminhada do braço e pontas geodésicas (calibração inicial) |
| evaluate.py | detector nos 7 casos → `output/eval.json`, erro médio por grupo (corpo, dedos, cauda) |
| draw.py | `output/autorig_bench.png`: esqueleto automático (vermelho) sobre o de referência (verde) |
| fingers.py | dedos e cauda: automático × referência, junta por junta |
| pose_test.py + pose_sheet.py | deformação numa pose difícil → `output/pose_test.png` (precisa de `output/rigged/<caso>.blend` do cli) |

```
B="C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe"
"$B" -b --factory-startup --python tools/general/blender_once.py -- projects/autorig-bench/evaluate.py && python projects/autorig-bench/draw.py
"$B" -b --factory-startup --python tools/06-rig/autorig/cli.py -- projects/autorig-bench/input/cuca.blend out.fbx --blend out.blend
```
