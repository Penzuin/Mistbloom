"""Mistbloom Studios sonic logo (~4.5 s): night mist swells, a music-box arpeggio climbs as the flower
opens, a warm lantern-bell chord blooms on the logo, star chimes twinkle, long reverb tail. D major add9."""
import numpy as np, wave, sys

SR = 48000
DUR = 4.6
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)
f = lambda n: 440.0 * 2 ** ((n - 69) / 12)            # MIDI -> Hz
L = np.zeros(N); R = np.zeros(N)

def add(sig, start, pan=0.0, gain=1.0):
    i = int(start * SR); j = min(N, i + len(sig))
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    L[i:j] += sig[:j - i] * gain * l * 1.414; R[i:j] += sig[:j - i] * gain * r * 1.414

def env(n, a, d):                                       # attack seconds, exp decay time constant
    tt = np.arange(n) / SR
    return np.minimum(1, tt / max(a, 1e-4)) * np.exp(-tt / d)

def musicbox(m, dur=1.6, dec=0.55):
    n = int(dur * SR); tt = np.arange(n) / SR; fr = f(m)
    s = (np.sin(2 * np.pi * fr * tt) + 0.35 * np.sin(2 * np.pi * fr * 3.0 * tt) * np.exp(-tt / 0.15)
         + 0.18 * np.sin(2 * np.pi * fr * 5.04 * tt) * np.exp(-tt / 0.08))
    return s * env(n, 0.002, dec)

def bell(m, dur=3.2, dec=1.3):
    n = int(dur * SR); tt = np.arange(n) / SR; fr = f(m); s = np.zeros(n)
    for ratio, amp, dk in ((1, 1, 1.0), (2.0, 0.45, 0.7), (2.76, 0.25, 0.45), (4.07, 0.12, 0.25), (0.5, 0.3, 1.2)):
        s += amp * np.sin(2 * np.pi * fr * ratio * tt + rng.uniform(0, 6)) * np.exp(-tt / (dec * dk))
    return s * np.minimum(1, tt / 0.004)

def pad(ms, start, dur, a=0.9, rel=1.4):
    n = int(dur * SR); tt = np.arange(n) / SR; s = np.zeros(n)
    for m in ms:
        for det in (-0.06, 0.0, 0.07):
            fr = f(m + det)
            s += np.sin(2 * np.pi * fr * tt + rng.uniform(0, 6)) + 0.25 * np.sin(2 * np.pi * 2 * fr * tt)
    e = np.minimum(1, tt / a) * np.clip((dur - tt) / rel, 0, 1)
    return s * e / (3 * len(ms))

def lowpass(x, cut):
    a = np.exp(-2 * np.pi * cut / SR); y = np.zeros_like(x); acc = 0.0
    for i in range(len(x)):                             # one-pole, fine for short buffers
        acc = (1 - a) * x[i] + a * acc; y[i] = acc
    return y

# 1. night mist: airy filtered noise swelling in and settling
n = int(3.4 * SR); tt = np.arange(n) / SR
mist = lowpass(lowpass(rng.standard_normal(n), 1100), 1600) - lowpass(rng.standard_normal(n), 300) * 0.5
mist *= np.minimum(1, tt / 1.2) ** 2 * np.clip((3.4 - tt) / 2.0, 0, 1)
add(mist, 0.0, -0.3, 0.07); add(np.roll(mist, 900), 0.0, 0.3, 0.07)
# 2. soft pad, D add9, under everything
add(pad([50, 57, 64, 66], 0.0, 4.2, a=1.1, rel=1.8), 0.0, 0.0, 0.16)
# 3. the bloom: music box climbs A4 D5 F#5 A5 E6
for k, (m, at) in enumerate(((69, 0.55), (74, 0.72), (78, 0.88), (81, 1.03), (88, 1.18))):
    add(musicbox(m), at, -0.4 + 0.2 * k, 0.20)
# 4. the logo hit at 1.45 s: lantern bell chord + soft low body
for m, pan, g in ((74, -0.25, 0.38), (78, 0.2, 0.28), (81, -0.1, 0.25), (88, 0.35, 0.12)):
    add(bell(m), 1.45, pan, g)
n = int(1.6 * SR); tt = np.arange(n) / SR
add(np.sin(2 * np.pi * f(38) * tt) * env(n, 0.01, 0.45), 1.45, 0.0, 0.22)
# 5. star chimes sprinkling after the hit
for at, m, pan in ((1.62, 93, 0.6), (1.78, 100, -0.5), (1.95, 97, 0.3), (2.15, 105, -0.2), (2.4, 100, 0.7), (2.7, 93, -0.6)):
    add(musicbox(m, 1.2, 0.35), at, pan, 0.07)

# reverb: exponential-decay noise impulse, per channel
ir_n = int(2.6 * SR); it = np.arange(ir_n) / SR
def ir(seed):
    r = np.random.default_rng(seed).standard_normal(ir_n) * np.exp(-it / 0.75)
    r[:int(0.012 * SR)] = 0
    return lowpass(r, 5200) / np.sqrt(np.sum(r ** 2))
def conv(x, h):
    m = len(x) + len(h); nf = 1 << (m - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, nf) * np.fft.rfft(h, nf), nf)[:len(x)]
wetL, wetR = conv(L, ir(1)), conv(R, ir(2))
outL, outR = L * 0.8 + wetL * 0.55, R * 0.8 + wetR * 0.55
fade = np.clip((DUR - t) / 0.5, 0, 1); outL *= fade; outR *= fade
pk = max(np.abs(outL).max(), np.abs(outR).max()); g = 10 ** (-1 / 20) / pk
st = (np.stack([outL, outR], 1) * g * 32767).astype(np.int16)
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "mistbloom-intro.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
print("ok", DUR, "s")
