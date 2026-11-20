# Rigging humanoide (estilo Mixamo)

Dois caminhos, mesma saída: armature com ossos `mixamorig:*`, pesos com no máximo 4 ossos por vértice, FBX.
1. **Auto-rig** (`tools/06-rig/autorig`): acha as juntas pela malha. Tente primeiro.
2. **Juntas à mão** (`tools/06-rig/rig_mixamo.py`): quando o auto-rig não serve (pose ou anatomia fora do padrão).
   Exemplo: `projects/stylized-cuca/cuca_rig.py`.

## Antes de riggar
- Topologia com loops nas articulações (3 no cotovelo e no joelho, um anel por junta de dedo): `docs/02-retopologia/topologia.md`.
- Em pé em +Z, de frente para −Y (esquerda do personagem = +X), em metros, T-pose ou A-pose (testado até braços 40°
  abaixo da horizontal), dedos separados.
- Armature e animações antigas são descartadas pelo auto-rig; as transformações são aplicadas na malha.

## Auto-rig
```
"<blender.exe>" -b --factory-startup --python tools/06-rig/autorig/cli.py -- modelo.fbx saida.fbx [--blend saida.blend] [--name Nome_Rig] [--asym] [--textures]
```
- Entrada .fbx, .obj, .glb, .gltf ou .blend; usa todas as malhas (corpo e roupas); se o modelo olha para +Y, é girado.
- Imprime `AUTORIG_QA: {...}`: ossos, dígitos achados, cauda, vértices sem peso, ossos deformantes vazios.
- Dentro do Blender: `rig, qa = autorig([corpo, roupa], "Nome_Rig")` (`tools/06-rig/autorig/rig.py`).
- Precisão contra esqueletos do Mixamo: juntas do corpo a 0,6–0,9% da altura; dedos ~0,9%. 1–2 s por personagem.
- Limites: braços colados ao corpo ("I-pose") não funcionam; dedos em luva viram 1 dígito; a cauda fica no plano de
  simetria; o rig sai simétrico (`--asym` mantém cada lado como achado). Módulos e calibração: `tools/06-rig/autorig/README.md`.

## Onde ficam as juntas (regras do auto-rig, H = altura)
| junta | posição |
|---|---|
| UpLeg (quadril) | 0,045 H acima da virilha, no centro do corte da coxa |
| Hips | no plano de simetria, 0,028 H acima das juntas do quadril |
| Leg (joelho) | 52,5% do caminho quadril → tornozelo |
| Foot (tornozelo) | onde o pé começa a alargar (1,25× a canela mais fina); ToeBase a 64% do tornozelo à ponta |
| Spine, Spine1, Spine2 | em linha reta, a 0,20 / 0,435 / 0,70 do Hips ao Neck |
| Neck | 0,027 H acima das juntas do ombro |
| Head | no queixo (o corte volta a crescer acima do pescoço); HeadTop_End inclinado 10° para a frente |
| Shoulder (clavícula) | do pescoço em direção ao ombro (x a 0,33 do ombro) |
| Arm (ombro) | onde os cortes verticais começam a subir a curva da axila |
| ForeArm (cotovelo) | 46,5% do ombro ao pulso |
| Hand (pulso) | primeiro corte depois da palma tão fino quanto o antebraço |
| dedos 1–4 | 1 no nó (polegar fundo na palma, perto do pulso), 2 e 3 a 39% e 74% do caminho até a ponta, 4 na ponta |

As juntas ficam no **centro do corte** do membro. Em low-poly, a junta vai para o **anel de vértices** mais próximo:
o osso dobra onde a malha tem loop (`tools/06-rig/autorig/rings.py`).

## Pesos (skin)
- Bone heat do Blender (`ARMATURE_AUTO`), depois, por vértice, os 4 maiores pesos ≥ 0,01, normalizados.
- Vértice que o heat deixou vazio (malha non-manifold, cascas soltas): peso 1 no osso mais próximo.
- Osso curto entre dois anéis que ficou vazio recebe metade do peso do anel mais próximo.
- Ossos de ponta (`*_End`) não deformam.

## Cauda e dedos fora do padrão
- Cadeia `Tail1..Tail5` + `Tail_End` pendurada no Hips: `chain(TAIL, "Hips")`, `sideways=TAIL`.
- A cauda dobra entre segmentos rígidos (Cuca: nos vãos entre escamas, cada escama num osso só).
- Menos dedos: `bones(("Thumb", "Index", "Middle", "Ring"))`; o auto-rig cria só os dedos que achou.

## Rig à mão (`rig_mixamo.py`)
```python
J = {"Hips": (0, -0.02, 0.48), ..., "LeftHand": (...), "LeftHandIndex1": (...)}   # metros, só o lado esquerdo (+X)
J = mirror_left(J)
rig = build("Body", "Nome_Rig", J, bones(dedos) + chain(TAIL, "Hips"), sideways=TAIL)
qa = skin("Body", rig)
export_fbx(path, rig, "Body", textures=False)
```
Meça as juntas na própria low-poly: `retopo.centred` no corte do membro, cotovelo e joelho no anel do meio, pulso no
anel mais fino.

## Conferir
- QA do skin: 0 vértices sem peso e nenhum osso deformante vazio, exceto onde não há malha (a perna que o Saci não tem).
- Pose de teste: dobrar cotovelos, joelhos, ombros, dedos e cauda e renderizar (`projects/autorig-bench/pose_test.py`).
  Olhar volume no cotovelo e no joelho, axila sem rasgo, dedos sem arrastar a palma.

## Export
`export_fbx`: armature + malha selecionadas, sem leaf bones, `FBX_SCALE_UNITS`, `bake_space_transform`, sem animação;
`textures=True` copia as imagens. Godot e onde pôr o FBX no jogo: `docs/05-entrega/entrega.md`.
