# Regras inegociáveis de retopologia

1. **Nunca usar retopologia automática** para gerar a malha entregue: QuadriFlow, Remesh (voxel/quad), Instant
   Meshes, Decimate/Planar como resultado final, shrinkwrap de malha gerada. Erro já cometido na vaca (3117 quads,
   6234 tris, grade uniforme sem intenção) e rejeitado pelo usuário. Não repetir, nem "como primeira passada".
2. **Sempre manual: vértice a vértice com snap** na referência, com espelho quando houver simetria. Peça dura:
   `tools/02-retopologia/snap_retopo.py` + `docs/02-retopologia/retopo-snap-mirror.md`; personagem ou orgânico: `tools/02-retopologia/retopo/` + `docs/02-retopologia/retopo-llm.md`.
3. **Só quads**: a malha entregue tem 100% quads, **nenhum triângulo e nenhum n-gon** (`topo_qa(...)["quad_only"]`
   tem que ser `True`). Ponta de cone vira polo com quads em volta; contorno ímpar se resolve mudando contagens, não
   com triângulo (`docs/02-retopologia/topologia.md`). A engine triangula na importação; isso não é motivo para entregar tris.
4. **Boas práticas**: edge loops seguindo a forma (anéis em torno de pernas, pescoço, focinho, olhos, articulações),
   poucos polos (e fora de áreas que deformam), densidade só onde há silhueta/deformação, detalhes pequenos ficam na
   textura. Teoria completa: `docs/02-retopologia/topologia.md`.
5. **Orçamento**: partir de um alvo baixo (vaca: ~2000 tris depois de triangular, ~1000 quads) e justificar cada loop.
6. Ferramentas automáticas só **medem** (BVH, raycast, fit_report), não geram a malha final.
7. Estátua no modo "como está": se a referência é torta/assimétrica, o usuário corrige depois; não simetrizar
   nem editar a referência sem pedido.
