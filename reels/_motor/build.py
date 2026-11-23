#!/usr/bin/env python3
"""Motor de Reels Tuga Boss: roteiro.json -> narração -> trilha + efeitos -> vídeo 1080x1920.

Uso:
  python3 build.py <pasta-do-reel>                 # gera tudo e renderiza out/reels.mp4
  python3 build.py <pasta-do-reel> --stills 2,9.5  # só PNGs de conferência
  python3 build.py <pasta-do-reel> --so-audio      # só narração, trilha e mix

Voz fixa (masculina, pt-BR): Piper "faber". O modelo é baixado uma vez para ~/.cache/tuga-voz.
"""
import hashlib, json, os, subprocess, sys, tempfile, urllib.request, wave, datetime
import numpy as np

MOTOR = os.path.dirname(os.path.abspath(__file__))
VOZ = os.environ.get('TUGA_VOZ', 'pt_BR-faber-medium')
VOZ_DIR = os.path.expanduser('~/.cache/tuga-voz')
VOZ_URL = 'https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/{n}/medium/{f}'
VELOCIDADE = float(os.environ.get('TUGA_VELOCIDADE', '0.92'))  # <1 = mais rápido
SR_V, SR = 22050, 48000
LEAD, GAP, GAP_CENA, TAIL = 0.35, 0.14, 0.55, 1.6


def sh(*a, **k):
    return subprocess.run(a, check=True, **k)


def modelo():
    os.makedirs(VOZ_DIR, exist_ok=True)
    nome = VOZ.split('-')[1]
    for f in (VOZ + '.onnx', VOZ + '.onnx.json'):
        p = os.path.join(VOZ_DIR, f)
        if not os.path.exists(p):
            print('baixando voz', f)
            urllib.request.urlretrieve(VOZ_URL.format(n=nome, f=f), p + '.part'); os.replace(p + '.part', p)
    return os.path.join(VOZ_DIR, VOZ + '.onnx')


def ler_wav(p):
    w = wave.open(p); a = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(np.float32) / 32768
    if w.getnchannels() == 2: a = a.reshape(-1, 2).mean(1)
    return a, w.getframerate()


def gravar_wav(p, a, sr, ch=1):
    w = wave.open(p, 'wb'); w.setnchannels(ch); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((np.clip(a, -1, 1) * 32767).astype('<i2').tobytes()); w.close()


def tts(texto, cache):
    h = hashlib.sha1(f'{VOZ}|{VELOCIDADE}|{texto}'.encode()).hexdigest()[:16]
    p = os.path.join(cache, h + '.wav')
    if not os.path.exists(p):
        tmp = tempfile.mktemp(suffix='.wav')
        sh(sys.executable, '-m', 'piper', '-m', modelo(), '-f', tmp, '--length-scale', str(VELOCIDADE), '--sentence-silence', '0.1',
           input=texto.encode(), capture_output=True)
        a, sr = ler_wav(tmp); os.remove(tmp)
        idx = np.where(np.abs(a) > 0.012)[0]
        gravar_wav(p, a[max(0, idx[0] - 300): idx[-1] + 1600], sr)
    return ler_wav(p)[0]


def preparar_midia(reel, cenas):
    """Vídeos .mp4/.mov viram .webm (o Chromium do render não lê H.264)."""
    def todos(sc):
        for k in ('media',):
            if sc.get(k): yield sc[k]
        for m in sc.get('cartas', []): yield m
        for k in ('antes', 'depois'):
            if sc.get(k, {}).get('media'): yield sc[k]['media']
    for sc in cenas:
        for m in todos(sc):
            src = os.path.join(reel, m)
            if not os.path.exists(src): sys.exit(f'mídia não encontrada: {m}')
            if m.lower().endswith(('.mp4', '.mov')):
                dst = os.path.splitext(src)[0] + '.webm'
                if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
                    print('convertendo', m)
                    sh('ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-an', '-vf', 'scale=1080:-2', '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '32',
                       '-deadline', 'good', '-cpu-used', '4', '-row-mt', '1', '-g', '15', dst)


