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
import random
import subprocess
import json
import sys
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
from googletrans import Translator
import Mux_Subtitle

def mux_subtitle_wrapper(video_path, subtitle_path, output_path=None, lang_code='vi', lang_name='Vietnamese'):
    try:
        return Mux_Subtitle.mux_subtitle_to_video(video_path, subtitle_path, output_path, lang_code=lang_code, lang_name=lang_name)
    except TypeError:
        return Mux_Subtitle.mux_subtitle_to_video(video_path, subtitle_path, output_path)

_mux_has_multi = hasattr(Mux_Subtitle, 'mux_multiple_subtitles')

def mux_multiple_wrapper(video_path, subtitles, output_path=None):
    if _mux_has_multi:
        return Mux_Subtitle.mux_multiple_subtitles(video_path, subtitles, output_path)
    print(f"  {col('✖', C.red)} Function 'mux_multiple_subtitles' not found in Mux_Subtitle.py.")
    print(f"  {col('ℹ', C.cyan)} Merging one by one instead...")
    merged = None
    for sub_path, lang_code, lang_name in subtitles:
        merged = mux_subtitle_wrapper(video_path, sub_path, merged or output_path, lang_code=lang_code, lang_name=lang_name)
        if not merged:
            return None
    return merged

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

LANG_NAMES = {
    'en': 'English', 'vi': 'Vietnamese', 'ja': 'Japanese',
    'ko': 'Korean', 'zh-cn': 'Chinese', 'fr': 'French',
    'th': 'Thai', 'es': 'Spanish', 'de': 'German',
    'ru': 'Russian', 'pt': 'Portuguese', 'it': 'Italian',
}

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
    print(col("  │", C.cyan) + col("     🎬 SUBTITLE TRANSLATOR by BKhanggDesu 🎬     ", C.bold, C.magenta) + col("│", C.cyan))
    print(col("  │", C.cyan) + col("         ══════════════════════════════════       ", C.dim) + col("│", C.cyan))
    print(col("  │", C.cyan) + f"           {col('✦', C.gold)} ASS  +  SRT  +  MKV  {col('✦', C.gold)}               " + col("│", C.cyan))
    print(col("  │", C.cyan) + f"           {col('▸', C.blue)} Translate  •  Extract {col('◂', C.blue)}              " + col("│", C.cyan))
    print(col("  ╰──────────────────────────────────────────────────╯", C.cyan))
    print(col(f"              crafted with {col('♥', C.red)} by BKhangDesu          ", C.dim))
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


def get_multiple_languages_input(prompt, default='vi'):
    """Menu chọn nhiều ngôn ngữ đích (comma-separated)"""
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
    print(f"  {col('(comma-separated, e.g. 1,3,4)', C.dim)}")
    for k, (code, name) in common.items():
        print(f"    {col(f'{k}', C.gold)}  {name}  {col(f'({code})', C.dim)}")
    choice = input(f"  {col('▸', C.magenta)} [{col('default:', C.dim)} {col(default, C.cyan)}]: ").strip()
    if not choice:
        return [(default, LANG_NAMES.get(default, default))]
    selected = []
    for part in choice.split(','):
        part = part.strip()
        if part in common:
            code = common[part][0]
            selected.append((code, LANG_NAMES.get(code, code)))
        elif part in LANG_NAMES:
            selected.append((part, LANG_NAMES[part]))
    if not selected:
        return [(default, LANG_NAMES.get(default, default))]
    return selected


_cache = {}
_DISK_CACHE_DIRTY = False
_CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.trans_cache.json')

