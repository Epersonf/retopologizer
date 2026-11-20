# Retopologia de personagens e formas orgânicas (`tools/retopo`)

O agente faz o que o artista faz no Blender com snap e RetopoFlow: desenha anéis (contornos) em volta dos tubos,
decide quantos vértices cada anel tem, fecha com quads e cola tudo na referência. Nenhum remesh. Exemplo completo:
a Cuca (`projects/stylized-cuca/cuca_*.py`). Peças duras: `retopo-snap-mirror.md`. Teoria: `topologia.md`.

## Carregar (dentro do Blender: worker ou one-shot, ver `blender-automacao.md`)
```python
import sys; sys.path.insert(0, r"C:/Users/epers/Desktop/retopologizer/tools")
import importlib, retopo; importlib.reload(retopo); from retopo import *   # o reload pega edições do código
R = Ref("HiPoly")                 # referência em espaço de mundo; BVH em cache entre chamadas
T = Topo(R)                       # malha nova; Topo(R, start="LowPoly_user") continua a malha do artista
```

## O fluxo
Trabalhe **por partes**, uma rodada e uma entrega por parte (mão, perna, pé, cauda...): `retopo-por-partes.md`.
1. **Plano de topologia** antes de qualquer vértice: partes, contagem de cada anel, onde ficam os polos e quais laços
   passam de uma parte para a outra. A Cuca:
   - tronco em layout de caixa, 20 em volta (por metade: frente 4 colunas, lado 2, costas 4); buraco 2×2 para o
     braço (anel de 8) e buraco no topo para o pescoço (12 em volta);
   - braço de 8 lados com 3 anéis no cotovelo; perna de 12 com 3 no joelho; pescoço de 12;
   - mão: pulso 12 → palma → nós 14 → 3 dedos de 6 (colunas 0, 2, 4) com garras;
   - pé em box rings (topo 3, lados 2, sola 5) → 3 dedos; cauda de 12, um anel em cada vão entre escamas.
2. **Uma parte por arquivo** (`cuca_arm.py`...). Cada uma roda num namespace com `T`, `R` e `L` (laços nomeados:
   `L["wrist"]`, `L["arm_root"]`...) e deixa em `L` o laço de onde a próxima começa: mesma contagem na emenda.
3. **Meia malha** (x ≥ 0) com modificador Mirror (Clipping, Merge 1 mm) enquanto trabalha; costura em x = 0.
4. **Escrever e olhar**: `T.orient(); T.write("Cuca_retopo")`, depois `wire_overlay` da vista que importa, mostrar
   ao usuário, corrigir o que está visivelmente errado. Uma parte por vez, ciclos curtos.
5. **Conferir**: `topo_qa("Cuca_retopo", R, seam_x=0.0)` e depois `qa.md`.

Drivers de exemplo: `cuca_build.py` (malha nova, `PARTS` em ordem) e `cuca_user_build.py` (continua a malha do artista).

## Ferramentas do pacote
| módulo | use para |
|---|---|
| `Ref` | `nearest(p)`, `ray(o, d)`, `hits(o, d)`; `snap(p, n)` = snap to face (com a normal esperada `n` não pula para o vizinho); `exit(c, d)` = onde o raio sai do volume, de dentro; `outer(c, d)` = casco mais externo |
| `curves` | `ring` (laço em volta de um eixo), `arc` (parte de laço; meia volta para o espelho), `line` (n segmentos sobre a superfície), `arcline`, `resample`, `sample` |
| `contour` | `track` (espinha de um tubo: centro, eixo, raio), `centred` (centro do corte), `cring` (anel fechado, igualmente espaçado no corte real), `chalf` (meio anel de x=0 a x=0), `align` (anel sem torção em relação ao anterior), `box_ring` (corte achatado: palma, pé), `at_width` |
| `Topo` | `v`, `vs` (vértices já com snap), `f`, `strip(A, B)` (tira de quads entre anéis), `fan`, `grid(B, Tp, L, R)` (Grid Fill com snap), `old(i)` (vértice do artista pelo índice original), `relax`, `orient`, `chain`, `mirror_x`, `write` |
| `patches` | `solve_spokes` + `poly_patch`: buraco de 3 ou 5 lados fechado com quads em volta de um polo |
| `digits` | `digit(T, R, raiz, p_dentro, ponta)`: dedo, garra ou chifre crescido de um anel par até a ponta, seguindo a curva |
| `qa` | `topo_qa(nome, ref, seam_x)`: buracos, non-manifold, duplicados, winding, faces para dentro, polos, distância |
| `part` | `part_object(low, base, nome)`: só as faces da rodada como objeto próprio; `export_obj(nome, path)`: OBJ dessa parte |

