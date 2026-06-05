"""
=============================================================
🎬 SUBTITLE TRANSLATOR - Dịch phụ đề ASS & SRT
=============================================================

CÔNG DỤNG:
- Dịch file phụ đề .ass (Advanced SubStation Alpha) và .srt (SubRip)
- Trích xuất phụ đề từ file video .mkv / .mp4
- Tự động bỏ qua các dòng drawing/vector (mã vẽ hình)
- Cho phép chọn style cần dịch (Default, Overlap, Flashback...)
- Hiển thị thanh tiến trình với thời gian ước tính (ETA)

CÔNG CỤ LIÊN QUAN:
    python mux_subtitle.py   - Ghép phụ đề vào file video

THƯ VIỆN CẦN CÀI:
    pip install googletrans==4.0.0rc1

CÁCH DÙNG:
    python subtitle_translator.py

=============================================================
"""

import re
import os
import glob
import asyncio
import time
import subprocess
import json
import sys
from googletrans import Translator
import Mux_Subtitle

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

# =============================================================
# GIẢI THÍCH CÁC THUẬT NGỆ SUB ASS
# =============================================================
#
# 1. STYLE (Kiểu dáng chữ)
#    -------------------------
#    Giống như "trang phục" của dòng chữ. Quy định màu sắc,
#    cỡ chữ, viền, vị trí hiển thị trên màn hình.
#
#    Các Style phổ biến:
#    - Default:   Đối thoại chính (trắng, viền đen, giữa màn hình)
#    - Overlap:   2 người nói cùng lúc (hiện 2 dòng đồng thời)
#    - Flashback: Hồi tưởng/ký ức (thường in nghiêng, màu xám)
#    - OPE:       Opening Effect (bài hát mở đầu có hiệu ứng phức tạp)
#    - OPR:       Opening Romaji (lời bài hát OP viết bằng chữ La-tinh)
#    - Sign:      Chữ trên biển bảng, tờ giấy trong anime
#
# 2. TAGS (Mã trong ngoặc nhọn {})
#    -------------------------
#    Lệnh điều khiển đặc biệt, chỉ áp dụng cho dòng đó:
#
#    - {\\an8}:     Alignment - Đẩy chữ lên trên
#    - {\\pos(x,y)}: Position - Đặt chữ ở tọa độ chính xác
#    - {\\i1}...{\\i0}: Italic - Chữ nghiêng (bật/tắt)
#    - {\\b1}...{\\b0}: Bold - Chữ đậm (bật/tắt)
#    - {\\c&HFF0000&}: Color - Đổi màu chữ (mã BGR)
#    - {\\p1}:      Drawing Mode - BẬT CHẾ ĐỘ VẼ VECTOR
#
# 3. DRAWING / VECTOR (Mã vẽ hình)
#    -------------------------
#    Khi làm hiệu ứng OP/ED (karaoke), subber dùng mã vẽ
#    để tạo hình ảnh (ánh sáng, vòng tròn, tia sáng...)
#
#    Các lệnh vẽ:
#    - m: Move    - Di chuyển bút vẽ đến tọa độ (nhấc bút lên)
#    - l: Line    - Vẽ đường thẳng đến tọa độ (kéo bút)
#    - b: Bézier  - Vẽ đường cong
#    - s: Spline  - Vẽ đường cong trơn
#    - p: Extend  - Tiếp tục đường vẽ trước đó
#    - c: Close   - Đóng đường vẽ (nối điểm cuối về đầu)
#    - n: New     - Bắt đầu đường vẽ mới (không đóng)
#
#    Ví dụ: m 44,7 1,8 l 52 3,3 51,1 7,8
#    -> Nhấc bút tới (44.7, 1.8), vẽ thẳng tới (52, 3.3),
#      vẽ thẳng tới (51.1, 7.8)
#
#    QUAN TRỌNG: Tool PHẢI bỏ qua các dòng này!
#    Nếu dịch, tọa độ sẽ bị hỏng, hiệu ứng nát, crash player.
#
# =============================================================


