# Reels — Neymar: o último ato na Vila? (@camisa10gyn · Trilha do Craque #08)

- `out/reels.mp4` — vídeo final, 1080×1920, 30 fps, ~56 s.
- `roteiro.json` — frases da narração (`say`) e legendas (`cap`), por cena.
- `tts.py` — gera `audio/voz.wav` e `cues.js` (tempos exatos de cada frase). Voz local Piper `pt_BR-faber-medium`.
- `music.py` — trilha sintetizada, sincronizada com as cenas.
- `index.html` — animação; todos os tempos vêm de `cues.js`, por isso trocar a voz não exige re-sincronizar.
- `render.js` — `node render.js` renderiza e junta com `audio/mix.wav`.
- `img/` — fotos enviadas pelo cliente (reprodução).

## Fontes
- Santos FC, ESPN, CNN Brasil — contrato até 31/12/2026
- Metrópoles, Correio Braziliense — fim de contrato e eleição do Santos em 12/12
- Band, O Povo, Folha PE — 80 gols em 130 jogos; adeus à Seleção em 29/07/2026
- Carrossel de referência (Wikipédia) — dados de carreira
