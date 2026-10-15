"""Halloween Festival trailer score, written as a BeepBox song (beepbox.co).

43 bars of 4/4 at 116 bpm (one bar = 2.069 s, 89 s), D minor. Built on the same original festival
theme the in-game showcase plays (hollowmere/music/festival.py), so the ad and the island sound
like the same place. Cut points of the edit land on these bar lines.

  bars  1-2   title ................... organ pad + bells, a friendly theremin swoop
  bars  3-6   island arrival .......... pad and bells keep building, chimes like distant lanterns
  bars  7-14  gate, lantern lane ...... theme A on the music-box pluck, oom-pah bass, kick + snap
  bars 15-22  cat, bonfire, orbit ..... theme A again, ghostly theremin lead takes it, shaker joins
  bars 23-30  orbit, stall, witch ..... B section, harp arpeggios, wood blocks
  bars 31-34  graveyard ............... break: drums out, ticking clock, the "boooo" swoop
  bars 35-38  patch ................... theme A, everyone back in
  bars 39-43  goodnight ............... strips back to the pluck hook and bells, last chord rings
"""
import json

NAMES = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
         "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def p(n):              # "A4" -> BeepBox pitch (A4 = 57)
    return NAMES[n[:-1]] + 12 * int(n[-1])


TPB = 4                # ticks per beat
BAR = 4 * TPB

# the festival theme (same notes as the in-game loop): per bar (beat, length, note)
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
PROG_A = ["Dm", "Dm", "Bb", "A7", "Dm", "Gm", "A7", "Dm"]
PROG_B = ["F", "C", "Gm", "Dm", "Bb", "F", "Gm", "A7"]
CHORD = {"Dm": ("D2", ["D4", "F4", "A4"]), "Bb": ("Bb1", ["D4", "F4", "Bb4"]), "Gm": ("G2", ["D4", "G4", "Bb4"]),
         "A7": ("A1", ["C#4", "E4", "G4"]), "F": ("F2", ["C4", "F4", "A4"]), "C": ("C2", ["C4", "E4", "G4"])}
HOOK = [(0, .5, "D5"), (.5, .5, "F5"), (1, .5, "A5"), (1.5, .5, "F5"), (2, 1, "D5")]

# ---------------- bar plan: (melody bar or None, chord, section)
PLAN = []
PLAN += [(None, c, "title") for c in ("Dm", "Bb")]
PLAN += [(None, c, "arrive") for c in ("Gm", "A7", "Dm", "A7")]
PLAN += [(MEL_A[i], PROG_A[i], "a1") for i in range(8)]
PLAN += [(MEL_A[i], PROG_A[i], "a2") for i in range(8)]
PLAN += [(MEL_B[i], PROG_B[i], "b") for i in range(8)]
PLAN += [(None, c, "break") for c in ("Dm", "Dm", "Bb", "A7")]
PLAN += [(MEL_A[i], PROG_A[i], "a3") for i in range(4)]
PLAN += [(HOOK, "Dm", "outro"), (HOOK, "Bb", "outro"), (HOOK, "A7", "outro"), ([(0, 4, "D5")], "Dm", "outro"),
         (None, "Dm", "end")]
assert len(PLAN) == 43, len(PLAN)
SEC_START = {s: next(k for k, x in enumerate(PLAN) if x[2] == s) for s in ("a1", "a2", "b", "break", "a3", "outro")}


def note(pitches, start, length, v0, v1=None):
    v1 = v0 if v1 is None else v1
    return {"pitches": [p(x) if isinstance(x, str) else x for x in pitches],
            "points": [{"tick": int(start), "pitchBend": 0, "volume": v0}, {"tick": int(start + length), "pitchBend": 0, "volume": v1}]}


def up(n, k=1):
    return n[:-1] + str(int(n[-1]) + k)


def down(n, k=1):
    return n[:-1] + str(int(n[-1]) - k)


