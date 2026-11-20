# Fiber cards (cabelo em planos com textura de fios)

Alternativa ao cabelo em malha: planos simples com uma textura de fios (cor + normal + alfa). A face de trás pode aparecer; no jogo o material liga
*backface / render both sides*. Retopologia manual não se aplica: o cabelo vira planos encaixados na cabeça (projeto `projects/cuca-hair`).

## Gerar a folha de cards (`tools/07-fibercards/`)
O gerador é uma porta do app `epersonf/fiber-card-gen` (commit `eccffc9`); o render é do Blender (Cycles, ortográfica, fundo transparente).

    python -I tools/07-fibercards/fibercards.py --out DIR --tag blonde --blonde [--seed 1] [--samples 32] [--lighting soft|flat] [--blend f.blend] [--set chave=valor ...]

- `fc_params.py`: estado do app (mesmas chaves do JSON "copy state", então um preset cola no app e volta) e o preset `BLONDE`.
- `fc_strands.py`: fios (mulberry32, disco de spawn elíptico inclinado, spread/clump, curl, frizz, Catmull-Rom centrípeta). O ruído do frizz é de valor; o app usa open-simplex.
- `fc_blender.py`: cada fio vira um tubo de 8 lados (raio e cor por anel: gradiente raiz→ponta), uma malha por card; câmera ortográfica olhando −z.
- `fibercards.py`: monta a folha (grade de `cardsPerSheet` cards, do mais ralo ao mais denso pela curva de quantidade) e chama o Blender. Saída: `<tag>_color.png`,
  `<tag>_normal.png` (RGBA, `baseSize` px), `<tag>_preview.png`, `<tag>_preset.json`. 12 cards 2048 px: cerca de 8 s na GPU.
- Cor `soft`: sol de (0,10,5) + mundo cinza, Principled com glossiness/sheen do preset; `flat`: albedo puro. Normal: normal de vista × 0.5 + 0.5, espaço cru (sem sRGB).
- Layout do card como no app: x na largura (0 no meio da célula), y para cima a partir da borda de baixo, raiz no topo, fios descendo.
- Variação de brilho de 5 % por fio é extensão desta porta.
