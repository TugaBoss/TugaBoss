// Gera o PDF do material (isca) de um Reels na identidade Tuga Boss.
//   node pdf.js <pasta-do-reel>   -> lê material.json, grava out/material-aberto.pdf
// A proteção com senha (palavra-chave) é aplicada depois pelo pdf_senha.py.
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const reel = path.resolve(process.argv[2]);
const M = JSON.parse(fs.readFileSync(path.join(reel, 'material.json'), 'utf8'));
const F = 'file://' + path.join(__dirname, 'fonts') + '/';
const LOGO = { claro: path.join(__dirname, 'marca/logo_escura.png'), escuro: path.join(__dirname, 'marca/logo_clara.png') };
const ANO = M.ano || new Date().getFullYear();
const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;');
const fmt = s => esc(s).replace(/_(.+?)_/g, '<span class="serif acc">$1</span>').replace(/\*(.+?)\*/g, '<b class="acc">$1</b>').replace(/\n/g, '<br>');
const CHECK = `<svg class="chk" viewBox="0 0 24 24"><circle cx="12" cy="12" r="12" fill="#1D9BF0"/><path d="M7 12.5l3.2 3.2L17.2 8.6" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

function bloco(b) {
  if (b.h) return `<h2 class="anton">${fmt(b.h)}</h2>`;
  if (b.p) return `<p>${fmt(b.p)}</p>`;
  if (b.nota) return `<p class="nota">${fmt(b.nota)}</p>`;
  if (b.passos) return `<ol>${b.passos.map((x, i) => `<li><span class="anton acc">${String(i + 1).padStart(2, '0')}</span><div>${fmt(x)}</div></li>`).join('')}</ol>`;
  if (b.check) return `<ul class="check">${b.check.map(x => `<li><i></i><div>${fmt(x)}</div></li>`).join('')}</ul>`;
  if (b.prompt) return `<div class="prompt"><div class="ph"><span class="mono">● ${esc(b.prompt.titulo)}</span><span class="mono sub">copie e cole</span></div><pre>${esc(b.prompt.texto)}</pre></div>`;
  return '';
}

const paginas = [{ capa: true }, ...M.paginas, { final: true }];
const N = paginas.length;
const html = `<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:Anton;src:url(${F}anton-latin-400-normal.woff2)}
@font-face{font-family:Serif;font-style:italic;src:url(${F}instrument-serif-latin-400-italic.woff2)}
@font-face{font-family:Mono;font-weight:500;src:url(${F}jetbrains-mono-latin-500-normal.woff2)}
@font-face{font-family:Mono;font-weight:700;src:url(${F}jetbrains-mono-latin-700-normal.woff2)}
@font-face{font-family:Jak;font-weight:400;src:url(${F}plus-jakarta-sans-latin-400-normal.woff2)}
@font-face{font-family:Jak;font-weight:500;src:url(${F}plus-jakarta-sans-latin-500-normal.woff2)}
@font-face{font-family:Jak;font-weight:700;src:url(${F}plus-jakarta-sans-latin-700-normal.woff2)}
@font-face{font-family:Jak;font-weight:800;src:url(${F}plus-jakarta-sans-latin-800-normal.woff2)}
@page{size:1080px 1350px;margin:0}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Jak}
.pg{width:1080px;height:1350px;position:relative;overflow:hidden;page-break-after:always;background:var(--bg);color:var(--fg);padding:190px 80px 150px}
.claro{--bg:#E6E5C7;--fg:#000;--sub:#3E3B2C;--card:#F1F0DA;--line:rgba(62,59,44,.2)}
.escuro{--bg:#000;--fg:#E6E5C7;--sub:#B9B79A;--card:#1C1B14;--line:rgba(230,229,199,.2)}
.acc{color:#FF4E08}.sub{color:var(--sub)}
.anton{font-family:Anton;text-transform:uppercase;line-height:.95;font-weight:400}
.serif{font-family:Serif;font-style:italic;font-weight:400;text-transform:none}
.mono{font-family:Mono;font-weight:700;letter-spacing:.04em;text-transform:uppercase}
.sig{position:absolute;left:80px;top:70px;display:flex;align-items:center;gap:14px;font-weight:700;font-size:28px}
.sig img{width:68px;height:68px;border-radius:50%}.chk{width:28px;height:28px;margin-left:-6px}
.copy{position:absolute;right:80px;top:92px;font-family:Mono;font-weight:500;font-size:20px;color:var(--sub)}
.foot{position:absolute;left:80px;right:80px;bottom:56px;display:flex;align-items:center;gap:28px}
.seg{flex:1;display:flex;gap:8px}.seg div{flex:1;height:8px;border-radius:4px;background:var(--line)}.seg div.on{background:#FF4E08}
.cnt{font-family:Mono;font-weight:700;font-size:26px}
.rot{font-size:24px;color:#FF4E08;margin-bottom:22px}
h2{font-size:72px;margin:6px 0 26px}
p{font-size:31px;line-height:1.42;font-weight:500;margin-bottom:22px}
p.nota{font-size:24px;color:var(--sub);font-family:Mono;font-weight:500;line-height:1.5}
ol,ul{list-style:none;display:flex;flex-direction:column;gap:16px;margin-bottom:26px}
ol li{display:flex;gap:22px;align-items:flex-start;background:var(--card);border-radius:20px;padding:20px 26px;font-size:30px;font-weight:600;line-height:1.32}
ol li .anton{font-size:50px;line-height:1}
ul.check li{display:flex;gap:18px;align-items:flex-start;font-size:30px;font-weight:600;line-height:1.35}
ul.check i{flex:none;width:36px;height:36px;border-radius:9px;border:3px solid #FF4E08;margin-top:2px}
.prompt{border-radius:20px;overflow:hidden;border:2px solid var(--line);margin-bottom:26px}
.prompt .ph{display:flex;justify-content:space-between;padding:14px 22px;background:#12110D;color:#E6E5C7;font-size:18px}
.prompt pre{background:#1C1B14;color:#E6E5C7;font-family:Mono;font-weight:500;font-size:24px;line-height:1.5;padding:22px 24px;white-space:pre-wrap;word-break:break-word}
.big{font-size:150px;line-height:.9}
.btn{display:inline-block;font-family:Anton;font-size:64px;padding:18px 48px 12px;border-radius:999px;background:#FF4E08;color:#000}
</style></head><body>
${paginas.map((pg, i) => {
  const tema = pg.capa || pg.final ? 'escuro' : 'claro';
  const segs = Array.from({ length: N }, (_, j) => `<div class="${j <= i ? 'on' : ''}"></div>`).join('');
  let corpo;
  if (pg.capa) corpo = `<div class="mono rot" style="margin-top:80px">${esc(M.kicker)}</div>
    <div class="anton big">${fmt(M.titulo)}</div>
    <p class="serif acc" style="font-size:72px;line-height:1.05;margin-top:30px">${esc(M.subtitulo)}</p>
    <p style="margin-top:60px;font-size:30px;color:var(--sub)">${fmt(M.resumo)}</p>
    <div style="position:absolute;left:80px;bottom:150px" class="mono sub">Material do Reels · palavra-chave <span class="acc">${esc(M.palavraChave)}</span></div>`;
  else if (pg.final) corpo = `<div class="mono rot" style="margin-top:80px">Próximo passo</div>
    <div class="anton" style="font-size:110px">${fmt(M.final?.titulo || 'Quer ir além?')}</div>
    <p style="margin-top:36px;font-size:36px">${fmt(M.final?.texto || '')}</p>
    <div style="margin-top:50px"><span class="btn">${esc(M.final?.botao || 'Comenta CLAUDE')}</span></div>
    <p class="nota" style="margin-top:80px">${fmt(M.final?.nota || 'Siga @tugabossdigital para mais métodos de IA aplicada a vendas.')}</p>`;
  else corpo = `<div class="mono rot">${esc(pg.rotulo)}</div>` + pg.blocos.map(bloco).join('');
  return `<section class="pg ${tema}" data-i="${i}"><div class="sig"><img src="file://${LOGO[tema]}">@tugabossdigital${CHECK}</div>
    <div class="copy">©${ANO} Tuga Boss Digital</div>${corpo}
    <div class="foot"><div class="seg">${segs}</div><div class="cnt">${String(i + 1).padStart(2, '0')}/${String(N).padStart(2, '0')}</div></div></section>`;
}).join('')}
</body></html>`;

(async () => {
  const tmp = path.join(reel, 'out', 'material.html');
  fs.mkdirSync(path.join(reel, 'out'), { recursive: true });
  fs.writeFileSync(tmp, html);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1350 } });
  await p.goto('file://' + tmp);
  await p.evaluate(() => document.fonts.ready);
  const over = await p.evaluate(() => [...document.querySelectorAll('.pg')].filter(s => {
    const foot = s.querySelector('.foot').getBoundingClientRect().top;
    return [...s.children].some(c => !c.classList.contains('foot') && c.getBoundingClientRect().bottom > foot - 10);
  }).map(s => +s.dataset.i + 1));
  if (over.length) console.log('ATENÇÃO: texto encostando no rodapé nas páginas', over.join(', '));
  await p.pdf({ path: path.join(reel, 'out', 'material-aberto.pdf'), width: '1080px', height: '1350px', printBackground: true });
  await p.screenshot({ path: path.join(reel, 'out', 'material-capa.png'), clip: { x: 0, y: 0, width: 1080, height: 1350 } });
  await b.close();
  console.log('pdf ok', N, 'páginas');
})();