# ==================== TIỆN ÍCH UI ====================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_progress(current, total, start_time):
    if total == 0:
        return
    percent = current / total
    bar_length = 30
    filled = int(bar_length * percent)
    bar_fill = col('█' * filled, C.cyan)
    bar_empty = '░' * (bar_length - filled)
    bar = bar_fill + bar_empty
    elapsed = time.time() - start_time
    if current > 0 and current < total:
        eta_secs = (elapsed / current) * (total - current)
        eta_str = f"{int(eta_secs // 60):02d}:{int(eta_secs % 60):02d}"
    elif current >= total:
        eta_str = "00:00"
    else:
        eta_str = "--:--"
    speed = current / elapsed if elapsed > 0 else 0
    pct_str = col(f"{percent:>5.1%}", C.gold)
    count_str = col(f"{current}/{total}", C.magenta)
    eta_label = col(f"ETA: {eta_str}", C.dim if not USE_COLOR else '\033[2m')
    spd_str = col(f"{speed:.1f} lines/s", C.blue)
    print(
        f"\r  {col('▶', C.cyan)} [{bar}] {pct_str} | "
        f"{count_str} | "
        f"{eta_label} | "
        f"{spd_str}",
        end='', flush=True
    )


def print_banner():
    clear_screen()
    b = C.bold if USE_COLOR else type('', (), {})()
    print()
    print(col("  ╭──────────────────────────────────────────────────╮", C.cyan))
    print(col("  │", C.cyan) + col("      🎬  SUBTITLE TRANSLATOR  🎬        ", C.bold, C.magenta) + col("│", C.cyan))
    print(col("  │", C.cyan) + col("      ═══════════════════════════          ", C.dim) + col("│", C.cyan))
    print(col("  │", C.cyan) + f"      {col('✦', C.gold)} ASS  +  SRT  +  MKV  {col('✦', C.gold)}        " + col("│", C.cyan))
    print(col("  │", C.cyan) + f"      {col('▸', C.blue)} Translate  •  Extract {col('◂', C.blue)}            " + col("│", C.cyan))
    print(col("  ╰──────────────────────────────────────────────────╯", C.cyan))
    print(col(f"          crafted with {col('♥', C.red)} by BKhangDesu          ", C.dim))
    print()


