"""Hollowmere festival loop - an original spooky-cute synth tune for a Halloween market.
D minor, 116 bpm with a light swing, ~91 s, loops seamlessly (reverb tail folded back to the start).

Band: plucky square-wave melody, a theremin-style lead with vibrato and glides, a drawbar organ pad,
oom-pah synth bass, tubular bells, a harpsichord-ish arpeggio for the bridge, and soft synth percussion
(kick, shaker, finger-snap, wood block). Pure numpy, no samples."""
import numpy as np, wave, sys

SR = 44100
BPM = 116
BEAT = 60 / BPM
SWING = 0.10                     # off-beat eighths land a touch late
rng = np.random.default_rng(31)

def m2f(m): return 440 * 2 ** ((m - 69) / 12)
NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
        "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
def n(s):
    name, octv = s[:-1], int(s[-1])
    return NOTE[name] + 12 * (octv + 1)

def swing(beat):
    whole, frac = divmod(beat, 1.0)
    if abs(frac - 0.5) < 1e-6:
        frac += SWING
    return (whole + frac) * BEAT

# ------------------------------------------------------------------ the song plan
CH = {"Dm": ("D2", ["D4", "F4", "A4"]), "Bb": ("Bb1", ["D4", "F4", "Bb4"]), "Gm": ("G1", ["D4", "G4", "Bb4"]),
      "A7": ("A1", ["C#4", "E4", "G4"]), "F": ("F1", ["C4", "F4", "A4"]), "C": ("C2", ["C4", "E4", "G4"]),
      "A": ("A1", ["C#4", "E4", "A4"])}
PROG_A = ["Dm", "Dm", "Bb", "A7", "Dm", "Gm", "A7", "Dm"]
PROG_B = ["F", "C", "Gm", "Dm", "Bb", "F", "Gm", "A7"]

# melodies: per bar a list of (beat, length, note); 4 beats a bar
MEL_A = [
    [(0, .5, "D5"), (.5, .5, "F5"), (1, .5, "A5"), (1.5, .5, "F5"), (2, 1, "D5"), (3, .5, "C#5"), (3.5, .5, "D5")],
    [(0, .5, "E5"), (.5, .5, "F5"), (1, 1, "E5"), (2, 1.5, "D5")],
    [(0, .5, "Bb4"), (.5, .5, "D5"), (1, .5, "F5"), (1.5, .5, "D5"), (2, .5, "Bb4"), (2.5, .5, "D5"), (3, 1, "F5")],
    [(0, 1, "E5"), (1, .5, "C#5"), (1.5, .5, "E5"), (2, 1.5, "A4")],
    [(0, .5, "D5"), (.5, .5, "F5"), (1, .5, "A5"), (1.5, .5, "D6"), (2, 1, "C6"), (3, .5, "A5"), (3.5, .5, "F5")],
    [(0, .5, "G5"), (.5, .5, "F5"), (1, .5, "E5"), (1.5, .5, "D5"), (2, 1, "Bb4"), (3, 1, "D5")],
    [(0, .5, "C#5"), (.5, .5, "E5"), (1, .5, "G5"), (1.5, .5, "E5"), (2, .5, "A5"), (2.5, .5, "G5"), (3, .5, "E5"), (3.5, .5, "C#5")],
    [(0, 2.5, "D5"), (3, .5, "A4"), (3.5, .5, "C#5")],
]
MEL_B = [
    [(0, 1, "A5"), (1, .5, "G5"), (1.5, .5, "F5"), (2, 1.5, "C6")],
    [(0, .5, "G5"), (.5, .5, "E5"), (1, 1, "C5"), (2, 1.5, "E5")],
    [(0, 1, "D5"), (1, .5, "G5"), (1.5, .5, "Bb5"), (2, 1, "A5"), (3, 1, "G5")],
    [(0, 3, "F5")],
    [(0, .5, "D5"), (.5, .5, "F5"), (1, .5, "Bb5"), (1.5, .5, "D6"), (2, 1.5, "C6")],
    [(0, .5, "A5"), (.5, .5, "C6"), (1, 1, "F6"), (2, 1.5, "C6")],
    [(0, .5, "Bb5"), (.5, .5, "A5"), (1, .5, "G5"), (1.5, .5, "F5"), (2, 1, "E5"), (3, 1, "D5")],
    [(0, 1, "C#5"), (1, 1, "E5"), (2, 1, "A5"), (3, .5, "G5"), (3.5, .5, "E5")],
]
# sections: name, bars, chords, melody, which parts play
PLAN = [
    ("intro", 4, ["Dm", "Bb", "Gm", "A7"], None, {"organ", "bells", "swoop"}),
    ("A1", 8, PROG_A, MEL_A, {"organ", "bass", "pluck", "kick", "shaker", "snap"}),
    ("A2", 8, PROG_A, MEL_A, {"organ", "bass", "theremin", "kick", "shaker", "snap", "bells", "pluckcounter"}),
    ("B", 8, PROG_B, MEL_B, {"organ", "bass", "harpsi", "pluck", "kick", "shaker", "snap", "block"}),
    ("break", 4, ["Dm", "Dm", "Bb", "A7"], None, {"organ", "tick", "boo"}),
    ("A3", 8, PROG_A, MEL_A, {"organ", "bass", "theremin", "pluck", "kick", "shaker", "snap", "bells", "harpsi"}),
    ("outro", 4, ["Dm", "Bb", "A7", "Dm"], None, {"organ", "bells", "pluckhook"}),
]
BARS = sum(p[1] for p in PLAN)
LOOP = BARS * 4 * BEAT
N = int((LOOP + 4.0) * SR)            # extra room for tails; folded back afterwards
L = np.zeros(N); R = np.zeros(N)

