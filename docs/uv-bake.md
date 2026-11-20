# UV, mapas PBR e bake (alta → baixa)

Pré-requisito: malha aprovada no QA (`qa.md`). Depois da UV não rode builders de novo (recriam a malha e a UV some):
só mova vértices.

## UV
- **Um atlas 0–1 para todas as peças do asset**: um material, uma textura por mapa, um draw call.
- **Zero overlap**: o bake escreve um texel por lugar; UV espelhada ou empilhada não passa no `qa_uv`.
- **Costuras escondidas** (embaixo, atrás, por dentro, em quinas) e **toda quina dura com costura**, senão o normal
  map marca a quina.
- **Densidade de texel igual** entre as peças; ilhas retas quando der (menos desperdício e serrilhado).
- **Gap ≥ 8 px a 2048** entre ilhas, para mip-maps e a margem do bake não vazarem para a vizinha.
- `unwrap_atlas(nomes, margin=0.012, angle=66)` (`qa_uv.py`: smart project + densidade igual + pack) serve para
  destravar e medir; 89° dobrou as ilhas dos arcos. Em geral o usuário faz a UV à mão: respeite a dele.
- Conferir: `qa_uv(nomes, size=2048, min_gap_px=8)["pass"]`.

## Mapas PBR
| mapa | espaço de cor | guarda |
|---|---|---|
| basecolor | sRGB | cor, sem luz nem sombra |
| normal (tangente) | Non-Color | relevo fino da high; Blender e Godot usam OpenGL (Y+), Unreal usa DirectX (inverter o verde) |
| roughness | Non-Color | 0 liso e brilhante, 1 fosco |
| metallic | Non-Color | 0 dielétrico, 1 metal (quase sempre um ou outro) |
| AO | Non-Color | oclusão das cavidades |

No glTF, roughness e metallic vêm num mapa só (G = roughness, B = metallic; R = AO no ORM). O material da high
precisa estar ligado assim (albedo, metal-rough, normal) para o bake ler os canais.

## Bake robusto — Cycles GPU (`bake_robust.py`)
> **Sempre na GPU.** Antes de qualquer bake ou render Cycles: `use_gpu()` (`tools/cycles_gpu.py`; `bake_robust`,
> `bake_all` e `render_thumbnail` já chamam e o relatório traz `device`). Só `scene.cycles.device = 'GPU'` não basta,
> principalmente no worker/background: é preciso o tipo (OPTIX/CUDA/HIP...) nas preferências e os dispositivos
> ligados. Na CPU um bake 2048 leva muitas vezes mais. Se voltar `CPU (no GPU found)`, avise o usuário.

`r = bake_robust(["chest_base", "chest_lid"], "REFERENCE", outdir, "chest")`
1. **Um bake só para todas as peças, numa imagem só**: o script junta cópias das peças (mundo, UV intacta) num objeto
   ativo temporário e faz selected-to-active. Assar peça por peça na mesma imagem apagou a primeira.
2. **Extrusão e max ray**: normal invertida (azul ≈ 0) = o raio nasce dentro da referência (extrusão menor que o
   desvio low↔high). Regra: extrusão ≈ 3–4× o p95 do `compare_mesh`. Baú: 0.03 → 31% invertido; 0.10/0.20 → 6%.
3. **Validação por texel**: assa também onde o raio bateu e se foi backface. Válido = achou hit + face da frente + hit
   a < `max_dist` (padrão 0,05 m) da low. Inválidos são re-assados com o próximo par extrusão/ray do `schedule`
   (0.10/0.20 → 0.05/0.10 → 0.03/0.06 → 0.20/0.40 → 0.02/0.04) e o resto vira inpaint dentro da mesma ilha UV
   (`bake_inpaint.py`, um clone automático); ilhas dilatadas na margem.
4. **Relatório**: `worst_unbaked_faces` e `poor_fit_faces_mm` (faces da low longe da ref: mover vértices), mais um mapa
   de máscara opcional (verde ok, amarelo recuperado, vermelho inpaint). Baú: 1,27% inválido no 1º passe → 0,43%.
5. Mapas: basecolor, normal, roughness, metallic (via emissão do canal B), AO. 2048 px, margem 8 px (EXTEND, escala
   com o tamanho). `high_mat=` é o nome do material da high (padrão `"Material.001"`).
6. **Checar**: % de faces pretas no basecolor por peça (< 3%) e um render workbench TEXTURE.

Bake simples: `bake_all(lows, high, outdir, prefix, size=2048, extrusion=0.03, max_ray=0.06, cage_dist=None)`
(`bake_maps.py`). **Cage** só se o padrão falhar em quinas duras: duplicar a low e `Alt+S` (empurrar pelas normais)
até cobrir toda a referência; `cage_dist=<m>` faz isso por script. Cage fino (0.02) não resolve: precisa cobrir o
maior desvio.

## Artefatos: o que olhar
| sintoma | causa | correção |
|---|---|---|
| faces pretas, normal invertida | extrusão menor que o desvio | extrusão 3–4× p95, ou cage |
| quadrados pretos no Cycles | faces coplanares (z-fight) | `qa_zfight`, afastar 2–4 mm |
| borrão em placas e presilhas | peça 2–3 cm além da ref (raio longe) | mover os vértices até a superfície |
| "No valid selected objects" | referência escondida (`hide_set`) ou travada (`hide_select`) | visível e selecionável no bake (`bake_robust` já faz e restaura) |
| bake lento (minutos para 2048) | Cycles na CPU | `use_gpu()` antes; conferir `device` no relatório |
| costura marcada no normal map | quina dura sem costura de UV | costura na quina |

## Ajustar depois da UV ou do bake (sem quebrar a UV)
- Partir de um backup em `draft/backups/`; mudar só posições de vértices (mesma topologia).
- Snap de todos os vértices ao ponto mais próximo amassou placas pequenas: medir os perfis da ref por região e
  deslocar por região.
- Distância alta nas quinas = quina de caixa contra bisel arredondado da ref: esperado.
- Depois: `qa_all`, rebake, conferir de novo.
