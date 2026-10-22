#!/usr/bin/env python3
"""
T-ZERO VIRAL PROMO VIDEO GENERATOR
Renders 35-second 1080p 60/30fps Remotion video + Edge-TTS AI Voiceover + FFmpeg Master
Outputs:
  - out/tzero_viral_promo_en.mp4 (Global English Launch)
  - out/tzero_viral_promo_tr.mp4 (Turkish Community Launch)
"""

import os
import sys
import subprocess
import shutil

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "out")
os.makedirs(OUT_DIR, exist_ok=True)

NARRATION_EN = (
  "Are your AI coding prompts bleeding money and choking on context window limits? "
  "Meet T-Zero. "
  "Powered by a mathematical AST engine, T-Zero slashes prompt context by up to 95 percent across 10 polyglot languages. "
  "Packed with 37 autonomous Model Context Protocol tools for deep memory synthesis, architecture mapping, and zero-leak security. "
  "Guarded by a 4D causal graph and Byzantine fault-tolerant swarm consensus, guaranteeing zero hallucinations. "
  "Saving engineering teams over 400,000 dollars a year. "
  "Run pip install tzero-mcp or download the standalone executable. Scale your AI today."
)

NARRATION_TR = (
  "Yapay zeka kodlama araçlarınız yüksek token maliyetiyle bütçenizi mi tüketiyor? "
  "Karşınızda T-Zero. "
  "Matematiksel AST motoruyla kod context boyutunu yüzde 95'e kadar düşürün. On farklı dilde tam optimizasyon. "
  "Otuz yedi otonom Model Context Protocol aracıyla mimari haritalama, hafıza sentezi ve sıfır sızıntı güvenliği. "
  "Dört boyutlu nedensellik ağı ve Bizans hata toleranslı sürü konsensüsüyle sıfır halüsinasyon güvencesi. "
  "Yazılım ekiplerine yılda dörtyüz bin doların üzerinde net tasarruf. "
  "Pip install tzero-mcp ile tek komutta kurun veya bağımsız binary'yi indirin."
)

def run_cmd(cmd, cwd=BASE_DIR):
    print(f"\n[RUNNING] {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=cwd)
    if res.returncode != 0:
        print(f"[ERROR] Command failed with exit code {res.returncode}: {cmd}")
        return False
    return True

def generate_voiceover(lang="en"):
    voice = "en-US-ChristopherNeural" if lang == "en" else "tr-TR-EmelNeural"
    text = NARRATION_EN if lang == "en" else NARRATION_TR
    out_audio = os.path.join(OUT_DIR, f"voiceover_{lang}.mp3")
    txt_file = os.path.join(OUT_DIR, f"script_{lang}.txt")

    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"\n[1/3] Generating AI voiceover ({lang.upper()}) using Edge-TTS ({voice})...")
    cmd = f'python -m edge_tts --file "{txt_file}" --write-media "{out_audio}" --voice "{voice}"'
    if not run_cmd(cmd):
        return None
    return out_audio

def render_remotion_video(force=False):
    out_video = os.path.join(OUT_DIR, "tzero_visual.mp4")
    if os.path.exists(out_video) and os.path.getsize(out_video) > 1000000 and not force:
        print(f"\n[2/3] Visual video already rendered ({os.path.getsize(out_video):,} bytes): {out_video}")
        return out_video

    print("\n[2/3] Rendering 1080p 35s Remotion Video Composition (TZeroPromo)...")
    cmd = f'npx remotion render TZeroPromo "{out_video}" --codec h264'
    if not run_cmd(cmd):
        return None
    return out_video

def merge_video_audio(video_path, audio_path, out_final):
    print(f"\n[3/3] Merging video + audio with FFmpeg into {out_final}...")
    cmd = (
        f'ffmpeg -y -i "{video_path}" -i "{audio_path}" '
        f'-c:v copy -c:a aac -b:a 192k -shortest "{out_final}"'
    )
    return run_cmd(cmd)

def main():
    print("=" * 65)
    print("🚀 T-ZERO VIRAL 35s PROMO GENERATION PIPELINE")
    print("=" * 65)

    # 1. Render Video
    video_path = render_remotion_video()
    if not video_path or not os.path.exists(video_path):
        print("[FAIL] Visual render failed!")
        sys.exit(1)

    # 2. English Voiceover & Master
    en_audio = generate_voiceover("en")
    if en_audio and os.path.exists(en_audio):
        final_en = os.path.join(OUT_DIR, "tzero_viral_promo_en.mp4")
        merge_video_audio(video_path, en_audio, final_en)
        print(f"\n🎉 GLOBAL ENGLISH PROMO READY: {final_en}")

    # 3. Turkish Voiceover & Master
    tr_audio = generate_voiceover("tr")
    if tr_audio and os.path.exists(tr_audio):
        final_tr = os.path.join(OUT_DIR, "tzero_viral_promo_tr.mp4")
        merge_video_audio(video_path, tr_audio, final_tr)
        print(f"\n🎉 TURKISH COMMUNITY PROMO READY: {final_tr}")

    print("\n" + "=" * 65)
    print("✅ ALL PROMO ASSETS GENERATED IN: " + OUT_DIR)
    print("=" * 65)

if __name__ == "__main__":
    main()