def narracao(reel, R):
    cache = os.path.join(reel, '.cache', 'tts'); os.makedirs(cache, exist_ok=True)
    partes, t, cues, cenas = [np.zeros(int(LEAD * SR_V), np.float32)], LEAD, [], []
    for k, sc in enumerate(R['cenas']):
        if k: partes.append(np.zeros(int(GAP_CENA * SR_V), np.float32)); t += GAP_CENA
        ini = max(0.0, t - 0.25) if k else 0.0
        falas = sc.get('fala', [])
        if not falas:
            d = float(sc.get('duracao', 3)); partes.append(np.zeros(int(d * SR_V), np.float32)); t += d
        for i, f in enumerate(falas):
            f = {'say': f, 'cap': f} if isinstance(f, str) else f
            if i: partes.append(np.zeros(int(GAP * SR_V), np.float32)); t += GAP
            a = tts(f['say'], cache); d = len(a) / SR_V
            cues.append({'k': k, 'i': i, 's': round(t, 3), 'e': round(t + d, 3), 'cap': f.get('cap', f['say'])})
            partes.append(a); t += d
        cenas.append({'s': round(ini, 3)})
    partes.append(np.zeros(int(TAIL * SR_V), np.float32)); t += TAIL
    for k, c in enumerate(cenas): c['e'] = cenas[k + 1]['s'] if k + 1 < len(cenas) else round(t, 3)
    gravar_wav(os.path.join(reel, 'audio', 'voz.wav'), np.concatenate(partes), SR_V)
    ano = R.get('ano') or datetime.date.today().year
    with open(os.path.join(reel, 'data.js'), 'w', encoding='utf-8') as fp:
        fp.write('window.ROTEIRO=%s;\nwindow.CUES=%s;\nwindow.SCENES=%s;\nwindow.DUR=%.3f;\nwindow.ANO=%s;\n' % (
            json.dumps(R, ensure_ascii=False), json.dumps(cues, ensure_ascii=False), json.dumps(cenas), t, json.dumps(str(ano))))
    print('duração %.1fs · %d frases · %d cenas' % (t, len(cues), len(cenas)))
    return t, cenas


# ---------- trilha e efeitos (sintetizados, sem direitos de terceiros) ----------
rng = np.random.default_rng(7)


def lowpass(x, a):
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc); y[i] = acc
    return y


def env(n, at, rel):
    e = np.ones(n); a = int(at * SR); e[:a] = np.linspace(0, 1, a) if a else 1
    e *= np.exp(-np.arange(n) / SR * rel); return e


def sfx(k):
    if k == 'whoosh':
        n = int(.5 * SR); x = rng.standard_normal(n); t = np.arange(n) / n
        cut = 0.02 + 0.25 * np.sin(np.pi * t) ** 2
        y = lowpass(x, cut) * np.sin(np.pi * t) ** 1.5
        return y / (np.abs(y).max() + 1e-9) * .7
    if k == 'pop':
        n = int(.09 * SR); t = np.arange(n) / SR; f = 980 - 3600 * t
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 45) * .55
    if k == 'tick':
        n = int(.03 * SR); t = np.arange(n) / SR
        return np.sin(2 * np.pi * 1700 * t) * np.exp(-t * 160) * .35
    if k == 'type':
        n = int(.018 * SR); x = np.diff(rng.standard_normal(n + 1)); t = np.arange(n) / SR
        return x * np.exp(-t * 320) * (.18 + .1 * rng.random())
    if k in ('slam', 'impact'):
        d = .5 if k == 'slam' else 1.4; n = int(d * SR); t = np.arange(n) / SR
        f = 42 + 95 * np.exp(-t * 26)
        b = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (7 if k == 'slam' else 3.2))
        no = np.convolve(rng.standard_normal(n), np.ones(30) / 30, 'same') * np.exp(-t * 16)
        return (b + 1.2 * no) * (.6 if k == 'slam' else .85)
    return np.zeros(1)