def _load_disk_cache():
    if not os.path.exists(_CACHE_PATH):
        return
    try:
        with open(_CACHE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for k, v in data.items():
            parts = k.split('\x00')
            if len(parts) == 3:
                _cache[(parts[0], parts[1], parts[2])] = v
    except Exception:
        pass

def _flush_cache():
    global _DISK_CACHE_DIRTY
    if not _DISK_CACHE_DIRTY:
        return
    try:
        data = {}
        for (t, s, d), v in _cache.items():
            data[f'{t}\x00{s}\x00{d}'] = v
        with open(_CACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        _DISK_CACHE_DIRTY = False
    except Exception:
        pass

_load_disk_cache()

LLM_SYSTEM_PROMPT = (
    "You are a professional anime/movie subtitle translator. "
    "Translate naturally and conversationally. "
    "Use appropriate pronouns and honorifics based on context. "
    "Keep the tone, emotion, and style of the original speaker. "
    "Preserve cultural references when possible."
)
LLM_BATCH_SIZE = 20
LLM_CONTEXT_SIZE = 10

def _parse_json_response(raw):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    raw = re.sub(r'```(?:json)?\s*', '', raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    brace_match = re.search(r'\{.*"translations"\s*:\s*\[.*\]\}', raw, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass
    return None

async def translate_batch_llm(entries, context, src_lang, dest_lang, llm_config):
    cached = {}
    todo_entries = []
    todo_indices = []
    for i, entry in enumerate(entries):
        key = (entry['clean'], src_lang, dest_lang)
        if key in _cache:
            cached[i] = _cache[key]
        else:
            todo_indices.append(i)
            todo_entries.append(entry)

    if not todo_entries:
        return [cached[i] for i in range(len(entries))]

    try:
        client = openai.AsyncClient(
            api_key=llm_config.get('api_key', ''),
            base_url=llm_config.get('base_url', 'https://api.openai.com/v1')
        )
        model = llm_config.get('model', 'gpt-4o-mini')
        system_prompt = llm_config.get('system_prompt', LLM_SYSTEM_PROMPT)

        src_name = src_lang
        dest_name = dest_lang
        for name, code in LANGUAGES.items():
            if code == src_lang:
                src_name = name
            if code == dest_lang:
                dest_name = name

        user_parts = []
        user_parts.append(f"Translate the following subtitle lines from {src_name} to {dest_name}.\n")
        if context:
            user_parts.append("Context (preceding lines for reference):")
            for c in context:
                user_parts.append(f"- {c}")
            user_parts.append("")
        user_parts.append("Lines to translate:")
        for idx, entry in enumerate(todo_entries, 1):
            user_parts.append(f"{idx}. {entry['clean']}")
        user_parts.append("")
        user_parts.append(
            'Respond with ONLY a valid JSON object in this exact format: '
            '{"translations": ["translation1", "translation2", ...]}'
        )
        user_prompt = "\n".join(user_parts)

        kwargs = dict(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
        )
        base_url = llm_config.get('base_url', '')
        if 'deepseek' not in base_url.lower():
            kwargs['response_format'] = {"type": "json_object"}

        response = await client.chat.completions.create(**kwargs)
        raw = response.choices[0].message.content.strip()
        data = _parse_json_response(raw)
        results = data.get("translations", []) if data else []

        if len(results) != len(todo_entries):
            print(f"\n  {col('⚠', C.gold)} LLM returned {len(results)} lines, expected {len(todo_entries)}. Using original text.")
            results = [e['clean'] for e in todo_entries]

        for j, entry in enumerate(todo_entries):
            trans = results[j] if j < len(results) else entry['clean']
            _cache[(entry['clean'], src_lang, dest_lang)] = trans
            _DISK_CACHE_DIRTY = True
            cached[todo_indices[j]] = trans

        return [cached[i] for i in range(len(entries))]

    except openai.AuthenticationError as e:
        print(f"\n  {col('✖', C.red)} API key invalid: {e}")
        return [e['clean'] for e in entries]
    except json.JSONDecodeError:
        print(f"\n  {col('✖', C.red)} LLM returned invalid JSON.")
        return [e['clean'] for e in entries]
    except Exception as e:
        print(f"\n  {col('✖', C.red)} LLM error: {e}")
        return [e['clean'] for e in entries]

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
            _DISK_CACHE_DIRTY = True
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


async def translate_ass(input_file, output_file, src_lang, dest_lang, batch_idx=None, batch_total=None, translate_styles=None, llm_config=None):
    r"""
    Dịch file ASS
    
    Quy trình:
    1. Đọc file
    2. Phân tích style -> Cho user chọn (nếu translate_styles=None)
    3. Lọc dòng cần dịch (bỏ drawing, style không chọn, dòng trống)
    4. Dịch theo batch (30 dòng/lần)
    5. Ghi file mới (giữ nguyên các dòng không dịch)
    """
    translator = Translator() if llm_config is None else None
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
    if translate_styles is None:
        styles_info = analyze_ass(lines)
        translate_styles = select_styles(styles_info)
    all_styles_list = None
    if translate_styles is not None and len(translate_styles) == 0:
        all_styles_list = True
        translate_styles = None
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
        if not all_styles_list and translate_styles is not None and style not in translate_styles:
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
    batch_tag = col(f" [{batch_idx}/{batch_total}] ", C.gold) if batch_idx else " "
    print()
    print(col(f"  ╭{'─'*48}╮", C.cyan))
    print(col(f"  │", C.cyan) + batch_tag + col(f"📊  TRANSLATION PLAN (ASS) ", C.bold, C.magenta) + col(f"│", C.cyan))
    print(col(f"  ╰{'─'*48}╯", C.cyan))
    print(f"     {col('✅', C.green)} Translate: {col(str(len(entries)), C.bold)} lines")
    print(f"     {col('⏭', C.gold)} Skipped:   {skipped}")
    print(f"     {col('🌐', C.blue)} {src_lang} {col('→', C.dim)} {dest_lang}\n")
    if not entries:
        print(f"  {col('⚠', C.gold)} Nothing to translate!")
        return 0, 0
    start_time = time.time()
    translations = [''] * len(entries)
    batch_size = 15 if llm_config is None else LLM_BATCH_SIZE
    for i in range(0, len(entries), batch_size):
        if llm_config:
            prev_idx = max(0, i - LLM_CONTEXT_SIZE)
            context = [e['clean'] for e in entries[prev_idx:i]]
            results = await translate_batch_llm(
                entries[i:i+batch_size], context, src_lang, dest_lang, llm_config
            )
        else:
            batch = [e['clean'] for e in entries[i:i+batch_size]]
            for attempt in range(3):
                try:
                    results = await translate_batch(translator, batch, src_lang, dest_lang)
                    break
                except Exception:
                    if attempt < 2:
                        await asyncio.sleep(random.uniform(2, 4))
                        continue
                    results = batch[:]
        for j, r in enumerate(results):
            translations[i+j] = r
        current = min(i + batch_size, len(entries))
        print_progress(current, len(entries), start_time)
        _flush_cache()
        if i + batch_size < len(entries):
            await asyncio.sleep(random.uniform(1.5, 3))
    print()

    # Verification: retry any lines still in source language
    still_bad = 0
    for idx in range(len(entries)):
        if is_untranslated(entries[idx]['clean'], translations[idx], src_lang):
            try:
                if llm_config:
                    r = await translate_batch_llm([entries[idx]], [], src_lang, dest_lang, llm_config)
                    translations[idx] = r[0]
                else:
                    r = await translator.translate(entries[idx]['clean'], src=src_lang, dest=dest_lang)
                    if not is_untranslated(entries[idx]['clean'], r.text, src_lang):
                        translations[idx] = r.text
                        _DISK_CACHE_DIRTY = True
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


async def translate_srt(input_file, output_file, src_lang, dest_lang, batch_idx=None, batch_total=None, llm_config=None):
    translator = Translator() if llm_config is None else None
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    entries = parse_srt(content)
    clear_screen()
    batch_tag = col(f" [{batch_idx}/{batch_total}] ", C.gold) if batch_idx else " "
    print()
    print(col(f"  ╭{'─'*48}╮", C.cyan))
    print(col(f"  │", C.cyan) + batch_tag + col(f"📊  TRANSLATION PLAN (SRT) ", C.bold, C.magenta) + col(f"│", C.cyan))
    print(col(f"  ╰{'─'*48}╯", C.cyan))
    print(f"     {col('✅', C.green)} Translate: {col(str(len(entries)), C.bold)} lines")
    print(f"     {col('🌐', C.blue)} {src_lang} {col('→', C.dim)} {dest_lang}\n")
    if not entries:
        print(f"  {col('⚠', C.gold)} Empty file!")
        return 0, 0
    start_time = time.time()
    translations = [''] * len(entries)
    batch_size = 15 if llm_config is None else LLM_BATCH_SIZE
    for i in range(0, len(entries), batch_size):
        if llm_config:
            prev_idx = max(0, i - LLM_CONTEXT_SIZE)
            context = [e['clean'] for e in entries[prev_idx:i]]
            results = await translate_batch_llm(
                entries[i:i+batch_size], context, src_lang, dest_lang, llm_config
            )
        else:
            batch = [e['clean'] for e in entries[i:i+batch_size]]
            for attempt in range(3):
                try:
                    results = await translate_batch(translator, batch, src_lang, dest_lang)
                    break
                except Exception:
                    if attempt < 2:
                        await asyncio.sleep(random.uniform(2, 4))
                        continue
                    results = batch[:]
        for j, r in enumerate(results):
            translations[i+j] = r
        current = min(i + batch_size, len(entries))
        print_progress(current, len(entries), start_time)
        _flush_cache()
        if i + batch_size < len(entries):
            await asyncio.sleep(random.uniform(1.5, 3))
    print()

    # Verification: retry any lines still in source language
    still_bad = 0
    for idx in range(len(entries)):
        if is_untranslated(entries[idx]['clean'], translations[idx], src_lang):
            try:
                if llm_config:
                    r = await translate_batch_llm([entries[idx]], [], src_lang, dest_lang, llm_config)
                    translations[idx] = r[0]
                else:
                    r = await translator.translate(entries[idx]['clean'], src=src_lang, dest=dest_lang)
                    if not is_untranslated(entries[idx]['clean'], r.text, src_lang):
                        translations[idx] = r.text
                        _DISK_CACHE_DIRTY = True
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


AUDIO_OUTPUT_FORMATS = {
    'aac': '.m4a', 'mp3': '.mp3', 'flac': '.flac', 'opus': '.opus',
    'vorbis': '.ogg', 'ac3': '.ac3', 'eac3': '.eac3', 'truehd': '.mka',
    'dts': '.dts', 'pcm_s16le': '.wav', 'pcm_s24le': '.wav', 'pcm_f32le': '.wav',
}

def get_audio_streams(video_path):
    """Dùng ffprobe để liệt kê các luồng audio trong file video"""
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_streams', '-select_streams', 'a', video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        streams = data.get('streams', [])
        audio_info = []
        for s in streams:
            index = s.get('index', 0)
            codec = s.get('codec_name', 'unknown')
            lang = s.get('tags', {}).get('language', 'und')
            title = s.get('tags', {}).get('title', '')
            channels = s.get('channels', 0)
            sample_rate = s.get('sample_rate', '0')
            bit_rate = s.get('bit_rate', '0')
            audio_info.append({
                'index': index,
                'codec': codec,
                'language': lang,
                'title': title,
                'channels': channels,
                'sample_rate': sample_rate,
                'bit_rate': bit_rate,
            })
        return audio_info
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  {col('✖', C.red)} Error reading audio streams: {e}")
        return []

def extract_audio_track(video_path, stream_index, output_path):
    """Dùng ffmpeg để extract 1 luồng audio từ video ra file audio"""
    cmd = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-map', f'0:{stream_index}',
        '-c:a', 'copy',
        output_path
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=300, check=True)
        return os.path.isfile(output_path)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"  {col('✖', C.red)} Audio extract error: {e}")
        if os.path.isfile(output_path):
            try: os.remove(output_path)
            except: pass
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


# ==================== MAIN ====================

def show_mux_menu(scan_dir):
    """Mux subtitle file into video file directly"""
    vids = scan_video_files(scan_dir)
    subs = scan_subtitle_files(scan_dir)
    if not vids:
        print(f"  {col('✖', C.red)} No video files found!")
        return
    if not subs:
        print(f"  {col('✖', C.red)} No subtitle files (.ass/.srt) found!")
        return

    print(f"\n  {col('🎬', C.magenta)} Video files:\n")
    for idx, f in enumerate(vids, 1):
        print(f"    {col(f'{idx}.', C.gold)} {os.path.basename(f)}")
    vid_choice = input(f"\n  {col('▸', C.magenta)} Choose video (1-{len(vids)}): ").strip()
    if not vid_choice.isdigit() or not (1 <= int(vid_choice) <= len(vids)):
        print(f"  {col('✖', C.red)} Invalid!")
        return
    video_file = vids[int(vid_choice) - 1]

    print(f"\n  {col('📄', C.blue)} Subtitle files:\n")
    for idx, f in enumerate(subs, 1):
        print(f"    {col(f'{idx}.', C.gold)} {os.path.basename(f)}")
    sub_choice = input(f"\n  {col('▸', C.magenta)} Choose subtitle (1-{len(subs)}): ").strip()
    if not sub_choice.isdigit() or not (1 <= int(sub_choice) <= len(subs)):
        print(f"  {col('✖', C.red)} Invalid!")
        return
    subtitle_file = subs[int(sub_choice) - 1]

    print(f"\n  {col('🎬', C.magenta)} Video: {col(os.path.basename(video_file), C.bold)}")
    print(f"  {col('📄', C.blue)} Sub:   {col(os.path.basename(subtitle_file), C.bold)}")
    confirm = input(f"\n  {col('💽', C.cyan)} Start muxing? (Y/n): ").strip().lower()
    if confirm not in ('', 'y'):
        print(f"  {col('✖', C.red)} Cancelled!")
        return

    muxed = mux_subtitle_wrapper(video_file, subtitle_file, lang_code='und', lang_name='')
    if muxed:
        print(f"\n  {col('✓', C.green)} Created: {col(os.path.basename(muxed), C.bold)}")
    else:
        print(f"\n  {col('✖', C.red)} Mux failed!")


def print_batch_progress(current, total, video_name, status):
    bar_length = 30
    percent = current / total if total > 0 else 0
    filled = int(bar_length * percent)
    bar_fill = col('█' * filled, C.cyan)
    bar_empty = '░' * (bar_length - filled)
    bar = bar_fill + bar_empty
    pct = col(f"{percent:>5.1%}", C.gold)
    count = col(f"{current}/{total}", C.magenta)
    label = col(video_name, C.bold)
    st = col(status, C.green if '✓' in status else C.red if '✖' in status else C.gold)
    print(f"\r  {col('▶', C.cyan)} [{bar}] {pct} | {count} | {label:40s} | {st}", end='', flush=True)


async def batch_translate_videos(scan_dir):
    """Batch translate all video files in directory"""
    vids = scan_video_files(scan_dir)
    if not vids:
        print(f"  {col('✖', C.red)} No video files found!")
        return

    # Filter only videos that have subtitle streams
    valid = []
    for v in vids:
        streams = get_subtitle_streams(v)
        if streams:
            valid.append((v, streams))
    if not valid:
        print(f"  {col('✖', C.red)} No videos with subtitle streams found!")
        return

    print(f"\n  {col('🎬', C.magenta)} Found {col(str(len(valid)), C.bold)} videos with subtitles:\n")
    for idx, (v, _) in enumerate(valid, 1):
        print(f"    {col(f'{idx}.', C.gold)} {os.path.basename(v)}")

    # Track selection mode
    print(f"\n  {col('🔢', C.cyan)} Track selection:")
    print(f"    {col('1.', C.gold)} Auto-select first track for all")
    print(f"    {col('2.', C.gold)} Pick track index manually")
    track_mode = input(f"  {col('▸', C.magenta)} Choose (1-2): ").strip()
    manual_track_idx = None
    if track_mode == '2':
        tk = input(f"  {col('▸', C.magenta)} Track number (1-based): ").strip()
        if tk.isdigit():
            manual_track_idx = int(tk) - 1

    src_lang = get_language_input(col("🌐", C.blue) + " Source language:", 'en')
    dest_lang = get_language_input(col("🎯", C.magenta) + " Target language:", 'vi')

    # Mux option
    print(f"\n  {col('🎬', C.magenta)} After translating, mux back into original video?")
    do_mux = input(f"  {col('▸', C.magenta)} Mux (Y/n): ").strip().lower() in ('', 'y')

    print(f"\n  {col('📊', C.cyan)} Ready: {col(str(len(valid)), C.bold)} videos, "
          f"{col(src_lang, C.gold)} → {col(dest_lang, C.gold)}, "
          f"{'with' if do_mux else 'without'} mux")
    if input(f"\n  {col('🚀', C.cyan)} Start batch? (Y/n): ").strip().lower() not in ('', 'y'):
        print(f"  {col('✖', C.red)} Cancelled!")
        return

    total_videos = len(valid)
    success_count = 0
    start_time = time.time()

    for idx, (video_path, streams) in enumerate(valid, 1):
        display_name = os.path.basename(video_path)
        print_batch_progress(idx - 1, total_videos, display_name, col("⏳ Extracting...", C.gold))
        print()

        # Select track
        if manual_track_idx is not None:
            if manual_track_idx < len(streams):
                sel_stream = streams[manual_track_idx]
            else:
                print(f"  {col('⚠', C.gold)} Track #{manual_track_idx + 1} not found, using first track")
                sel_stream = streams[0]
        else:
            sel_stream = streams[0]

        out_ext = '.ass' if sel_stream['codec'] in ('ass', 'ssa') else '.srt'
        extracted_path = video_path.rsplit('.', 1)[0] + f'_track{sel_stream["index"]}_{sel_stream["language"]}{out_ext}'
        if not extract_subtitle(video_path, sel_stream['index'], extracted_path):
            print(f"    {col('✖', C.red)} Extract failed for track #{sel_stream['index']}")
            continue

        # Translate
        print_batch_progress(idx - 1, total_videos, display_name, col("⏳ Translating...", C.gold))
        print()
        if out_ext == '.ass':
            total, elapsed = await translate_ass(extracted_path, extracted_path, src_lang, dest_lang, batch_idx=idx, batch_total=total_videos, llm_config=None)
        else:
            total, elapsed = await translate_srt(extracted_path, extracted_path, src_lang, dest_lang, batch_idx=idx, batch_total=total_videos, llm_config=None)

        # Clean up temp extracted file if not muxing (mux keeps it embedded)
        mux_ok = True
        if do_mux:
            print_batch_progress(idx - 1, total_videos, display_name, col("⏳ Muxing...", C.gold))
            print()
            lang_name = LANG_NAMES.get(dest_lang, dest_lang)
            muxed = mux_subtitle_wrapper(video_path, extracted_path, lang_code=dest_lang, lang_name=lang_name)
            if muxed:
                mux_ok = True
            else:
                mux_ok = False
                print(f"    {col('✖', C.red)} Mux failed!")

        # Clean up extracted subtitle file
        if os.path.isfile(extracted_path):
            try:
                os.remove(extracted_path)
            except OSError:
                pass

        if mux_ok:
            success_count += 1
            print_batch_progress(idx, total_videos, display_name, col("✓ Done", C.green))
        else:
            print_batch_progress(idx, total_videos, display_name, col("✖ Failed", C.red))
        print()

    elapsed = time.time() - start_time
    clear_screen()
    print()
    print(col(f"  ╭{'─'*48}╮", C.green))
    print(col(f"  │", C.green) + col(f"        ✅  BATCH COMPLETE  ✅                  ", C.bold, C.green) + col(f"│", C.green))
    print(col(f"  ╰{'─'*48}╯", C.green))
    print(f"     {col('✓', C.green)} Success: {col(str(success_count), C.bold)}/{col(str(total_videos), C.bold)} videos")
    print(f"     {col('⏱', C.cyan)} Time:    {col(f'{int(elapsed//60):02d}:{int(elapsed%60):02d}', C.bold)}")
    print()


async def multi_lang_translate(scan_dir):
    """Merge multiple subtitle files into one video."""
    vids = scan_video_files(scan_dir)
    if not vids:
        manual = input(f"  {col('✖', C.red)} Enter video path: ").strip()
        if os.path.isfile(manual):
            vids = [manual]
        else:
            print(f"  {col('✖', C.red)} Not found!")
            return

    print(f"\n  {col('🎬', C.magenta)} Video files:\n")
    for idx, f in enumerate(vids, 1):
        print(f"    {col(f'{idx}.', C.gold)} {os.path.basename(f)}")
    v_choice = input(f"\n  {col('▸', C.magenta)} Choose video (1-{len(vids)}): ").strip()
    if not v_choice.isdigit() or not (1 <= int(v_choice) <= len(vids)):
        print(f"  {col('✖', C.red)} Invalid!")
        return
    video_path = vids[int(v_choice) - 1]

    subs = scan_subtitle_files(scan_dir)
    if not subs:
        print(f"  {col('✖', C.red)} No subtitle files found!")
        return
    print(f"\n  {col('📄', C.blue)} Subtitle files (select multiple, comma-separated):\n")
    for idx, f in enumerate(subs, 1):
        print(f"    {col(f'{idx}.', C.gold)} {os.path.basename(f)}")
    raw = input(f"\n  {col('▸', C.magenta)} Choices (e.g. 1,3,5): ").strip()
    selected = []
    for part in raw.split(','):
        part = part.strip()
        if part.isdigit() and 1 <= int(part) <= len(subs):
            fp = subs[int(part) - 1]
            base = os.path.splitext(os.path.basename(fp))[0]
            parts = base.rsplit('_', 1)
            if len(parts) == 2 and parts[1] in LANG_NAMES:
                lang_code = parts[1]
                lang_name = LANG_NAMES[lang_code]
            else:
                lang_code = 'und'
                lang_name = os.path.basename(fp)
            selected.append((fp, lang_code, lang_name))
    if not selected:
        print(f"  {col('✖', C.red)} No valid files selected!")
        return

    output = video_path.rsplit('.', 1)[0] + '_merged.' + video_path.rsplit('.', 1)[1]
    print(f"\n  {col('📊', C.cyan)} Merging {len(selected)} subs into {col(os.path.basename(video_path), C.bold)}")
    for fp, code, name in selected:
        print(f"    {col('📄', C.blue)} {os.path.basename(fp)}  {col(f'({code}: {name})', C.dim)}")
    confirm = input(f"\n  {col('🚀', C.cyan)} Start? (Y/n): ").strip().lower()
    if confirm not in ('', 'y'):
        print(f"  {col('✖', C.red)} Cancelled!")
        return

    print(f"\n  {col('🎬', C.magenta)} Merging...")
    result = mux_multiple_wrapper(video_path, selected, output)
    if result:
        print(f"  {col('✓', C.green)} Merged: {col(os.path.basename(result), C.bold)}")
    else:
        print(f"  {col('✖', C.red)} Merge failed!")


def switch_audio_menu(scan_dir):
    """Chọn & chuyển đổi audio dub trong file video (remux với audio track khác)"""
    vids = scan_video_files(scan_dir)
    if not vids:
        manual = input(f"  {col('✖', C.red)} Not found! Enter video path: ").strip()
        if os.path.isfile(manual):
            vids = [manual]
        else:
            print(f"  {col('✖', C.red)} File not found!")
            return

    print(f"\n  {col('🎬', C.magenta)} Video files:\n")
    for idx, f in enumerate(vids, 1):
        print(f"    {col(f'{idx}.', C.gold)} {os.path.basename(f)}")
    v_choice = input(f"\n  {col('▸', C.magenta)} Choose video (1-{len(vids)}): ").strip()
    if not v_choice.isdigit() or not (1 <= int(v_choice) <= len(vids)):
        print(f"  {col('✖', C.red)} Invalid!")
        return
    video_path = vids[int(v_choice) - 1]

    print(f"\n  {col('🔍', C.cyan)} Scanning audio tracks in {col(os.path.basename(video_path), C.bold)}...")
    streams = get_audio_streams(video_path)
    if not streams:
        print(f"  {col('✖', C.red)} No audio streams found!")
        return

    print(f"\n  {col('🎵', C.magenta)} Available audio dubs:\n")
    for idx, s in enumerate(streams, 1):
        lang = s['language']
        codec = s['codec']
        title = f" - {s['title']}" if s['title'] else ""
        ch = f"{s['channels']}ch" if s['channels'] else ""
        sr = f"{int(s['sample_rate'])//1000}kHz" if s['sample_rate'] != '0' else ""
        info = f"  {ch} {sr}" if ch or sr else ""
        print(f"    {col(f'{idx}.', C.gold)} [{col(codec, C.cyan)}] {col(lang, C.bold)}{title}{info}")

    sel = input(f"\n  {col('▸', C.magenta)} Select audio track to switch to (1-{len(streams)}): ").strip()
    if not sel.isdigit() or not (1 <= int(sel) <= len(streams)):
        print(f"  {col('✖', C.red)} Invalid!")
        return
    selected = streams[int(sel) - 1]

    # Create output directory
    base_dir = os.path.dirname(video_path) or '.'
    out_dir = os.path.join(base_dir, '_audio_switched')
    os.makedirs(out_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(video_path))[0]
    video_ext = os.path.splitext(video_path)[1]
    lang_tag = selected['language'] if selected['language'] != 'und' else f'track{selected["index"]}'
    output_path = os.path.join(out_dir, f'{base_name}_{lang_tag}{video_ext}')

    print(f"\n  {col('🎵', C.cyan)} Switching to: {col(selected['language'], C.bold)} audio ({selected['codec']})")
    print(f"  {col('💾', C.green)} Output:       {col(os.path.basename(output_path), C.bold)}")
    print(f"  {col('📁', C.blue)} Directory:    {col(out_dir, C.dim)}")
    print(f"  {col('ℹ', C.gold)} Video & subtitles kept, only audio switched")
    confirm = input(f"\n  {col('🚀', C.cyan)} Remux? (Y/n): ").strip().lower()
    if confirm not in ('', 'y'):
        print(f"  {col('✖', C.red)} Cancelled!")
        return

    # Find the index of the selected audio within audio-only streams (0-based)
    audio_streams = get_audio_streams(video_path)
    audio_order = -1
    for i, s in enumerate(audio_streams):
        if s['index'] == selected['index']:
            audio_order = i
            break

    cmd = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-map', '0:v',
        '-map', f'0:a:{audio_order}',
        '-map', '0:s?',
        '-c', 'copy',
        '-disposition:a:0', 'default',
        output_path
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=600, check=True)
        if os.path.isfile(output_path):
            print(f"\n  {col('✓', C.green)} Switched: {col(os.path.basename(output_path), C.bold)}")
        else:
            print(f"\n  {col('✖', C.red)} Remux failed!")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"\n  {col('✖', C.red)} Remux error: {e}")


