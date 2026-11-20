# Regras inegociáveis de retopologia

1. **Nunca usar retopologia automática** para gerar a malha entregue: QuadriFlow, Remesh (voxel/quad), Instant
   Meshes, Decimate/Planar como resultado final, shrinkwrap de malha gerada. Erro já cometido na vaca (3117 quads,
   6234 tris, grade uniforme sem intenção) e rejeitado pelo usuário. Não repetir, nem "como primeira passada".
2. **Sempre manual: vértice a vértice com snap** na referência, com espelho quando houver simetria. Peça dura:
   `tools/snap_retopo.py` + `retopo-snap-mirror.md`; personagem ou orgânico: `tools/retopo/` + `retopo-llm.md`.
3. **Boas práticas**: edge loops seguindo a forma (anéis em torno de pernas, pescoço, focinho, olhos, articulações),
   quads em tudo, triângulos só onde ajudam, poucos polos (e fora de áreas que deformam), densidade só onde há
   silhueta/deformação, detalhes pequenos ficam na textura. Teoria completa: `topologia.md`.
4. **Orçamento**: partir de um alvo baixo (vaca: ~2000 tris) e justificar cada loop. Mais que isso exige motivo.
5. Ferramentas automáticas só **medem** (BVH, raycast, fit_report), não geram a malha final.
6. Estátua no modo "como está": se a referência é torta/assimétrica, o usuário corrige depois; não simetrizar
   nem editar a referência sem pedido.