def add(sig, t0, pan=0.0, g=1.0):
    i = int(t0 * SR)
    if i >= N: return
    j = min(N, i + len(sig)); s = sig[:j - i] * g
    L[i:j] += s * np.cos((pan + 1) * np.pi / 4) * 1.414
    R[i:j] += s * np.sin((pan + 1) * np.pi / 4) * 1.414

def tt(d): return np.arange(int(d * SR)) / SR

def env(d, a=0.005, decay=None, rel=0.05, sus=1.0):
    t = tt(d)
    e = np.minimum(1, t / max(a, 1e-4))
    if decay: e = e * (sus + (1 - sus) * np.exp(-t / decay))
    e *= np.clip((d - t) / rel, 0, 1)
    return e

def additive(f, d, harms, phase_rand=True):
    t = tt(d); s = np.zeros_like(t)
    for k, a in harms:
        if f * k < SR / 2.2:
            s += a * np.sin(2 * np.pi * f * k * t + (rng.uniform(0, 6) if phase_rand else 0))
    return s

def onepole(x, cut):
    a = np.exp(-2 * np.pi * cut / SR)
    from scipy.signal import lfilter
    return lfilter([1 - a], [1, -a], x)

# ------------------------------------------------------------------ instruments
def pluck(m, d):          # bright little square, quick decay: the "music box from a pumpkin" voice
    f = m2f(m)
    s = additive(f, d + 0.3, [(k, 1 / k) for k in (1, 3, 5, 7, 9, 11)])
    s = onepole(s, 3200) * env(d + 0.3, 0.003, 0.22, 0.08, sus=0.0)
    return s

def harpsi(m, d):
    f = m2f(m)
    s = additive(f, d + 0.4, [(k, 1 / k ** 0.8) for k in range(1, 12)])
    return onepole(s, 4500) * env(d + 0.4, 0.002, 0.35, 0.1, sus=0.0) * 0.6

def organ(ms, d):
    t = tt(d); s = np.zeros_like(t)
    for m in ms:
        f = m2f(m)
        s += additive(f, d, [(0.5, 0.6), (1, 1), (2, 0.55), (3, 0.3), (4, 0.18), (6, 0.08)])
    trem = 1 + 0.08 * np.sin(2 * np.pi * 5.6 * t)
    return onepole(s * trem, 2200) * env(d, 0.06, None, 0.15) / len(ms)

def bass(m, d):
    f = m2f(m); t = tt(d + 0.1)
    saw = additive(f, d + 0.1, [(k, 1 / k) for k in range(1, 9)])
    sub = np.sin(2 * np.pi * f * t)
    return onepole(0.6 * saw + 0.8 * sub, 900) * env(d + 0.1, 0.004, 0.18, 0.06, sus=0.35)

