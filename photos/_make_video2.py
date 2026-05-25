#!/usr/bin/env python3
"""
女性向け（おひとり様・カップル）プロモ動画。
人物の入れ替わりが起きないよう、お一人様＝黄ワンピ女性、カップル＝同一カップルで統一。
numpyで高速化。
"""
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import numpy as np
from pathlib import Path
import subprocess
import math
from functools import lru_cache

ROOT = Path("/home/user/Shinzenen0528")
FRAMES = ROOT / "photos" / "_frames2"
OUT = ROOT / "photos" / "for_women_solo_couple.mp4"
FRAMES.mkdir(parents=True, exist_ok=True)
for old in FRAMES.glob("*.png"):
    old.unlink()

W, H = 1080, 1920
FPS = 30
FONT = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"

GOLD = (212, 175, 95)
GOLD_SOFT = (240, 218, 165)
CREAM = (248, 244, 232)
ROSE = (220, 175, 175)
INK = (18, 14, 12)

def f(size):
    return ImageFont.truetype(FONT, size)

def text_w(draw, txt, ft):
    b = draw.textbbox((0, 0), txt, font=ft)
    return b[2] - b[0]

def draw_text(draw, txt, y, size, color, center=True, x=None):
    ft = f(size)
    if center:
        x = (W - text_w(draw, txt, ft)) // 2
    draw.text((x, y), txt, font=ft, fill=color)

# 写真の基礎クロップ(1080x1920にフィットする最大の中央クロップ)をキャッシュ
@lru_cache(maxsize=16)
def get_base_crop(path_str):
    src = Image.open(path_str).convert("RGB")
    sw, sh = src.size
    target_ratio = W / H
    src_ratio = sw / sh
    if src_ratio > target_ratio:
        new_h = sh
        new_w = int(sh * target_ratio)
    else:
        new_w = sw
        new_h = int(sw / target_ratio)
    left = (sw - new_w) // 2
    top = (sh - new_h) // 2
    cropped = src.crop((left, top, left + new_w, top + new_h))
    # 1.3倍ぐらいまで拡大しても余裕のあるサイズで保持(2160x3840)
    return cropped.resize((W * 2, H * 2), Image.LANCZOS)

def kenburns(path, t, zoom_start=1.05, zoom_end=1.20, pan=(0, 0)):
    """ベース2倍解像度から、zoom*Wサイズの窓を切り出して1080x1920にリサイズ"""
    base = get_base_crop(str(path))  # 2W x 2H
    zoom = zoom_start + (zoom_end - zoom_start) * t
    # ベースは2倍解像度なので、(2W/zoom) x (2H/zoom) の窓を取り出す
    win_w = int(2 * W / zoom)
    win_h = int(2 * H / zoom)
    bw, bh = base.size
    max_x = bw - win_w
    max_y = bh - win_h
    px, py = pan
    # t=0で右端寄り、t=1で左端寄り (panの符号で方向)
    cx = max_x / 2 + px * max_x / 2 * (1 - 2 * t)
    cy = max_y / 2 + py * max_y / 2 * (1 - 2 * t)
    cx = max(0, min(max_x, int(cx)))
    cy = max(0, min(max_y, int(cy)))
    cropped = base.crop((cx, cy, cx + win_w, cy + win_h))
    return cropped.resize((W, H), Image.LANCZOS)

# 帯(上下グラデーション)をnumpyで生成・キャッシュ
@lru_cache(maxsize=32)
def make_band(h, alpha, reverse):
    ys = np.arange(h, dtype=np.float32) / max(1, h - 1)
    if reverse:
        a = (alpha * (ys ** 1.5)).astype(np.uint8)
    else:
        a = (alpha * ((1 - ys) ** 1.5)).astype(np.uint8)
    arr = np.zeros((h, W, 4), dtype=np.uint8)
    arr[..., 3] = a[:, None]
    return arr

def add_bands(img, top_h=520, bot_h=560, top_a=215, bot_a=235):
    base = np.array(img.convert("RGBA"), dtype=np.uint8)
    top = make_band(top_h, top_a, False)
    bot = make_band(bot_h, bot_a, True)
    # アルファブレンド
    def blend(dst_slice, ov):
        a = ov[..., 3:4].astype(np.float32) / 255.0
        dst_slice[..., :3] = (dst_slice[..., :3] * (1 - a) + ov[..., :3] * a).astype(np.uint8)
    blend(base[:top_h], top)
    blend(base[H - bot_h:], bot)
    return Image.fromarray(base[..., :3])

def fade(img, alpha):
    if alpha >= 1:
        return img
    if alpha <= 0:
        return Image.new("RGB", (W, H), (0, 0, 0))
    black = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.blend(black, img, alpha)

