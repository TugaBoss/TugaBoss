// Renderiza um Reels do motor Tuga Boss.
//   node render.js <pasta-do-reel>                  -> <pasta>/out/reels.mp4 (usa <pasta>/audio/mix.wav)
//   node render.js <pasta-do-reel> --events         -> <pasta>/audio/events.json (momentos dos efeitos sonoros)
//   node render.js <pasta-do-reel> --stills 1.5,8   -> PNGs de conferência em <pasta>/out/
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const FPS = 30;
const reel = path.resolve(process.argv[2] || '.');
const mode = process.argv[3] || '';
const out = path.join(reel, 'out');
fs.mkdirSync(out, { recursive: true });
const rel = path.relative(__dirname, reel).split(path.sep).join('/') + '/';
const url = 'file://' + path.join(__dirname, 'motor.html') + '?reel=' + encodeURIComponent(rel);

(async () => {
  const browser = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => { console.error('ERRO NA PÁGINA:', e.message); process.exitCode = 1; });
  await page.goto(url);
  await page.evaluate(() => window.ready);
  const DUR = await page.evaluate(() => window.DUR);
  const clip = { x: 0, y: 0, width: 1080, height: 1920 };

  if (mode === '--events') {
    const ev = await page.evaluate(() => window.EVENTS);
    fs.writeFileSync(path.join(reel, 'audio', 'events.json'), JSON.stringify(ev));
    console.log('eventos', ev.length);
  } else if (mode === '--stills') {
    for (const t of process.argv[4].split(',').map(Number)) {
      await page.evaluate(t => window.seek(t), t);
      await page.screenshot({ path: path.join(out, `still-${t.toFixed(2)}.png`), clip });
    }
  } else {
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-i', path.join(reel, 'audio', 'mix.wav'), '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p',
      '-r', String(FPS), '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', '-shortest', path.join(out, 'reels.mp4')],
      { stdio: ['pipe', 'inherit', 'inherit'] });
    const n = Math.round(DUR * FPS);
    for (let i = 0; i < n; i++) {
      await page.evaluate(t => window.seek(t), i / FPS);
      const buf = await page.screenshot({ type: 'jpeg', quality: 95, clip });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 300 === 0) console.log(`quadro ${i}/${n}`);
    }
    ff.stdin.end();
    await new Promise(r => ff.on('close', r));
    console.log('ok', path.join(out, 'reels.mp4'));
  }
  await browser.close();
})();