def bell(m, d=2.5):
    f = m2f(m); t = tt(d); s = np.zeros_like(t)
    for r, a, dk in ((1, 1, 1.0), (2.0, 0.5, 0.6), (2.76, 0.35, 0.4), (4.07, 0.18, 0.25), (5.4, 0.08, 0.15)):
        s += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / (1.1 * dk))
    return s * np.minimum(1, t / 0.003) * 0.5

def theremin_line(notes, bar_t0):
    """One continuous voice across a bar: glides between notes, vibrato that blooms after each attack."""
    end = max(b + l for b, l, _ in notes)
    d = end * BEAT + 0.35
    t = tt(d)
    pitch = np.full_like(t, float(n(notes[0][2])))
    amp = np.zeros_like(t)
    for k, (b, l, s) in enumerate(notes):
        i0, i1 = int(swing(b) * SR), int(min(len(t), (swing(b) + l * BEAT + 0.12) * SR))
        target = n(s)
        prev = pitch[i0 - 1] if i0 > 0 else target
        glide = int(0.06 * SR)
        seg = np.full(i1 - i0, float(target))
        g = min(glide, len(seg))
        seg[:g] = np.linspace(prev, target, g)
        pitch[i0:i1] = seg
        amp[i0:i1] = np.maximum(amp[i0:i1], 1.0)
    since = np.zeros_like(t)                                  # vibrato depth grows through each note
    vib = 0.35 * np.sin(2 * np.pi * 5.4 * t)
    freq = m2f(pitch + vib * np.clip(np.convolve(amp, np.ones(int(0.25 * SR)) / (0.25 * SR), "same"), 0, 1))
    ph = 2 * np.pi * np.cumsum(freq) / SR
    s = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.06 * np.sin(3 * ph)
    a = onepole(amp, 14)                                      # soft swells, no clicks
    return s * a * 0.55

def kick():
    t = tt(0.35); f = 45 + 80 * np.exp(-t / 0.04)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)

def shaker():
    t = tt(0.07); x = rng.standard_normal(len(t)); x = x - onepole(x, 5000)
    return onepole(x, 11000) * np.exp(-t / 0.02) * 0.30

def snap():
    t = tt(0.12); x = rng.standard_normal(len(t)); x = onepole(x, 3500) - onepole(x, 1200)
    return x * np.exp(-t / 0.03) * 1.2

def block(m=84):
    t = tt(0.12); f = m2f(m)
    return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.3 * t)) * np.exp(-t / 0.035)

def tick(hi=True):
    t = tt(0.05); x = rng.standard_normal(len(t)); x = x - onepole(x, 2500)
    return x * np.exp(-t / 0.008) * (0.5 if hi else 0.35)

def swoop(m0, m1, d):
    t = tt(d); p = np.linspace(m0, m1, len(t)) + 0.4 * np.sin(2 * np.pi * 5 * t)
    ph = 2 * np.pi * np.cumsum(m2f(p)) / SR
    return (np.sin(ph) + 0.15 * np.sin(2 * ph)) * np.sin(np.pi * t / d) ** 1.5 * 0.5

