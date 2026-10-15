"""Moonlit Ballroom ad score, written as a BeepBox song (beepbox.co).

79 s trailer, 3/4 waltz in A minor at 105 bpm (one bar = 1.714 s), 46 bars.
Built on the same original waltz theme the in-game showcase plays, so the ad
and the ballroom sound like the same place.

  bars  1-2   island reveal ......... mist pad + star chimes
  bars  3-10  gate, lantern ......... theme A, music box alone over the pad
  bars 11-15  doorway ............... bass and harp creep in, swell on E
  bars 16-31  waltz orbit, couple ... full waltz: music box, strings, pizz bass, harp
  bars 32-39  stage, candelabra ..... B section, ghost choir "ooh" joins
  bars 40-46  back out, goodnight ... strips back to the music box, last chime
"""
import json

NAMES = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}

def p(n):  # "A4" -> BeepBox pitch (A4 = 57)
    return NAMES[n[:-1]] + 12 * int(n[-1])

TPB = 4                # ticks per beat in the JSON
BAR = 3 * TPB

THEME = [  # same tune as the showcase datapack
    [(1, "E4"), (1, "A4"), (1, "B4")], [(2, "C5"), (1, "B4")], [(1, "A4"), (1, "E4"), (1, "A4")], [(3, "G4")],
    [(1, "D4"), (1, "G4"), (1, "A4")], [(2, "B4"), (1, "A4")], [(1, "G4"), (1, "E4"), (1, "G4")], [(3, "E4")],
    [(1, "E4"), (1, "A4"), (1, "B4")], [(2, "C5"), (1, "D5")], [(1, "E5"), (1, "D5"), (1, "C5")], [(3, "B4")],
    [(1, "C5"), (1, "B4"), (1, "A4")], [(2, "G4"), (1, "B4")], [(1, "A4"), (1, "C5"), (1, "B4")], [(3, "A4")],
]
THEME_CH = ["Am", "Am", "F", "G", "G", "Em", "C", "E", "Am", "Am", "F", "G", "F", "G", "Am", "Am"]

B_MEL = [
    [(1, "A4"), (1, "C5"), (1, "F5")], [(2, "E5"), (1, "D5")], [(1, "B4"), (1, "E5"), (1, "G5")], [(3, "E5")],
    [(1, "D5"), (1, "F5"), (1, "A5")], [(2, "G5"), (1, "F5")], [(1, "E5"), (1, "D5"), (1, "C5")], [(2, "B4"), (1, "G#4")],
]
B_CH = ["F", "G", "Em", "Am", "Dm", "G", "C", "E"]

CHORD = {  # root (bass), voicing (pad/harp)
    "Am": ("A2", ["A3", "C4", "E4"]), "F": ("F2", ["A3", "C4", "F4"]), "G": ("G2", ["B3", "D4", "G4"]),
    "Em": ("E2", ["B3", "E4", "G4"]), "C": ("C3", ["C4", "E4", "G4"]), "E": ("E2", ["B3", "E4", "G#4"]),
    "Dm": ("D3", ["A3", "D4", "F4"]),
}

# ---------- the bar plan: (melody bar or None, chord, section) ----------
PLAN = []
PLAN += [(None, "Am", "intro")] * 2
PLAN += [(THEME[i], THEME_CH[i], "a_solo") for i in range(8)]
PLAN += [(THEME[i], THEME_CH[i], "build") for i in (8, 9, 10, 11)] + [(B_MEL[7], "E", "build")]
PLAN += [(THEME[i], THEME_CH[i], "waltz") for i in range(16)]
PLAN += [(B_MEL[i], B_CH[i], "b") for i in range(8)]
PLAN += [(THEME[i], THEME_CH[i], "outro") for i in (0, 1, 2, 3)] + [(THEME[14], "Am", "outro"), (None, "Am", "end"), (None, "Am", "end")]
assert len(PLAN) == 46, len(PLAN)

def note(pitches, start, length, v0, v1=None):
    v1 = v0 if v1 is None else v1
    return {"pitches": [p(x) for x in pitches], "points": [{"tick": start, "pitchBend": 0, "volume": v0},
                                                          {"tick": start + length, "pitchBend": 0, "volume": v1}]}