# ---------------- per-bar writers
def pluck(k, sec):
    mel = PLAN[k][0]
    if mel is None or sec == "a2":
        return []
    vol = {"a1": 80, "b": 74, "a3": 84, "outro": 70}[sec]
    if sec == "outro":
        vol = 72 - 6 * (k - SEC_START["outro"])
    return [note([n], b * TPB, l * TPB, vol, vol - 25 if l >= 1 else vol) for b, l, n in mel]


def theremin(k, sec):
    mel = PLAN[k][0]
    if sec in ("a2", "a3") and mel is not None:
        return [note([down(n)], b * TPB, l * TPB, 78, 70) for b, l, n in mel]
    if sec == "title" and k == 1:                          # opening swoop A5 -> D5
        n = note(["A4"], 2, 12, 0, 60)
        n["points"] = [{"tick": 2, "pitchBend": 0, "volume": 0}, {"tick": 6, "pitchBend": 0, "volume": 60},
                       {"tick": 14, "pitchBend": -7, "volume": 0}]
        return [n]
    if sec == "break" and k == SEC_START["break"] + 2:     # the friendly "boooo"
        n = note(["D5"], 4, 10, 0, 0)
        n["points"] = [{"tick": 4, "pitchBend": 0, "volume": 0}, {"tick": 7, "pitchBend": 0, "volume": 75},
                       {"tick": 14, "pitchBend": -12, "volume": 0}]
        return [n]
    return []


def counter(k, sec):
    """Music-box answer phrase in the gaps of theme A2."""
    if sec != "a2":
        return []
    v = CHORD[PLAN[k][1]][1]
    return [note([up(v[2])], 10, 2, 50), note([up(v[1])], 12, 2, 46), note([up(v[0])], 14, 2, 42)]


def pad(k, sec):
    ch = CHORD[PLAN[k][1]][1]
    v = {"title": 62, "arrive": 64, "a1": 44, "a2": 42, "b": 46, "break": 60, "a3": 42, "outro": 48, "end": 44}[sec]
    if k == 0:
        return [note(ch, 0, BAR, 5, 62)]
    if sec == "end":
        return [note(["D4", "F4", "A4"], 0, BAR, 44, 0)]
    return [note(ch, 0, BAR, v)]


def bass(k, sec):
    if sec in ("title", "arrive", "break", "end"):
        return []
    r = CHORD[PLAN[k][1]][0]
    v = 88 if sec != "outro" else 60 - 6 * (k - SEC_START["outro"])
    if sec == "outro" and k - SEC_START["outro"] >= 3:
        return [note([r], 0, 8, v)]
    fifth = {"D2": "A2", "Bb1": "F2", "G2": "D3", "A1": "E2", "F2": "C3", "C2": "G2"}[r]
    return [note([r], 0, 3, v), note([fifth], 6, 2, v - 15), note([r], 8, 3, v), note([up(r)], 14, 2, v - 15)]


def harp(k, sec):
    if sec not in ("b", "a3"):
        return []
    v = CHORD[PLAN[k][1]][1]
    seq = [up(v[0]), up(v[1]), up(v[2]), up(v[0], 2), up(v[2]), up(v[1]), up(v[2]), up(v[0], 2)]
    return [note([n], i * 2, 2, 50 if sec == "b" else 40) for i, n in enumerate(seq)]


def bells(k, sec):
    ch = CHORD[PLAN[k][1]][1]
    if sec in ("title", "arrive"):
        out = [note([up(ch[2])], 0, 8, 60)]
        if sec == "arrive" or k == 1:
            out.append(note([up(ch[0], 2)], 8, 8, 40))
        return out
    if sec in ("a2", "a3") and k % 2 == 0:
        return [note([up(ch[2])], 0, 16, 45)]
    if sec == "outro":
        return [note([up(ch[2])], 0, 16, 50 - 5 * (k - SEC_START["outro"]))]
    if sec == "end":
        return [note(["D6"], 0, 16, 45, 0)]
    if sec == "break":                                     # an old clock ticking in the empty market
        return [note(["A6" if i % 2 == 0 else "E6"], i * 4, 1, 28) for i in range(4)]
    return []