# ------------------------------------------------------------------ arrange
bar0 = 0
for name, bars, prog, mel, parts in PLAN:
    for b in range(bars):
        t0 = (bar0 + b) * 4 * BEAT
        chord = prog[b % len(prog)]
        root, voicing = CH[chord]
        last_bar = (b == bars - 1)
        if "organ" in parts:
            add(organ([n(x) for x in voicing], 4 * BEAT + 0.05), t0, 0.0, 0.16 if name not in ("intro", "break", "outro") else 0.30)
        if "bass" in parts:                                   # oom-pah: root on 1 and 3, fifth-ish answer on the swung "and" of 2/4
            r = n(root)
            for beat, mm, ln in ((0, r, .9), (1.5, r + 7, .4), (2, r, .9), (3.5, r + 12, .4)):
                add(bass(mm, ln * BEAT), t0 + swing(beat), -0.05, 0.34)
        if "kick" in parts:
            for beat in (0, 2):
                add(kick(), t0 + beat * BEAT, 0, 0.55)
        if "snap" in parts:
            for beat in (1, 3):
                add(snap(), t0 + beat * BEAT, 0.25, 0.18)
        if "shaker" in parts:
            for k in range(8):
                add(shaker(), t0 + swing(k * 0.5), -0.35, 0.22 if k % 2 else 0.12)
        if "block" in parts and b % 2 == 1:
            for beat, mm in ((2.5, 84), (3, 79), (3.5, 84)):
                add(block(mm), t0 + swing(beat), 0.45, 0.25)
        if mel is not None:
            notes = mel[b % len(mel)]
            if "pluck" in parts:
                for beat, ln, s in notes:
                    add(pluck(n(s), ln * BEAT), t0 + swing(beat), -0.2, 0.30 if "theremin" not in parts else 0.18)
            if "theremin" in parts:
                add(theremin_line([(bt, ln, s) for bt, ln, s in notes], t0), t0, 0.15, 0.42)
            if "pluckcounter" in parts:                       # answer phrase an octave down in the gaps
                for beat, s in ((2.5, voicing[2]), (3, voicing[1]), (3.5, voicing[0])):
                    add(pluck(n(s), 0.4 * BEAT), t0 + swing(beat), -0.5, 0.14)
        if "harpsi" in parts:                                 # rolling arpeggio, sixteenths
            seq = [n(x) for x in voicing] + [n(voicing[0]) + 12]
            for k in range(8):
                mm = seq[[0, 1, 2, 3, 2, 1, 2, 3][k]] + 12
                add(harpsi(mm, 0.5 * BEAT), t0 + swing(k * 0.5), 0.45, 0.13)
        if "bells" in parts and (b % 2 == 0 or name in ("intro", "outro")):
            add(bell(n(voicing[2]) + 12), t0, 0.55, 0.16 if name not in ('intro', 'outro') else 0.24)
            if name == "intro":
                add(bell(n(voicing[0]) + 24), t0 + 2 * BEAT, -0.55, 0.10)
        if "swoop" in parts and b in (0, 2):
            add(swoop(n("A5"), n("D5"), 2.6), t0 + 0.6 * BEAT, 0.2, 0.32)
        if "tick" in parts:                                   # an old clock in the empty market
            for beat in range(4):
                add(tick(beat % 2 == 0), t0 + beat * BEAT, -0.3 if beat % 2 else 0.3, 0.6)
        if "boo" in parts and b == 2:
            add(swoop(n("D6"), n("D4"), 1.6), t0 + 1 * BEAT, -0.1, 0.42)       # the friendly "boooo"
        if "pluckhook" in parts:
            hook = [(0, .5, "D5"), (.5, .5, "F5"), (1, .5, "A5"), (1.5, .5, "F5"), (2, 1, "D5")] if b < 3 else [(0, 2, "D5")]
            for beat, ln, s in hook:
                add(pluck(n(s), ln * BEAT), t0 + swing(beat), -0.2, 0.22 if b < 3 else 0.18)
    bar0 += bars

# ------------------------------------------------------------------ space + seamless loop
from scipy.signal import fftconvolve
ir_t = tt(2.2)
def ir(seed):
    r = np.random.default_rng(seed).standard_normal(len(ir_t)) * np.exp(-ir_t / 0.55)
    r[:int(0.015 * SR)] = 0
    r = onepole(r, 6000)
    return r / np.sqrt(np.sum(r ** 2))
wl, wr = fftconvolve(L, ir(1))[:N], fftconvolve(R, ir(2))[:N]
outL, outR = L + 0.32 * wl, R + 0.32 * wr
nl = int(LOOP * SR)
loopL, loopR = outL[:nl].copy(), outR[:nl].copy()
tail = N - nl                                                 # whatever rings past the loop point wraps to the start
loopL[:tail] += outL[nl:]; loopR[:tail] += outR[nl:]
st = np.stack([loopL, loopR], 1)
st = np.tanh(st / (np.abs(st).max() * 0.9) * 1.1)            # gentle glue
st = st / np.abs(st).max() * 10 ** (-1 / 20)
out = sys.argv[1] if len(sys.argv) > 1 else "hollowmere-festival-loop.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print(f"{BARS} bars, {LOOP:.1f} s loop")