def up(n, k=1):
    return n[:-1] + str(int(n[-1]) + k)

# ---------- per-bar note writers ----------
def melody(bar, sec, k):
    mel, ch, _ = PLAN[k]
    if mel is None:
        return []
    vol = {"a_solo": 70, "build": 78, "waltz": 92, "b": 96, "outro": 66}[sec]
    if sec == "outro":
        vol = 66 - 6 * max(0, k - 39)
    out, t = [], 0
    for beats, n in mel:
        out.append(note([up(n)], t * TPB, beats * TPB, vol, vol - 20 if beats > 1 else vol))
        t += beats
    if k == 43:  # last outro phrase: hold the final A
        out = out[:-1] + [note([up("A4")], 2 * TPB, TPB, vol)]
    return out

def pad(bar, sec, k):
    ch = CHORD[PLAN[k][1]][1]
    v = {"intro": 55, "a_solo": 50, "build": 58, "waltz": 52, "b": 60, "outro": 45, "end": 40}[sec]
    if k == 0:
        return [note(ch, 0, BAR, 10, 55)]
    if k == 45:
        return [note(["A3", "C4", "E4"], 0, BAR, 35, 0)]
    return [note(ch, 0, BAR, v)]

def bass(bar, sec, k):
    if sec in ("intro", "a_solo", "end"):
        return []
    root = CHORD[PLAN[k][1]][0]
    v = {"build": 40 + 10 * (k - 10), "waltz": 90, "b": 90, "outro": 55}[sec]
    if sec == "outro" and k >= 42:
        v = 40
    return [note([root], 0, TPB, min(v, 90))]

def harp(bar, sec, k):
    """The 'pah-pah' of the waltz on beats 2 and 3."""
    if sec in ("intro", "a_solo", "end") or (sec == "build" and k < 12):
        return []
    ch = CHORD[PLAN[k][1]][1][1:]
    v = {"build": 45, "waltz": 70, "b": 72, "outro": 40}[sec]
    if sec == "outro" and k >= 42:
        return []
    return [note(ch, TPB, TPB, v), note(ch, 2 * TPB, TPB, v)]

def choir(bar, sec, k):
    """Ghost choir 'ooh' in the B section: long top notes of each chord."""
    if sec != "b":
        return []
    top = up(CHORD[PLAN[k][1]][1][-1], 0)
    return [note([top, CHORD[PLAN[k][1]][1][0]], 0, BAR, 45 if k < 35 else 60, 40)]

SPARKLE = {0: [("E6", 2), ("B6", 1)], 1: [("A6", 0), ("E6", 2)], 9: [("E6", 2)], 14: [("G#6", 1), ("B6", 2)],
           15: [("A6", 0)], 23: [("E6", 2)], 30: [("E6", 2)], 38: [("G#6", 2)], 44: [("E6", 1)], 45: [("A6", 0)]}

def chime(bar, sec, k):
    hits = sorted(SPARKLE.get(k, []), key=lambda h: h[1])
    ends = [b for _, b in hits[1:]] + [3]     # a chime rings until the next one (one channel can't overlap notes)
    return [note([n], b * TPB, TPB * (e - b), 55 if k < 39 else 45) for (n, b), e in zip(hits, ends)]

# ---------- instruments (BeepBox presets, lightly tuned) ----------
MUSIC_BOX = {"type": "Picked String", "volume": 100, "eqFilter": [{"type": "low-pass", "cutoffHz": 4756.83, "linearGain": 0.5}],
             "effects": ["reverb"], "reverb": 55, "fadeInSeconds": 0, "fadeOutTicks": 48, "chord": "strum",
             "harmonics": [100, 0, 0, 100, 0, 0, 0, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 0, 86, 0, 0, 0, 0, 0, 0, 71, 0],
             "unison": "none", "stringSustain": 64, "envelopes": []}
