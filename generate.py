#!/usr/bin/env python3
"""
Faceless Shorts Generator
=========================
Script dosyasi ver -> yayina hazir 9:16 video al.

Pipeline:
  1. scripts/*.txt dosyasini sahnelere ayirir
  2. Her sahne icin edge-tts ile seslendirme uretir (ucretsiz, kelime zamanlamali)
  3. Her sahne icin Pexels'ten dikey stok video indirir (ucretsiz API)
  4. ffmpeg ile birlestirir: 1080x1920, altyazi gomulu, opsiyonel muzik

Kullanim:
  python generate.py scripts/video1.txt
  python generate.py scripts/video1.txt --voice en-US-ChristopherNeural
"""

import argparse
import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import edge_tts
    import requests
except ImportError:
    sys.exit("Eksik paket. Once calistir:  pip install -r requirements.txt")

# ---------------------------------------------------------------- config ----

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
DEFAULT_VOICE = "en-US-ChristopherNeural"   # alternatifler: en-US-GuyNeural, en-GB-RyanNeural
WIDTH, HEIGHT = 1080, 1920
MUSIC_FILE = Path("assets/music.mp3")        # opsiyonel; varsa %12 seste altta calar

# Altyazi stili (ASS formati) — renkler &HBBGGRR& (BGR!) formatinda
SUB_FONT = "Arial"
SUB_SIZE = 88
SUB_PRIMARY = "&H00FFFFFF"    # beyaz metin
SUB_OUTLINE = "&H00000000"    # siyah kontur
SUB_HIGHLIGHT = "&H0000D7FF"  # amber vurgu (aktif kelime)

# ---------------------------------------------------------------- parsing ---

@dataclass
class Scene:
    keywords: str                      # Pexels arama terimi
    text: str                          # seslendirilecek metin
    audio: Path = None                 # uretilen mp3
    video: Path = None                 # indirilen stok klip
    duration: float = 0.0
    words: list = field(default_factory=list)  # [(word, start_s, end_s)]


def parse_script(path: Path) -> list[Scene]:
    """
    Script formati:

        [scene: jellyfish underwater macro]
        This tiny jellyfish has figured out how to never die.

        [scene: ocean deep blue]
        It reverses its own aging...

    Her [scene: ...] satiri yeni bir sahne baslatir; arama terimi Pexels'e gider.
    """
    scenes = []
    current = None
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        m = re.match(r"\[scene:\s*(.+?)\]", line, re.IGNORECASE)
        if m:
            if current and current.text.strip():
                scenes.append(current)
            current = Scene(keywords=m.group(1).strip(), text="")
        elif line and current is not None:
            current.text += (" " if current.text else "") + line
    if current and current.text.strip():
        scenes.append(current)
    if not scenes:
        sys.exit("Script'te sahne bulunamadi. Format: [scene: arama terimi] + metin satirlari")
    return scenes

# ------------------------------------------------------------------- tts ----

async def tts_scene(scene: Scene, voice: str, out: Path):
    """edge-tts ile mp3 uret + kelime zamanlamalarini (WordBoundary) topla."""
    communicate = edge_tts.Communicate(scene.text, voice, rate="+8%")
    words = []
    with open(out, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 10_000_000            # 100ns -> saniye
                end = start + chunk["duration"] / 10_000_000
                words.append((chunk["text"], start, end))
    scene.audio = out
    scene.words = words
    scene.duration = probe_duration(out)


def probe_duration(media: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(media)],
        capture_output=True, text=True, check=True)
    return float(json.loads(r.stdout)["format"]["duration"])

# ---------------------------------------------------------------- pexels ----

def fetch_stock(scene: Scene, out: Path, used_ids: set):
    """Sahne anahtar kelimeleriyle Pexels'ten dikey video indir."""
    if not PEXELS_API_KEY:
        sys.exit("PEXELS_API_KEY ortam degiskeni bos. README'deki adimlari izle.")
    r = requests.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": PEXELS_API_KEY},
        params={"query": scene.keywords, "orientation": "portrait", "per_page": 10},
        timeout=30)
    r.raise_for_status()
    videos = r.json().get("videos", [])
    if not videos:
        sys.exit(f"Pexels'te sonuc yok: '{scene.keywords}' — daha genel bir terim dene.")

    for v in videos:                      # ayni videoyu iki sahnede kullanma
        if v["id"] in used_ids:
            continue
        used_ids.add(v["id"])
        files = sorted(v["video_files"], key=lambda f: abs((f.get("height") or 0) - HEIGHT))
        url = files[0]["link"]
        with requests.get(url, stream=True, timeout=120) as dl:
            dl.raise_for_status()
            with open(out, "wb") as f:
                shutil.copyfileobj(dl.raw, f)
        scene.video = out
        return
    sys.exit(f"'{scene.keywords}' icin kullanilmamis klip kalmadi.")

# ------------------------------------------------------------- subtitles ----

