#!/usr/bin/env python3
"""Build web photos and trimmed videos from the supplied WeTransfer media.
The brand logo is retained from the archive. Originals are never modified.
"""
import os
import argparse
import subprocess
from pathlib import Path
from collections import deque
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "source/live-site/content/www.shearearth.com/wp-content/uploads")
OUT = os.path.join(ROOT, "wordpress/plugin/spe-site-importer/media")

# Supplied filename -> published filename. Names describe the subject so the
# client can recognise them in the WordPress media library.
PHOTOS = {
    "IMG_7698.jpeg": "team-and-mulcher.jpg",
    "IMG_7699.jpeg": "mulching-teeth.jpg",
    "IMG_7700.jpeg": "forestry-equipment.jpg",
    "IMG_7701.jpeg": "mulcher-attachment.jpg",
    "IMG_7702.jpeg": "hydraulic-detail.jpg",
    "IMG_7703.jpeg": "tracked-loader.jpg",
    "IMG_7708.jpeg": "woodland-worksite.jpg",
}
CLIPS = {
    "forestry-mulching": ("IMG_7706.mov", 3, 18),
    "brush-removal": ("IMG_7707.mov", 0, 14),
    "woodland-edge": ("IMG_7710.mov", 3, 18),
    "clearing-pass": ("IMG_7705.mov", 4, 16),
    "mulcher-at-work": ("IMG_7709.mov", 2, 16),
}

LOGO = "2024/10/calvin_shear_performance.png"

def build_photos(source):
    for original, name in PHOTOS.items():
        im = ImageOps.exif_transpose(Image.open(source / original)).convert("RGB")
        im.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
        im.save(os.path.join(OUT, name), "JPEG", quality=85, optimize=True, progressive=True)
        print(f"{name:28} {im.width}x{im.height}", flush=True)


def build_clips(source):
    for name, (original, start, duration) in CLIPS.items():
        # The largest player is 350px wide.  A 640px rendition stays sharp on
        # desktop high-density displays, while the 480px file avoids sending
        # substantially more pixels than a phone can show.
        renditions = (
            (".mp4", "640:-2", "29", "1200k", "2400k"),
            ("-mobile.mp4", "480:-2", "31", "700k", "1400k"),
        )
        for suffix, size, crf, maxrate, bufsize in renditions:
            subprocess.run([
                "ffmpeg", "-v", "error", "-y", "-ss", str(start), "-i", str(source / original),
                "-t", str(duration), "-map", "0:v:0", "-an", "-map_metadata", "-1",
                "-vf", f"scale={size},setsar=1",
                "-c:v", "libx264", "-threads", "2", "-preset", "medium", "-crf", crf, "-maxrate", maxrate, "-bufsize", bufsize,
                "-pix_fmt", "yuv420p", "-r", "30", "-movflags", "+faststart",
                os.path.join(OUT, name + suffix),
            ], check=True)
        subprocess.run([
            "ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", os.path.join(OUT, name + ".mp4"),
            "-frames:v", "1", "-update", "1", os.path.join(OUT, name + ".jpg"),
        ], check=True)
        print(f"{name:28} {duration}s, 640px desktop + 480px mobile H.264, silent + poster", flush=True)


def transparent_background(im, tolerance=26):
    """Flood-fill the uniform backdrop from the edges and clear its alpha.

    The logo is drawn on a solid #1b1a1d card and is ringed by a light outline,
    so an edge-seeded fill stops at the artwork instead of eating into it.
    """
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    bg = px[0, 0][:3]
    seen = bytearray(w * h)
    q = deque()
    for x in range(w):
        q.append((x, 0))
        q.append((x, h - 1))
    for y in range(h):
        q.append((0, y))
        q.append((w - 1, y))
    while q:
        x, y = q.popleft()
        i = y * w + x
        if seen[i]:
            continue
        r, g, b, _ = px[x, y]
        if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > tolerance:
            continue
        seen[i] = 1
        px[x, y] = (r, g, b, 0)
        if x > 0:
            q.append((x - 1, y))
        if x < w - 1:
            q.append((x + 1, y))
        if y > 0:
            q.append((x, y - 1))
        if y < h - 1:
            q.append((x, y + 1))
    return im


def build_logo():
    im = Image.open(os.path.join(SRC, LOGO))

    # The source PNG is the artwork sitting off-centre on a wide #1b1a1d card.
    # Cutting the backdrop out gives one asset that works on the hero, the
    # header and the footer, all of which sit on different darks.
    cut = transparent_background(im).crop(transparent_background(im).getbbox())

    for name, width in (("logo.png", 1120), ("logo-mark.png", 260)):
        out = cut.copy()
        out.thumbnail((width, width), Image.LANCZOS)
        out = out.quantize(colors=192, method=Image.FASTOCTREE,
                           dither=Image.FLOYDSTEINBERG)
        out.save(os.path.join(OUT, name), "PNG", optimize=True)
        print(f"{name:22} {out.size[0]}x{out.size[1]}")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    parser = argparse.ArgumentParser(description="Build optimized photos and silent video clips from the supplied originals.")
    parser.add_argument("--source", type=Path, default=Path("/mnt/c/Users/mkern/Downloads/wetransfer_videos-and-photos_2026-08-24_1650"))
    args = parser.parse_args()
    build_photos(args.source)
    build_clips(args.source)
    build_logo()
