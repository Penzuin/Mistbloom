"""Moonlit Ballroom ad, v2: same beat-matched cut as edit.py, with dissolves instead of hard cuts.

Each dissolve is centred on its beat, so the timing against the music doesn't move.
Clips get extra frames ("handles") on each side for the overlap: real footage where the
shot has some to spare, otherwise a held frame under the dissolve, so no shot changes speed.
"""
import subprocess, os, sys
REUSE = "--reuse" in sys.argv   # keep already-rendered clips, redo only the dissolves

SRC = "/mnt/user-data/uploads/2026-10-14_23-21-39.mkv"
TITLE = "/root/cut/title.mp4"   # moonlit-ballroom/media/title/moonlit-ballroom-title.mp4
MUSIC = "/root/score/out/moonlit-ballroom-ad-music-v2.wav"   # 42-bar version
BEAT = 60 / 105
FPS = 60
M = 2 / FPS                      # keep 2 frames clear of a camera cut in the recording

# (name, beats, src in, src out, shot start, shot end, transition INTO the next clip, its length in beats)
EDIT = [
    ("title",       9,  0.00,  5.00,  0.00,  5.00, "fade",      2),   # title fades to dark, island drifts in
    ("island",      9, 22.24, 27.38, 19.15, 27.38, "fade",      1),
    ("gate",       12, 27.58, 34.44, 27.38, 34.44, "fade",      1),
    ("lantern",     6, 35.24, 38.67, 34.44, 39.47, "fade",      1),
    ("doorway",     9, 40.40, 45.54, 39.47, 45.54, "fade",      1),   # the hall opens on the full waltz
    ("orbit",      21, 45.54, 57.52, 45.54, 57.52, "fade",      1),
    ("couple",     13, 57.52, 63.59, 57.52, 63.59, "fade",      1),
    ("portrait",   11, 63.59, 68.64, 63.59, 68.64, "fade",      1),
    ("stage",      15, 68.64, 75.69, 68.64, 75.69, "fade",    1.5),   # B phrase + choir; slower dissolve into the outro
    # candelabra close-up: cut
    ("goodnight",  21, 89.80, 99.35, 89.80, 99.35, None,        0),   # runs to the end of the last bar, no black
]
AUDIO_FADE = 1.5  # music fades under the final frames

def run(cmd):
    subprocess.run(cmd, check=True)

def main():
    os.makedirs("seg2", exist_ok=True)
    starts, t = [], 0.0
    for e in EDIT:
        starts.append(t); t += e[1] * BEAT
    music_len = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", MUSIC],
                                     capture_output=True, text=True).stdout)
    clips = []
    for k, (name, beats, a, b, s0, s1, _, _) in enumerate(EDIT):
        pre = EDIT[k - 1][7] * BEAT / 2 if k else 0.0          # half of the dissolve coming in
        post = EDIT[k][7] * BEAT / 2                            # half of the dissolve going out
        L = beats * BEAT + pre + post
        n = round(L * FPS)
        slot_speed = (b - a) / (beats * BEAT)
        # borrow real footage for the handles where the shot allows, at the clip's own speed
        a2 = max(s0 + M, a - pre * slot_speed) if k else a
        b2 = min(s1 - M, b + post * slot_speed)
        speed = slot_speed
        lead = pre - (a - a2) / speed                           # handle with no footage before it: hold the first frame
        vf = f"setpts=(PTS-STARTPTS)/{speed:.5f}"
        if abs(speed - 1) > 0.01:
            vf += f",framerate=fps={FPS}"
        vf += f",fps={FPS},tpad=start_mode=clone:start_duration={max(0.0, lead):.4f}:stop_mode=clone:stop_duration=5,setsar=1,format=yuv420p"
        out = f"seg2/{k:02d}.mp4"
        if not (REUSE and os.path.exists(out)):
          run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{a2:.3f}", "-to", f"{b2:.3f}", "-i", TITLE if k == 0 else SRC,
             "-vf", vf, "-an", "-frames:v", str(n), "-r", str(FPS), "-c:v", "libx264", "-crf", "15", "-preset", "fast", out])
        clips.append((out, n / FPS, pre))
        print(f"{name:11s} {starts[k]:6.2f}s  clip {n / FPS:5.2f}s  speed {speed:.3f}  handles {pre:.2f}/{post:.2f}")
    # chain the dissolves
    inputs, fc, prev = [], [], "[0:v]"
    for out, _, _ in clips:
        inputs += ["-i", out]
    for k in range(1, len(clips)):
        tr, tb = EDIT[k - 1][6], EDIT[k - 1][7]
        d = tb * BEAT
        offset = starts[k] - d / 2
        lab = f"[x{k}]"
        fc.append(f"{prev}[{k}:v]xfade=transition={tr}:duration={d:.4f}:offset={offset:.4f}{lab}")
        prev = lab
    end = sum(e[1] for e in EDIT) * BEAT                        # 42 bars, 72.0 s: video ends on the last shot
    fc.append(f"[{len(clips)}:a]atrim=duration={end:.4f},afade=t=out:st={end - AUDIO_FADE:.4f}:d={AUDIO_FADE}[a]")
    fc.append(f"{prev}trim=duration={end:.4f},"
              f"setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709[v]")
    run(["ffmpeg", "-loglevel", "error", "-y"] + inputs + ["-i", MUSIC, "-filter_complex", ";".join(fc),
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "moonlit-ballroom-ad-v2.mp4"])

if __name__ == "__main__":
    main()
