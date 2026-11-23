# Trilha de fundo sintetizada (sem direitos de terceiros), sincronizada com as cenas de audio/cues.json.
import numpy as np, wave, json
J=json.load(open('audio/cues.json')); DUR=J['dur']; C={c['id']:c['s'] for c in J['cues']}
SR=48000; n=int(SR*DUR); t=np.arange(n)/SR
rng=np.random.default_rng(10); out=np.zeros(n)
def put(sig,at,g=1.0):
    i=int(at*SR)
    if i>=n or i<0: return
    sig=sig[:n-i]; out[i:i+len(sig)]+=g*sig
def kick():
    x=np.arange(int(.32*SR))/SR; f=45+110*np.exp(-x*32)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-x*11)
def hat():
    x=np.arange(int(.05*SR))/SR; w=np.diff(rng.standard_normal(len(x)),prepend=0)
    return w*np.exp(-x*90)
def impact():
    x=np.arange(int(1.6*SR))/SR; f=38+70*np.exp(-x*9)
    b=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-x*3.2)
    w=np.convolve(rng.standard_normal(len(x)),np.ones(40)/40,'same')
    return b+0.9*w*np.exp(-x*7)
def riser(d):
    x=np.arange(int(d*SR))/SR; w=np.diff(rng.standard_normal(len(x)),prepend=0)
    return w*(x/d)**2.5
def pluck(f,d=.9):
    x=np.arange(int(d*SR))/SR
    return (np.sin(2*np.pi*f*x)+.4*np.sin(2*np.pi*2*f*x)+.2*np.sin(2*np.pi*3*f*x))*np.exp(-x*5)
BPM=92; beat=60/BPM
corpo=[s['s'] for s in J['scenes'] if s['id']=='corpo'][0]; sel=[s['s'] for s in J['scenes'] if s['id']=='selecao'][0]
for f,g in((43.65,.5),(87.31,.3),(130.81,.1)):  # drone em Fá
    out+=g*np.sin(2*np.pi*f*t)*(0.75+0.25*np.sin(2*np.pi*0.09*t+f))
mel=[349.23,415.30,523.25,415.30,311.13,415.30,466.16,415.30]  # arpejo menor, melancólico
for k in range(int(DUR/(beat/2))):
    at=k*beat/2; x=np.arange(int(0.22*SR))/SR
    note=87.31 if (k//16)%2==0 else 77.78
    put(np.sin(2*np.pi*note*x)*np.exp(-x*14),at,.4)
    if k%2==0: put(pluck(mel[(k//2)%8]),at,.11)
for k in range(int(DUR/beat)):
    at=k*beat
    if at>0.3 and not (corpo<=at<corpo+1.6): put(kick(),at,.9)
    put(hat(),at+beat/2,.14); put(hat(),at+beat*.75,.07)
for s in J['scenes']:
    put(impact(),s['s'],1.1)
    if s['s']>1: put(riser(1.0),s['s']-1.0,.16)
for c,o in (('c1',.75),('c2',0),('c3',0),('c4',0),('c5',.15),('t2',.7),('s1',.85),('e2',0),('f1',0)): put(impact(),C[c]+o,1.15)
env=np.ones(n); f=int(1.2*SR); env[-f:]=np.linspace(1,0,f)
out*=env; out/=np.abs(out).max(); out=np.tanh(out*1.4)*0.9
st=np.stack([out,out],1)
w=wave.open('audio/trilha.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((st*32767).astype('<i2').tobytes()); w.close()