WARM_PAD = {"type": "FM", "volume": 70, "eqFilter": [], "effects": ["note filter", "chorus", "reverb"],
            "noteFilter": [{"type": "low-pass", "cutoffHz": 2378.41, "linearGain": 1}], "chorus": 100, "reverb": 60,
            "fadeInSeconds": 0.15, "fadeOutTicks": 96, "chord": "simultaneous", "algorithm": "1←(2 3 4)", "feedbackType": "1⟲",
            "feedbackAmplitude": 5, "operators": [{"frequency": "1×", "amplitude": 13}, {"frequency": "1×", "amplitude": 5},
                                                  {"frequency": "1×", "amplitude": 0}, {"frequency": "1×", "amplitude": 0}],
            "envelopes": [{"target": "noteFilterAllFreqs", "envelope": "swell 3"}]}
PIZZ_BASS = {"type": "Picked String", "volume": 85, "eqFilter": [{"type": "low-pass", "cutoffHz": 1414.21, "linearGain": 1}],
             "effects": ["reverb"], "reverb": 30, "fadeInSeconds": 0, "fadeOutTicks": 24, "chord": "simultaneous",
             "harmonics": [100, 71, 43, 29, 14, 14, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
             "unison": "none", "stringSustain": 43, "envelopes": []}
HARP = {"type": "Picked String", "volume": 60, "eqFilter": [{"type": "low-pass", "cutoffHz": 2828.43, "linearGain": 0.7071}],
        "effects": ["reverb"], "reverb": 50, "fadeInSeconds": 0, "fadeOutTicks": 24, "chord": "strum",
        "harmonics": [100, 57, 29, 14, 14, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "unison": "none", "stringSustain": 57, "envelopes": []}
GHOST_CHOIR = {"type": "harmonics", "volume": 55, "eqFilter": [{"type": "low-pass", "cutoffHz": 2000, "linearGain": 1}],
               "effects": ["vibrato", "chorus", "reverb"], "vibrato": "shaky", "chorus": 100, "reverb": 80,
               "fadeInSeconds": 0.3, "fadeOutTicks": 96, "chord": "simultaneous",
               "harmonics": [100, 57, 43, 43, 14, 14, 0, 0, 0, 14, 29, 29, 14, 0, 14, 29, 29, 14, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
               "unison": "none", "envelopes": []}
CHIME = {"type": "Picked String", "volume": 55, "eqFilter": [{"type": "low-pass", "cutoffHz": 4000, "linearGain": 0.5},
                                                             {"type": "high-pass", "cutoffHz": 105.11, "linearGain": 0.3536}],
         "effects": ["reverb"], "reverb": 80, "fadeInSeconds": 0, "fadeOutTicks": 96, "chord": "strum",
         "harmonics": [43, 71, 0, 100, 0, 100, 0, 86, 0, 0, 86, 0, 14, 71, 14, 14, 57, 14, 14, 43, 14, 14, 43, 14, 14, 43, 14, 14],
         "unison": "shimmer", "stringSustain": 86, "envelopes": []}

TRACKS = [("Music box", MUSIC_BOX, melody, 4), ("Mist pad", WARM_PAD, pad, 3), ("Pizz bass", PIZZ_BASS, bass, 1),
          ("Harp", HARP, harp, 3), ("Ghost choir", GHOST_CHOIR, choir, 3), ("Star chimes", CHIME, chime, 5)]

def build():
    chans = []
    for name, inst, fn, octv in TRACKS:
        pats, seq, seen = [], [], {}
        for k, (_, _, sec) in enumerate(PLAN):
            notes = fn(k, sec, k)
            if not notes:
                seq.append(0)
                continue
            key = json.dumps(notes)
            if key not in seen:
                pats.append({"notes": notes})
                seen[key] = len(pats)
            seq.append(seen[key])
        chans.append({"type": "pitch", "name": name, "instruments": [inst], "patterns": pats or [{"notes": []}],
                      "sequence": seq, "octaveScrollBar": octv})
    return {"format": "BeepBox", "version": 9, "scale": "expert", "key": "C", "introBars": 0, "loopBars": len(PLAN),
            "beatsPerBar": 3, "ticksPerBeat": TPB, "beatsPerMinute": 105, "layeredInstruments": False,
            "patternInstruments": False, "channels": chans}

if __name__ == "__main__":
    json.dump(build(), open("moonlit-ballroom-ad.json", "w"), ensure_ascii=False)
    print("bars", len(PLAN), "seconds", round(len(PLAN) * 3 * 60 / 105, 2))