async def main():
    """Hàm chính - Điều hướng toàn bộ program"""
    print_banner()

    scan_dir = input(f"  {col('📁', C.cyan)} Directory (Enter=current): ").strip() or '.'
    print(f"\n  {col('🔍', C.cyan)} Scan: {col(os.path.abspath(scan_dir), C.bold)}")

    # === Main Menu ===
    print()
    print(col(f"  ╭{'─'*48}╮", C.cyan))
    print(col(f"  │", C.cyan) + col(f"                📋  MAIN MENU                   ", C.bold, C.magenta) + col(f"│", C.cyan))
    print(col(f"  ╰{'─'*48}╯", C.cyan))
    print(f"    {col('1.', C.gold)} {col('Translate', C.bold, C.cyan)}     {col('Dịch phụ đề ASS/SRT', C.dim)}")
    print(f"    {col('2.', C.gold)} {col('Mux', C.bold, C.cyan)}          {col('Ghép phụ đề vào video MP4/MKV', C.dim)}")
    print(f"    {col('3.', C.gold)} {col('Batch Translate', C.bold, C.cyan)}  {col('Dịch & mux hàng loạt video', C.dim)}")
    print(f"    {col('4.', C.gold)} {col('Merge Subs', C.bold, C.cyan)}  {col('Gộp nhiều sub vào 1 video', C.dim)}")
    print(f"    {col('5.', C.gold)} {col('Switch Audio', C.bold, C.cyan)}  {col('Chuyển đổi audio dub trong video', C.dim)}")
    mode = input(f"\n  {col('▸', C.magenta)} Choose (1-5): ").strip()

    if mode == '2':
        show_mux_menu(scan_dir)
        return
    if mode == '3':
        await batch_translate_videos(scan_dir)
        return
    if mode == '4':
        await multi_lang_translate(scan_dir)
        return
    if mode == '5':
        switch_audio_menu(scan_dir)
        return

    # === TRANSLATE FLOW ===
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
    dest_langs = get_multiple_languages_input(col("🎯", C.magenta) + " Target language(s):", 'vi')

    llm_config = None
    if HAS_OPENAI:
        print(f"\n  {col('⚙', C.cyan)} Translation engine:")
        print(f"    {col('1.', C.gold)} Google Translate  {col('(default)', C.dim)}")
        print(f"    {col('2.', C.gold)} LLM  {col('(DeepSeek/OpenAI...)', C.dim)}")
        eng = input(f"  {col('▸', C.magenta)} Choose (1-2): ").strip()
        if eng == '2':
            api_key = os.environ.get('OPENAI_API_KEY', '')
            if not api_key:
                api_key = input(f"  {col('🔑', C.gold)} API key (or set OPENAI_API_KEY env): ").strip()
            base_url = input(f"  {col('🌐', C.cyan)} Base URL (Enter = {col('https://api.openai.com/v1', C.dim)}): ").strip() or 'https://api.openai.com/v1'
            model = input(f"  {col('🤖', C.magenta)} Model (Enter = {col('gpt-4o-mini', C.dim)}): ").strip() or 'gpt-4o-mini'
            llm_config = {'api_key': api_key, 'base_url': base_url, 'model': model}
    elif not HAS_OPENAI:
        print(f"\n  {col('⚙', C.cyan)} Engine: Google Translate  {col('(pip install openai for LLM)', C.dim)}")

    if len(dest_langs) > 1:
        print(f"\n  {col('📊', C.cyan)} Translating to {col(str(len(dest_langs)), C.bold)} languages:")
        for code, name in dest_langs:
            print(f"    {col('▸', C.gold)} {name} ({code})")
        if input(f"\n  {col('🚀', C.cyan)} Start? (Y/n): ").strip().lower() not in ('', 'y'):
            print(f"  {col('✖', C.red)} Cancelled!")
            return

        base_dir = os.path.dirname(input_file) or '.'
        out_dir = os.path.join(base_dir, '_multi')
        os.makedirs(out_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        translated = []
        for lang_code, lang_name in dest_langs:
            out_file = os.path.join(out_dir, f'{base_name}_{lang_code}{ext}')
            print(f"\n  {col('📄', C.cyan)} Translating to {col(lang_name, C.bold)} ({lang_code})...")
            if ext == '.ass':
                total, elapsed = await translate_ass(input_file, out_file, src_lang, lang_code, llm_config=llm_config)
            else:
                total, elapsed = await translate_srt(input_file, out_file, src_lang, lang_code, llm_config=llm_config)
            if total > 0:
                translated.append((out_file, lang_code, lang_name))

        if original_video and translated:
            print(f"\n  {col('🎬', C.magenta)} Muxing {col(str(len(translated)), C.bold)} subtitle tracks into video...")
            output_video = original_video.rsplit('.', 1)[0] + '_multi.' + original_video.rsplit('.', 1)[1]
            muxed = mux_multiple_wrapper(original_video, translated, output_video)
            if muxed:
                print(f"  {col('✓', C.green)} Muxed: {col(os.path.basename(muxed), C.bold)}")
            else:
                print(f"  {col('✖', C.red)} Mux failed!")
        elif translated:
            print(f"\n  {col('✓', C.green)} Translated to {col(str(len(translated)), C.bold)} languages:")
            for fp, code, name in translated:
                print(f"    {col('📄', C.blue)} {os.path.basename(fp)}  {col(f'({name})', C.dim)}")

        if original_video and os.path.isfile(input_file):
            try: os.remove(input_file)
            except: pass
        return

    dest_lang = dest_langs[0][0]
    default_out = input_file.replace(ext, f'_{dest_lang}{ext}')
    out = input(f"\n  {col('💾', C.green)} Output (Enter = {col(os.path.basename(default_out), C.cyan)}): ").strip()
    output_file = out or default_out
    clear_screen()
    print()
    print(col(f"  ╭{'─'*48}╮", C.cyan))
    print(col(f"  │", C.cyan) + col(f"            🚀  READY TO TRANSLATE 🚀           ", C.bold, C.magenta) + col(f"│", C.cyan))
    print(col(f"  ╰{'─'*48}╯", C.cyan))
    print(f"     {col('📄', C.cyan)} File:  {col(os.path.basename(input_file), C.bold)}")
    print(f"     {col('📦', C.magenta)} Type:  {col(ext.upper(), C.bold)}  {col('|', C.dim)}  {col(src_lang, C.gold)} {col('→', C.dim)} {col(dest_lang, C.gold)}")
    print(f"     {col('💾', C.green)} Out:   {col(os.path.basename(output_file), C.bold)}\n")
    if input(f"  {col('🚀', C.cyan)} Start? (Y/n): ").strip().lower() not in ('', 'y'):
        print(f"  {col('✖', C.red)} Cancelled!")
        return
    if ext == '.ass':
        total, elapsed = await translate_ass(input_file, output_file, src_lang, dest_lang, llm_config=llm_config)
    else:
        total, elapsed = await translate_srt(input_file, output_file, src_lang, dest_lang, llm_config=llm_config)
    if total > 0:
        print_summary(input_file, output_file, src_lang, dest_lang, total, elapsed)
        if original_video and os.path.isfile(original_video):
            print(f"\n  {col('🎬', C.magenta)} Mux translated subtitle into video?")
            mux_choice = input(f"  {col('▸', C.magenta)} Mux (Y/n): ").strip().lower()
            if mux_choice in ('', 'y'):
                lang_name = LANG_NAMES.get(dest_lang, dest_lang)
                muxed = mux_subtitle_wrapper(original_video, output_file, lang_code=dest_lang, lang_name=lang_name)
                if muxed:
                    print(f"  {col('✓', C.green)} Muxed: {col(os.path.basename(muxed), C.bold)}")
                else:
                    print(f"  {col('✖', C.red)} Mux failed!")
        else:
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
                        lang_name = LANG_NAMES.get(dest_lang, dest_lang)
                        muxed = mux_subtitle_wrapper(video_file, output_file, lang_code=dest_lang, lang_name=lang_name)
                        if muxed:
                            print(f"  {col('✓', C.green)} Muxed: {col(os.path.basename(muxed), C.bold)}")
                        else:
                            print(f"  {col('✖', C.red)} Mux failed!")

if __name__ == '__main__':
    asyncio.run(main())