def trilha(reel, dur, cenas):
    n = int(dur * SR); t = np.arange(n) / SR; mus = np.zeros(n); fx = np.zeros(n)
    def put(buf, sig, at, g=1.0):
        i = int(at * SR)
        if 0 <= i < n: s = sig[:n - i]; buf[i:i + len(s)] += g * s
    BPM = 104; beat = 60 / BPM
    prog = [(110.0, 220.0), (87.31, 174.61), (130.81, 261.63), (98.0, 196.0)]  # Lá menor · Fá · Dó · Sol
    arp = [0, 3, 7, 12, 7, 3, 7, 10]
    for b in range(int(dur / beat) + 1):
        at = b * beat; root = prog[(b // 4) % 4]
        if b % 2 == 0:
            x = np.arange(int(.32 * SR)) / SR; f = 45 + 110 * np.exp(-x * 30)
            put(mus, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 10), at, .8)
        else:
            x = np.arange(int(.18 * SR)) / SR
            put(mus, np.convolve(rng.standard_normal(len(x)), np.ones(8) / 8, 'same') * np.exp(-x * 26), at, .32)
        for h in (.5, .75):
            x = np.arange(int(.04 * SR)) / SR
            put(mus, np.diff(rng.standard_normal(len(x) + 1)) * np.exp(-x * 110), at + h * beat, .1)
        for e in (0, .5):
            x = np.arange(int(.2 * SR)) / SR
            put(mus, np.sin(2 * np.pi * root[0] / 2 * x) * np.exp(-x * 11), at + e * beat, .42)
        for e in (0, .5):
            st = arp[(b * 2 + int(e * 2)) % 8]; f = root[1] * 2 ** (st / 12)
            x = np.arange(int(.35 * SR)) / SR
            put(mus, (np.sin(2 * np.pi * f * x) + .3 * np.sin(4 * np.pi * f * x)) * np.exp(-x * 9), at + e * beat, .07)
    for c in range(0, n, int(SR * beat * 4)):
        root = prog[(c // int(SR * beat * 4)) % 4][1]; m = min(n - c, int(SR * beat * 4)); x = np.arange(m) / SR
        mus[c:c + m] += .05 * (np.sin(2 * np.pi * root * x) + np.sin(2 * np.pi * root * 1.5 * x)) * np.minimum(1, x * 4)
    e = np.ones(n); e[:int(.4 * SR)] = np.linspace(0, 1, int(.4 * SR)); e[-int(1.4 * SR):] = np.linspace(1, 0, int(1.4 * SR))
    mus *= e
    evs = json.load(open(os.path.join(reel, 'audio', 'events.json')))
    last = {}
    for ev in sorted(evs, key=lambda x: x['t']):
        k = ev['k']
        if ev['t'] - last.get(k, -9) < (.03 if k == 'type' else .08): continue
        last[k] = ev['t']; put(fx, sfx(k), ev['t'])
    mus /= np.abs(mus).max() + 1e-9; fx /= max(1.0, np.abs(fx).max())
    gravar_wav(os.path.join(reel, 'audio', 'musica.wav'), mus * .9, SR)
    gravar_wav(os.path.join(reel, 'audio', 'efeitos.wav'), fx * .9, SR)


def mix(reel, dur):
    a = os.path.join(reel, 'audio')
    sh('ffmpeg', '-y', '-loglevel', 'error', '-i', f'{a}/voz.wav', '-i', f'{a}/musica.wav', '-i', f'{a}/efeitos.wav', '-filter_complex',
       f'[0:a]aresample={SR},highpass=f=80,equalizer=f=180:t=q:w=1:g=2,equalizer=f=3400:t=q:w=1.2:g=3,'
       f'acompressor=threshold=-20dB:ratio=3.5:attack=4:release=110:makeup=5,apad=whole_dur={dur},asplit=2[v][sc];'
       f'[1:a]volume=0.42[m];[m][sc]sidechaincompress=threshold=0.025:ratio=7:attack=12:release=280[md];'
       f'[2:a]volume=0.55[f];[v][md][f]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9,atrim=0:{dur}[o]',
       '-map', '[o]', '-ac', '2', '-ar', str(SR), f'{a}/mix.wav')


def main():
    reel = os.path.abspath(sys.argv[1]); args = sys.argv[2:]
    R = json.load(open(os.path.join(reel, 'roteiro.json'), encoding='utf-8'))
    os.makedirs(os.path.join(reel, 'audio'), exist_ok=True)
    preparar_midia(reel, R['cenas'])
    dur, cenas = narracao(reel, R)
    node = ['node', os.path.join(MOTOR, 'render.js'), reel]
    if '--stills' in args:
        sh(*node, '--stills', args[args.index('--stills') + 1]); return
    sh(*node, '--events')
    trilha(reel, dur, cenas); mix(reel, dur)
    if '--so-audio' not in args: sh(*node)


if __name__ == '__main__':
    main()
