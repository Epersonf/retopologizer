# Retopologia: qual método para qual modelo

Etapa 2 do pipeline. Aqui a escolha é **por parte**, não pelo modelo inteiro. Regras que valem para todos os métodos
(`docs/00-regras-e-ferramentas/regras-retopologia.md`): retopo é sempre manual, vértice a vértice com snap na ref;
só quads; ferramenta automática mede e confere, não gera a malha; a ref nunca é editada.

## 1. Classifique a parte
| a parte é... | método | guia | exemplo no repo |
|---|---|---|---|
| peça dura com cantos e detalhe (baú, tampa, caixa, alça) | anéis por ângulo + espelho | `retopo-snap-mirror.md` | `projects/stylized-chest` |
| prop simples (caixa, tubo, prisma) | `mesh_lib` (caixa, loft, sweep) | `tools/README.md` | `projects/stylized-chest` |
| tronco, tubo ou árvore em volta de um eixo | anéis em volta do eixo com snap | `retopo-snap-mirror.md` | `projects/stylized-tree` |
| personagem ou orgânico (corpo, mão, garras, cauda, cabeça) | pacote `tools/02-retopologia/retopo` (anéis, patches, dedos) | `retopo-llm.md` | `projects/stylized-cuca` |
| pano com abertura e eixo torto (gorro, capuz, manga, ponta caída) | anéis por campo de Laplace | `retopo-casca-campo.md` | `projects/hat-hair` |
| estátua torta ou assimétrica | "como está", partes em cascas separadas, sem simetrizar | `retopo-llm.md` | `projects/stylized-cow` |

Dúvida entre dois: cabe numa **casca com abertura**? Laplace. Tem **cantos duros**? Snap + espelho. **Deforma** ou tem
braços/pernas? `tools/02-retopologia/retopo`.

## 2. Decida loops, polos e contagens
Antes de qualquer vértice: `topologia.md` (loops nas juntas, polos longe de dobras, orçamento). Cada loop precisa de
motivo: silhueta, deformação ou bake.

## 3. Se o todo está difícil, divida
`retopo-por-partes.md`: uma parte por rodada, entregue em OBJ e integrada pelo usuário antes da próxima.
- Uma parte é uma forma com fronteira clara; a fronteira é um **anel** com contagem par e igual dos dois lados.
- Ordem: do tronco para as pontas; extras (cauda, orelhas) e costuras por último.
- Cada parte escolhe o seu método na tabela acima (ex.: corpo com `tools/02-retopologia/retopo`, chapéu por campo, fivela por snap).
- Se um método falhar na mesma parte duas vezes, troque de método ou divida mais, em vez de ajustar parâmetros.

## 4. Antes de entregar a parte
Mostrar uma vista (`wire_overlay`), conferir erro em mm (`fit_report`) e `topo_qa(...)["quad_only"]`. Depois, etapa 3
(`docs/03-qa/qa.md`).

## 5. Registrar o que descobriu
Método novo que funcionou numa peça vira guia próprio nesta pasta (foi assim com `retopo-casca-campo.md`, do chapéu):
quando usar, o processo em passos, números do exemplo, armadilhas com sintoma e correção, como adaptar a outra peça.
Depois adicione a linha na tabela da seção 1 e em `docs/README.md`.
