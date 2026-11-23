# Gera a narração frase a frase (Piper, voz pt-BR) e grava audio/voz.wav + cues.js com os tempos exatos.
# Uso: python3 tts.py /caminho/pt_BR-faber-medium.onnx
import json, subprocess, sys, wave, os, tempfile
import numpy as np
MODEL = sys.argv[1]
SR = 22050
LEAD, GAP, GAP_SCENE, TAIL = 0.30, 0.16, 0.42, 1.3
lines = json.load(open('roteiro.json', encoding='utf-8'))
def synth(text):
    f = tempfile.mktemp(suffix='.wav')
    subprocess.run([sys.executable, '-m', 'piper', '-m', MODEL, '-f', f, '--length-scale', '0.94', '--sentence-silence', '0.12'],
                   input=text.encode(), check=True, capture_output=True)
    w = wave.open(f); assert w.getframerate() == SR
    a = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(np.float32) / 32768; os.remove(f)
    idx = np.where(np.abs(a) > 0.012)[0]
    return a[max(0, idx[0] - 400): idx[-1] + 1800]
out = [np.zeros(int(LEAD * SR), np.float32)]; t = LEAD; cues = []; scenes = []
for i, l in enumerate(lines):
    if i: 
        g = GAP_SCENE if 'scene' in l else GAP
        out.append(np.zeros(int(g * SR), np.float32)); t += g
    a = synth(l['say']); d = len(a) / SR
    cues.append({'id': l['id'], 's': round(t, 3), 'e': round(t + d, 3), 'cap': l['cap']})
    if 'scene' in l: scenes.append({'id': l['scene'], 's': round(max(0, t - 0.22), 3)})
    out.append(a); t += d
out.append(np.zeros(int(TAIL * SR), np.float32)); t += TAIL
a = np.concatenate(out)
w = wave.open('audio/voz.wav', 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(a, -1, 1) * 32767).astype('<i2').tobytes()); w.close()
scenes[0]['s'] = 0
open('cues.js', 'w', encoding='utf-8').write('window.DUR=%.2f;\nwindow.SCENES=%s;\nwindow.CUES=%s;\n' % (t, json.dumps(scenes), json.dumps(cues, ensure_ascii=False)))
json.dump({'dur': round(t, 2), 'scenes': scenes, 'cues': cues}, open('audio/cues.json', 'w'), ensure_ascii=False)
print('dur', round(t, 2)); print(' '.join('%s@%.1f' % (s['id'], s['s']) for s in scenes))