def print_summary(input_file, output_file, src_lang, dest_lang, total_lines, elapsed):
    clear_screen()
    elapsed_min = int(elapsed // 60)
    elapsed_sec = int(elapsed % 60)
    print()
    print(col("  ╭──────────────────────────────────────────────────╮", C.green))
    print(col("  │", C.green) + col("            ✅  COMPLETE!  ✅              ", C.bold, C.green) + col("│", C.green))
    print(col("  ╰──────────────────────────────────────────────────╯", C.green))
    print()
    print(f"  {col('📂', C.cyan)} Input  :  {col(os.path.basename(input_file), C.bold)}")
    print(f"  {col('💾', C.magenta)} Output :  {col(os.path.basename(output_file), C.bold)}")
    print(f"  {col('🌐', C.blue)} Lang   :  {col(src_lang, C.gold)} {col('→', C.dim)} {col(dest_lang, C.gold)}")
    print(f"  {col('📊', C.magenta)} Lines  :  {col(str(total_lines), C.bold)}")
    print(f"  {col('⏱', C.cyan)} Time   :  {col(f'{elapsed_min:02d}:{elapsed_sec:02d}', C.bold)}")
    print()


# ==================== PHẦN CHUNG ====================

def scan_subtitle_files(directory='.'):
    """Quét thư mục tìm file .ass và .srt, sắp xếp mới nhất lên đầu"""
    files = []
    for ext in ('*.ass', '*.srt'):
        files += glob.glob(os.path.join(directory, ext))
        files += glob.glob(os.path.join(directory, '**', ext), recursive=True)
    files = list(set(files))
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return files


def get_language_input(prompt, default='en'):
    """Menu chọn ngôn ngữ nguồn/đích"""
    common = {
        '1': ('en', '🇬🇧 English'),
        '2': ('vi', '🇻🇳 Vietnamese'),
        '3': ('ja', '🇯🇵 Japanese'),
        '4': ('ko', '🇰🇷 Korean'),
        '5': ('zh-cn', '🇨🇳 Chinese'),
        '6': ('fr', '🇫🇷 French'),
        '7': ('th', '🇹🇭 Thai'),
    }
    print(f"\n  {col(prompt, C.bold)}")
    for k, (code, name) in common.items():
        print(f"    {col(f'{k}', C.gold)}  {name}  {col(f'({code})', C.dim)}")
    choice = input(f"  {col('▸', C.magenta)} [{col('default:', C.dim)} {col(default, C.cyan)}]: ").strip()
    if not choice:
        return default
    return common.get(choice, (choice,))[0]


_cache = {}

def is_untranslated(original, translated, src_lang):
    if not translated or not original:
        return False
    if original.strip().lower() == translated.strip().lower():
        return True
    if src_lang == 'en':
        orig_words = set(re.findall(r'[a-zA-Z]{2,}', original.lower()))
        trans_words = set(re.findall(r'[a-zA-Z]{2,}', translated.lower()))
        if orig_words and trans_words:
            overlap = len(orig_words & trans_words) / len(orig_words)
            if overlap > 0.8:
                return True
    return False


async def translate_batch(translator, texts, src_lang, dest_lang):
    r"""
    Dịch một nhóm câu cùng lúc (batch translation)
    
    Tại sao dùng batch?
    - Gửi 30 câu cùng lúc thay vì 1 câu -> Nhanh hơn 30 lần
    - Giảm số lượng request -> Ít bị giới hạn (rate limit)
    
    Nếu lỗi batch, tự động thử lại từng dòng riêng lẻ.
    Phát hiện dòng chưa dịch và thử lại.
    """
    # Check cache first
    cached = {}
    todo_idx = []
    todo_texts = []
    for i, t in enumerate(texts):
        key = (t, src_lang, dest_lang)
        if key in _cache:
            cached[i] = _cache[key]
        else:
            todo_idx.append(i)
            todo_texts.append(t)

    if todo_texts:
        try:
            results = await translator.translate(todo_texts, src=src_lang, dest=dest_lang)
            translated = [r.text for r in results]
        except Exception as e:
            print(f"\n  {col('⚠', C.gold)} Batch error ({len(todo_texts)} lines): {e}")
            translated = list(todo_texts)

        # Retry items that were not actually translated
        for j in range(len(todo_texts)):
            i = todo_idx[j]
            trans = translated[j]
            if is_untranslated(todo_texts[j], trans, src_lang):
                try:
                    await asyncio.sleep(1)
                    r = await translator.translate(todo_texts[j], src=src_lang, dest=dest_lang)
                    if not is_untranslated(todo_texts[j], r.text, src_lang):
                        trans = r.text
                except Exception:
                    pass
            _cache[(todo_texts[j], src_lang, dest_lang)] = trans
            cached[i] = trans

    return [cached[i] for i in range(len(texts))]


# ==================== XỬ LÝ ASS ====================

def parse_ass_line(line):
    r"""
    Tách dòng Dialogue thành 2 phần: prefix + text
    
    Cấu trúc dòng Dialogue:
    Dialogue: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
    
    Ví dụ:
    prefix = "Dialogue: 0,0:00:02.48,0:00:05.19,Default,,0,0,0,,"
    text   = "Allow me to introduce myself!"
    
    Chỉ dịch phần text, giữ nguyên prefix
    """
    match = re.match(
        r'^(Dialogue:\s*\d+,'
        r'[^,]*,[^,]*,[^,]*,[^,]*,'
        r'[^,]*,[^,]*,[^,]*,[^,]*,'
        r')(.+)$',
        line
    )
    if match:
        return match.group(1), match.group(2)
    return None, None


def is_drawing(text):
    r"""
    Kiểm tra text có phải là mã vẽ vector (drawing) không
    
    Cách nhận biết:
    1. Text bắt đầu bằng lệnh vẽ: m, l, b, s, p, c, n
    2. Có tag {\p1} (bật chế độ vẽ)
    3. Toàn là số và tọa độ (không có chữ)
    4. Tỷ lệ số/chữ rất cao (> 3:1)
    
    Nếu trả về True -> BỎ QUA dòng này, KHÔNG dịch!
    """
    stripped = text.strip()
    clean = re.sub(r'\{[^}]*\}', '', stripped).strip()
    
    # 1. Text bắt đầu bằng lệnh vẽ
    if re.match(r'^[mblspcn]\s', clean):
        return True
    
    # 2. Có tag {\p1} (drawing mode)
    if re.search(r'\{.*\\p\d+.*\}', stripped):
        return True
    
    # 3. Toàn là tọa độ
    if re.match(r'^[\d\s,.\-lmbnspc]+$', clean):
        return True
    
    # 4. Tỷ lệ số/chữ cao
    nums = len(re.findall(r'[\d\-]+', clean))
    words = len(re.findall(r'[a-zA-Z]{2,}', clean))
    if nums > 10 and (words == 0 or nums / max(words, 1) > 3):
        return True
    
    return False


def clean_ass_text(text):
    r"""
    Làm sạch text trước khi gửi đi dịch
    
    Các bước:
    1. Bỏ override tags: {\an8}, {\pos(100,200)}...
    2. Bỏ tất cả tags trong ngoặc {}
    3. Thay \\N và \\n bằng khoảng trắng
       (\\N = xuống dòng trong ASS, \\n = xuống dòng mềm)
    """
    clean = re.sub(r'\{\\[^}]*\}', '', text)
    clean = re.sub(r'\{[^}]*\}', '', clean)
    clean = clean.replace('\\N', ' ').replace('\\n', ' ')
    return clean.strip()


def restore_ass_tags(original, translated):
    r"""
    Khôi phục tag \\N sau khi dịch
    
    \\N trong ASS = xuống dòng cứng
    
    Nếu text gốc có \\N, text dịch cũng phải có \\N
    Ví dụ:
        Gốc:       "Hello\\NWorld" (2 dòng)
        Dịch:      "Xin chào\\NThế giới" (vẫn 2 dòng)
    """
    if '\\N' in original:
        translated = translated.replace('\n', '\\N')
    return translated


def analyze_ass(lines):
    r"""
    Phân tích file ASS - đếm số dòng theo từng Style
    
    Trả về dict:
    {
        'Default': {'total': 280, 'drawing': 0, 'text': 275, 'samples': [...]},
        'OPE':     {'total': 180, 'drawing': 175, 'text': 5, 'samples': [...]},
    }
    """
    styles = {}
    for line in lines:
        if not line.strip().startswith('Dialogue:'):
            continue
        prefix, text = parse_ass_line(line)
        if not prefix:
            continue
        style_match = re.search(r'Dialogue:\s*\d+,[^,]*,[^,]*,([^,]*),', prefix)
        style = style_match.group(1) if style_match else '(unknown)'
        if style not in styles:
            styles[style] = {'total': 0, 'drawing': 0, 'text': 0, 'samples': []}
        styles[style]['total'] += 1
        if is_drawing(text):
            styles[style]['drawing'] += 1
        else:
            clean = clean_ass_text(text)
            if clean:
                styles[style]['text'] += 1
                if len(styles[style]['samples']) < 3:
                    styles[style]['samples'].append(clean[:80])
    return styles


def select_styles(styles_info):
    r"""
    Menu chọn style cần dịch
    
    Logic gợi ý mặc định:
    - Dịch nếu: text > 0 VÀ drawing < 50% tổng số dòng
    - Bỏ qua nếu: toàn drawing (như OPE, OPR)
    
    Cách chọn:
    - Nhập số: "1,2,3"
    - Nhập tên: "Default,Overlap"
    - Nhập "all": dịch tất cả
    - Enter: dùng gợi ý mặc định
    """
    print()
    print(col(f"  ╭{'─'*56}╮", C.cyan))
    print(col(f"  │", C.cyan) + col(f"  📋  STYLE ANALYSIS (ASS)  ", C.bold, C.magenta) + col(f"│", C.cyan))
    print(col(f"  ╰{'─'*56}╯", C.cyan))
    style_list = list(styles_info.keys())
    for idx, (style, info) in enumerate(styles_info.items(), 1):
        print()
        print(f"    {col(f'{idx}.', C.gold)} {col(style, C.bold, C.cyan)}")
        print(f"       {col('Total:', C.dim)} {info['total']}  {col('|', C.dim)} {col('Text:', C.green)} {info['text']}  {col('|', C.dim)} {col('Drawing:', C.red)} {info['drawing']}")
        if info['samples']:
            for s in info['samples']:
                print(f"       {col('📄', C.dim)} \"{s}\"")
    default_translate = [
        s for s, i in styles_info.items()
        if i['text'] > 0 and i['drawing'] < i['total'] * 0.5
    ]
    print(f"\n  {col('💡', C.gold)} Suggest: {col(', '.join(default_translate), C.cyan)}")
    choice = input(f"  {col('▸', C.magenta)} Choose style (1,2,3 / all / Enter=suggest): ").strip()
    if not choice:
        return default_translate
    if choice.lower() == 'all':
        return list(styles_info.keys())
    selected = set()
    for part in choice.split(','):
        part = part.strip()
        if part.isdigit() and 1 <= int(part) <= len(style_list):
            selected.add(style_list[int(part) - 1])
        elif part in styles_info:
            selected.add(part)
    return list(selected) if selected else default_translate


async def translate_ass(input_file, output_file, src_lang, dest_lang):
    r"""
    Dịch file ASS
    
    Quy trình:
    1. Đọc file
    2. Phân tích style -> Cho user chọn
    3. Lọc dòng cần dịch (bỏ drawing, style không chọn, dòng trống)
    4. Dịch theo batch (30 dòng/lần)
    5. Ghi file mới (giữ nguyên các dòng không dịch)
    """
    translator = Translator()
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
    styles_info = analyze_ass(lines)
    translate_styles = select_styles(styles_info)
    entries = []
    skipped = {'draw': 0, 'style': 0, 'empty': 0}
    for i, line in enumerate(lines):
        if not line.strip().startswith('Dialogue:'):
            continue
        prefix, text = parse_ass_line(line)
        if not text:
            continue
        style_match = re.search(r'Dialogue:\s*\d+,[^,]*,[^,]*,([^,]*),', prefix)
        style = style_match.group(1) if style_match else ''
        if style not in translate_styles:
            skipped['style'] += 1
            continue
        if is_drawing(text):
            skipped['draw'] += 1
            continue
        clean = clean_ass_text(text)
        if not clean:
            skipped['empty'] += 1
            continue
        entries.append({'line_idx': i, 'prefix': prefix, 'original': text, 'clean': clean})
    clear_screen()
    print()
    print(col(f"  ╭{'─'*48}╮", C.cyan))
    print(col(f"  │", C.cyan) + col(f"  📊  TRANSLATION PLAN (ASS)     ", C.bold, C.magenta) + col(f"│", C.cyan))
    print(col(f"  ╰{'─'*48}╯", C.cyan))
    print(f"     {col('✅', C.green)} Translate: {col(str(len(entries)), C.bold)} lines")
    print(f"     {col('⏭', C.gold)} Skipped:   {skipped}")
    print(f"     {col('🌐', C.blue)} {src_lang} {col('→', C.dim)} {dest_lang}\n")
    if not entries:
        print(f"  {col('⚠', C.gold)} Nothing to translate!")
        return 0, 0
    start_time = time.time()
    translations = [''] * len(entries)
    batch_size = 30
    for i in range(0, len(entries), batch_size):
        batch = [e['clean'] for e in entries[i:i+batch_size]]
        results = await translate_batch(translator, batch, src_lang, dest_lang)
        for j, r in enumerate(results):
            translations[i+j] = r
        current = min(i + batch_size, len(entries))
        print_progress(current, len(entries), start_time)
        if i + batch_size < len(entries):
            await asyncio.sleep(1)
    print()

    # Verification: retry any lines still in source language
    still_bad = 0
    for idx in range(len(entries)):
        if is_untranslated(entries[idx]['clean'], translations[idx], src_lang):
            try:
                r = await translator.translate(entries[idx]['clean'], src=src_lang, dest=dest_lang)
                if not is_untranslated(entries[idx]['clean'], r.text, src_lang):
                    translations[idx] = r.text
                else:
                    still_bad += 1
            except Exception:
                still_bad += 1
    if still_bad:
        print(f"  {col('⚠', C.gold)} {still_bad} lines could not be translated (rate limit).")

    # Ghép lại file ASS
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        original_lines = f.readlines()

    for idx, entry in enumerate(entries):
        translated = translations[idx]
        if entry['original'].strip().startswith('<i>') and not translated.strip().startswith('<i>'):
            translated = f'<i>{translated}</i>'
        translated = restore_ass_tags(entry['original'], translated)
        translated = translated.replace('\n', ' ').replace('\r', '')
        original_lines[entry['line_idx']] = f"{entry['prefix']}{translated}\n"

    with open(output_file, 'w', encoding='utf-8-sig') as f:
        f.writelines(original_lines)
    elapsed = time.time() - start_time
    return len(entries), elapsed


# ==================== XỬ LÝ SRT ====================

def parse_srt(content):
    blocks = re.split(r'\r?\n\r?\n', content.strip())
    entries = []
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        index = lines[0].strip()
        timecode = lines[1].strip()
        text_lines = lines[2:]
        original_text = '\n'.join(text_lines)
        clean = re.sub(r'<[^>]+>', '', original_text).strip()
        if clean and re.match(r'^\d+$', index) and '-->' in timecode:
            entries.append({
                'index': index,
                'time': timecode,
                'original': original_text,
                'clean': clean
            })
    return entries


async def translate_srt(input_file, output_file, src_lang, dest_lang):
    translator = Translator()
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    entries = parse_srt(content)
    clear_screen()
    print()
    print(col(f"  ╭{'─'*48}╮", C.cyan))
    print(col(f"  │", C.cyan) + col(f"  📊  TRANSLATION PLAN (SRT)     ", C.bold, C.magenta) + col(f"│", C.cyan))
    print(col(f"  ╰{'─'*48}╯", C.cyan))
    print(f"     {col('✅', C.green)} Translate: {col(str(len(entries)), C.bold)} lines")
    print(f"     {col('🌐', C.blue)} {src_lang} {col('→', C.dim)} {dest_lang}\n")
    if not entries:
        print(f"  {col('⚠', C.gold)} Empty file!")
        return 0, 0
    start_time = time.time()
    translations = [''] * len(entries)
    batch_size = 30
    for i in range(0, len(entries), batch_size):
        batch = [e['clean'] for e in entries[i:i+batch_size]]
        results = await translate_batch(translator, batch, src_lang, dest_lang)
        for j, r in enumerate(results):
            translations[i+j] = r
        current = min(i + batch_size, len(entries))
        print_progress(current, len(entries), start_time)
        if i + batch_size < len(entries):
            await asyncio.sleep(1)
    print()

    # Verification: retry any lines still in source language
    still_bad = 0
    for idx in range(len(entries)):
        if is_untranslated(entries[idx]['clean'], translations[idx], src_lang):
            try:
                r = await translator.translate(entries[idx]['clean'], src=src_lang, dest=dest_lang)
                if not is_untranslated(entries[idx]['clean'], r.text, src_lang):
                    translations[idx] = r.text
                else:
                    still_bad += 1
            except Exception:
                still_bad += 1
    if still_bad:
        print(f"  {col('⚠', C.gold)} {still_bad} lines could not be translated (rate limit).")

    output_blocks = []
    for idx, entry in enumerate(entries):
        translated = translations[idx]
        if entry['original'].strip().startswith('<i>') and not translated.strip().startswith('<i>'):
            translated = f'<i>{translated}</i>'
        block = f"{entry['index']}\n{entry['time']}\n{translated}"
        output_blocks.append(block)
    with open(output_file, 'w', encoding='utf-8-sig') as f:
        f.write('\n\n'.join(output_blocks))
    elapsed = time.time() - start_time
    return len(entries), elapsed


# ==================== EXTRACT SUBTITLE TỪ VIDEO ====================

VIDEO_EXTENSIONS = ('.mkv', '.mp4', '.avi', '.mov', '.ts', '.m2ts')

def get_subtitle_streams(video_path):
    """Dùng ffprobe để liệt kê các luồng phụ đề trong file video"""
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


def extract_subtitle(video_path, stream_index, output_path):
    """Dùng ffmpeg để extract 1 luồng phụ đề từ video ra file .srt hoặc .ass"""
    ext = os.path.splitext(output_path)[1]
    cmd = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-map', f'0:{stream_index}',
        '-map_metadata', '-1',
        output_path
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=True)
        return os.path.isfile(output_path)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"  {col('✖', C.red)} Extract error: {e}")
        return False


