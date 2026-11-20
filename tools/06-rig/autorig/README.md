# tools/06-rig/autorig — auto-rig humanoide estilo Mixamo

```
"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe" -b --factory-startup ^
    --python tools/06-rig/autorig/cli.py -- modelo.fbx saida.fbx [--blend saida.blend] [--name Rig] [--asym] [--textures]
```

- **Entrada:** .fbx .obj .glb .gltf ou .blend. Usa todas as malhas da cena; a armature antiga e as animações são descartadas.
- **Pose esperada:** o modelo em pé em +Z, em T-pose ou A-pose, de frente para -Y. Se estiver de frente para +Y, é girado.
- **Saída:**
  - FBX com ossos `mixamorig:*`: 65 com 5 dedos, mais os dedos que existirem e uma cadeia de cauda se houver.
  - Pesos por bone heat, com no máximo 4 por vértice.
  - Imprime `AUTORIG_QA: {...}` com ossos, dígitos, cauda, vértices sem peso e ossos deformantes vazios.

| arquivo | o que faz |
|---|---|
| cli.py | entrada: importa, roda o auto-rig, exporta FBX (e .blend), imprime o QA |
| rig.py | armature (tools/06-rig/rig_mixamo.py), skin, fallback por osso mais próximo, osso vazio recebe metade do anel mais próximo |
| detect.py | junta as regras: pernas, braços, mãos, coluna, cauda; espelha membro que falta e simetriza |
| body.py | altura H, plano de simetria, cortes horizontais (cache), pontas (cabeça, mãos, pés, cauda), frente ±Y |
| legs.py | quadril (virilha + 0,045 H), joelho (52,5% quadril→tornozelo), tornozelo (onde o pé alarga), dedos do pé |
| arms.py | pulso (1ª seção depois da palma tão fina quanto o antebraço), ombro (cortes verticais na curva da axila), cotovelo (46,5%) |
| spine.py | Hips, Spine×3 (0,20 / 0,435 / 0,70 até o pescoço), Neck, Head (queixo), HeadTop (10° p/ frente), clavículas |
| hands.py | dedos: pontas geodésicas a partir do pulso, caminhada até a palma; polegar = o que nasce bem mais perto do pulso |
| rings.py | low-poly: juntas dos dedos vão para os anéis de vértices quando um osso ficaria sem vértices |
| tail.py | cauda: caminhada da ponta até o corpo, 5 ossos iguais |
| sections.py, tube.py, geodesic.py | cortes exatos da malha, caminhada num tubo, Dijkstra + picos persistentes |
| load.py | malha em espaço de mundo (numpy) e casos do banco de teste |

As constantes foram calibradas contra esqueletos do Mixamo em `projects/autorig-bench`. Erro médio das juntas do
corpo: 0,6–0,9% da altura nos casos do Mixamo (T-pose, pose de bind e A-pose); dedos ~0,9%.

Limites:
- Precisa de T-pose ou A-pose. Braços colados no corpo e "I-pose" não funcionam.
- Dedos em luva (mitten) viram 1 dígito.
- A cauda fica no plano de simetria.
- O rig sai simétrico (`--asym` mantém cada lado como foi achado).
