#!/usr/bin/env python3
"""intro と outro のみ再描画して、既存フレームを上書き → 再エンコード"""
import sys
sys.path.insert(0, "/home/user/Shinzenen0528/photos")
# _make_video2 を import するとシーン関数だけ使えるが、import時にfor文が走るのでNG。
# よって関数定義を直接抜き出して実行する代わりに、必要な処理を再実装するのは冗長。
# → 簡単に: _make_video2.py の SCENES と FRAMES, FPS, fade を読み込む
import importlib.util
spec = importlib.util.spec_from_file_location("mv2", "/home/user/Shinzenen0528/photos/_make_video2.py")
# import すると最後まで走ってしまうので、関数だけ抜き出す版を作る代わりに
# モジュール全体を実行せず、source を読んで定義部分だけ exec する。
src = open("/home/user/Shinzenen0528/photos/_make_video2.py").read()
# "SCENES = [" 以降を消す
cut = src.index("SCENES = [")
defs = src[:cut]
# それでも SCENES 定義の前にimport/定義しかない想定
ns = {}
exec(defs, ns)

FRAMES = ns["FRAMES"]
FPS = ns["FPS"]
fade = ns["fade"]
s_intro = ns["s_intro"]
s_outro = ns["s_outro"]

# 再描画対象
targets = [
    (0, 90, 3.0, s_intro, True, False),     # is_first(no fade-in cross), not last
    (990, 1140, 5.0, s_outro, False, True), # not first, is_last
]

import time
t0 = time.time()
for start, end, dur, fn, is_first, is_last in targets:
    n = end - start
    for i in range(n):
        p = i / max(1, n - 1)
        img = fn(p, dur)
        # シーン境界フェード(s_intro は前なし、s_outro は後ろなし)
        if not is_first and i < 5:
            img = fade(img, (i + 1) / 6)
        if not is_last and i > n - 6:
            img = fade(img, (n - i) / 6)
        img.save(FRAMES / f"f_{start+i:05d}.png", optimize=False, compress_level=1)
    print(f"  {fn.__name__}: {n} frames re-rendered ({time.time()-t0:.1f}s)", flush=True)

import subprocess
from pathlib import Path
OUT = Path("/home/user/Shinzenen0528/photos/for_women_solo_couple.mp4")
print("Encoding...", flush=True)
subprocess.run([
    "ffmpeg", "-y", "-framerate", str(FPS),
    "-i", str(FRAMES / "f_%05d.png"),
    "-c:v", "libx264", "-pix_fmt", "yuv420p",
    "-preset", "medium", "-crf", "20",
    "-movflags", "+faststart",
    str(OUT),
], check=True)
print(f"OK -> {OUT}", flush=True)
