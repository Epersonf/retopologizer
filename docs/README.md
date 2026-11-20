# docs — índice

Guias curtos, um assunto por arquivo; cada um aponta para o próximo. Entrada geral: `../README.md`.
Ordem de um projeto: workflow → topologia → retopo por partes → qa → uv-bake → entrega → rigging → git.

| arquivo | leia quando |
|---|---|
| regras-retopologia.md | sempre, antes de criar qualquer malha |
| blender-automacao.md | antes de rodar código no Blender: MCP, worker, one-shot, armadilhas |
| workflow-retopology.md | ao começar um projeto: pastas, medir a referência, ordem das etapas, conferir a forma |
| topologia.md | ao decidir loops, polos, contagens e orçamento (teoria do artista) |
| retopo-por-partes.md | sempre que for retopologizar: dividir em partes, uma rodada por parte, entregar e integrar |
| retopo-snap-mirror.md | retopo de peça dura ou prop com detalhe: anéis por ângulo + espelho (tampa do baú) |
| retopo-llm.md | retopo de personagem ou forma orgânica com o pacote `tools/retopo` (Cuca) |
| retopo-casca-campo.md | retopo de peça de pano com abertura (gorro, capuz, manga): anéis por campo de Laplace |
| qa.md | para conferir a malha antes de UV, bake e export |
| uv-bake.md | UV, mapas PBR, bake alta → baixa, artefatos |
| entrega.md | FBX, Godot (jogo Braziletto), thumbnail e descrição da loja Fab |
| rigging.md | auto-rig humanoide, rig à mão, pesos, cauda |
| git-reproducao.md | o que commitar, regenerar `output/`, GLBs pesados |