def scan_video_files(directory='.'):
    """Quét thư mục tìm file video có chứa phụ đề"""
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


def pick_file(files, label='file'):
    for idx, f in enumerate(files, 1):
        size = os.path.getsize(f)
        ext = os.path.splitext(f)[1].upper()
        mtime = time.strftime('%H:%M %d/%m', time.localtime(os.path.getmtime(f)))
        icon = col('🎬', C.magenta) if is_video_file(f) else col('📄', C.blue)
        print(f"    {col(f'{idx}.', C.gold)} {icon} {os.path.basename(f):40s} {col(ext, C.dim):<5s} {col(f'{size:>8,}B', C.dim)}  {mtime}")
    choice = input(f"  {col('▸', C.magenta)} Choose {label} (1-{len(files)}): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(files):
        return files[int(choice) - 1]
    return None


def run_batch_mux():
    scan_dir = input(f"  {col('📁', C.cyan)} Directory (Enter=current): ").strip() or '.'
    print(f"\n  {col('🔍', C.cyan)} Scan: {col(os.path.abspath(scan_dir), C.bold)}")

    vids = scan_video_files(scan_dir)
    subs = Mux_Subtitle.scan_subtitle_files(scan_dir)

    if not vids:
        print(f"  {col('✖', C.red)} No video files found!")
        return
    if not subs:
        print(f"  {col('✖', C.red)} No subtitle files found!")
        return

    print(f"\n  {col('🎬', C.magenta)} Video files:\n")
    video = pick_file(vids, 'video')
    if not video:
        print(f"  {col('✖', C.red)} Invalid!")
        return

    print(f"\n  {col('📄', C.blue)} Subtitle files:\n")
    sub = pick_file(subs, 'subtitle')
    if not sub:
        print(f"  {col('✖', C.red)} Invalid!")
        return

    print(f"\n  {col('🎬', C.magenta)} Video: {col(os.path.basename(video), C.bold)}")
    print(f"  {col('📄', C.blue)} Sub:   {col(os.path.basename(sub), C.bold)}")
    confirm = input(f"\n  {col('💽', C.cyan)} Start muxing? (Y/n): ").strip().lower()
    if confirm not in ('', 'y'):
        print(f"  {col('✖', C.red)} Cancelled!")
        return

    print(f"\n  {col('⏳', C.cyan)} Muxing...")
    result = Mux_Subtitle.mux_subtitle_to_video(video, sub)
    if result:
        print(f"  {col('✓', C.green)} Muxed: {col(os.path.basename(result), C.bold)}")
    else:
        print(f"  {col('✖', C.red)} Mux failed!")


# ==================== MAIN ====================

async def main():
    """Hàm chính - Điều hướng toàn bộ program"""
    print_banner()

    mode = input(f"  {col('▸', C.magenta)} Mode ({col('1', C.gold)} Translate {col('2', C.gold)} Batch Mux [1]): ").strip()
    if mode == '2':
        run_batch_mux()
        return

    scan_dir = input(f"  {col('📁', C.cyan)} Directory (Enter=current): ").strip() or '.'
    print(f"\n  {col('🔍', C.cyan)} Scan: {col(os.path.abspath(scan_dir), C.bold)}")
    sub_files = scan_subtitle_files(scan_dir)
    video_files = scan_video_files(scan_dir)
    all_files = sub_files + video_files
    if not all_files:
        manual = input(f"  {col('✖', C.red)} Not found! Enter path: ").strip()
        if os.path.isfile(manual):
            all_files = [manual]
        else:
            print(f"  {col('✖', C.red)} File not found!")
            return
    print(f"\n  {col('📂', C.cyan)} {len(all_files)} files:\n")
    for idx, f in enumerate(all_files, 1):
        size = os.path.getsize(f)
        ext = os.path.splitext(f)[1].upper()
        mtime = time.strftime('%H:%M %d/%m', time.localtime(os.path.getmtime(f)))
        label = col("🎬", C.magenta) if is_video_file(f) else col("📄", C.blue)
        print(f"    {col(f'{idx}.', C.gold)} {label} {os.path.basename(f):40s} {col(ext, C.dim):<5s} {col(f'{size:>8,}B', C.dim)}  {mtime}")
    choice = input(f"\n  {col('▸', C.magenta)} Choose (1-{len(all_files)}) or path: ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(all_files):
        input_file = all_files[int(choice) - 1]
    elif os.path.isfile(choice):
        input_file = choice
    else:
        print(f"  {col('✖', C.red)} Invalid!")
        return
    ext = os.path.splitext(input_file)[1].lower()

    original_video = None
    if is_video_file(input_file):
        original_video = input_file
        print(f"\n  {col('🔍', C.cyan)} Scanning subtitles in {col(os.path.basename(input_file), C.bold)}...")
        streams = get_subtitle_streams(input_file)
        if not streams:
            print(f"  {col('✖', C.red)} No subtitle streams found in this video!")
            return
        print(f"\n  {col('📋', C.magenta)} Subtitle streams:\n")
        for idx, s in enumerate(streams, 1):
            lang = s['language']
            title = f" - {s['title']}" if s['title'] else ""
            print(f"    {col(f'{idx}.', C.gold)} [{col(s['codec'], C.cyan)}] {col(lang, C.bold)}{title}")
        sub_choice = input(f"\n  {col('▸', C.magenta)} Select track (1-{len(streams)}): ").strip()
        if not sub_choice.isdigit() or not (1 <= int(sub_choice) <= len(streams)):
            print(f"  {col('✖', C.red)} Invalid choice!")
            return
        selected_stream = streams[int(sub_choice) - 1]
        out_ext = '.ass' if selected_stream['codec'] in ('ass', 'ssa') else '.srt'
        extracted_path = input_file.rsplit('.', 1)[0] + f'_track{selected_stream["index"]}_{selected_stream["language"]}{out_ext}'
        print(f"\n  {col('📤', C.cyan)} Extracting {col(out_ext, C.bold)} track #{selected_stream['index']}...")
        if not extract_subtitle(input_file, selected_stream['index'], extracted_path):
            print(f"  {col('✖', C.red)} Extract failed!")
            return
        print(f"  {col('✓', C.green)} Extracted: {col(os.path.basename(extracted_path), C.bold)}")
        input_file = extracted_path
        ext = out_ext
    elif ext not in ('.ass', '.srt'):
        print(f"  {col('✖', C.red)} Format {ext} not supported!")
        return

    src_lang = get_language_input(col("🌐", C.blue) + " Source language:", 'en')
    dest_lang = get_language_input(col("🎯", C.magenta) + " Target language:", 'vi')
    default_out = input_file.replace(ext, f'_{dest_lang}{ext}')
    out = input(f"\n  {col('💾', C.green)} Output (Enter = {col(os.path.basename(default_out), C.cyan)}): ").strip()
    output_file = out or default_out
    clear_screen()
    print()
    print(col(f"  ╭{'─'*48}╮", C.cyan))
    print(col(f"  │", C.cyan) + col(f"  🚀  READY TO TRANSLATE       ", C.bold, C.magenta) + col(f"│", C.cyan))
    print(col(f"  ╰{'─'*48}╯", C.cyan))
    print(f"     {col('📄', C.cyan)} File:  {col(os.path.basename(input_file), C.bold)}")
    print(f"     {col('📦', C.magenta)} Type:  {col(ext.upper(), C.bold)}  {col('|', C.dim)}  {col(src_lang, C.gold)} {col('→', C.dim)} {col(dest_lang, C.gold)}")
    print(f"     {col('💾', C.green)} Out:   {col(os.path.basename(output_file), C.bold)}\n")
    if input(f"  {col('🚀', C.cyan)} Start? (Y/n): ").strip().lower() not in ('', 'y'):
        print(f"  {col('✖', C.red)} Cancelled!")
        return
    if ext == '.ass':
        total, elapsed = await translate_ass(input_file, output_file, src_lang, dest_lang)
    else:
        total, elapsed = await translate_srt(input_file, output_file, src_lang, dest_lang)
    if total > 0:
        print_summary(input_file, output_file, src_lang, dest_lang, total, elapsed)
        # Mux translated subtitle into video
        if original_video and os.path.isfile(original_video):
            print(f"\n  {col('🎬', C.magenta)} Mux translated subtitle into video?")
            mux_choice = input(f"  {col('▸', C.magenta)} Mux (Y/n): ").strip().lower()
            if mux_choice in ('', 'y'):
                muxed = Mux_Subtitle.mux_subtitle_to_video(original_video, output_file)
                if muxed:
                    print(f"  {col('✓', C.green)} Muxed: {col(os.path.basename(muxed), C.bold)}")
                else:
                    print(f"  {col('✖', C.red)} Mux failed!")
        else:
            # Input was a standalone subtitle file; offer to scan and mux
            print(f"\n  {col('🎬', C.magenta)} Mux translated subtitle into a video file?")
            mux_choice = input(f"  {col('▸', C.magenta)} Mux (Y/n): ").strip().lower()
            if mux_choice in ('', 'y'):
                vids = scan_video_files('.')
                if not vids:
                    print(f"  {col('✖', C.red)} No video files found in current directory!")
                else:
                    print(f"\n  {col('🎬', C.magenta)} Video files:\n")
                    for idx, f in enumerate(vids, 1):
                        print(f"    {col(f'{idx}.', C.gold)} {os.path.basename(f)}")
                    vid_choice = input(f"\n  {col('▸', C.magenta)} Choose video (1-{len(vids)}): ").strip()
                    if vid_choice.isdigit() and 1 <= int(vid_choice) <= len(vids):
                        video_file = vids[int(vid_choice) - 1]
                        muxed = Mux_Subtitle.mux_subtitle_to_video(video_file, output_file)
                        if muxed:
                            print(f"  {col('✓', C.green)} Muxed: {col(os.path.basename(muxed), C.bold)}")
                        else:
                            print(f"  {col('✖', C.red)} Mux failed!")

if __name__ == '__main__':
    asyncio.run(main())