# retopologizer

- Comece pelo `README.md`: regras, jeito de trabalhar, pipeline e qual guia de `docs/` ler em cada etapa.
- Retopologia é SEMPRE manual (vértice a vértice com snap). NUNCA usar QuadriFlow/Remesh/Decimate para gerar a
  malha entregue. Regras completas: `docs/00-regras-e-ferramentas/regras-retopologia.md`. Fluxo: `docs/01-entrada-e-medicao/workflow-retopology.md`.
- Retopologia entregue é só quads: nenhum triângulo, nenhum n-gon (`topo_qa(...)["quad_only"]`).
- Limite de 150 linhas por arquivo; sem Co-Authored-By.
