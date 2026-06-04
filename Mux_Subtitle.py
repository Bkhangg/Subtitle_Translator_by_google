"""
=============================================================
🎬 MUX SUBTITLE - Ghép phụ đề vào file video
=============================================================

CÔNG DỤNG:
- Ghép file .srt / .ass vào file .mp4 / .mkv
- Hỗ trợ MP4 (mov_text) và MKV (ass / srt)

YÊU CẦU:
- ffmpeg + ffprobe có trong PATH

CÁCH DÙNG:
    python mux_subtitle.py
=============================================================
"""

import re
import os
import glob
import subprocess
import json
import time
import sys
import shutil

# ==================== ANSI COLORS ====================
C = type('', (), {})()
C.cyan = '\033[96m'
C.magenta = '\033[95m'
C.gold = '\033[93m'
C.green = '\033[92m'
C.red = '\033[91m'
C.blue = '\033[94m'
C.bold = '\033[1m'
C.dim = '\033[2m'
C.end = '\033[0m'

def c(text, *colors):
    return ''.join(colors) + text + C.end

def supports_color():
    if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
        return False
    if os.name == 'nt':
        return True
    return True

USE_COLOR = supports_color()
def col(text, *colors):
    return c(text, *colors) if USE_COLOR else text


# ==================== TIỆN ÍCH ====================

VIDEO_EXTENSIONS = ('.mkv', '.mp4', '.avi', '.mov', '.ts', '.m2ts')

def scan_subtitle_files(directory='.'):
    files = []
    for ext in ('*.ass', '*.srt'):
        files += glob.glob(os.path.join(directory, ext))
        files += glob.glob(os.path.join(directory, '**', ext), recursive=True)
    files = list(set(files))
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return files

def scan_video_files(directory='.'):
    files = []
    for ext in ('*.mkv', '*.mp4', '*.avi', '*.mov'):
        files += glob.glob(os.path.join(directory, ext))
        files += glob.glob(os.path.join(directory, '**', ext), recursive=True)
    files = list(set(files))
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return files

def is_video_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    return ext in VIDEO_EXTENSIONS

def get_subtitle_streams(video_path):
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_streams', '-select_streams', 's', video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        streams = data.get('streams', [])
        subtitle_info = []
        for s in streams:
            index = s.get('index', 0)
            codec = s.get('codec_name', 'unknown')
            lang = s.get('tags', {}).get('language', 'und')
            title = s.get('tags', {}).get('title', '')
            subtitle_info.append({
                'index': index,
                'codec': codec,
                'language': lang,
                'title': title
            })
        return subtitle_info
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  {col('✖', C.red)} Error reading subtitle streams: {e}")
        return []


# ==================== MUX ====================

def find_mkvmerge():
    exe = shutil.which('mkvmerge')
    if exe:
        return exe
    common = [
        r'C:\Program Files\MKVToolNix\mkvmerge.exe',
        r'C:\Program Files (x86)\MKVToolNix\mkvmerge.exe',
    ]
    for p in common:
        if os.path.isfile(p):
            return p
    return None

def mux_subtitle_to_video(video_path, subtitle_path, output_path=None):
    if output_path is None:
        base, ext = os.path.splitext(video_path)
        output_path = f"{base}_with_sub{ext}"
    sub_ext = os.path.splitext(subtitle_path)[1].lower()
    video_ext = os.path.splitext(video_path)[1].lower()

    # MKV: dùng mkvmerge nếu có (xử lý ASS tốt hơn ffmpeg)
    mkvmerge_exe = find_mkvmerge()
    if video_ext == '.mkv' and mkvmerge_exe:
        cmd = [
            mkvmerge_exe, '-o', output_path,
            video_path,
            '--language', '0:vi',
            '--track-name', '0:Vietnamese subtitle',
            subtitle_path
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=300, check=True)
            return output_path
        except subprocess.CalledProcessError as e:
            out = e.stdout or ''
            err = e.stderr or ''
            print(f"  {col('✖', C.red)} mkvmerge error:")
            for line in (out + err).split('\n'):
                if line.strip():
                    print(f"    {line}")
            return None
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"  {col('✖', C.red)} mkvmerge error: {e}")
            return None

    # Fallback: ffmpeg
    existing_sub_count = len(get_subtitle_streams(video_path))
    cmd = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-i', subtitle_path,
        '-map', '0:v', '-map', '0:a', '-map', '0:s?', '-map', '1',
    ]
    if video_ext == '.mp4':
        if sub_ext == '.ass':
            print(f"  {col('⚠', C.gold)} MP4 does not support ASS subtitles. Converting ASS to SRT first...")
            srt_path = subtitle_path.rsplit('.', 1)[0] + '.srt'
            with open(subtitle_path, 'r', encoding='utf-8-sig') as f:
                ass_content = f.read()
            srt_lines = []
            for line in ass_content.split('\n'):
                if line.startswith('Dialogue:'):
                    parts = line.split(',', 9)
                    if len(parts) >= 10:
                        start = parts[1].strip().replace('.', ',')
                        end = parts[2].strip().replace('.', ',')
                        text = parts[9].replace('\\N', '\n').replace('{\\i1}', '<i>').replace('{\\i0}', '</i>')
                        text = re.sub(r'\{[^}]*\}', '', text).strip()
                        if text:
                            srt_lines.append(f"{len(srt_lines)+1}\n{start} --> {end}\n{text}\n")
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(srt_lines))
            subtitle_path = srt_path
        cmd += ['-c', 'copy', '-c:s', 'mov_text']
    else:
        cmd += ['-c:v', 'copy', '-c:a', 'copy']
        for i in range(existing_sub_count):
            cmd += [f'-c:s:{i}', 'copy']
        if sub_ext == '.ass':
            cmd += [f'-c:s:{existing_sub_count}', 'ass']
        else:
            cmd += [f'-c:s:{existing_sub_count}', 'srt']
    cmd += [
        f'-metadata:s:s:{existing_sub_count}', 'language=vi',
        f'-metadata:s:s:{existing_sub_count}', 'title=Vietnamese subtitle',
        output_path
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=300, check=True)
        return output_path
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"  {col('✖', C.red)} Mux error: {e}")
        return None


