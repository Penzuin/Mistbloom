"""Cut the Moonlit Ballroom trailer recording to the ad music (BeepBox, 105 bpm 3/4).

Every cut lands on a beat (0.5714 s). Title-slide gap at the front, moon-window
exterior shot removed, dance-floor reveal lands on the full-waltz entrance (bar 16).
"""
import subprocess, os

SRC = "/mnt/user-data/uploads/2026-10-14_23-21-39.mkv"
MUSIC = "/root/score/out/moonlit-ballroom-ad-music.wav"
BEAT = 60 / 105
FPS = 60

# (name, slot in beats, source in, source out)  -- speed = footage / slot
EDIT = [
    ("title gap",   6,  None,  None),     # bars 1-2: mist pad, room for the title slide
    ("island",     12, 20.52, 27.38),     # theme A starts on the music box
    ("gate",       12, 27.58, 34.44),
    ("lantern",     6, 35.24, 38.67),     # build begins
    ("doorway",     9, 40.40, 45.54),     # reveal of the dance floor...
    ("orbit",      21, 45.54, 57.52),     # ...lands on bar 16, the full waltz
    ("couple",     13, 57.52, 63.59),
    ("portrait",   10, 63.59, 68.64),
    ("stage",      14, 68.64, 75.69),     # ghost choir / B section enters during the glide
    ("candelabra", 14, 75.69, 81.75),
    # 81.75-89.80 moon-window exterior: cut
    ("goodnight",  20, 89.80, 99.35),     # outro (bar 40): music box alone, dolly back out
]
FADE_OUT = 1.6   # seconds of fade to black at the end of the last shot

def run(cmd):
    subprocess.run(cmd, check=True)

def main():
    os.makedirs("seg", exist_ok=True)
    beat_pos, frame_pos, parts = 0, 0, []
    for k, (name, beats, a, b) in enumerate(EDIT):
        beat_pos += beats
        end_frame = round(beat_pos * BEAT * FPS)
        n = end_frame - frame_pos
        out = f"seg/{k:02d}.mp4"
        enc = ["-an", "-frames:v", str(n), "-r", str(FPS), "-c:v", "libx264", "-crf", "17", "-preset", "medium",
               "-pix_fmt", "yuv420p", out]
        if a is None:
            run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"color=c=black:s=1920x1080:r={FPS}"] + enc)
        else:
            speed = (b - a) / (n / FPS)
            vf = f"setpts=(PTS-STARTPTS)/{speed:.5f}"
            if abs(speed - 1) > 0.01:
                vf += f",framerate=fps={FPS}"
            vf += f",fps={FPS},tpad=stop_mode=clone:stop_duration=1"
            if k == len(EDIT) - 1:
                vf += f",fade=t=out:st={n / FPS - FADE_OUT:.3f}:d={FADE_OUT}"
            run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", SRC, "-vf", vf] + enc)
            print(f"{name:11s} {frame_pos / FPS:6.2f}s  {n / FPS:5.2f}s  speed {speed:.3f}")
        parts.append(out)
        frame_pos = end_frame
    # black tail while the last chime rings out
    music_len = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", MUSIC],
                                     capture_output=True, text=True).stdout)
    tail = round(music_len * FPS) - frame_pos
    run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"color=c=black:s=1920x1080:r={FPS}", "-an",
         "-frames:v", str(tail), "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", "seg/99.mp4"])
    parts.append("seg/99.mp4")
    open("seg/list.txt", "w").write("".join(f"file '{os.path.basename(p)}'\n" for p in parts))
    run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", "seg/list.txt", "-i", MUSIC,
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest",
         "-movflags", "+faststart", "moonlit-ballroom-ad.mp4"])
    print("total", round(music_len, 2), "s")

if __name__ == "__main__":
    main()