# drum channel: noise pitches 0 (low) .. 11 (high)
def drums(k, sec):
    if sec in ("title", "arrive", "break", "end"):
        if sec == "arrive" and k == SEC_START["a1"] - 1:     # little pickup fill into the theme
            return [note([4], 8, 2, 40), note([6], 12, 2, 50), note([8], 14, 2, 60)]
        return []
    if sec == "outro":
        if k - SEC_START["outro"] >= 3:
            return []
        return [note([1], 0, 2, 60), note([1], 8, 2, 55)]
    out = [note([1], 0, 2, 90), note([1], 8, 2, 85),          # kick on 1 and 3
           note([7], 4, 2, 55), note([7], 12, 2, 55)]          # snap on 2 and 4
    return out


def shaker(k, sec):
    if sec not in ("a2", "b", "a3"):
        return []
    return [note([11], i * 2, 1, 32 if i % 2 else 20) for i in range(8)]


def block(k, sec):
    if sec != "b" or k % 2 == 0:
        return []
    return [note(["A5"], 10, 2, 60), note(["E5"], 12, 2, 55), note(["A5"], 14, 2, 60)]


# ---------------- instruments (BeepBox presets, lightly tuned)
PLUCK = {"type": "Picked String", "volume": 100, "eqFilter": [{"type": "low-pass", "cutoffHz": 4756.83, "linearGain": 0.5}],
         "effects": ["reverb"], "reverb": 45, "fadeInSeconds": 0, "fadeOutTicks": 24, "chord": "strum",
         "harmonics": [100, 0, 86, 0, 71, 0, 57, 0, 43, 0, 29, 0, 14, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
         "unison": "none", "stringSustain": 43, "envelopes": []}
THEREMIN = {"type": "harmonics", "volume": 70, "eqFilter": [{"type": "low-pass", "cutoffHz": 2378.41, "linearGain": 1}],
            "effects": ["vibrato", "reverb"], "vibrato": "delayed", "reverb": 70, "fadeInSeconds": 0.05, "fadeOutTicks": 48,
            "chord": "simultaneous",
            "harmonics": [100, 29, 14, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "unison": "none", "envelopes": []}
ORGAN = {"type": "FM", "volume": 60, "eqFilter": [], "effects": ["note filter", "chorus", "reverb"],
         "noteFilter": [{"type": "low-pass", "cutoffHz": 2378.41, "linearGain": 1}], "chorus": 100, "reverb": 60,
         "fadeInSeconds": 0.1, "fadeOutTicks": 96, "chord": "simultaneous", "algorithm": "1←(2 3 4)", "feedbackType": "1⟲",
         "feedbackAmplitude": 4, "operators": [{"frequency": "1×", "amplitude": 13}, {"frequency": "2×", "amplitude": 6},
                                               {"frequency": "1×", "amplitude": 0}, {"frequency": "1×", "amplitude": 0}],
         "envelopes": [{"target": "noteFilterAllFreqs", "envelope": "swell 3"}]}
BASS = {"type": "Picked String", "volume": 85, "eqFilter": [{"type": "low-pass", "cutoffHz": 1414.21, "linearGain": 1}],
        "effects": ["reverb"], "reverb": 25, "fadeInSeconds": 0, "fadeOutTicks": 24, "chord": "simultaneous",
        "harmonics": [100, 71, 43, 29, 14, 14, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "unison": "none", "stringSustain": 43, "envelopes": []}
HARP = {"type": "Picked String", "volume": 55, "eqFilter": [{"type": "low-pass", "cutoffHz": 2828.43, "linearGain": 0.7071}],
        "effects": ["reverb"], "reverb": 50, "fadeInSeconds": 0, "fadeOutTicks": 24, "chord": "strum",
        "harmonics": [100, 57, 29, 14, 14, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "unison": "none", "stringSustain": 57, "envelopes": []}
BELL = {"type": "Picked String", "volume": 55, "eqFilter": [{"type": "low-pass", "cutoffHz": 4000, "linearGain": 0.5},
                                                            {"type": "high-pass", "cutoffHz": 105.11, "linearGain": 0.3536}],
        "effects": ["reverb"], "reverb": 80, "fadeInSeconds": 0, "fadeOutTicks": 96, "chord": "strum",
        "harmonics": [43, 71, 0, 100, 0, 100, 0, 86, 0, 0, 86, 0, 14, 71, 14, 14, 57, 14, 14, 43, 14, 14, 43, 14, 14, 43, 14, 14],
        "unison": "shimmer", "stringSustain": 86, "envelopes": []}
BLOCK = {"type": "Picked String", "volume": 45, "eqFilter": [{"type": "low-pass", "cutoffHz": 5656.85, "linearGain": 1}],
         "effects": ["reverb"], "reverb": 20, "fadeInSeconds": 0, "fadeOutTicks": 12, "chord": "simultaneous",
         "harmonics": [100, 0, 0, 71, 0, 0, 0, 43, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
         "unison": "none", "stringSustain": 0, "envelopes": []}
KIT = {"type": "noise", "volume": 45, "eqFilter": [{"type": "low-pass", "cutoffHz": 6727.17, "linearGain": 1}],
       "effects": ["reverb"], "reverb": 20, "fadeInSeconds": 0, "fadeOutTicks": -3, "wave": "retro",
       "envelopes": [{"target": "noteVolume", "envelope": "decay 2"}]}
SHAKER = {"type": "noise", "volume": 40, "eqFilter": [{"type": "high-pass", "cutoffHz": 4000, "linearGain": 1}],
          "effects": [], "fadeInSeconds": 0, "fadeOutTicks": -3, "wave": "white",
          "envelopes": [{"target": "noteVolume", "envelope": "decay 3"}]}

TRACKS = [("Pumpkin pluck", "pitch", PLUCK, pluck, 4), ("Theremin", "pitch", THEREMIN, theremin, 4),
          ("Music box", "pitch", PLUCK, counter, 4), ("Organ", "pitch", ORGAN, pad, 3), ("Bass", "pitch", BASS, bass, 1),
          ("Harp", "pitch", HARP, harp, 3), ("Bells", "pitch", BELL, bells, 5), ("Wood block", "pitch", BLOCK, block, 4),
          ("Kit", "drum", KIT, drums, 0), ("Shaker", "drum", SHAKER, shaker, 0)]


def build():
    chans = []
    for name, kind, inst, fn, octv in TRACKS:
        pats, seq, seen = [], [], {}
        for k, (_, _, sec) in enumerate(PLAN):
            notes = fn(k, sec)
            if not notes:
                seq.append(0); continue
            key = json.dumps(notes)
            if key not in seen:
                pats.append({"notes": notes}); seen[key] = len(pats)
            seq.append(seen[key])
        ch = {"type": kind, "name": name, "instruments": [inst], "patterns": pats or [{"notes": []}], "sequence": seq}
        if kind == "pitch":
            ch["octaveScrollBar"] = octv
        chans.append(ch)
    return {"format": "BeepBox", "version": 9, "scale": "expert", "key": "C", "introBars": 0, "loopBars": len(PLAN),
            "beatsPerBar": 4, "ticksPerBeat": TPB, "beatsPerMinute": 116, "layeredInstruments": False,
            "patternInstruments": False, "channels": chans}


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "halloween-festival-ad.json"
    json.dump(build(), open(out, "w"), ensure_ascii=False)
    print("bars", len(PLAN), "seconds", round(len(PLAN) * 4 * 60 / 116, 2))
