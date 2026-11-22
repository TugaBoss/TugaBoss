# Trilha de fundo sintetizada (sem direitos de terceiros): pulso grave, chimbal, impactos nas viradas de cena.
import numpy as np, wave
SR=48000; DUR=50.6; n=int(SR*DUR); t=np.arange(n)/SR
rng=np.random.default_rng(7)
out=np.zeros(n)
def put(sig,at,g=1.0):
    i=int(at*SR)
    if i>=n or i<0: return
    sig=sig[:n-i]; out[i:i+len(sig)]+=g*sig
def kick():
    d=0.32; x=np.arange(int(d*SR))/SR
    f=45+110*np.exp(-x*32)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-x*11)
def hat():
    d=0.05; x=np.arange(int(d*SR))/SR
    w=rng.standard_normal(len(x)); w=np.diff(w,prepend=0)
    return w*np.exp(-x*90)
def impact():
    d=1.6; x=np.arange(int(d*SR))/SR
    f=38+70*np.exp(-x*9)
    b=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-x*3.2)
    w=rng.standard_normal(len(x)); w=np.convolve(w,np.ones(40)/40,'same')
    return b+0.9*w*np.exp(-x*7)
def riser(d):
    x=np.arange(int(d*SR))/SR
    w=rng.standard_normal(len(x)); w=np.diff(w,prepend=0)
    return w*(x/d)**2.5
BPM=100; beat=60/BPM
# drone em Ré menor
for f,g in((36.71,.5),(73.42,.35),(110.0,.12),(87.31,.08)):
    out+=g*np.sin(2*np.pi*f*t)*(0.75+0.25*np.sin(2*np.pi*0.11*t+f))
# baixo pulsante em colcheias
for k in range(int(DUR/(beat/2))):
    at=k*beat/2; x=np.arange(int(0.22*SR))/SR
    note=73.42 if (k//16)%2==0 else 65.41
    put(np.sin(2*np.pi*note*x)*np.exp(-x*14)+0.3*np.sin(2*np.pi*2*note*x)*np.exp(-x*20),at,.45)
for k in range(int(DUR/beat)):
    at=k*beat
    if at>0.3: put(kick(),at,.95)
    put(hat(),at+beat/2,.16); put(hat(),at+beat*.75,.08)
OFF=0.25
for s in (0.0,5.72,16.35,20.05,29.7,34.7,41.95):
    put(impact(),s+OFF,1.1)
    if s>1: put(riser(1.1),s+OFF-1.1,.18)
for s in (14.55,38.2,47.64): put(impact(),s+OFF,1.3)
env=np.ones(n); f=int(1.4*SR); env[-f:]=np.linspace(1,0,f)
out*=env; out/=np.abs(out).max(); out=np.tanh(out*1.4)*0.9
st=np.stack([out,out],1)
w=wave.open('audio/trilha.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((st*32767).astype('<i2').tobytes()); w.close()
