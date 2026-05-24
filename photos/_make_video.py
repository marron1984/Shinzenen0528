#!/usr/bin/env python3
"""
Instagram Reels用の縦型MP4を生成。
テーマ: サワー → ノンアル対応可（女性向け）
第3木曜「比較検討②」: 利用シーン（接待・顔合わせ）／個室・導線・安心感
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import subprocess
from pathlib import Path

ROOT = Path("/home/user/Shinzenen0528")
FRAMES = ROOT / "photos" / "_frames"
OUT = ROOT / "photos" / "sour_nonalc_private_room.mp4"
FRAMES.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1920
FPS = 30
FONT_PATH = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"

# 落ち着いた濃紺 × ゴールドの大人配色
NAVY = (18, 24, 48)
NAVY_DEEP = (10, 14, 30)
GOLD = (212, 175, 95)
GOLD_SOFT = (236, 214, 158)
CREAM = (245, 240, 228)
PINK = (232, 180, 184)  # 女性向けアクセント

def font(size, bold=False):
    return ImageFont.truetype(FONT_PATH, size)

def gradient_bg(c_top, c_bot):
    img = Image.new("RGB", (W, H), c_top)
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        r = int(c_top[0] * (1 - t) + c_bot[0] * t)
        g = int(c_top[1] * (1 - t) + c_bot[1] * t)
        b = int(c_top[2] * (1 - t) + c_bot[2] * t)
        for x in range(W):
            px[x, y] = (r, g, b)
    return img

def add_grain(img, amount=8):
    import random
    px = img.load()
    for _ in range(W * H // 40):
        x = random.randint(0, W - 1)
        y = random.randint(0, H - 1)
        r, g, b = px[x, y]
        d = random.randint(-amount, amount)
        px[x, y] = (max(0, min(255, r + d)),
                    max(0, min(255, g + d)),
                    max(0, min(255, b + d)))
    return img

def draw_text_center(draw, text, y, size, color, stroke=0, stroke_fill=None):
    f = font(size)
    bbox = draw.textbbox((0, 0), text, font=f)
    w = bbox[2] - bbox[0]
    x = (W - w) // 2
    if stroke:
        draw.text((x, y), text, font=f, fill=color, stroke_width=stroke, stroke_fill=stroke_fill)
    else:
        draw.text((x, y), text, font=f, fill=color)
    return bbox[3] - bbox[1]

def draw_text_left(draw, text, x, y, size, color):
    f = font(size)
    draw.text((x, y), text, font=f, fill=color)

def gold_line(draw, y, width=520):
    x0 = (W - width) // 2
    draw.rectangle([x0, y, x0 + width, y + 4], fill=GOLD)

def base_bg():
    img = gradient_bg(NAVY, NAVY_DEEP)
    return img

# ---- シーン定義 -------------------------------------------------------------
# (秒数, 描画関数)
def scene_hook(progress):
    """0-3s: フック"""
    img = base_bg()
    d = ImageDraw.Draw(img)
    # 上部タグ
    tag = "  接待・顔合わせ で 使える店  "
    f = font(38)
    bbox = d.textbbox((0, 0), tag, font=f)
    tw = bbox[2] - bbox[0]
    pad = 30
    tx = (W - tw) // 2
    ty = 220
    d.rectangle([tx - pad, ty - 20, tx + tw + pad, ty + 70], outline=GOLD, width=2)
    d.text((tx, ty), tag, font=f, fill=GOLD_SOFT)

    # アニメ: フェードイン
    alpha = min(1.0, progress / 0.8)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (1 - alpha))))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(img)

    draw_text_center(d, "そのサワー、", 780, 90, CREAM)
    draw_text_center(d, "ぜんぶ", 900, 110, CREAM)
    draw_text_center(d, "ノンアルに", 1040, 140, GOLD)
    draw_text_center(d, "できます。", 1220, 140, GOLD)

    gold_line(d, 1430)
    draw_text_center(d, "お酒が苦手な方も、安心。", 1480, 44, PINK)
    return img

def scene_who(progress):
    """3-7s: ターゲット刺し"""
    img = base_bg()
    d = ImageDraw.Draw(img)
    draw_text_center(d, "── こんなシーンで ──", 320, 42, GOLD_SOFT)

    items = [
        ("接 待", "取引先に失礼のない一席を。"),
        ("顔合わせ", "ご家族との大切な時間に。"),
        ("会  食", "下戸の方が居ても気兼ねなく。"),
    ]
    y = 560
    # アニメ: 順番に出す
    for i, (title, sub) in enumerate(items):
        appear = max(0.0, min(1.0, (progress - i * 0.25) / 0.4))
        if appear <= 0:
            continue
        offset = int((1 - appear) * 60)
        col_t = tuple(int(c * appear + NAVY[k] * (1 - appear)) for k, c in enumerate(GOLD))
        col_s = tuple(int(c * appear + NAVY[k] * (1 - appear)) for k, c in enumerate(CREAM))
        # カード
        card_y = y + i * 340 + offset
        d.rounded_rectangle([90, card_y, W - 90, card_y + 280], radius=28,
                            outline=col_t, width=3)
        f1 = font(86)
        bbox = d.textbbox((0, 0), title, font=f1)
        tw = bbox[2] - bbox[0]
        d.text(((W - tw) // 2, card_y + 40), title, font=f1, fill=col_t)
        f2 = font(40)
        bbox = d.textbbox((0, 0), sub, font=f2)
        sw = bbox[2] - bbox[0]
        d.text(((W - sw) // 2, card_y + 170), sub, font=f2, fill=col_s)
    return img

def scene_room(progress):
    """7-12s: 完全個室"""
    img = base_bg()
    d = ImageDraw.Draw(img)
    draw_text_center(d, "POINT  01", 280, 38, GOLD)
    gold_line(d, 360, 200)

    draw_text_center(d, "完全個室", 480, 160, CREAM)
    draw_text_center(d, "話に集中できる、静かな空間。", 720, 46, GOLD_SOFT)

    # 個室をイメージした矩形（引き戸の演出）
    cx, cy = W // 2, 1150
    rw, rh = 760, 460
    # 部屋枠
    d.rounded_rectangle([cx - rw // 2, cy - rh // 2, cx + rw // 2, cy + rh // 2],
                        radius=16, outline=GOLD, width=4)
    # 引き戸（progress で開く）
    open_ratio = min(1.0, max(0.0, (progress - 0.3) / 0.6))
    door_w = rw // 2
    left_x = cx - rw // 2 + int(door_w * open_ratio)
    right_x = cx + rw // 2 - int(door_w * open_ratio)
    d.rectangle([cx - rw // 2, cy - rh // 2, left_x, cy + rh // 2], fill=NAVY_DEEP)
    d.rectangle([right_x, cy - rh // 2, cx + rw // 2, cy + rh // 2], fill=NAVY_DEEP)
    # 戸の取っ手
    d.rectangle([left_x - 12, cy - 30, left_x - 4, cy + 30], fill=GOLD)
    d.rectangle([right_x + 4, cy - 30, right_x + 12, cy + 30], fill=GOLD)
    # 室内のテーブル
    if open_ratio > 0.5:
        d.ellipse([cx - 120, cy + 40, cx + 120, cy + 110], fill=GOLD_SOFT)

    draw_text_center(d, "── 周りを気にせず、ゆっくりと。 ──", 1500, 36, CREAM)
    return img

def scene_flow(progress):
    """12-17s: 別導線・安心感"""
    img = base_bg()
    d = ImageDraw.Draw(img)
    draw_text_center(d, "POINT  02", 280, 38, GOLD)
    gold_line(d, 360, 200)

    draw_text_center(d, "別 導 線", 480, 160, CREAM)
    draw_text_center(d, "人目を避けて、スマートに入店。", 720, 46, GOLD_SOFT)

    # 導線を線で描く
    base_y = 1100
    # メイン入口
    d.text((140, base_y - 80), "メイン", font=font(34), fill=CREAM)
    d.rounded_rectangle([100, base_y, 360, base_y + 120], radius=12, outline=CREAM, width=3)
    # 個室入口
    d.text((720, base_y - 80), "個室直行", font=font(34), fill=GOLD)
    d.rounded_rectangle([700, base_y, 980, base_y + 120], radius=12, outline=GOLD, width=3)

    # 矢印（progress で伸びる）
    arr_len = int(320 * min(1.0, progress / 0.7))
    ay = base_y + 250
    d.line([(180, ay), (180 + arr_len, ay)], fill=CREAM, width=6)
    d.line([(820, ay), (820 - arr_len * 0 + max(0, arr_len - 0), ay)], fill=GOLD, width=6)
    # 個室側の矢印（右から左ではなく、上に向かう演出）
    d.line([(840, ay + 80), (840, ay + 80 - arr_len)], fill=GOLD, width=6)
    if arr_len > 10:
        # 矢じり
        d.polygon([(180 + arr_len, ay - 14), (180 + arr_len + 24, ay),
                   (180 + arr_len, ay + 14)], fill=CREAM)
        d.polygon([(826, ay + 80 - arr_len), (840, ay + 80 - arr_len - 24),
                   (854, ay + 80 - arr_len)], fill=GOLD)

    draw_text_center(d, "── 知人と鉢合わせ、の心配なし。 ──", 1520, 36, CREAM)
    return img

def scene_safe(progress):
    """17-22s: 女性に安心ポイント"""
    img = base_bg()
    d = ImageDraw.Draw(img)
    draw_text_center(d, "FOR  YOU", 280, 38, PINK)
    gold_line(d, 360, 200)

    draw_text_center(d, "お酒が苦手でも、", 500, 84, CREAM)
    draw_text_center(d, "全サワー", 660, 110, GOLD)
    draw_text_center(d, "ノンアル対応", 800, 110, GOLD)

    bullets = [
        "・ 同じグラス、同じ見た目",
        "・ 「飲めないんです」と言わなくていい",
        "・ 妊娠中・授乳中・運転前 にも",
    ]
    y = 1050
    for i, b in enumerate(bullets):
        appear = max(0.0, min(1.0, (progress - i * 0.18) / 0.3))
        if appear <= 0:
            continue
        col = tuple(int(CREAM[k] * appear + NAVY[k] * (1 - appear)) for k in range(3))
        draw_text_left(d, b, 130, y + i * 110, 46, col)

    draw_text_center(d, "気を遣わせない、を、気遣う。", 1540, 42, PINK)
    return img

def scene_cta(progress):
    """22-26s: CTA"""
    img = base_bg()
    d = ImageDraw.Draw(img)
    # ロゴ風枠
    d.rounded_rectangle([140, 380, W - 140, 760], radius=32, outline=GOLD, width=4)
    draw_text_center(d, "大切な会食は、", 460, 70, CREAM)
    draw_text_center(d, "ここで。", 580, 110, GOLD)

    draw_text_center(d, "個室・別導線・ノンアル対応", 900, 46, GOLD_SOFT)
    draw_text_center(d, "── 接待 / 顔合わせ 歓迎 ──", 1000, 40, CREAM)

    # 点滅するCTA
    import math
    pulse = 0.6 + 0.4 * (0.5 + 0.5 * math.sin(progress * 6.28 * 1.5))
    col = tuple(int(c * pulse) for c in GOLD)
    d.rounded_rectangle([180, 1300, W - 180, 1480], radius=24, fill=col)
    draw_text_center(d, "ご予約はプロフィールから", 1350, 56, NAVY_DEEP)

    draw_text_center(d, "@ 親善園", 1620, 60, CREAM)
    return img

SCENES = [
    (3.0, scene_hook),
    (4.0, scene_who),
    (5.0, scene_room),
    (5.0, scene_flow),
    (5.0, scene_safe),
    (4.0, scene_cta),
]

# ---- 生成 ------------------------------------------------------------------
total = sum(d for d, _ in SCENES)
print(f"Total duration: {total}s, frames: {int(total * FPS)}")

idx = 0
for dur, fn in SCENES:
    n = int(dur * FPS)
    for i in range(n):
        p = i / max(1, n - 1)
        img = fn(p)
        img.save(FRAMES / f"f_{idx:05d}.png")
        idx += 1
    print(f"  {fn.__name__}: {n} frames done")

# ffmpegでmp4化
print("Encoding mp4...")
cmd = [
    "ffmpeg", "-y",
    "-framerate", str(FPS),
    "-i", str(FRAMES / "f_%05d.png"),
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-preset", "medium",
    "-crf", "20",
    "-movflags", "+faststart",
    str(OUT),
]
subprocess.run(cmd, check=True)
print(f"OK -> {OUT}")
