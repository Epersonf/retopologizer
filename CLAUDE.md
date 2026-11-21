# retopologizer

- Start with `README.md`: rules, way of working, pipeline and which guide in `docs/` to read at each stage.
- Retopology is ALWAYS manual (vertex by vertex with snap). NEVER use QuadriFlow/Remesh/Decimate to generate the
  delivered mesh. Full rules: `docs/00-rules-and-tools/retopology-rules.md`. Workflow: `docs/01-input-and-measurement/workflow-retopology.md`.
- The delivered retopology is quads only: no triangles, no n-gons (`topo_qa(...)["quad_only"]`).
- "Retopologize X" = the whole pipeline up to delivery (faithful quads, UV with no overlap, bake, QA): read `README.md`
  "Definition of done" and do not say "done" before it holds. Stopping at the mesh or at an OBJ is only a checkpoint.
- Read the guide of EVERY stage you will reach (`docs/02-retopology`, `03-qa`, `04-uv-bake`, `05-delivery`) before starting,
  not when the user complains. Run the `tools/03-qa/qa.py` battery and `fit_report`; never accept a part that reads as a "mass".
- New model with no high-poly (nothing to bake): paint a good texture in TextureCraft, and ask the user the style
  (look, palette, materials, references) BEFORE painting (`docs/04-uv-bake/uv-bake.md`).
- "From scratch / without the manual" does not turn these rules off: ask what exactly to skip.
- 150-line limit per file; no Co-Authored-By.