# ==================== MAIN ====================

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print()
    print(col("  ╭──────────────────────────────────────────────────╮", C.cyan))
    print(col("  │", C.cyan) + col("      🎬  MUX SUBTITLE INTO VIDEO  🎬       ", C.bold, C.magenta) + col("│", C.cyan))
    print(col("  │", C.cyan) + col("      ═══════════════════════════            ", C.dim) + col("│", C.cyan))
    print(col("  │", C.cyan) + f"      {col('✦', C.gold)} MP4  •  MKV  •  SRT  •  ASS   {col('✦', C.gold)}        " + col("│", C.cyan))
    print(col("  ╰──────────────────────────────────────────────────╯", C.cyan))
    print()

def main():
    print_banner()
    scan_dir = input(f"  {col('📁', C.cyan)} Directory (Enter=current): ").strip() or '.'
    print(f"\n  {col('🔍', C.cyan)} Scan: {col(os.path.abspath(scan_dir), C.bold)}")

    # Pick video
    vids = scan_video_files(scan_dir)
    if not vids:
        print(f"  {col('✖', C.red)} No video files found!")
        return
    print(f"\n  {col('🎬', C.magenta)} Video files:\n")
    for idx, f in enumerate(vids, 1):
        print(f"    {col(f'{idx}.', C.gold)} {os.path.basename(f)}")
    vid_choice = input(f"\n  {col('▸', C.magenta)} Choose video (1-{len(vids)}): ").strip()
    if not vid_choice.isdigit() or not (1 <= int(vid_choice) <= len(vids)):
        print(f"  {col('✖', C.red)} Invalid!")
        return
    video_file = vids[int(vid_choice) - 1]

    # Pick subtitle
    subs = scan_subtitle_files(scan_dir)
    if not subs:
        print(f"  {col('✖', C.red)} No subtitle files found!")
        return
    print(f"\n  {col('📄', C.blue)} Subtitle files:\n")
    for idx, f in enumerate(subs, 1):
        print(f"    {col(f'{idx}.', C.gold)} {os.path.basename(f)}")
    sub_choice = input(f"\n  {col('▸', C.magenta)} Choose subtitle (1-{len(subs)}): ").strip()
    if not sub_choice.isdigit() or not (1 <= int(sub_choice) <= len(subs)):
        print(f"  {col('✖', C.red)} Invalid!")
        return
    subtitle_file = subs[int(sub_choice) - 1]

    # Confirm
    print(f"\n  {col('🎬', C.magenta)} Video: {col(os.path.basename(video_file), C.bold)}")
    print(f"  {col('📄', C.blue)} Sub:   {col(os.path.basename(subtitle_file), C.bold)}")
    confirm = input(f"\n  {col('💽', C.cyan)} Start muxing? (Y/n): ").strip().lower()
    if confirm not in ('', 'y'):
        print(f"  {col('✖', C.red)} Cancelled!")
        return

    muxed = mux_subtitle_to_video(video_file, subtitle_file)
    if muxed:
        print(f"\n  {col('✓', C.green)} Created: {col(os.path.basename(muxed), C.bold)}")
    else:
        print(f"\n  {col('✖', C.red)} Mux failed!")

if __name__ == '__main__':
    main()
