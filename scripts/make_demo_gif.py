"""Build the README demo GIF from the two partner videos recorded by the S2 browser test.

Reproduce (API on :8031 with FUNDFORGE_TEST_VARIANTS=1, `next start` on :3031, as in docs/PROGRESS.md):

    cd frontend
    FUNDFORGE_RECORD=$PWD/test-results/demo-rec E2E_BASE_URL=http://127.0.0.1:3031 npx playwright test e2e/s2.spec.ts
    cd ..
    py -3 scripts/make_demo_gif.py frontend/test-results/demo-rec docs/images/s2-two-partners.gif

The test writes pm.webm and mp.webm there (git-ignored; base market only). This script samples both at
SAMPLE_FPS with ffmpeg, puts the partners side by side and writes a GIF played SPEEDUP times faster.
Needs Pillow and an ffmpeg that can decode VP8 WebM: $FFMPEG, `ffmpeg` on PATH, or the minimal build
Playwright installs under ms-playwright/ffmpeg-*/ (it has no fps/palette filters, hence Pillow).
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SAMPLE_FPS = 1  # frames taken per second of the test run
SPEEDUP = 4  # so each sampled frame shows for 250 ms
PANE = (640, 457)  # each partner's 1400x1000 page, scaled
LABEL_H = 28
COLORS = 32
HOLD_LAST_MS = 4000


def find_ffmpeg() -> str:
    found = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
    if found:
        return found
    root = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or Path.home() / "AppData/Local/ms-playwright")
    if not root.exists():
        root = Path.home() / ".cache/ms-playwright"
    hits = sorted(glob.glob(str(root / "ffmpeg-*" / "ffmpeg*")))
    if not hits:
        sys.exit("no ffmpeg found; set FFMPEG")
    return hits[-1]


def frames(ffmpeg: str, video: Path, out: Path) -> list[Path]:
    out.mkdir()
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(video),
                    "-r", str(SAMPLE_FPS), str(out / "%04d.png")], check=True)
    return sorted(out.glob("*.png"))


def main(rec: Path, gif: Path) -> None:
    ffmpeg = find_ffmpeg()
    font = ImageFont.load_default(size=18)
    with tempfile.TemporaryDirectory() as tmp:
        pm = frames(ffmpeg, rec / "pm.webm", Path(tmp) / "pm")
        mp = frames(ffmpeg, rec / "mp.webm", Path(tmp) / "mp")
        n = max(len(pm), len(mp))
        out = []
        for i in range(n):  # the shorter clip holds its last frame
            canvas = Image.new("RGB", (PANE[0] * 2 + 8, PANE[1] + LABEL_H), "#0f1b2d")
            draw = ImageDraw.Draw(canvas)
            for col, (paths, label) in enumerate([(pm, "Ana, portfolio manager (browser 1)"),
                                                   (mp, "Ben, managing partner (browser 2)")]):
                x = col * (PANE[0] + 8)
                with Image.open(paths[min(i, len(paths) - 1)]) as im:
                    canvas.paste(im.convert("RGB").resize(PANE, Image.LANCZOS), (x, LABEL_H))
                draw.text((x + 10, 4), label, fill="#e8edf5", font=font)
            out.append(canvas)
    # One shared palette (from a strip of sampled frames) lets the GIF store only changed regions per frame.
    strip = Image.new("RGB", (out[0].width, out[0].height * 8))
    for k in range(8):
        strip.paste(out[k * (len(out) - 1) // 7], (0, k * out[0].height))
    palette = strip.quantize(colors=COLORS, method=Image.Quantize.MEDIANCUT)
    out = [im.quantize(palette=palette, dither=Image.Dither.NONE) for im in out]
    step = int(1000 / SAMPLE_FPS / SPEEDUP)
    durations = [step] * (len(out) - 1) + [HOLD_LAST_MS]
    gif.parent.mkdir(parents=True, exist_ok=True)
    out[0].save(gif, save_all=True, append_images=out[1:], duration=durations, loop=0, optimize=True)
    print(f"{gif}: {len(out)} frames, {gif.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: make_demo_gif.py <recording dir with pm.webm, mp.webm> <out.gif>")
    main(Path(sys.argv[1]), Path(sys.argv[2]))
