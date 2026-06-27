#!/usr/bin/env python3
"""
Generates a transparent 1080x1920 WebM overlay with:
  - Animated steam rising from the coffee cup (centered ~47% x, origin ~76% y)
  - Animated TV static noise on the CRT screen (~27-62% x, ~52-67% y)

Aligned to the 9:16 reference photo (Flicker / @zx_james / SUNO).
"""

import math
import random
import subprocess
import sys

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# ─── Output ──────────────────────────────────────────────────────────────────
WIDTH  = 1080
HEIGHT = 1920
FPS    = 30
SECS   = 10
FRAMES = FPS * SECS
OUTPUT = "/home/user/Prism/coffee_tv_overlay.mp4"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

# ─── Anchor positions (% of 1080×1920, mapped from reference photo) ──────────
# Coffee cup opening — steam starts here
STEAM_CX   = 490    # x center of cup opening
STEAM_CY   = 1455   # y of cup rim (bottom of steam column)
STEAM_HALF = 28     # half-width of spawn zone

# CRT TV screen inner bounds
TV_L, TV_R, TV_T, TV_B = 295, 668, 1002, 1283

# Steam crop box: must reach above TV top (y≈1002) up to y≈580 (cup at 1455,
# fastest particles travel 240*3.5=840px up → reach y=615)
_SB_L = max(0,     STEAM_CX - 190)
_SB_T = max(0,     560)
_SB_R = min(WIDTH, STEAM_CX + 190)
_SB_B = min(HEIGHT, STEAM_CY + 30)
STEAM_BOX = (_SB_L, _SB_T, _SB_R, _SB_B)
SBW = _SB_R - _SB_L
SBH = _SB_B - _SB_T

# ─── Particle system ─────────────────────────────────────────────────────────
class Particle:
    __slots__ = ['x','y','vx','vy','life','maxlife','size','ws','wa','wp']

    def spawn(self):
        self.x       = STEAM_CX + random.uniform(-STEAM_HALF, STEAM_HALF)
        self.y       = float(STEAM_CY)
        self.vx      = random.uniform(-0.30, 0.30)
        self.vy      = random.uniform(-3.5, -1.8)   # faster: particles rise ~500-840px
        self.life    = 0
        self.maxlife = random.randint(130, 240)      # longer life for full column height
        self.size    = random.uniform(7, 19)
        self.ws      = random.uniform(0.04, 0.11)   # wobble speed
        self.wa      = random.uniform(4.0, 16.0)    # wobble amplitude
        self.wp      = random.uniform(0, 2*math.pi) # wobble phase

    def __init__(self):
        self.spawn()
        frac = random.random()
        self.life = int(self.maxlife * frac)
        self.y    = STEAM_CY + self.vy * self.life  # approximate position

    def step(self, t: int):
        wobble  = self.wa * math.sin(t * self.ws + self.wp) * 0.07
        self.x  += self.vx + wobble
        self.y  += self.vy
        self.size += 0.05
        self.life += 1
        if self.life >= self.maxlife:
            self.spawn()

    @property
    def alpha(self) -> float:
        p = self.life / self.maxlife
        if p < 0.12:
            return p / 0.12
        return 1.0 - (p - 0.12) / 0.88


particles = [Particle() for _ in range(28)]

# ─── Frame renderer ───────────────────────────────────────────────────────────
def render_frame(t: int) -> np.ndarray:
    # Chroma-key green background — remove in CapCut with Chroma Key tool
    canvas = Image.new('RGB', (WIDTH, HEIGHT), (0, 255, 0))

    # ── TV static ──
    tw = TV_R - TV_L
    th = TV_B - TV_T
    noise = np.random.randint(15, 255, (th, tw), dtype=np.uint8)
    noise[::2] = (noise[::2] * 0.50).astype(np.uint8)   # scanlines (every other row)

    # Occasional horizontal roll bar
    if random.random() < 0.14:
        by = random.randint(0, th - 7)
        bh = random.randint(2, 8)
        noise[by:by+bh] = np.clip(noise[by:by+bh].astype(np.int32) + 115, 0, 255).astype(np.uint8)

    pix = np.empty((th, tw, 3), dtype=np.uint8)
    pix[..., 0] = (noise * 0.50).astype(np.uint8)  # R
    pix[..., 1] = (noise * 0.68).astype(np.uint8)  # G
    pix[..., 2] = noise                              # B — blue-white CRT tint
    canvas.paste(Image.fromarray(pix, 'RGB'), (TV_L, TV_T))

    # ── Steam (work in a cropped region for speed) ──
    # Draw steam onto an RGBA crop, blur it, then composite onto the RGB canvas
    steam_crop = Image.new('RGBA', (SBW, SBH), (0, 0, 0, 0))
    draw = ImageDraw.Draw(steam_crop)

    for p in particles:
        a = int(p.alpha * 108)
        if a < 3:
            continue
        r  = p.size
        lx = p.x - _SB_L
        ly = p.y - _SB_T
        if lx + r < 0 or lx - r > SBW or ly + r < 0 or ly - r > SBH:
            continue
        draw.ellipse([lx-r, ly-r, lx+r, ly+r], fill=(212, 226, 244, a))

    steam_crop = steam_crop.filter(ImageFilter.GaussianBlur(radius=8))

    # Paste steam crop over the black canvas using alpha compositing
    canvas_crop = canvas.crop((_SB_L, _SB_T, _SB_R, _SB_B)).convert('RGBA')
    composited  = Image.alpha_composite(canvas_crop, steam_crop).convert('RGB')
    canvas.paste(composited, (_SB_L, _SB_T))

    return np.array(canvas, dtype=np.uint8)


# ─── Encode ───────────────────────────────────────────────────────────────────
cmd = [
    FFMPEG, '-y',
    '-f', 'rawvideo', '-vcodec', 'rawvideo',
    '-pix_fmt', 'rgb24', '-s', f'{WIDTH}x{HEIGHT}', '-r', str(FPS),
    '-i', 'pipe:0',
    '-c:v', 'libx264',
    '-pix_fmt', 'yuv420p',
    '-crf', '28',          # higher = smaller file; 28 still looks great for an overlay
    '-preset', 'fast',
    '-movflags', '+faststart',
    OUTPUT,
]

print(f"Rendering {FRAMES} frames @ {FPS}fps → {OUTPUT}")
print(f"Steam origin: ({STEAM_CX}, {STEAM_CY})   TV screen: ({TV_L},{TV_T})→({TV_R},{TV_B})")

proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

for f in range(FRAMES):
    for p in particles:
        p.step(f)
    proc.stdin.write(render_frame(f).tobytes())
    if f % 30 == 0:
        print(f"  {100*f//FRAMES:3d}%  frame {f}/{FRAMES}", flush=True)

proc.stdin.close()
proc.wait()
if proc.returncode != 0:
    sys.exit(1)

print(f"\nDone!  →  {OUTPUT}")
