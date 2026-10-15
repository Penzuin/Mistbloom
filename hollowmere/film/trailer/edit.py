"""Halloween Festival trailer: beat-matched cut of the MistCam film with soft dissolves (same method as the
Moonlit Ballroom ad). Every cut sits on a bar or half-bar of the 116 bpm score; each dissolve is centred on
its beat. Clips get handles for the overlap: real footage where the shot has some to spare, otherwise a
held frame. Shots longer than their slot are trimmed (never sped up); shorter ones are slowed slightly."""
import os, subprocess, sys

SRC = "/mnt/user-data/uploads/2026-10-15_09-44-17.mkv"
TITLE = "title.mp4"
MUSIC = "score.wav"
BEAT = 60 / 116
FPS = 60
M = 3 / FPS                     # stay clear of the camera cuts in the recording
REUSE = "--reuse" in sys.argv

# shot boundaries in the recording (scene detection)
SHOT = {"arrival": (5.788, 15.038), "gate": (15.038, 22.088), "lane": (22.088, 30.138), "cat": (30.138, 35.288),
        "bonfire": (35.288, 43.738), "orbit": (43.738, 55.738), "stall": (55.738, 60.788), "witch": (60.788, 67.871),
        "graveyard": (67.871, 75.921), "patch": (75.921, 83.938), "goodnight": (83.938, 94.504)}

# (shot, beats, where to sit a trimmed window: 0 = start, 0.5 = centre, 1 = end, dissolve INTO next (beats))
EDIT = [
    ("title",      8, 0.0, 2),
    ("arrival",   16, 1.0, 1),      # keep the end of the drift, where the island fills the frame
    ("gate",      12, 0.3, 1),
    ("lane",      16, 0.0, 1),
    ("cat",        8, 0.4, 1),
    ("bonfire",   16, 0.5, 1),
    ("orbit",     24, 0.0, 1),
    ("stall",      8, 0.5, 1),
    ("witch",     12, 0.6, 1.5),    # slower dissolve into the graveyard break
    ("graveyard", 16, 0.0, 1),
    ("patch",     14, 1.0, 1.5),    # keep the crane up to the barn
    ("goodnight", 22, 0.0, 0),      # runs to the last bar, no black screen
]
AUDIO_FADE = 2.5


def run(cmd):
    subprocess.run(cmd, check=True)


def main(out="halloween-festival-ad.mp4"):
    os.makedirs("seg", exist_ok=True)
    starts, t = [], 0.0
    for e in EDIT:
        starts.append(t); t += e[1] * BEAT
    end = t
    clips = []
    for k, (name, beats, sit, _) in enumerate(EDIT):
        pre = EDIT[k - 1][3] * BEAT / 2 if k else 0.0
        post = EDIT[k][3] * BEAT / 2
        slot = beats * BEAT
        n = round((slot + pre + post) * FPS)
        if name == "title":
            s0, s1 = 0.0, 5.5
        else:
            s0, s1 = SHOT[name][0] + M, SHOT[name][1] - M
        avail = s1 - s0
        if avail >= slot:                                   # trim, real speed
            speed = 1.0
            a = s0 + (avail - slot) * sit
        else:                                               # a little slow-motion to fill the slot
            speed = avail / slot
            a = s0
        b = a + slot * speed
        a2 = max(s0, a - pre * speed)                       # handles from real footage where possible
        b2 = min(s1, b + post * speed)
        lead = pre - (a - a2) / speed                       # missing lead-in: hold the first frame
        vf = f"setpts=(PTS-STARTPTS)/{speed:.5f}"
        if abs(speed - 1) > 0.005:
            pass
        vf += f",fps={FPS},tpad=start_mode=clone:start_duration={max(0.0, lead):.4f}:stop_mode=clone:stop_duration=5,setsar=1,format=yuv420p"
        seg = f"seg/{k:02d}.mp4"
        if not (REUSE and os.path.exists(seg)):
            run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{a2:.3f}", "-to", f"{b2:.3f}", "-i", TITLE if k == 0 else SRC,
                 "-vf", vf, "-an", "-frames:v", str(n), "-r", str(FPS), "-c:v", "libx264", "-crf", "14", "-preset", "fast", seg])
        clips.append(seg)
        print(f"{name:10s} {starts[k]:6.2f}s  slot {slot:5.2f}s  speed {speed:.3f}  src {a:6.2f}-{b:6.2f}")
    inputs, fc, prev = [], [], "[0:v]"
    for c in clips:
        inputs += ["-i", c]
    for k in range(1, len(clips)):
        d = EDIT[k - 1][3] * BEAT
        lab = f"[x{k}]"
        fc.append(f"{prev}[{k}:v]xfade=transition=fade:duration={d:.4f}:offset={starts[k] - d / 2:.4f}{lab}")
        prev = lab
    # light grade: a touch of contrast and warmth so the night footage doesn't look washed out
    fc.append(f"{prev}trim=duration={end:.4f},eq=contrast=1.05:saturation=1.08:gamma=0.98,"
              f"colorbalance=rm=0.02:bm=-0.01,setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709[v]")
    fc.append(f"[{len(clips)}:a]atrim=duration={end:.4f},afade=t=out:st={end - AUDIO_FADE:.4f}:d={AUDIO_FADE}[a]")
    run(["ffmpeg", "-loglevel", "error", "-y"] + inputs + ["-i", MUSIC, "-filter_complex", ";".join(fc),
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", out])
    print("total", round(end, 2), "s ->", out)


if __name__ == "__main__":
    main()