def ass_time(t: float) -> str:
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def build_subtitles(scenes: list[Scene], out: Path):
    """Kelime kelime vurgulu, 3'lu gruplar halinde ASS altyazi uret."""
    header = f"""[Script Info]
PlayResX: {WIDTH}
PlayResY: {HEIGHT}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Word,{SUB_FONT},{SUB_SIZE},{SUB_PRIMARY},{SUB_PRIMARY},{SUB_OUTLINE},&H80000000,-1,0,0,0,100,100,0,0,1,6,2,2,60,60,420,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    offset = 0.0
    for scene in scenes:
        words = scene.words
        for i in range(0, len(words), 3):                     # 3 kelimelik gruplar
            group = words[i:i + 3]
            g_start = group[0][1] + offset
            g_end = group[-1][2] + offset
            for j, (w, ws, we) in enumerate(group):           # aktif kelime vurgusu
                parts = []
                for k, (w2, _, _) in enumerate(group):
                    w2 = w2.replace("{", "").replace("}", "")
                    if k == j:
                        parts.append(f"{{\\c{SUB_HIGHLIGHT}&}}{w2.upper()}{{\\c{SUB_PRIMARY}&}}")
                    else:
                        parts.append(w2.upper())
                start = ws + offset
                end = (group[j + 1][1] + offset) if j + 1 < len(group) else g_end
                lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Word,,0,0,0,,{' '.join(parts)}")
        offset += scene.duration
    out.write_text(header + "\n".join(lines), encoding="utf-8")

# -------------------------------------------------------------- assembly ----

def assemble(scenes: list[Scene], subs: Path, out: Path, tmp: Path):
    """Her sahneyi kendi ses suresine kirp -> birlestir -> altyazi + muzik."""
    seg_files = []
    for i, sc in enumerate(scenes):
        seg = tmp / f"seg_{i}.mp4"
        # klibi sahne suresi kadar dondurerek kirp, 1080x1920'ye crop/scale et
        vf = (f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
              f"crop={WIDTH}:{HEIGHT},fps=30,setsar=1")
        subprocess.run([
            "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(sc.video),
            "-i", str(sc.audio),
            "-t", f"{sc.duration:.3f}",
            "-vf", vf,
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "fast", "-crf", "21",
            "-c:a", "aac", "-b:a", "192k",
            str(seg)], check=True, capture_output=True)
        seg_files.append(seg)

    concat_list = tmp / "concat.txt"
    concat_list.write_text("\n".join(f"file '{s.resolve()}'" for s in seg_files))
    merged = tmp / "merged.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", str(concat_list), "-c", "copy", str(merged)],
                   check=True, capture_output=True)

    # altyazi gom + opsiyonel muzik
    if MUSIC_FILE.exists():
        subprocess.run([
            "ffmpeg", "-y", "-i", str(merged), "-stream_loop", "-1", "-i", str(MUSIC_FILE),
            "-filter_complex",
            f"[0:v]subtitles={subs}[v];"
            f"[1:a]volume=0.12[m];[0:a][m]amix=inputs=2:duration=first[a]",
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "21",
            "-c:a", "aac", "-shortest", str(out)], check=True, capture_output=True)
    else:
        subprocess.run([
            "ffmpeg", "-y", "-i", str(merged),
            "-vf", f"subtitles={subs}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "21",
            "-c:a", "copy", str(out)], check=True, capture_output=True)

# ------------------------------------------------------------------ main ----

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script", type=Path, help="scripts/ altindaki .txt dosyasi")
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    args = ap.parse_args()

    name = args.script.stem
    tmp = Path(f"output/.tmp_{name}")
    tmp.mkdir(parents=True, exist_ok=True)
    final = Path(f"output/{name}.mp4")

    print(f"[1/4] Script okunuyor: {args.script}")
    scenes = parse_script(args.script)
    print(f"      {len(scenes)} sahne bulundu.")

    print(f"[2/4] Seslendirme uretiliyor ({args.voice})...")
    for i, sc in enumerate(scenes):
        asyncio.run(tts_scene(sc, args.voice, tmp / f"scene_{i}.mp3"))
        print(f"      sahne {i + 1}: {sc.duration:.1f} sn, {len(sc.words)} kelime")

    print("[3/4] Pexels'ten stok video indiriliyor...")
    used = set()
    for i, sc in enumerate(scenes):
        fetch_stock(sc, tmp / f"scene_{i}.mp4", used)
        print(f"      sahne {i + 1}: '{sc.keywords}' OK")

    print("[4/4] Video birlestiriliyor (altyazi + muzik)...")
    subs = tmp / "subs.ass"
    build_subtitles(scenes, subs)
    assemble(scenes, subs, final, tmp)

    total = sum(s.duration for s in scenes)
    print(f"\nHazir: {final}  ({total:.0f} saniye)")
    print("Kontrol et, sonra Metricool ile 3 platforma planla.")


if __name__ == "__main__":
    main()
