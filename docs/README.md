# docs: índice por etapa do workflow

Uma pasta por etapa, na ordem em que um projeto avança; cada guia aponta para o próximo. Entrada geral: `../README.md`.
Caminhos nos guias: sempre `docs/<pasta>/<arquivo>.md`, a partir da raiz do repo.

| pasta (etapa do pipeline) | arquivo | leia quando |
|---|---|---|
| 00-regras-e-ferramentas (sempre) | regras-retopologia.md | antes de criar qualquer malha |
| | blender-automacao.md | antes de rodar código no Blender: MCP, worker, one-shot, armadilhas |
| 01-entrada-e-medicao (0 e 1) | workflow-retopology.md | ao começar: pastas, medir a referência, ordem das etapas, conferir a forma |
| 02-retopologia (2 e 3) | README.md | escolher o método certo para cada tipo de parte |
| | topologia.md | decidir loops, polos, contagens e orçamento (teoria do artista) |
| | retopo-por-partes.md | dividir o modelo, uma rodada por parte, entregar e integrar |
| | retopo-snap-mirror.md | peça dura ou prop: anéis por ângulo + espelho (tampa do baú) |
| | retopo-llm.md | personagem ou orgânico com o pacote `tools/02-retopologia/retopo` (Cuca) |
| | retopo-casca-campo.md | pano com abertura (gorro, capuz, manga): anéis por campo de Laplace |
| | retopo-tubos-cabelo.md | madeixas/tubos fundidos: detector de cachos + tubo por madeixa (tentativa, com problemas conhecidos) |
| 03-qa (4) | qa.md | conferir a malha antes de UV, bake e export |
| 04-uv-bake (5 e 6) | uv-bake.md | UV, mapas PBR, bake alta para baixa, artefatos |
| 05-entrega (7 e 9) | entrega.md | FBX, Godot (jogo Braziletto), adereço preso à cabeça + editor, thumbnail e loja Fab |
| | git-reproducao.md | o que commitar, regenerar `output/`, GLBs pesados |
| 06-rig (8) | rigging.md | auto-rig humanoide, rig à mão, pesos, cauda |