def small_label(draw, txt, y, color=GOLD):
    ft = f(34)
    tw = text_w(draw, txt, ft)
    x = (W - tw) // 2
    line_w = 90
    draw.line([(x - line_w - 20, y + 22), (x - 20, y + 22)], fill=color, width=2)
    draw.line([(x + tw + 20, y + 22), (x + tw + 20 + line_w, y + 22)], fill=color, width=2)
    draw.text((x, y), txt, font=ft, fill=color)

# ---- シーン -----------------------------------------------------------------

def s_intro(p, dur):
    img = kenburns(ROOT / "_MG_1135.jpg", p, 1.10, 1.25)
    img = add_bands(img, top_h=720, bot_h=480, top_a=210, bot_a=200)
    d = ImageDraw.Draw(img)
    draw_text(d, "ひとりでも、ふたりでも。", 280, 64, CREAM)
    draw_text(d, "── 大人のための、夜の時間 ──", 380, 36, GOLD_SOFT)
    draw_text(d, "心斎橋 禅園", 1480, 110, GOLD)
    draw_text(d, "for women  /  for couples", 1640, 32, ROSE)
    return fade(img, min(1.0, p * 3)) if p < 0.3 else img

def s_solo_label(p, dur):
    img = kenburns(ROOT / "DSC06696.jpg", p, 1.05, 1.18, pan=(-0.3, 0))
    img = add_bands(img, top_h=540, bot_h=560)
    d = ImageDraw.Draw(img)
    small_label(d, "  SCENE  01  ", 240, GOLD)
    draw_text(d, "ひとりで来ても、", 340, 72, CREAM)
    draw_text(d, "浮かない店。", 440, 80, GOLD)
    draw_text(d, "── おひとり様、歓迎です ──", 1500, 38, GOLD_SOFT)
    draw_text(d, "落ち着いた個室と、静かなカウンター。", 1580, 32, CREAM)
    return img

def s_solo_counter(p, dur):
    img = kenburns(ROOT / "DSC06714.jpg", p, 1.06, 1.18, pan=(0.2, 0))
    img = add_bands(img, top_h=480, bot_h=560)
    d = ImageDraw.Draw(img)
    draw_text(d, "「今日は、自分のために。」", 240, 60, CREAM)
    draw_text(d, "カウンターに座る、それだけの贅沢。", 1500, 38, GOLD_SOFT)
    draw_text(d, "店主との、ちいさな会話も楽しんで。", 1570, 32, CREAM)
    return img

def s_solo_drink(p, dur):
    img = kenburns(ROOT / "DSC06851.jpg", p, 1.08, 1.22, pan=(0.3, 0))
    img = add_bands(img, top_h=520, bot_h=560)
    d = ImageDraw.Draw(img)
    small_label(d, "  自 分 ご 褒 美  ", 240, ROSE)
    draw_text(d, "スパークリングと、", 320, 58, CREAM)
    draw_text(d, "出来立ての天ぷらを。", 400, 64, GOLD)
    draw_text(d, "── すこし背筋が伸びる、夜 ──", 1530, 36, GOLD_SOFT)
    return img

def s_solo_sake(p, dur):
    img = kenburns(ROOT / "DSC06863.jpg", p, 1.05, 1.18, pan=(-0.2, 0))
    img = add_bands(img, top_h=520, bot_h=540)
    d = ImageDraw.Draw(img)
    draw_text(d, "好きな一献を、ゆっくり。", 280, 58, CREAM)
    draw_text(d, "もちろん、ノンアルもご用意。", 1500, 38, ROSE)
    draw_text(d, "「飲めない」も、気兼ねなく。", 1570, 32, GOLD_SOFT)
    return img

def s_solo_flower(p, dur):
    img = kenburns(ROOT / "DSC06676.jpg", p, 1.06, 1.18, pan=(0.2, 0))
    img = add_bands(img, top_h=520, bot_h=520)
    d = ImageDraw.Draw(img)
    draw_text(d, "ふと、心がほどける。", 280, 60, CREAM)
    draw_text(d, "季節の花、しつらえ、灯り。", 380, 38, GOLD_SOFT)
    return img

def s_transition(p, dur):
    img = kenburns(ROOT / "320A9411.jpg", p, 1.10, 1.20)
    img = ImageEnhance.Brightness(img).enhance(0.85)
    img = add_bands(img, top_h=600, bot_h=600, top_a=230, bot_a=230)
    d = ImageDraw.Draw(img)
    draw_text(d, "── それとも、 ──", 760, 50, GOLD_SOFT)
    draw_text(d, "ふたりで。", 880, 130, CREAM)
    return fade(img, min(1.0, p * 4)) if p < 0.25 else img

