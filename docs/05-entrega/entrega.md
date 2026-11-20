# Entrega: FBX, Godot e loja (Fab)

## Prop (estático)
- `wire_and_export(lows, mat_name, outdir, prefix, fbx_name, maps=(...))` (`wire_material.py`): liga os PNGs num
  Principled e exporta **só os low-poly** (seleção). A referência nunca vai para `output/`.
- `finalize(lows, ref, fbx, blend, budget=2000)` (`finalize_export.py`): coleções, UV, material, confere o orçamento,
  salva o `.blend` e exporta.
- PNGs e FBX em `projects/<nome>/output/`; `.blend` de trabalho em `draft/`; o enxuto na raiz do projeto
  (`docs/05-entrega/git-reproducao.md`).
- Nunca `img.reload()` antes de exportar: o que o artista pintou no Blender mora na imagem empacotada do `.blend`, e
  o PNG em disco ainda é o bake antigo (isso já apagou uma edição).

## Personagem (rig)
`export_fbx(path, rig, mesh_name, textures=False)` (`rig_mixamo.py`): armature + malha, sem leaf bones, sem animação.
Como montar o rig: `docs/06-rig/rigging.md`.

## Godot (jogo Braziletto)
- Godot 4.7: `C:\Program Files (x86)\Steam\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe`.
  `--headless --path <projeto> --import` importa; `--script <arquivo>` roda um script (com janela, salva screenshots).
- Personagens vão para `Braziletto/frontend/godot-client/assets/characters/` como `<Nome>.fbx` + `Albedo<Nome>.jpg`
  (rig `<Nome>_Rig`). A Godot importa `mixamorig:` como `mixamorig_`. No jogo: `tools/retarget_fbx.gd` (importa →
  retarget → importa) e `world/human_body.gd` (PATHS, BARE, BODY_BY_MODEL).
- O FBX aponta o material para a imagem ao lado; albedo em JPG 1024 basta para o jogo. Exemplo:
  `projects/stylized-cuca/cuca_rig_export.py`.

## Adereço preso à cabeça no jogo (chapéu, gorro, cabelo, cachimbo)
Um FBX estático pendurado num `BoneAttachment3D` no osso `Head` segue a cabeça na animação. Exemplos: o gorro, o cabelo
e o cachimbo do Saci; o chapéu da Cuca (`projects/hat-hair/hat_to_cuca.py`).
1. **Exportar** (Blender, one-shot no `.blend` com a malha assada): o script carrega o rig do personagem
   (`bpy.data.libraries.load`), põe o adereço na cabeça (escala pela largura da cabeça) e leva os vértices para o
   espaço do osso (`head.inverted() @ colocação`). Mesmas opções do corpo (`FBX_SCALE_UNITS`,
   `bake_space_transform=True`). Saem em `assets/characters/`: `<Modelo>.fbx`, `Albedo<Modelo>.jpg` (o material do FBX
   aponta para ele) e, se houver, `Normal<Modelo>.png` (1024, salvos pelo PIL: a Godot 4.7 não lê o JPEG do Blender 5).
   A colocação é só um ponto de partida: no chapéu da Cuca os eixos do osso não bateram e o usuário girou ~80/−139/−136°
   no editor. Abra o editor e deixe o usuário ajustar; não tente acertar no número.
2. **Registrar no jogo**: `world/body_props.gd`, tabela `SETS`: `"<corpo>": {"models": [...], "placements":
   "res://data/<corpo>_props.json"}`. `HumanCharacter` já chama `BodyProps.attach(skeleton, human.body)`; o material
   é achatado como o do corpo e o `Normal<Modelo>.png` é ligado se existir.
3. **Importar e testar**: `godot --headless --path frontend/godot-client --import`; teste em `test/<corpo>_body_test.gd`
   (adereço no osso `Head`, texturas). Se o teste do corpo conta malhas, desconte as do nó `BodyProps.NODE`.
4. **Ajuste à mão (o usuário)**: abrir o editor com janela, em segundo plano:
   `godot --path frontend/godot-client res://tools/prop_editor.tscn -- --model=<id>` (101 Saci, 137 Cuca; ids em
   `BODY_BY_MODEL`). Clique seleciona, W/E/R move/gira/escala, botão direito orbita, roda dá zoom, "Salvar" (canto
   inferior direito) grava `data/<corpo>_props.json` (posição, rotação em graus e escala no espaço do osso).
5. **Commit no Braziletto** depois que o usuário salvar: FBX + `.import`, texturas, o json, `body_props.gd`, testes.
   Nunca a pasta `.codex/` (configuração local).

## Listagem na loja (Fab)
Gerar no fim, com o material final ligado, em `projects/<nome>/listing/`.
- **Thumbnail**: `render_thumbnail(peças, "listing/thumbnail.jpg", samples=768)` (`render_thumbnail.py`):
  1920×1080 (mínimo do Fab), jpg/png/webp ≤ 3 MB (sai ~0,2 MB), Cycles com estúdio (AgX, softbox quente, fill frio,
  2 rim, spot no chão brilhante, 85 mm, DOF leve), ~1 min a 768 amostras. Testar com `samples=64`, ajustar `cam` e
  `look_at` à escala e **abrir o arquivo** antes de subir (enquadramento, nada cortado, textura final).
- **description.md**: título, o que vem, tabela técnica (tris, malhas, UV, tamanho, pivô, formato), checks de QA,
  limitações (ex.: só albedo) e aviso de IA generativa (conferir as regras atuais do Fab). Exemplo:
  `projects/stylized-chest/listing/description.md`.
- Só o albedo: `wire_and_export(..., maps=("basecolor",))`.