## Medir rápido (fora do Blender)
Exporte a referência uma vez para numpy e corte quantas vezes quiser com `tools/slice_plot.py` (PNG com grade em cm):
```python
import bpy, numpy as np                        # dentro do Blender, uma vez
H = bpy.data.objects["HiPoly"]; me = H.data
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co)
M = np.array(H.matrix_world); W = (co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]).astype(np.float32)
me.calc_loop_triangles(); tri = np.empty(len(me.loop_triangles) * 3, np.int32)
me.loop_triangles.foreach_get("vertices", tri)
np.savez(r"<repo>\projects\<nome>\draft\hi_world.npz", V=W, T=tri.reshape(-1, 3))
```
`python tools/slice_plot.py draft/hi_world.npz draft/renders/sl_z.png z 0.60 0.70 --box -0.2 0.2 -0.1 0.1`
(eixo z: plota x,y; `--low low.npz` desenha a retopo por cima). Os cortes dão centros e larguras dos membros e onde
ficam joelho, cotovelo e pulso.

## Continuar a malha do artista
O ciclo completo (cópia do arquivo atual, isolar a região, imagem, separar a parte, OBJ, integração) está em
`retopo-por-partes.md`. Específico deste pacote:
- `Topo(R, start="LowPoly_user")` parte da malha intocada dele; `T.old(53, 61)` pega vértices pelos índices que
  `wire_overlay` + `label_png` mostram.
- Mantenha as contagens dele nas emendas; limpe só o que impede quads (pares quase duplicados, vértice que viraria
  valência 2: `cuca_fix.py`).

## Padrões que funcionaram (Cuca)
- **Tubo** (braço, perna, pescoço): `track` para a espinha, `cring`/`chalf` em cada estação, `align` com o anel
  anterior, `T.strip` entre anéis. Estações pela forma: deltoide, braço, 3 no cotovelo, antebraço, pulso.
- **Região de 5 lados** (costas + topo do ombro): `poly_patch` com um 5-polo; pontos internos projetados a partir de um
  ponto **dentro** do corpo (`inside=`), para o patch não atravessar a malha.
- **Mão e pé**: box rings (palma, peito do pé); dedos com `digit`: raiz par, um anel de cada lado da base da garra,
  vértice na ponta.
- **Cauda com escamas**: um segmento por escama; meio anel em cada vão (onde a altura dorsal cai), nenhum entre vãos.

## Armadilhas
| sintoma | causa | correção |
|---|---|---|
| vértice pulou para o braço ou a saia vizinha | snap pelo ponto mais próximo | `snap(p, n)` com a normal esperada, ou `exit` a partir do centro |
| anel pega orelha ou chifre no caminho | o raio do centro acerta outra parte | mudar a estação ou o centro (`snap_section.py` tem `despike`) |
| tira torcida entre anéis | anéis começando em ângulos diferentes | `align(P, Q)` |
| patch atravessa o corpo | pontos internos projetados pela normal | projetar de um ponto interno (`inside=`) |
| garra torta | espinha reta da raiz à ponta | `digit` (espinha re-centrada a cada corte) |
| edição no código não pegou | módulo em cache no Blender | `importlib.reload(retopo)` |
| `.blend` abre em EDIT no worker | foi salvo em Edit Mode | `bpy.ops.object.mode_set(mode='OBJECT')` antes |
