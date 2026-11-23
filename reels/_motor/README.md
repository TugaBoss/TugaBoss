# Motor de Reels · Tuga Boss Digital

Um roteiro em JSON vira um Reels 1080×1920 com motion graphics, transições, legendas palavra a palavra, trilha, efeitos sonoros e narração — sempre na mesma voz masculina (Piper `pt_BR-faber-medium`).

```bash
python3 reels/_motor/build.py reels/<pasta-do-reel>                  # vídeo completo → out/reels.mp4
python3 reels/_motor/build.py reels/<pasta-do-reel> --stills 2,9.5   # só PNGs para conferir
```

A pasta do reel tem `roteiro.json` e as mídias (`img/…`). Vídeos `.mp4/.mov` são convertidos sozinhos.
Todos os tempos saem da narração: mudar uma frase re-sincroniza tudo.

## Identidade (Paleta A)
Creme `#E6E5C7` · laranja `#FF4E08` · carvão `#3E3B2C` · preto. Anton (manchetes), Instrument Serif itálico (destaque),
JetBrains Mono (rótulos), Plus Jakarta Sans (texto). Assinatura com logo + @tugabossdigital + selo, © do ano,
barra segmentada no topo e contador no rodapé direito. Zona segura: conteúdo entre y=200 e y=1560.

## Roteiro
```json
{ "tema": "claro", "cenas": [ { "tipo": "capa", "titulo": "...", "fala": ["frase 1", {"say": "texto falado", "cap": "legenda"}] } ] }
```
Marcação nos textos: `*palavra*` = laranja · `_palavra_` = serifa itálica laranja · `\n` = quebra de linha.
`say` permite escrever a pronúncia (ex.: "Clóde", "Ríls") mantendo a legenda certa em `cap`.

| tipo | campos | base |
|---|---|---|
| `capa` | kicker, titulo, tamanho, pilula, `cartas` (até 3 imagens) ou `media` (arco) | R1 / C1 |
| `forte` | rotulo, numero (conta até o valor), titulo, texto — fundo escuro, sem foto | slide forte |
| `lista` | numero, titulo, subtitulo, itens (cada item acende na sua frase) | C5 |
| `tela` | janela, media (imagem ou vídeo), etiqueta, texto (máquina de escrever), serif | R2 / C2 |
| `antesdepois` | titulo, antes{media,rotulo}, depois{media,rotulo}, comando, nota | R5 / C3 |
| `palavra` | kicker, palavras (sincronizadas com a fala), serif, media (círculo) | R3 |
| `dia` | dia, total, etiqueta, itens (checklist), media | R4 / C4 |
| `cta` | titulo, palavraChave, chaveFalada, texto, botoes | final |

Opcionais em qualquer cena: `tema` (claro/escuro), `transicao` (wipeUp, sweep, circle, slideIn, wipeL, zoomIn).

## Pendências
- Logo: `marca/` tem um recorte dos modelos renderizados (serve até ~140 px). Trocar pelos PNGs aprovados do Projeto.
- Selo azul: genérico, como no `gen.py` (não há arquivo oficial).