def s_couple_back(p, dur):
    img = kenburns(ROOT / "DSC00654.jpg", p, 1.06, 1.18, pan=(0.2, 0))
    img = add_bands(img, top_h=520, bot_h=560)
    d = ImageDraw.Draw(img)
    small_label(d, "  SCENE  02  ", 240, GOLD)
    draw_text(d, "並んで座る、特等席。", 340, 64, CREAM)
    draw_text(d, "誕生日、記念日、はじめての夜に。", 1530, 36, GOLD_SOFT)
    return img

def s_couple_toast(p, dur):
    img = kenburns(ROOT / "DSC00462.jpg", p, 1.05, 1.18, pan=(-0.2, 0))
    img = add_bands(img, top_h=520, bot_h=560)
    d = ImageDraw.Draw(img)
    draw_text(d, "「いつもありがとう。」", 260, 60, CREAM)
    draw_text(d, "そっと、グラスを重ねて。", 360, 50, GOLD_SOFT)
    draw_text(d, "── ふたりだけの、しずかな乾杯 ──", 1520, 36, ROSE)
    return img

def s_couple_meal(p, dur):
    img = kenburns(ROOT / "DSC00465.jpg", p, 1.06, 1.18, pan=(0.2, 0))
    img = add_bands(img, top_h=480, bot_h=560)
    d = ImageDraw.Draw(img)
    draw_text(d, "目の前で仕上がる、旬の一皿。", 220, 50, CREAM)
    draw_text(d, "「美味しいね」が、何度も増えていく。", 1520, 36, GOLD_SOFT)
    return img

def s_outro(p, dur):
    img = kenburns(ROOT / "_MG_1135.jpg", p, 1.20, 1.10)
    img = ImageEnhance.Brightness(img).enhance(0.75)
    img = add_bands(img, top_h=800, bot_h=900, top_a=230, bot_a=240)
    d = ImageDraw.Draw(img)
    draw_text(d, "── 夜風に、ひと息 ──", 360, 38, GOLD_SOFT)
    draw_text(d, "あなたの今夜を、", 460, 72, CREAM)
    draw_text(d, "やさしく迎える店。", 560, 80, GOLD)
    d.line([(W // 2 - 320, 1180), (W // 2 + 320, 1180)], fill=GOLD, width=2)
    draw_text(d, "心斎橋 禅園", 1220, 130, GOLD)
    d.line([(W // 2 - 320, 1390), (W // 2 + 320, 1390)], fill=GOLD, width=2)
    pulse = 0.75 + 0.25 * (0.5 + 0.5 * math.sin(p * 6.28 * 1.2))
    btn_color = tuple(int(c * pulse) for c in GOLD)
    d.rounded_rectangle([180, 1500, W - 180, 1680], radius=24, fill=btn_color)
    draw_text(d, "ご予約はプロフィールから", 1555, 52, INK)
    draw_text(d, "@ 心斎橋 禅園   /   solo  &  couple  welcome", 1760, 30, CREAM)
    return img

SCENES = [
    (3.0, s_intro),
    (3.5, s_solo_label),
    (3.5, s_solo_counter),
    (4.0, s_solo_drink),
    (3.0, s_solo_sake),
    (3.0, s_solo_flower),
    (2.5, s_transition),
    (3.0, s_couple_back),
    (4.0, s_couple_toast),
    (3.5, s_couple_meal),
    (5.0, s_outro),
]

total = sum(d for d, _ in SCENES)
print(f"Total: {total}s, frames: {int(total*FPS)}", flush=True)

import time
t0 = time.time()
idx = 0
for si, (dur, fn) in enumerate(SCENES):
    n = int(dur * FPS)
    for i in range(n):
        p = i / max(1, n - 1)
        img = fn(p, dur)
        if i < 5 and si > 0:
            img = fade(img, (i + 1) / 6)
        if i > n - 6 and si < len(SCENES) - 1:
            img = fade(img, (n - i) / 6)
        img.save(FRAMES / f"f_{idx:05d}.png", optimize=False, compress_level=1)
        idx += 1
    el = time.time() - t0
    print(f"  {fn.__name__}: {n} frames done (total {idx}, {el:.1f}s)", flush=True)

print("Encoding...", flush=True)
cmd = [
    "ffmpeg", "-y", "-framerate", str(FPS),
    "-i", str(FRAMES / "f_%05d.png"),
    "-c:v", "libx264", "-pix_fmt", "yuv420p",
    "-preset", "medium", "-crf", "20",
    "-movflags", "+faststart",
    str(OUT),
]
subprocess.run(cmd, check=True)
print(f"OK -> {OUT}", flush=True)
