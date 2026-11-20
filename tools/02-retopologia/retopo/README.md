# tools/02-retopologia/retopo — retopologia à mão de personagens, comandada pelo agente

Cada vértice é decidido e colado na referência; nada de remesh. Guia: `docs/02-retopologia/retopo-llm.md`. Exemplo completo:
`projects/stylized-cuca/cuca_*.py`.

```python
import sys; sys.path.insert(0, r"C:/Users/epers/Desktop/retopologizer/tools")
import importlib, retopo; importlib.reload(retopo); from retopo import *
R = Ref("HiPoly"); T = Topo(R)      # ... T.strip(A, B); T.orient(); T.write("Nome_retopo"); topo_qa("Nome_retopo", R)
```

| arquivo | o que faz |
|---|---|
| ref.py | `Ref`: BVH da high em espaço de mundo, em cache entre chamadas: `nearest`, `ray`, `hits`, `snap`, `exit`, `outer` |
| curves.py | laços e linhas sobre a superfície: `ring`, `arc`, `line`, `arcline`, `resample`, `sample` |
| contour.py | contornos no corte real: `cring`, `chalf`, `track` (espinha de tubo), `centred`, `align`, `box_ring`, `at_width` |
| topo.py | `Topo`: construtor bmesh com snap (`v`, `vs`, `f`, `strip`, `fan`, `grid`, `old`, `write`) |
| topo_ops.py | operações do `Topo`: `relax` com snap, `orient` (winding para fora), `chain`, `mirror_x` |
| patches.py | `solve_spokes` + `poly_patch`: buraco de 3 ou 5 lados fechado com quads em volta de um polo |
| digits.py | `digit`, `claw_base`, `spine`: dedo, garra ou chifre crescido de um anel até a ponta |
| qa.py | `topo_qa`: contagens, buracos, non-manifold, duplicados, winding, faces para dentro, polos, distância |
| part.py | `part_object` (só as faces da rodada, como objeto próprio) e `export_obj` (OBJ da parte para o artista); ver `docs/02-retopologia/retopo-por-partes.md` |
| \_\_init\_\_.py | exporta tudo; `importlib.reload(retopo)` recarrega os submódulos na ordem certa |
