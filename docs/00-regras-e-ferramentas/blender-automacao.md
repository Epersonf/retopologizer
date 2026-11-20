# Rodar código no Blender

Blender 5.3: `C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe` (abaixo, `B`).

## Três jeitos
| jeito | quando | como |
|---|---|---|
| MCP do usuário (porta 9876) | ler a cena que o usuário tem aberta | `python tools/general/blender_rpc.py script.py` ou `-c "código"` |
| worker headless (porta 9877) | construir, renderizar e assar num `.blend` de trabalho | `"$B" -b <cópia.blend> --python tools/general/blender_worker.py -- 9877` em segundo plano, depois `python tools/general/blender_rpc.py --port 9877 script.py` |
| one-shot | script que abre os próprios arquivos, ou sem worker no ar | `"$B" -b --factory-startup --python tools/general/blender_once.py -- script.py`; o resultado sai na linha `RESULT_JSON: {...}` |

As CLIs rodam direto: `"$B" -b --factory-startup --python tools/06-rig/autorig/cli.py -- modelo.fbx saida.fbx`.

- O Blender do usuário é **só leitura**: ele trabalha ao mesmo tempo (às vezes noutra instância). Construção e render
  vão para uma **cópia** do `.blend` dele, no worker.
- O worker guarda estado entre chamadas (ex.: o BVH em cache de `retopo.Ref`); `{"type": "quit"}` encerra. Ele morre
  no limite de tempo do shell em segundo plano (2 h); depois disso use one-shot ou suba outro.
- `blender_rpc` espera até 2 h pela resposta (bake e render longos cabem).

## Contrato de um script
- O script define `result` (um dict serializável em JSON); o stdout volta junto.
- Ferramentas soltas: `exec(open(r"C:\Users\epers\Desktop\retopologizer\tools\03-qa\qa_all.py", encoding="utf-8").read())`.
  Elas dividem o namespace: não reuse nomes globais entre ferramentas e scripts (ex.: `T`).
- Pacotes (`retopo`, `autorig`): `sys.path.insert(0, r"...\tools")`, `import` e `importlib.reload` depois de editar.
- Cada chamada ao socket tem namespace novo: `import bpy` em todas, sem contar com variáveis da anterior.

## Armadilhas
- **Nunca Edit Mode na referência** (500k+ tris trava o Blender): ler com `foreach_get` + numpy, BVH e raycast.
- **Nunca `raise SystemExit`** pelo MCP: fecha o Blender do usuário e perde o que não foi salvo.
- O MCP bloqueia `bpy.ops.wm.read_factory_settings`: limpe a cena removendo objetos.
- Arquivo salvo em Edit Mode abre em EDIT no worker: `bpy.ops.object.mode_set(mode='OBJECT')` antes de mexer.
- GLB importado vem com `matrix_world` girada (+90° X) e `BVHTree.FromObject` é local: converta para mundo (`Ref` e
  `ref_part` já fazem).
- Referência escondida com `hide_set` faz o bake falhar ("No valid selected objects").
- Arquivos sempre em UTF-8 (`open(..., encoding="utf-8")`): o padrão do Windows é cp1252.

## Mostrar ao usuário
Renderizar no worker (`render_views`, `wire_overlay`, `render_thumbnail`), salvar em `draft/renders/`, abrir a imagem
para conferir e só então mostrar. Uma imagem cedo vale mais que um relatório longo.
