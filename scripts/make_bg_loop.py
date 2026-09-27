"""Build a seamless forward-moving loop of the background video.

The clip's last FADE seconds dissolve into its first FADE seconds, and the
output starts FADE seconds in, so the last output frame and the first are
consecutive source frames and the camera never reverses.

Dev-only tool (not needed by the app): pip install imageio-ffmpeg
Usage: python scripts/make_bg_loop.py [input.mp4] [output.mp4] [fade_seconds]
"""

import re
import subprocess
import sys

import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def probe(path):
    """Return (fps, frame_count), counting frames by decoding for exactness."""
    info = subprocess.run([FFMPEG, "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    fps = float(re.search(r"([\d.]+) fps", info).group(1))
    decoded = subprocess.run(
        [FFMPEG, "-hide_banner", "-i", path, "-map", "0:v", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    frames = int(re.findall(r"frame=\s*(\d+)", decoded)[-1])
    return fps, frames


def make_loop(src, dst, fade_seconds):
    fps, frames = probe(src)
    fade = round(fade_seconds * fps)
    if frames < 3 * fade:
        sys.exit(f"Clip has {frames} frames; need at least {3 * fade} for a {fade_seconds}s crossfade.")

    body_frames = frames - fade
    offset = (body_frames - fade) / fps
    graph = (
        f"[0:v]split[a][b];"
        f"[a]trim=start_frame={fade}:end_frame={frames},setpts=PTS-STARTPTS,fps={fps:g}[body];"
        f"[b]trim=start_frame=0:end_frame={fade},setpts=PTS-STARTPTS,fps={fps:g}[head];"
        f"[body][head]xfade=transition=fade:duration={fade / fps}:offset={offset},format=yuv420p[out]"
    )
    subprocess.run(
        [
            FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-i", src,
            "-filter_complex", graph, "-map", "[out]", "-an",
            "-c:v", "libx264", "-preset", "slow", "-crf", "23",
            "-movflags", "+faststart", dst,
        ],
        check=True,
    )
    print(f"{src}: {frames} frames @ {fps:g} fps -> {dst}: {body_frames} frames ({body_frames / fps:.3f}s), {fade}-frame crossfade")


if __name__ == "__main__":
    args = sys.argv[1:]
    make_loop(
        args[0] if len(args) > 0 else "assets/skillup_bg.mp4",
        args[1] if len(args) > 1 else "assets/skillup_bg_loop.mp4",
        float(args[2]) if len(args) > 2 else 1.0,
    )
