# retopologizer

- Start with `README.md`: rules, way of working, pipeline and which guide in `docs/` to read at each stage.
- Retopology is ALWAYS manual (vertex by vertex with snap). NEVER use QuadriFlow/Remesh/Decimate to generate the
  delivered mesh. Full rules: `docs/00-rules-and-tools/retopology-rules.md`. Workflow: `docs/01-input-and-measurement/workflow-retopology.md`.
- The delivered retopology is quads only: no triangles, no n-gons (`topo_qa(...)["quad_only"]`).
- 150-line limit per file; no Co-Authored-By.
