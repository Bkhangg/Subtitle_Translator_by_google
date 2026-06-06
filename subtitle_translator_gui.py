"""
Subtitle Translator GUI - tkinter interface
Multi-language: English, Vietnamese, Chinese, Japanese, Korean
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import time
import threading
import asyncio
import re
import glob
import json
import subprocess

import Mux_Subtitle
import Subtitle_Translator

from googletrans import Translator

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

LANGUAGES = {
    'English': 'en', 'Vietnamese': 'vi', 'Japanese': 'ja',
    'Korean': 'ko', 'Chinese': 'zh-cn', 'French': 'fr',
    'Thai': 'th', 'Spanish': 'es', 'German': 'de',
    'Russian': 'ru', 'Portuguese': 'pt', 'Italian': 'it',
}

LANG_NAMES = {v: k for k, v in LANGUAGES.items()}

UI_LANGUAGES = ['en', 'vi', 'zh', 'ja', 'ko']
UI_LANG_NAMES = {
    'en': 'English',
    'vi': 'Tiếng Việt',
    'zh': '中文',
    'ja': '日本語',
    'ko': '한국어',
}

FONT_FAMILIES = ['Consolas', 'Segoe UI', 'Arial', 'Tahoma', 'Verdana', 'Calibri']

UI_STRINGS = {
    'en': {
        'app_title': '\U0001f3ac Subtitle Translator',
        'font_label': 'Font:',
        'lang_ui': 'Language:',
        'file_section': '\U0001f4c1 File Selection',
        'dir_label': 'Directory:',
        'browse': 'Browse',
        'scan': 'Scan',
        'no_files': '(No subtitle files found)',
        'no_files_log': 'No .ass or .srt files found.',
        'found_files': 'Found {count} subtitle file(s).',
        'lang_section': '\U0001f310 Language',
        'source': 'Source:',
        'target': 'Target:',
        'swap': '\u21c4',
        'same_lang_msg': 'Source and target languages are the same ({lang}). Please choose different languages.',
        'output_section': '\U0001f4be Output',
        'engine_section': '\u2699\ufe0f Translation Engine',
        'engine_label': 'Engine:',
        'google_engine': 'Google Translate',
        'llm_engine': 'LLM (AI)',
        'api_key': 'API Key:',
        'base_url': 'Base URL:',
        'model': 'Model:',
        'test': 'Test',
        'deepseek': 'DeepSeek',
        'sys_prompt': 'System prompt:',
        'style_section': '\U0001f3a8 ASS Style Selection',
        'select_styles': 'Select styles to translate:',
        'style_item': '{style}  (\U0001f4dd {text} | \U0001f3a8 {drawing} | {total} {count})',
        'total_label': 'Total:',
        'start': '\U0001f680 Start Translation',
        'cancel': '\u2715 Cancel',
        'progress_section': 'Progress',
        'ready': 'Ready',
        'log_section': 'Log',
        'mux_section': '\U0001f3ac Mux',
        'planned': 'Planned: {total} lines to translate',
        'translating_log': 'Translating {total} lines...',
        'progress_fmt': '{current}/{total} | ETA: {eta} | {speed:.1f} lines/s',
        'complete_status': '\u2705 Complete! {total} lines in {min:02d}:{sec:02d}',
        'done_log': '\u2705 Done! {total} lines translated in {min:02d}:{sec:02d}',
        'error_status': '\u274c Error: {msg}',
        'error_log': '\u274c Error: {msg}',
        'cancelled_status': 'Cancelled',
        'cancelled_log': '\u2715 Translation cancelled.',
        'starting_fmt': 'Starting ({engine})...',
        'engine_log': 'Engine: {engine}',
        'translating_log_fmt': 'Translating: {name}',
        'format_log_fmt': '  {ext} | {src} \u2192 {dest}',
        'output_log_fmt': '  Output: {name}',
        'selected_log': 'Selected: {name}',
        'cannot_read_log': 'Cannot read file: {name}',
        'quit_title': 'Quit?',
        'quit_msg': 'Translation in progress. Cancel?',
        'missing_dep_title': 'Missing Dependency',
        'missing_dep_msg': 'Install openai library:\n\npip install openai',
        'missing_key_title': 'Missing API Key',
        'missing_key_msg': 'Enter your API key for LLM mode.',
        'no_file_title': 'No file',
        'no_file_msg': 'Please select a subtitle file.',
        'no_style_title': 'No style',
        'no_style_msg': 'Select at least one style to translate.',
        'overwrite_title': 'Overwrite?',
        'overwrite_msg': "'{name}' exists. Overwrite?",
        'llm_enter_key': '\u274c Enter API key',
        'llm_enter_model': '\u274c Enter model name',
        'llm_testing': '\u23f3 Testing...',
        'llm_connected': '\u2705 Connected! Response: {response}',
        'llm_invalid_key': '\u274c Invalid API key',
        'llm_model_not_found': "\u274c Model '{model}' not found",
        'llm_error': '\u274c {msg}',
        'llm_deepseek_applied': '\u2705 DeepSeek preset applied. Enter your API key and click Test.',
        'llm_warning': '\u26a0\ufe0f pip install openai',
        'extract_btn': '\U0001f3ac Extract',
        'video_selected_log': '\U0001f3ac Video selected. Choose a subtitle track to extract.',
        'select_track_title': 'Select Subtitle Track',
        'select_track_header': 'Subtitle streams in:\n{name}',
        'select_track_ok': 'OK',
        'select_track_cancel': 'Cancel',
        'select_track_error': 'No subtitle streams found in this video file!',
        'select_track_error_log': 'No subtitle streams found.',
        'mux_checkbox': '\U0001f3ac Mux into video after translation',
        'mux_muxing': '\U0001f3ac Muxing subtitle into video...',
        'mux_success': '\u2705 Muxed: {name}',
        'mux_fail': '\u274c Mux failed!',
        'mux_no_video': 'No video files found!',
        'mux_no_video_log': 'No video files found for muxing.',
        'mux_choose_title': 'Select Video for Muxing',
        'mux_choose_header': 'Select a video file to mux the translated subtitle into:',
        'mux_ok': 'Mux',
        'mux_cancel': 'Cancel',
        'mux_cancelled_log': 'Mux cancelled.',
        'simple_mux_title': '\U0001f3ac Batch Mux',
        'batch_translate_title': '\U0001f3ac Batch Translate',
        'batch_translate_desc': 'Translate & mux all videos in folder',
        'batch_translate_btn': '\u25b6 Start',
        'help_text': (
            "Step 1 \u2192 \U0001f4c2 Pick folder + Scan\n"
            "Step 2 \u2192 \U0001f3ac Select a file / Extract from video\n"
            "Step 3 \u2192 \U0001f310 Choose languages + Start"
        ),
    },
    'vi': {
        'app_title': '\U0001f3ac Tr\u00ecnh D\u1ecbch Ph\u1ee5 \u0110\u1ec1',
        'font_label': 'Ph\u00f4ng:',
        'lang_ui': 'Ng\u00f4n ng\u1eef:',
        'file_section': '\U0001f4c1 Ch\u1ecdn T\u1ec7p',
        'dir_label': 'Th\u01b0 m\u1ee5c:',
        'browse': 'Duy\u1ec7t',
        'scan': 'Qu\u00e9t',
        'no_files': '(Kh\u00f4ng t\u00ecm th\u1ea5y t\u1ec7p ph\u1ee5 \u0111\u1ec1)',
        'no_files_log': 'Kh\u00f4ng t\u00ecm th\u1ea5y t\u1ec7p .ass ho\u1eb7c .srt.',
        'found_files': 'T\u00ecm th\u1ea5y {count} t\u1ec7p ph\u1ee5 \u0111\u1ec1.',
        'lang_section': '\U0001f310 Ng\u00f4n Ng\u1eef',
        'source': 'Ngu\u1ed3n:',
        'target': '\u0110\u00edch:',
        'swap': '\u21c4',
        'same_lang_msg': 'Ng\u00f4n ng\u1eef ngu\u1ed3n v\u00e0 \u0111\u00edch gi\u1ed1ng nhau ({lang}). Vui l\u00f2ng ch\u1ecdn ng\u00f4n ng\u1eef kh\u00e1c.',
        'output_section': '\U0001f4be \u0110\u1ea7u Ra',
        'engine_section': '\u2699\ufe0f C\u00f4ng C\u1ee5 D\u1ecbch',
        'engine_label': 'C\u00f4ng c\u1ee5:',
        'google_engine': 'Google D\u1ecbch',
        'llm_engine': 'LLM (AI)',
        'api_key': 'Kh\u00f3a API:',
        'base_url': 'URL G\u1ed1c:',
        'model': 'M\u00f4 h\u00ecnh:',
        'test': 'Ki\u1ec3m tra',
        'deepseek': 'DeepSeek',
        'sys_prompt': 'C\u00e2u l\u1ec7nh h\u1ec7 th\u1ed1ng:',
        'style_section': '\U0001f3a8 Ch\u1ecdn Ki\u1ec3u ASS',
        'select_styles': 'Ch\u1ecdn ki\u1ec3u c\u1ea7n d\u1ecbch:',
        'style_item': '{style}  (\U0001f4dd {text} | \U0001f3a8 {drawing} | {total} {count})',
        'total_label': 'T\u1ed5ng:',
        'start': '\U0001f680 B\u1eaft \u0110\u1ea7u D\u1ecbch',
        'cancel': '\u2715 H\u1ee7y',
        'progress_section': 'Ti\u1ebfn Tr\u00ecnh',
        'ready': 'S\u1eb5n s\u00e0ng',
        'log_section': 'Nh\u1eadt K\u00fd',
        'mux_section': '\U0001f3ac Gh\u00e9p',
        'planned': '\u0110\u00e3 l\u00ean k\u1ebf ho\u1ea1ch: {total} d\u00f2ng c\u1ea7n d\u1ecbch',
        'translating_log': '\u0110ang d\u1ecbch {total} d\u00f2ng...',
        'progress_fmt': '{current}/{total} | ETA: {eta} | {speed:.1f} d\u00f2ng/s',
        'complete_status': '\u2705 Ho\u00e0n th\u00e0nh! {total} d\u00f2ng trong {min:02d}:{sec:02d}',
        'done_log': '\u2705 Xong! {total} d\u00f2ng \u0111\u00e3 d\u1ecbch trong {min:02d}:{sec:02d}',
        'error_status': '\u274c L\u1ed7i: {msg}',
        'error_log': '\u274c L\u1ed7i: {msg}',
        'cancelled_status': '\u0110\u00e3 h\u1ee7y',
        'cancelled_log': '\u2715 \u0110\u00e3 h\u1ee7y d\u1ecbch.',
        'starting_fmt': '\u0110ang kh\u1edfi ch\u1ea1y ({engine})...',
        'engine_log': 'C\u00f4ng c\u1ee5: {engine}',
        'translating_log_fmt': '\u0110ang d\u1ecbch: {name}',
        'format_log_fmt': '  {ext} | {src} \u2192 {dest}',
        'output_log_fmt': '  \u0110\u1ea7u ra: {name}',
        'selected_log': '\u0110\u00e3 ch\u1ecdn: {name}',
        'cannot_read_log': 'Kh\u00f4ng th\u1ec3 \u0111\u1ecdc t\u1ec7p: {name}',
        'quit_title': 'Tho\u00e1t?',
        'quit_msg': '\u0110ang d\u1ecbch. H\u1ee7y b\u1ecf?',
        'missing_dep_title': 'Thi\u1ebfu Th\u01b0 Vi\u1ec7n',
        'missing_dep_msg': 'C\u00e0i \u0111\u1eb7t th\u01b0 vi\u1ec7n openai:\n\npip install openai',
        'missing_key_title': 'Thi\u1ebfu Kh\u00f3a API',
        'missing_key_msg': 'Nh\u1eadp kh\u00f3a API \u0111\u1ec3 d\u00f9ng ch\u1ebf \u0111\u1ed9 LLM.',
        'no_file_title': 'Ch\u01b0a ch\u1ecdn t\u1ec7p',
        'no_file_msg': 'Vui l\u00f2ng ch\u1ecdn m\u1ed9t t\u1ec7p ph\u1ee5 \u0111\u1ec1.',
        'no_style_title': 'Ch\u01b0a ch\u1ecdn ki\u1ec3u',
        'no_style_msg': 'Ch\u1ecdn \u00edt nh\u1ea5t m\u1ed9t ki\u1ec3u \u0111\u1ec3 d\u1ecbch.',
        'overwrite_title': 'Ghi \u0111\u00e8?',
        'overwrite_msg': "'{name}' \u0111\u00e3 t\u1ed3n t\u1ea1i. Ghi \u0111\u00e8?",
        'llm_enter_key': '\u274c Nh\u1eadp kh\u00f3a API',
        'llm_enter_model': '\u274c Nh\u1eadp t\u00ean m\u00f4 h\u00ecnh',
        'llm_testing': '\u23f3 \u0110ang ki\u1ec3m tra...',
        'llm_connected': '\u2705 \u0110\u00e3 k\u1ebft n\u1ed1i! Ph\u1ea3n h\u1ed3i: {response}',
        'llm_invalid_key': '\u274c Kh\u00f3a API kh\u00f4ng h\u1ee3p l\u1ec7',
        'llm_model_not_found': "\u274c Kh\u00f4ng t\u00ecm th\u1ea5y m\u00f4 h\u00ecnh '{model}'",
        'llm_error': '\u274c {msg}',
        'llm_deepseek_applied': '\u2705 \u0110\u00e3 \u00e1p d\u1ee5ng DeepSeek. Nh\u1eadp kh\u00f3a API v\u00e0 b\u1ea5m Ki\u1ec3m tra.',
        'llm_warning': '\u26a0\ufe0f pip install openai',
        'extract_btn': '\U0001f3ac Tr\u00edch xu\u1ea5t',
        'video_selected_log': '\U0001f3ac \u0110\u00e3 ch\u1ecdn video. Ch\u1ecdn lu\u1ed3ng ph\u1ee5 \u0111\u1ec1 \u0111\u1ec3 tr\u00edch xu\u1ea5t.',
        'select_track_title': 'Ch\u1ecdn Lu\u1ed3ng Ph\u1ee5 \u0110\u1ec1',
        'select_track_header': 'Lu\u1ed3ng ph\u1ee5 \u0111\u1ec1 trong:\n{name}',
        'select_track_ok': 'Ch\u1ecdn',
        'select_track_cancel': 'H\u1ee7y',
        'select_track_error': 'Kh\u00f4ng t\u00ecm th\u1ea5y lu\u1ed3ng ph\u1ee5 \u0111\u1ec1 n\u00e0o trong file video!',
        'select_track_error_log': 'Kh\u00f4ng t\u00ecm th\u1ea5y lu\u1ed3ng ph\u1ee5 \u0111\u1ec1.',
        'mux_checkbox': '\U0001f3ac Gh\u00e9p ph\u1ee5 \u0111\u1ec1 v\u00e0o video sau khi d\u1ecbch',
        'mux_muxing': '\U0001f3ac \u0110ang gh\u00e9p ph\u1ee5 \u0111\u1ec1 v\u00e0o video...',
        'mux_success': '\u2705 \u0110\u00e3 gh\u00e9p: {name}',
        'mux_fail': '\u274c Gh\u00e9p th\u1ea5t b\u1ea1i!',
        'mux_no_video': 'Kh\u00f4ng t\u00ecm th\u1ea5y file video n\u00e0o!',
        'mux_no_video_log': 'Kh\u00f4ng t\u00ecm th\u1ea5y file video n\u00e0o \u0111\u1ec3 gh\u00e9p.',
        'mux_choose_title': 'Ch\u1ecdn Video \u0110\u1ec3 Gh\u00e9p',
        'mux_choose_header': 'Ch\u1ecdn file video \u0111\u1ec3 gh\u00e9p ph\u1ee5 \u0111\u1ec1 \u0111\u00e3 d\u1ecbch v\u00e0o:',
        'mux_ok': 'Gh\u00e9p',
        'mux_cancel': 'H\u1ee7y',
        'mux_cancelled_log': '\u0110\u00e3 h\u1ee7y gh\u00e9p.',
        'simple_mux_title': '\U0001f3ac Gh\u00e9p H\u00e0ng Lo\u1ea1t',
        'batch_translate_title': '\U0001f3ac D\u1ecbch H\u00e0ng Lo\u1ea1t',
        'batch_translate_desc': 'D\u1ecbch & gh\xe9p t\u1ea5t c\u1ea3 video trong th\u01b0 m\u1ee5c',
        'batch_translate_btn': '\u25b6 B\u1eaft \u0111\u1ea7u',
        'help_text': (
            "B\u01b0\u1edbc 1 \u2192 \U0001f4c2 Ch\u1ecdn th\u01b0 m\u1ee5c + Qu\u00e9t\n"
            "B\u01b0\u1edbc 2 \u2192 \U0001f3ac Ch\u1ecdn file / Tr\u00edch xu\u1ea5t t\u1eeb video\n"
            "B\u01b0\u1edbc 3 \u2192 \U0001f310 Ch\u1ecdn ng\u00f4n ng\u1eef + Start"
        ),
    },
    'zh': {
        'app_title': '\U0001f3ac \u5b57\u5e55\u7ffb\u8bd1\u5668',
        'font_label': '\u5b57\u4f53:',
        'lang_ui': '\u754c\u9762\u8bed\u8a00:',
        'file_section': '\U0001f4c1 \u6587\u4ef6\u9009\u62e9',
        'dir_label': '\u76ee\u5f55:',
        'browse': '\u6d4f\u89c8',
        'scan': '\u626b\u63cf',
        'no_files': '(\u672a\u627e\u5230\u5b57\u5e55\u6587\u4ef6)',
        'no_files_log': '\u672a\u627e\u5230 .ass \u6216 .srt \u6587\u4ef6\u3002',
        'found_files': '\u627e\u5230 {count} \u4e2a\u5b57\u5e55\u6587\u4ef6\u3002',
        'lang_section': '\U0001f310 \u8bed\u8a00',
        'source': '\u6e90\u8bed\u8a00:',
        'target': '\u76ee\u6807\u8bed\u8a00:',
        'swap': '\u21c4',
        'same_lang_msg': '\u6e90\u8bed\u8a00\u548c\u76ee\u6807\u8bed\u8a00\u76f8\u540c ({lang})\u3002\u8bf7\u9009\u62e9\u4e0d\u540c\u7684\u8bed\u8a00\u3002',
        'output_section': '\U0001f4be \u8f93\u51fa',
        'engine_section': '\u2699\ufe0f \u7ffb\u8bd1\u5f15\u64ce',
        'engine_label': '\u5f15\u64ce:',
        'google_engine': '\u8c37\u6b4c\u7ffb\u8bd1',
        'llm_engine': 'LLM (AI)',
        'api_key': 'API \u5bc6\u94a5:',
        'base_url': '\u57fa\u7840 URL:',
        'model': '\u6a21\u578b:',
        'test': '\u6d4b\u8bd5',
        'deepseek': 'DeepSeek',
        'sys_prompt': '\u7cfb\u7edf\u63d0\u793a:',
        'style_section': '\U0001f3a8 ASS \u6837\u5f0f\u9009\u62e9',
        'select_styles': '\u9009\u62e9\u8981\u7ffb\u8bd1\u7684\u6837\u5f0f:',
        'style_item': '{style}  (\U0001f4dd {text} | \U0001f3a8 {drawing} | {total} {count})',
        'total_label': '\u603b\u8ba1:',
        'start': '\U0001f680 \u5f00\u59cb\u7ffb\u8bd1',
        'cancel': '\u2715 \u53d6\u6d88',
        'progress_section': '\u8fdb\u5ea6',
        'ready': '\u51c6\u5907\u5c31\u7eea',
        'log_section': '\u65e5\u5fd7',
        'mux_section': '\U0001f3ac \u6df7\u6d41',
        'planned': '\u8ba1\u5212\u7ffb\u8bd1 {total} \u884c',
        'translating_log': '\u6b63\u5728\u7ffb\u8bd1 {total} \u884c...',
        'progress_fmt': '{current}/{total} | ETA: {eta} | {speed:.1f} \u884c/\u79d2',
        'complete_status': '\u2705 \u5b8c\u6210! {total} \u884c\u7528\u65f6 {min:02d}:{sec:02d}',
        'done_log': '\u2705 \u5df2\u5b8c\u6210! {total} \u884c\u5df2\u7ffb\u8bd1\uff0c\u7528\u65f6 {min:02d}:{sec:02d}',
        'error_status': '\u274c \u9519\u8bef: {msg}',
        'error_log': '\u274c \u9519\u8bef: {msg}',
        'cancelled_status': '\u5df2\u53d6\u6d88',
        'cancelled_log': '\u2715 \u7ffb\u8bd1\u5df2\u53d6\u6d88\u3002',
        'starting_fmt': '\u6b63\u5728\u542f\u52a8 ({engine})...',
        'engine_log': '\u5f15\u64ce: {engine}',
        'translating_log_fmt': '\u6b63\u5728\u7ffb\u8bd1: {name}',
        'format_log_fmt': '  {ext} | {src} \u2192 {dest}',
        'output_log_fmt': '  \u8f93\u51fa: {name}',
        'selected_log': '\u5df2\u9009\u62e9: {name}',
        'cannot_read_log': '\u65e0\u6cd5\u8bfb\u53d6\u6587\u4ef6: {name}',
        'quit_title': '\u9000\u51fa?',
        'quit_msg': '\u7ffb\u8bd1\u8fdb\u884c\u4e2d\u3002\u53d6\u6d88?',
        'missing_dep_title': '\u7f3a\u5c11\u4f9d\u8d56',
        'missing_dep_msg': '\u8bf7\u5b89\u88c5 openai \u5e93:\n\npip install openai',
        'missing_key_title': '\u7f3a\u5c11 API \u5bc6\u94a5',
        'missing_key_msg': '\u8bf7\u8f93\u5165 API \u5bc6\u94a5\u4ee5\u4f7f\u7528 LLM \u6a21\u5f0f\u3002',
        'no_file_title': '\u672a\u9009\u6587\u4ef6',
        'no_file_msg': '\u8bf7\u9009\u62e9\u4e00\u4e2a\u5b57\u5e55\u6587\u4ef6\u3002',
        'no_style_title': '\u672a\u9009\u6837\u5f0f',
        'no_style_msg': '\u8bf7\u81f3\u5c11\u9009\u62e9\u4e00\u4e2a\u6837\u5f0f\u8fdb\u884c\u7ffb\u8bd1\u3002',
        'overwrite_title': '\u8986\u76d6?',
        'overwrite_msg': "'{name}' \u5df2\u5b58\u5728\u3002\u8986\u76d6?",
        'llm_enter_key': '\u274c \u8bf7\u8f93\u5165 API \u5bc6\u94a5',
        'llm_enter_model': '\u274c \u8bf7\u8f93\u5165\u6a21\u578b\u540d\u79f0',
        'llm_testing': '\u23f3 \u6b63\u5728\u6d4b\u8bd5...',
        'llm_connected': '\u2705 \u8fde\u63a5\u6210\u529f! \u54cd\u5e94: {response}',
        'llm_invalid_key': '\u274c API \u5bc6\u94a5\u65e0\u6548',
        'llm_model_not_found': "\u274c \u672a\u627e\u5230\u6a21\u578b '{model}'",
        'llm_error': '\u274c {msg}',
        'llm_deepseek_applied': '\u2705 \u5df2\u5e94\u7528 DeepSeek \u9884\u8bbe\u3002\u8bf7\u8f93\u5165 API \u5bc6\u94a5\u5e76\u70b9\u51fb\u6d4b\u8bd5\u3002',
        'llm_warning': '\u26a0\ufe0f pip install openai',
        'extract_btn': '\U0001f3ac \u63d0\u53d6',
        'video_selected_log': '\U0001f3ac \u5df2\u9009\u62e9\u89c6\u9891\u3002\u8bf7\u9009\u62e9\u5b57\u5e55\u6d41\u8fdb\u884c\u63d0\u53d6\u3002',
        'select_track_title': '\u9009\u62e9\u5b57\u5e55\u6d41',
        'select_track_header': '\u89c6\u9891\u4e2d\u7684\u5b57\u5e55\u6d41:\n{name}',
        'select_track_ok': '\u786e\u5b9a',
        'select_track_cancel': '\u53d6\u6d88',
        'select_track_error': '\u672a\u5728\u89c6\u9891\u6587\u4ef6\u4e2d\u627e\u5230\u5b57\u5e55\u6d41!',
        'select_track_error_log': '\u672a\u627e\u5230\u5b57\u5e55\u6d41\u3002',
        'mux_checkbox': '\U0001f3ac \u7ffb\u8bd1\u540e\u5c06\u5b57\u5e55\u6df7\u6d41\u5230\u89c6\u9891',
        'mux_muxing': '\U0001f3ac \u6b63\u5728\u5c06\u5b57\u5e55\u6df7\u6d41\u5230\u89c6\u9891...',
        'mux_success': '\u2705 \u5df2\u6df7\u6d41: {name}',
        'mux_fail': '\u274c \u6df7\u6d41\u5931\u8d25!',
        'mux_no_video': '\u672a\u627e\u5230\u89c6\u9891\u6587\u4ef6!',
        'mux_no_video_log': '\u672a\u627e\u5230\u89c6\u9891\u6587\u4ef6\u7528\u4e8e\u6df7\u6d41\u3002',
        'mux_choose_title': '\u9009\u62e9\u89c6\u9891\u8fdb\u884c\u6df7\u6d41',
        'mux_choose_header': '\u9009\u62e9\u8981\u6df7\u6d41\u5b57\u5e55\u7684\u89c6\u9891\u6587\u4ef6:',
        'mux_ok': '\u6df7\u6d41',
        'mux_cancel': '\u53d6\u6d88',
        'mux_cancelled_log': '\u5df2\u53d6\u6d88\u6df7\u6d41\u3002',
        'simple_mux_title': '\U0001f3ac \u6279\u91cf\u6df7\u6d41',
        'batch_translate_title': '\U0001f3ac \u6279\u91cf\u7ffb\u8bd1',
        'batch_translate_desc': '\u7ffb\u8bd1\u5e76\u6df7\u6d41\u6587\u4ef6\u5939\u4e2d\u7684\u6240\u6709\u89c6\u9891',
        'batch_translate_btn': '\u25b6 \u5f00\u59cb',
        'help_text': (
            "Step 1 \u2192 \U0001f4c2 \u9009\u6587\u4ef6\u5939 + \u626b\u63cf\n"
            "Step 2 \u2192 \U0001f3ac \u9009\u6587\u4ef6 / \u63d0\u53d6\u5b57\u5e55\n"
            "Step 3 \u2192 \U0001f310 \u9009\u8bed\u8a00 + Start"
        ),
    },
    'ja': {
        'app_title': '\U0001f3ac \u5b57\u5e55\u7ffb\u8a33\u30c4\u30fc\u30eb',
        'font_label': '\u30d5\u30a9\u30f3\u30c8:',
        'lang_ui': '\u8a00\u8a9e:',
        'file_section': '\U0001f4c1 \u30d5\u30a1\u30a4\u30eb\u9078\u629e',
        'dir_label': '\u30c7\u30a3\u30ec\u30af\u30c8\u30ea:',
        'browse': '\u53c2\u7167',
        'scan': '\u30b9\u30ad\u30e3\u30f3',
        'no_files': '(\u5b57\u5e55\u30d5\u30a1\u30a4\u30eb\u304c\u898b\u3064\u304b\u308a\u307e\u305b\u3093)',
        'no_files_log': '.ass \u307e\u305f\u306f .srt \u30d5\u30a1\u30a4\u30eb\u304c\u898b\u3064\u304b\u308a\u307e\u305b\u3093\u3002',
        'found_files': '{count} \u3064\u306e\u5b57\u5e55\u30d5\u30a1\u30a4\u30eb\u304c\u898b\u3064\u304b\u308a\u307e\u3057\u305f\u3002',
        'lang_section': '\U0001f310 \u8a00\u8a9e',
        'source': '\u5143\u8a00\u8a9e:',
        'target': '\u76ee\u7684\u8a00\u8a9e:',
        'swap': '\u21c4',
        'same_lang_msg': '\u5143\u8a00\u8a9e\u3068\u76ee\u7684\u8a00\u8a9e\u304c\u540c\u3058\u3067\u3059 ({lang})\u3002\u5225\u306e\u8a00\u8a9e\u3092\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044\u3002',
        'output_section': '\U0001f4be \u51fa\u529b',
        'engine_section': '\u2699\ufe0f \u7ffb\u8a33\u30a8\u30f3\u30b8\u30f3',
        'engine_label': '\u30a8\u30f3\u30b8\u30f3:',
        'google_engine': 'Google \u7ffb\u8a33',
        'llm_engine': 'LLM (AI)',
        'api_key': 'API \u30ad\u30fc:',
        'base_url': '\u30d9\u30fc\u30b9 URL:',
        'model': '\u30e2\u30c7\u30eb:',
        'test': '\u30c6\u30b9\u30c8',
        'deepseek': 'DeepSeek',
        'sys_prompt': '\u30b7\u30b9\u30c6\u30e0\u30d7\u30ed\u30f3\u30d7\u30c8:',
        'style_section': '\U0001f3a8 ASS \u30b9\u30bf\u30a4\u30eb\u9078\u629e',
        'select_styles': '\u7ffb\u8a33\u3059\u308b\u30b9\u30bf\u30a4\u30eb\u3092\u9078\u629e:',
        'style_item': '{style}  (\U0001f4dd {text} | \U0001f3a8 {drawing} | {total} {count})',
        'total_label': '\u5408\u8a08:',
        'start': '\U0001f680 \u7ffb\u8a33\u958b\u59cb',
        'cancel': '\u2715 \u30ad\u30e3\u30f3\u30bb\u30eb',
        'progress_section': '\u9032\u884c',
        'ready': '\u6e96\u5099\u5b8c\u4e86',
        'log_section': '\u30ed\u30b0',
        'mux_section': '\U0001f3ac \u7d50\u5408',
        'planned': '\u8a08\u753b: {total} \u884c\u3092\u7ffb\u8a33',
        'translating_log': '{total} \u884c\u3092\u7ffb\u8a33\u4e2d...',
        'progress_fmt': '{current}/{total} | ETA: {eta} | {speed:.1f} \u884c/\u79d2',
        'complete_status': '\u2705 \u5b8c\u4e86! {total} \u884c\u3092{min:02d}:{sec:02d}\u3067\u7ffb\u8a33',
        'done_log': '\u2705 \u5b8c\u4e86! {total} \u884c\u3092{min:02d}:{sec:02d}\u3067\u7ffb\u8a33\u3057\u307e\u3057\u305f',
        'error_status': '\u274c \u30a8\u30e9\u30fc: {msg}',
        'error_log': '\u274c \u30a8\u30e9\u30fc: {msg}',
        'cancelled_status': '\u30ad\u30e3\u30f3\u30bb\u30eb\u3057\u307e\u3057\u305f',
        'cancelled_log': '\u2715 \u7ffb\u8a33\u3092\u30ad\u30e3\u30f3\u30bb\u30eb\u3057\u307e\u3057\u305f\u3002',
        'starting_fmt': '\u8d77\u52d5\u4e2d ({engine})...',
        'engine_log': '\u30a8\u30f3\u30b8\u30f3: {engine}',
        'translating_log_fmt': '\u7ffb\u8a33\u4e2d: {name}',
        'format_log_fmt': '  {ext} | {src} \u2192 {dest}',
        'output_log_fmt': '  \u51fa\u529b: {name}',
        'selected_log': '\u9078\u629e\u6e08\u307f: {name}',
        'cannot_read_log': '\u30d5\u30a1\u30a4\u30eb\u3092\u8aad\u3081\u307e\u305b\u3093: {name}',
        'quit_title': '\u7d42\u4e86\u3057\u307e\u3059\u304b?',
        'quit_msg': '\u7ffb\u8a33\u4e2d\u3067\u3059\u3002\u30ad\u30e3\u30f3\u30bb\u30eb\u3057\u307e\u3059\u304b?',
        'missing_dep_title': '\u4f9d\u5b58\u95a2\u4fc2\u304c\u3042\u308a\u307e\u305b\u3093',
        'missing_dep_msg': 'openai \u30e9\u30a4\u30d6\u30e9\u30ea\u3092\u30a4\u30f3\u30b9\u30c8\u30fc\u30eb\u3057\u3066\u304f\u3060\u3055\u3044:\n\npip install openai',
        'missing_key_title': 'API \u30ad\u30fc\u304c\u3042\u308a\u307e\u305b\u3093',
        'missing_key_msg': 'LLM \u30e2\u30fc\u30c9\u3092\u4f7f\u7528\u3059\u308b\u306b\u306f API \u30ad\u30fc\u3092\u5165\u529b\u3057\u3066\u304f\u3060\u3055\u3044\u3002',
        'no_file_title': '\u30d5\u30a1\u30a4\u30eb\u304c\u3042\u308a\u307e\u305b\u3093',
        'no_file_msg': '\u5b57\u5e55\u30d5\u30a1\u30a4\u30eb\u3092\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044\u3002',
        'no_style_title': '\u30b9\u30bf\u30a4\u30eb\u304c\u3042\u308a\u307e\u305b\u3093',
        'no_style_msg': '\u5c11\u306a\u304f\u3068\u3082 1 \u3064\u306e\u30b9\u30bf\u30a4\u30eb\u3092\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044\u3002',
        'overwrite_title': '\u4e0a\u66f8\u304d\u3057\u307e\u3059\u304b?',
        'overwrite_msg': "'{name}' \u306f\u5b58\u5728\u3057\u307e\u3059\u3002\u4e0a\u66f8\u304d\u3057\u307e\u3059\u304b?",
        'llm_enter_key': '\u274c API \u30ad\u30fc\u3092\u5165\u529b\u3057\u3066\u304f\u3060\u3055\u3044',
        'llm_enter_model': '\u274c \u30e2\u30c7\u30eb\u540d\u3092\u5165\u529b\u3057\u3066\u304f\u3060\u3055\u3044',
        'llm_testing': '\u23f3 \u30c6\u30b9\u30c8\u4e2d...',
        'llm_connected': '\u2705 \u63a5\u7d9a\u6210\u529f! \u5fdc\u7b54: {response}',
        'llm_invalid_key': '\u274c API \u30ad\u30fc\u304c\u7121\u52b9\u3067\u3059',
        'llm_model_not_found': "\u274c \u30e2\u30c7\u30eb '{model}' \u304c\u898b\u3064\u304b\u308a\u307e\u305b\u3093",
        'llm_error': '\u274c {msg}',
        'llm_deepseek_applied': '\u2705 DeepSeek \u30d7\u30ea\u30bb\u30c3\u30c8\u3092\u9069\u7528\u3057\u307e\u3057\u305f\u3002API \u30ad\u30fc\u3092\u5165\u529b\u3057\u3066\u30c6\u30b9\u30c8\u3092\u30af\u30ea\u30c3\u30af\u3057\u3066\u304f\u3060\u3055\u3044\u3002',
        'llm_warning': '\u26a0\ufe0f pip install openai',
        'extract_btn': '\U0001f3ac \u63bd\u51fa\u3059',
        'video_selected_log': '\U0001f3ac \u52d5\u753b\u3092\u9078\u629e\u3057\u307e\u3057\u305f\u3002\u5b57\u5e55\u30c8\u30e9\u30c3\u30af\u3092\u9078\u629e\u3057\u3066\u63bd\u51fa\u3057\u3066\u304f\u3060\u3055\u3044\u3002',
        'select_track_title': '\u5b57\u5e55\u30c8\u30e9\u30c3\u30af\u3092\u9078\u629e',
        'select_track_header': '\u52d5\u753b\u306e\u5b57\u5e55\u30b9\u30c8\u30ea\u30fc\u30e0:\n{name}',
        'select_track_ok': 'OK',
        'select_track_cancel': '\u30ad\u30e3\u30f3\u30bb\u30eb',
        'select_track_error': '\u3053\u306e\u52d5\u753b\u30d5\u30a1\u30a4\u30eb\u306b\u5b57\u5e55\u30b9\u30c8\u30ea\u30fc\u30e0\u304c\u3042\u308a\u307e\u305b\u3093!',
        'select_track_error_log': '\u5b57\u5e55\u30b9\u30c8\u30ea\u30fc\u30e0\u304c\u898b\u3064\u304b\u308a\u307e\u305b\u3093\u3002',
        'mux_checkbox': '\U0001f3ac \u7ffb\u8a33\u5f8c\u306b\u5b57\u5e55\u3092\u52d5\u753b\u306b\u7d50\u5408',
        'mux_muxing': '\U0001f3ac \u5b57\u5e55\u3092\u52d5\u753b\u306b\u7d50\u5408\u4e2d...',
        'mux_success': '\u2705 \u7d50\u5408\u5b8c\u4e86: {name}',
        'mux_fail': '\u274c \u7d50\u5408\u5931\u6557!',
        'mux_no_video': '\u52d5\u753b\u30d5\u30a1\u30a4\u30eb\u304c\u898b\u3064\u304b\u308a\u307e\u305b\u3093!',
        'mux_no_video_log': '\u7d50\u5408\u7528\u306e\u52d5\u753b\u30d5\u30a1\u30a4\u30eb\u304c\u898b\u3064\u304b\u308a\u307e\u305b\u3093\u3002',
        'mux_choose_title': '\u7d50\u5408\u3059\u308b\u52d5\u753b\u3092\u9078\u629e',
        'mux_choose_header': '\u7ffb\u8a33\u6e08\u307f\u5b57\u5e55\u3092\u7d50\u5408\u3059\u308b\u52d5\u753b\u30d5\u30a1\u30a4\u30eb\u3092\u9078\u629e:',
        'mux_ok': '\u7d50\u5408',
        'mux_cancel': '\u30ad\u30e3\u30f3\u30bb\u30eb',
        'mux_cancelled_log': '\u7d50\u5408\u3092\u30ad\u30e3\u30f3\u30bb\u30eb\u3057\u307e\u3057\u305f\u3002',
        'simple_mux_title': '\U0001f3ac \u30d0\u30c3\u30c1\u7d50\u5408',
        'batch_translate_title': '\U0001f3ac \u30d0\u30c3\u30c1\u7ffb\u8a33',
        'batch_translate_desc': '\u30d5\u30a9\u30eb\u30c0\u5185\u306e\u3059\u3079\u3066\u306e\u52d5\u753b\u3092\u7ffb\u8a33\u30fb\u7d50\u5408',
        'batch_translate_btn': '\u25b6 \u958b\u59cb',
        'help_text': (
            "Step 1 \u2192 \U0001f4c2 \u30d5\u30a9\u30eb\u30c0\u9078\u629e + \u30b9\u30ad\u30e3\u30f3\n"
            "Step 2 \u2192 \U0001f3ac \u30d5\u30a1\u30a4\u30eb\u9078\u629e / \u63bd\u51fa\n"
            "Step 3 \u2192 \U0001f310 \u8a00\u8a9e\u9078\u629e + Start"
        ),
    },
    'ko': {
        'app_title': '\U0001f3ac \uc790\ub9c9 \ubc88\uc5ed\uae30',
        'font_label': '\uae00\uaf34:',
        'lang_ui': '\uc5b8\uc5b4:',
        'file_section': '\U0001f4c1 \ud30c\uc77c \uc120\ud0dd',
        'dir_label': '\ub514\ub809\ud1a0\ub9ac:',
        'browse': '\ucc3e\uc544\ubcf4\uae30',
        'scan': '\uac80\uc0c9',
        'no_files': '(\uc790\ub9c5 \ud30c\uc77c\uc774 \uc5c6\uc2b5\ub2c8\ub2e4)',
        'no_files_log': '.ass \ub610\ub294 .srt \ud30c\uc77c\uc774 \uc5c6\uc2b5\ub2c8\ub2e4.',
        'found_files': '{count}\uac1c\uc758 \uc790\ub9c5 \ud30c\uc77c\uc744 \ucc3e\uc558\uc2b5\ub2c8\ub2e4.',
        'lang_section': '\U0001f310 \uc5b8\uc5b4',
        'source': '\uc6d0\uc5b8:',
        'target': '\ubaa9\uc801\uc5b8:',
        'swap': '\u21c4',
        'same_lang_msg': '\uc18c\uc2a4\uc640 \ub300\uc0c1 \uc5b8\uc5b4\uac00 \ub3d9\uc77c\ud569\ub2c8\ub2e4 ({lang}). \ub2e4\ub978 \uc5b8\uc5b4\ub97c \uc120\ud0dd\ud558\uc138\uc694.',
        'output_section': '\U0001f4be \ucd9c\ub825',
        'engine_section': '\u2699\ufe0f \ubc88\uc5ed \uc5d4\uc9c4',
        'engine_label': '\uc5d4\uc9c4:',
        'google_engine': 'Google \ubc88\uc5ed',
        'llm_engine': 'LLM (AI)',
        'api_key': 'API \ud0a4:',
        'base_url': '\uae30\ubcf8 URL:',
        'model': '\ubaa8\ub378:',
        'test': '\ud14c\uc2a4\ud2b8',
        'deepseek': 'DeepSeek',
        'sys_prompt': '\uc2dc\uc2a4\ud15c \ud504\ub86c\ud504\ud2b8:',
        'style_section': '\U0001f3a8 ASS \uc2a4\ud0c0\uc77c \uc120\ud0dd',
        'select_styles': '\ubc88\uc5ed\ud560 \uc2a4\ud0c0\uc77c \uc120\ud0dd:',
        'style_item': '{style}  (\U0001f4dd {text} | \U0001f3a8 {drawing} | {total} {count})',
        'total_label': '\ud569\uacc4:',
        'start': '\U0001f680 \ubc88\uc5ed \uc2dc\uc791',
        'cancel': '\u2715 \ucde8\uc18c',
        'progress_section': '\uc9c4\ud589',
        'ready': '\uc900\ube44 \uc644\ub8cc',
        'log_section': '\ub85c\uadf8',
        'mux_section': '\U0001f3ac \ud569\uc131',
        'planned': '\uacc4\ud68d: {total}\uac1c \ub77c\uc778 \ubc88\uc5ed',
        'translating_log': '{total}\uac1c \ub77c\uc778 \ubc88\uc5ed \uc911...',
        'progress_fmt': '{current}/{total} | ETA: {eta} | {speed:.1f} \ub77c\uc778/\ucd08',
        'complete_status': '\u2705 \uc644\ub8cc! {total}\uac1c \ub77c\uc778, {min:02d}:{sec:02d} \uc18c\uc694',
        'done_log': '\u2705 \uc644\ub8cc! {total}\uac1c \ub77c\uc778\uc774 {min:02d}:{sec:02d}\ub9cc\uc5d0 \ubc88\uc5ed\ub418\uc5c8\uc2b5\ub2c8\ub2e4.',
        'error_status': '\u274c \uc624\ub958: {msg}',
        'error_log': '\u274c \uc624\ub958: {msg}',
        'cancelled_status': '\ucde8\uc18c\ub428',
        'cancelled_log': '\u2715 \ubc88\uc5ed\uc774 \ucde8\uc18c\ub418\uc5c8\uc2b5\ub2c8\ub2e4.',
        'starting_fmt': '\uc2dc\uc791\ud558\ub294 \uc911 ({engine})...',
        'engine_log': '\uc5d4\uc9c4: {engine}',
        'translating_log_fmt': '\ubc88\uc5ed \uc911: {name}',
        'format_log_fmt': '  {ext} | {src} \u2192 {dest}',
        'output_log_fmt': '  \ucd9c\ub825: {name}',
        'selected_log': '\uc120\ud0dd\ub428: {name}',
        'cannot_read_log': '\ud30c\uc77c\uc744 \uc77d\uc744 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4: {name}',
        'quit_title': '\uc885\ub8cc?',
        'quit_msg': '\ubc88\uc5ed \uc9c4\ud589 \uc911\uc785\ub2c8\ub2e4. \ucde8\uc18c\ud558\uc2dc\uaca0\uc2b5\ub2c8\uae4c?',
        'missing_dep_title': '\uc758\uc874\uc131 \ubd80\uc871',
        'missing_dep_msg': 'openai \ub77c\uc774\ube0c\ub7ec\ub9ac \uc124\uce58:\n\npip install openai',
        'missing_key_title': 'API \ud0a4 \ub204\ub77d',
        'missing_key_msg': 'LLM \ubaa8\ub4dc\ub97c \uc0ac\uc6a9\ud558\ub824\uba74 API \ud0a4\ub97c \uc785\ub825\ud558\uc138\uc694.',
        'no_file_title': '\ud30c\uc77c \uc5c6\uc74c',
        'no_file_msg': '\uc790\ub9c5 \ud30c\uc77c\uc744 \uc120\ud0dd\ud574 \uc8fc\uc138\uc694.',
        'no_style_title': '\uc2a4\ud0c0\uc77c \uc5c6\uc74c',
        'no_style_msg': '\uc801\uc5b4\ub3c4 \ud558\ub098\uc758 \uc2a4\ud0c0\uc77c\uc744 \uc120\ud0dd\ud574 \uc8fc\uc138\uc694.',
        'overwrite_title': '\uacb9\uccd0 \uc4f0\uae30?',
        'overwrite_msg': "'{name}'\uc774(\uac00) \uc874\uc7ac\ud569\ub2c8\ub2e4. \uacb9\uccd0 \uc4f0\uc2dc\uaca0\uc2b5\ub2c8\uae4c?",
        'llm_enter_key': '\u274c API \ud0a4\ub97c \uc785\ub825\ud558\uc138\uc694',
        'llm_enter_model': '\u274c \ubaa8\ub378 \uba85\uce6d\uc744 \uc785\ub825\ud558\uc138\uc694',
        'llm_testing': '\u23f3 \ud14c\uc2a4\ud2b8 \uc911...',
        'llm_connected': '\u2705 \uc5f0\uacb0 \uc131\uacf5! \uc751\ub2f5: {response}',
        'llm_invalid_key': '\u274c API \ud0a4\uac00 \uc798\ubabb\ub418\uc5c8\uc2b5\ub2c8\ub2e4',
        'llm_model_not_found': "\u274c \ubaa8\ub378 '{model}'\uc744(\ub97c) \ucc3e\uc744 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4",
        'llm_error': '\u274c {msg}',
        'llm_deepseek_applied': '\u2705 DeepSeek \ud504\ub9ac\uc14b\uc774 \uc801\uc6a9\ub418\uc5c8\uc2b5\ub2c8\ub2e4. API \ud0a4\ub97c \uc785\ub825\ud558\uace0 \ud14c\uc2a4\ud2b8\ub97c \ub204\ub974\uc138\uc694.',
        'llm_warning': '\u26a0\ufe0f pip install openai',
        'extract_btn': '\U0001f3ac \ucd94\ucd9c',
        'video_selected_log': '\U0001f3ac \ube44\ub514\uc624\uac00 \uc120\ud0dd\ub418\uc5c8\uc2b5\ub2c8\ub2e4. \uc790\ub9c9 \ud2b8\ub799\uc744 \uc120\ud0dd\ud574\uc8fc\uc138\uc694.',
        'select_track_title': '\uc790\ub9c9 \ud2b8\ub799 \uc120\ud0dd',
        'select_track_header': '\ube44\ub514\uc624\uc758 \uc790\ub9c9 \uc2a4\ud2b8\ub9bc:\n{name}',
        'select_track_ok': '\ud655\uc778',
        'select_track_cancel': '\ucde8\uc18c',
        'select_track_error': '\uc774 \ube44\ub514\uc624 \ud30c\uc77c\uc5d0 \uc790\ub9c9 \uc2a4\ud2b8\ub9bc\uc774 \uc5c6\uc2b5\ub2c8\ub2e4!',
        'select_track_error_log': '\uc790\ub9c9 \uc2a4\ud2b8\ub9bc\uc774 \uc5c6\uc2b5\ub2c8\ub2e4.',
        'mux_checkbox': '\U0001f3ac \ubc88\uc5ed \ud6c4 \ube44\ub514\uc624\uc5d0 \uc790\ub9c5 \ud569\uc131',
        'mux_muxing': '\U0001f3ac \ube44\ub514\uc624\uc5d0 \uc790\ub9c5 \ud569\uc131 \uc911...',
        'mux_success': '\u2705 \ud569\uc131 \uc644\ub8cc: {name}',
        'mux_fail': '\u274c \ud569\uc131 \uc2e4\ud328!',
        'mux_no_video': '\ube44\ub514\uc624 \ud30c\uc77c\uc744 \ucc3e\uc744 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4!',
        'mux_no_video_log': '\ud569\uc131\uc744 \uc704\ud55c \ube44\ub514\uc624 \ud30c\uc77c\uc774 \uc5c6\uc2b5\ub2c8\ub2e4.',
        'mux_choose_title': '\ud569\uc131\ud560 \ube44\ub514\uc624 \uc120\ud0dd',
        'mux_choose_header': '\ubc88\uc5ed\ub41c \uc790\ub9c5\uc744 \ud569\uc131\ud560 \ube44\ub514\uc624 \ud30c\uc77c\uc744 \uc120\ud0dd\ud558\uc138\uc694:',
        'mux_ok': '\ud569\uc131',
        'mux_cancel': '\ucde8\uc18c',
        'mux_cancelled_log': '\ud569\uc131\uc774 \ucde8\uc18c\ub418\uc5c8\uc2b5\ub2c8\ub2e4.',
        'simple_mux_title': '\U0001f3ac \uc77c\uad04 \ud569\uc131',
        'batch_translate_title': '\U0001f3ac \uc77c\uad04 \ubc88\uc5ed',
        'batch_translate_desc': '\ud3f4\ub354\uc758 \ubaa8\ub4e0 \ub3d9\uc601\uc0c1 \ubc88\uc5ed \ubc0f \ud569\uc131',
        'batch_translate_btn': '\u25b6 \uc2dc\uc791',
        'help_text': (
            "Step 1 \u2192 \U0001f4c2 \ud3f4\ub354 \uc120\ud0dd + \uc2a4\uce94\n"
            "Step 2 \u2192 \U0001f3ac \ud30c\uc77c \uc120\ud0dd / \ucd94\ucd9c\n"
            "Step 3 \u2192 \U0001f310 \uc5b8\uc5b4 \uc120\ud0dd + Start"
        ),
    },
}

LLM_BATCH_SIZE = 5
LLM_CONTEXT_SIZE = 3

DEFAULT_SYSTEM_PROMPT = (
    "You are a professional anime/movie subtitle translator. "
    "Translate naturally and conversationally. "
    "Use appropriate pronouns and honorifics based on context. "
    "Keep the tone, emotion, and style of the original speaker. "
    "Preserve cultural references when possible."
)

DEFAULT_LLM_MODEL = "gpt-4o-mini"
DEFAULT_LLM_BASE_URL = "https://api.openai.com/v1"

VIDEO_EXTENSIONS = ('.mkv', '.mp4', '.avi', '.mov', '.ts', '.m2ts')


def get_subtitle_streams(video_path):
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_streams', '-select_streams', 's', video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        subtitle_info = []
        for s in data.get('streams', []):
            subtitle_info.append({
                'index': s.get('index', 0),
                'codec': s.get('codec_name', 'unknown'),
                'language': s.get('tags', {}).get('language', 'und'),
                'title': s.get('tags', {}).get('title', ''),
            })
        return subtitle_info
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return []


def extract_subtitle(video_path, stream_index, output_path):
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
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False





def is_video_file(filepath):
    return os.path.splitext(filepath)[1].lower() in VIDEO_EXTENSIONS


def get_lang_choices():
    return list(LANGUAGES.keys())


class AsyncTranslator:
    """Handle async translation in a separate thread"""

    def __init__(self, callback, use_llm=False, llm_config=None):
        self.callback = callback
        self._cancel = False
        self.use_llm = use_llm
        self.llm_config = llm_config or {}
        self._cache = {}

    def cancel(self):
        self._cancel = True

    def run_translate(self, input_file, output_file, src_lang, dest_lang, styles=None):
        self._cancel = False
        thread = threading.Thread(
            target=self._translate_thread,
            args=(input_file, output_file, src_lang, dest_lang, styles),
            daemon=True
        )
        thread.start()

    def _translate_thread(self, input_file, output_file, src_lang, dest_lang, styles):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            ext = os.path.splitext(input_file)[1].lower()
            if ext == '.ass':
                total, elapsed = loop.run_until_complete(
                    self._translate_ass(input_file, output_file, src_lang, dest_lang, styles)
                )
            else:
                total, elapsed = loop.run_until_complete(
                    self._translate_srt(input_file, output_file, src_lang, dest_lang)
                )
            self.callback('done', total=total, elapsed=elapsed)
        except Exception as e:
            self.callback('error', message=str(e))
        finally:
            loop.close()

    async def _translate_srt(self, input_file, output_file, src_lang, dest_lang):
        with open(input_file, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        entries = self._parse_srt(content)
        if not entries:
            self.callback('plan', total=0)
            return 0, 0
        self.callback('plan', total=len(entries))
        start_time = time.time()
        translations = [''] * len(entries)

        if self.use_llm:
            batch_size = LLM_BATCH_SIZE
            for i in range(0, len(entries), batch_size):
                if self._cancel:
                    return 0, 0
                batch = entries[i:i + batch_size]
                prev_idx = max(0, i - LLM_CONTEXT_SIZE)
                context = [e['clean'] for e in entries[prev_idx:i]]
                results = await self._translate_batch_llm(
                    batch, context, src_lang, dest_lang
                )
                for j, r in enumerate(results):
                    if j < len(translations[i:]):
                        translations[i + j] = r
                current = min(i + batch_size, len(entries))
                self.callback('progress', current=current, total=len(entries), start_time=start_time)
        else:
            translator = Translator()
            batch_size = 30
            for i in range(0, len(entries), batch_size):
                if self._cancel:
                    return 0, 0
                batch = [e['clean'] for e in entries[i:i + batch_size]]
                results = await self._translate_batch(batch, src_lang, dest_lang, translator)
                for j, r in enumerate(results):
                    translations[i + j] = r
                current = min(i + batch_size, len(entries))
                self.callback('progress', current=current, total=len(entries), start_time=start_time)
                if i + batch_size < len(entries):
                    await asyncio.sleep(1)

        # Verification: retry any lines still in source language
        for idx in range(len(entries)):
            if self._is_untranslated(entries[idx]['clean'], translations[idx], src_lang):
                try:
                    if not self.use_llm:
                        r = await translator.translate(entries[idx]['clean'], src=src_lang, dest=dest_lang)
                        if not self._is_untranslated(entries[idx]['clean'], r.text, src_lang):
                            translations[idx] = r.text
                    else:
                        r = await self._translate_batch_llm([entries[idx]], [], src_lang, dest_lang)
                        translations[idx] = r[0]
                except Exception:
                    pass

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

    async def _translate_ass(self, input_file, output_file, src_lang, dest_lang, styles):
        with open(input_file, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
        entries = []
        for i, line in enumerate(lines):
            if not line.strip().startswith('Dialogue:'):
                continue
            prefix, text = self._parse_ass_line(line)
            if not text:
                continue
            style_match = re.search(r'Dialogue:\s*\d+,[^,]*,[^,]*,([^,]*),', prefix)
            style = style_match.group(1) if style_match else ''
            if styles and style not in styles:
                continue
            if self._is_drawing(text):
                continue
            clean = self._clean_ass_text(text)
            if not clean:
                continue
            entries.append({'line_idx': i, 'prefix': prefix, 'original': text, 'clean': clean})
        if not entries:
            self.callback('plan', total=0)
            return 0, 0
        self.callback('plan', total=len(entries))
        start_time = time.time()
        translations = [''] * len(entries)

        if self.use_llm:
            batch_size = LLM_BATCH_SIZE
            for i in range(0, len(entries), batch_size):
                if self._cancel:
                    return 0, 0
                batch = entries[i:i + batch_size]
                prev_idx = max(0, i - LLM_CONTEXT_SIZE)
                context = [e['clean'] for e in entries[prev_idx:i]]
                results = await self._translate_batch_llm(
                    batch, context, src_lang, dest_lang
                )
                for j, r in enumerate(results):
                    if j < len(translations[i:]):
                        translations[i + j] = r
                current = min(i + batch_size, len(entries))
                self.callback('progress', current=current, total=len(entries), start_time=start_time)
        else:
            translator = Translator()
            batch_size = 30
            for i in range(0, len(entries), batch_size):
                if self._cancel:
                    return 0, 0
                batch = [e['clean'] for e in entries[i:i + batch_size]]
                results = await self._translate_batch(batch, src_lang, dest_lang, translator)
                for j, r in enumerate(results):
                    translations[i + j] = r
                current = min(i + batch_size, len(entries))
                self.callback('progress', current=current, total=len(entries), start_time=start_time)
                if i + batch_size < len(entries):
                    await asyncio.sleep(1)

        # Verification: retry any lines still in source language
        for idx in range(len(entries)):
            if self._is_untranslated(entries[idx]['clean'], translations[idx], src_lang):
                try:
                    if not self.use_llm:
                        r = await translator.translate(entries[idx]['clean'], src=src_lang, dest=dest_lang)
                        if not self._is_untranslated(entries[idx]['clean'], r.text, src_lang):
                            translations[idx] = r.text
                    else:
                        r = await self._translate_batch_llm([entries[idx]], [], src_lang, dest_lang)
                        translations[idx] = r[0]
                except Exception:
                    pass

        output_lines = lines.copy()
        for idx, entry in enumerate(entries):
            translated = self._restore_ass_tags(entry['original'], translations[idx])
            translated = translated.replace('\n', ' ').replace('\r', '')
            output_lines[entry['line_idx']] = entry['prefix'] + translated + '\n'
        with open(output_file, 'w', encoding='utf-8-sig') as f:
            f.writelines(output_lines)
        elapsed = time.time() - start_time
        return len(entries), elapsed

    async def _translate_batch(self, texts, src_lang, dest_lang, translator):
        # Check cache first
        cached = {}
        todo_idx = []
        todo_texts = []
        for i, t in enumerate(texts):
            key = (t, src_lang, dest_lang)
            if key in self._cache:
                cached[i] = self._cache[key]
            else:
                todo_idx.append(i)
                todo_texts.append(t)

        if todo_texts:
            try:
                results = await translator.translate(todo_texts, src=src_lang, dest=dest_lang)
                translated = [r.text for r in results]
            except Exception:
                translated = list(todo_texts)

            # Retry items that were not actually translated (rate-limited / skipped)
            for j in range(len(todo_texts)):
                i = todo_idx[j]
                trans = translated[j]
                if self._is_untranslated(todo_texts[j], trans, src_lang):
                    try:
                        await asyncio.sleep(1)
                        r = await translator.translate(todo_texts[j], src=src_lang, dest=dest_lang)
                        if not self._is_untranslated(todo_texts[j], r.text, src_lang):
                            trans = r.text
                    except Exception:
                        pass
                self._cache[(todo_texts[j], src_lang, dest_lang)] = trans
                cached[i] = trans

        return [cached[i] for i in range(len(texts))]

    async def _translate_batch_llm(self, entries, context, src_lang, dest_lang):
        # Check cache for each entry
        cached = {}
        todo_entries = []
        todo_indices = []
        for i, entry in enumerate(entries):
            key = (entry['clean'], src_lang, dest_lang)
            if key in self._cache:
                cached[i] = self._cache[key]
            else:
                todo_indices.append(i)
                todo_entries.append(entry)

        if not todo_entries:
            return [cached[i] for i in range(len(entries))]

        try:
            client = openai.AsyncClient(
                api_key=self.llm_config.get('api_key', ''),
                base_url=self.llm_config.get('base_url', DEFAULT_LLM_BASE_URL)
            )
            model = self.llm_config.get('model', DEFAULT_LLM_MODEL)
            system_prompt = self.llm_config.get('system_prompt', DEFAULT_SYSTEM_PROMPT)

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
            base_url = self.llm_config.get('base_url', '')
            if 'deepseek' not in base_url.lower():
                kwargs['response_format'] = {"type": "json_object"}

            response = await client.chat.completions.create(**kwargs)

            raw = response.choices[0].message.content.strip()
            data = self._parse_json_response(raw)
            results = data.get("translations", []) if data else []

            if len(results) != len(todo_entries):
                self.callback('error', message=f"LLM returned {len(results)} lines, expected {len(todo_entries)}. Using original text.")
                results = [e['clean'] for e in todo_entries]

            # Cache and store results
            for j, entry in enumerate(todo_entries):
                trans = results[j] if j < len(results) else entry['clean']
                self._cache[(entry['clean'], src_lang, dest_lang)] = trans
                cached[todo_indices[j]] = trans

            return [cached[i] for i in range(len(entries))]

        except openai.AuthenticationError as e:
            self.callback('error', message=f"API key invalid: {e}")
            return [e['clean'] for e in entries]
        except json.JSONDecodeError:
            self.callback('error', message="LLM returned invalid JSON. Check your model's response format support.")
            return [e['clean'] for e in entries]
        except Exception as e:
            self.callback('error', message=f"LLM error: {e}")
            return [e['clean'] for e in entries]

    def _parse_json_response(self, raw):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        # Strip markdown code block fences
        raw = re.sub(r'```(?:json)?\s*', '', raw).strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        # Greedy extraction from first { to last }
        brace_match = re.search(r'\{.*"translations"\s*:\s*\[.*\]\}', raw, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group())
            except json.JSONDecodeError:
                pass
        self.callback('error', message="LLM returned invalid JSON. Try setting Base URL / Model correctly for your provider.")
        return None

    def _parse_ass_line(self, line):
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

    def _is_drawing(self, text):
        stripped = text.strip()
        clean = re.sub(r'\{[^}]*\}', '', stripped).strip()
        if re.match(r'^[mblspcn]\s', clean):
            return True
        if re.search(r'\{.*\\p\d+.*\}', stripped):
            return True
        if re.match(r'^[\d\s,.\-lmbnspc]+$', clean):
            return True
        nums = len(re.findall(r'[\d\-]+', clean))
        words = len(re.findall(r'[a-zA-Z]{2,}', clean))
        if nums > 10 and (words == 0 or nums / max(words, 1) > 3):
            return True
        return False

    def _clean_ass_text(self, text):
        clean = re.sub(r'\{\\[^}]*\}', '', text)
        clean = re.sub(r'\{[^}]*\}', '', clean)
        clean = clean.replace('\\N', ' ').replace('\\n', ' ')
        return clean.strip()

    def _restore_ass_tags(self, original, translated):
        if '\\N' in original:
            translated = translated.replace('\n', '\\N')
        return translated

    def _is_untranslated(self, original, translated, src_lang):
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

    def _parse_srt(self, content):
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


def create_rounded_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    points = [
        x1+r, y1, x2-r, y1,
        x2, y1, x2, y1+r,
        x2, y2-r, x2, y2,
        x2-r, y2, x1+r, y2,
        x1, y2, x1, y2-r,
        x1, y1+r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, splinesteps=20, **kwargs)


class CardFrame(tk.Frame):
    def __init__(self, parent, title='', font_family='Segoe UI', **kwargs):
        super().__init__(parent, bg=SubtitleTranslatorGUI.BG_LIGHT, **kwargs)
        self._title = title
        self._font_family = font_family
        self._redrawing = False
        self._canvas = tk.Canvas(self, highlightthickness=0, bd=0,
                                 bg=SubtitleTranslatorGUI.BG_LIGHT)
        self._canvas.pack(fill=tk.BOTH, expand=True)
        self._content = ttk.Frame(self._canvas)
        self._content_id = self._canvas.create_window(
            (14, 36), window=self._content, anchor='nw', tags='content'
        )
        self._content.bind('<Configure>', self._on_content_resize)
        self._canvas.bind('<Configure>', self._on_canvas_resize)
        self.bind('<Map>', lambda e: self._redraw())

    @property
    def content(self):
        return self._content

    def set_title(self, title):
        self._title = title
        self._redraw()

    def set_font(self, family):
        self._font_family = family
        self._redraw()

    def _on_content_resize(self, event):
        self._redraw()

    def _on_canvas_resize(self, event):
        self._canvas.itemconfig(self._content_id, width=event.width - 28)

    def _redraw(self):
        if self._redrawing:
            return
        self._redrawing = True
        try:
            cw = self._content.winfo_width() or 200
            ch = self._content.winfo_height() or 40
            if cw < 10 or ch < 10:
                self.after(50, self._redraw)
                return
            canvas_w = self._canvas.winfo_width()
            if canvas_w < 10:
                canvas_w = cw + 28
            ph = ch + 54
            self._canvas.configure(height=ph)
            self._canvas.delete('border', 'title')
            create_rounded_rect(self._canvas, 2, 2, canvas_w - 2, ph - 2, 12,
                                fill=SubtitleTranslatorGUI.CARD_BG,
                                outline=SubtitleTranslatorGUI.CARD_BORDER, width=1,
                                tags='border')
            self._canvas.create_text(18, 20, text=self._title, anchor='w',
                                     font=(self._font_family, 10, 'bold'),
                                     fill=SubtitleTranslatorGUI.ACCENT, tags='title')
        finally:
            self._redrawing = False


class SubtitleTranslatorGUI(tk.Tk):
    PADDING = 14
    ACCENT = '#6366f1'
    ACCENT_DARK = '#4f46e5'
    ACCENT_LIGHT = '#eef2ff'
    BG_LIGHT = '#f1f5f9'
    CARD_BG = '#ffffff'
    CARD_BORDER = '#cbd5e1'
    TEXT_PRIMARY = '#1e293b'
    TEXT_SECONDARY = '#64748b'
    RED = '#ef4444'
    RED_DARK = '#dc2626'
    GREEN = '#059669'

    def __init__(self):
        super().__init__()
        self._current_lang = self._detect_ui_language()
        self._current_font = 'Consolas'
        self.title(UI_STRINGS[self._current_lang]['app_title'])
        self.geometry("1100x580")
        self.minsize(900, 500)
        self.translator = None
        self.scanned_files = []
        self.style_vars = {}
        self.running = False
        self._cached_styles_path = None
        self._cached_styles_info = None
        self._original_video_path = None
        self._current_output_path = None
        self._mux_var = tk.BooleanVar(value=False)

        self._setup_style()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _detect_ui_language(self):
        try:
            lang = os.environ.get('LANG', '')[:2]
            if lang in UI_LANGUAGES:
                return lang
        except Exception:
            pass
        return 'en'

    def _tr(self, key):
        return UI_STRINGS.get(self._current_lang, {}).get(key) or UI_STRINGS['en'].get(key, key)

    def _setup_style(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        self._apply_font()
        self._apply_theme_colors(style)

    def _apply_font(self):
        style = ttk.Style(self)
        f = self._current_font
        style.configure('TLabel', font=(f, 10))
        style.configure('TLabelframe.Label', font=(f, 9, 'bold'))
        style.configure('TButton', font=(f, 10))
        style.configure('Cancel.TButton', font=(f, 10))
        style.configure('Header.TLabel', font=(f, 16, 'bold'))
        style.configure('TCombobox', font=(f, 10))
        self._apply_theme_colors(style)
        for attr in ('_file_card', '_lang_card', '_out_card', '_engine_card', '_prog_card', '_simple_mux_card'):
            card = getattr(self, attr, None)
            if card:
                card.set_font(f)
        try:
            self.file_listbox.config(font=(f, 10))
            self.log_text.config(font=(f, 9))
            self._llm_status_label.config(font=(f, 9))
            self._help_label.config(font=(f, 10, 'bold'))
            self._header_icon.config(font=(f, 18))
            self._spinner_label.config(font=(f, 12))
            self._browse_btn.config(font=(f, 10))
            self._mux_checkbox_icon.config(font=(f, 14))
            self._mux_cb.config(font=(f, 10))
        except AttributeError:
            pass

    def _apply_theme_colors(self, style=None):
        if style is None:
            style = ttk.Style(self)
        style.configure('TFrame', background=self.BG_LIGHT)
        style.configure('TLabelframe', background=self.CARD_BG,
                        bordercolor=self.CARD_BORDER, lightcolor=self.CARD_BORDER,
                        darkcolor=self.CARD_BORDER)
        style.configure('TLabelframe.Label', foreground=self.ACCENT,
                        font=(self._current_font, 9, 'bold'))

        style.configure('TButton',
                        background=self.ACCENT, foreground='white',
                        borderwidth=0, focusthickness=0,
                        font=(self._current_font, 10))
        style.map('TButton',
                  background=[('active', self.ACCENT_DARK), ('disabled', '#cbd5e1')],
                  foreground=[('disabled', '#94a3b8')])

        style.configure('Cancel.TButton',
                        background=self.RED, foreground='white',
                        borderwidth=0, focusthickness=0,
                        font=(self._current_font, 10))
        style.map('Cancel.TButton',
                  background=[('active', self.RED_DARK), ('disabled', '#fca5a5')],
                  foreground=[('disabled', '#94a3b8')])

        style.configure('Header.TLabel',
                        foreground=self.ACCENT_DARK,
                        background=self.BG_LIGHT)

        style.configure('Horizontal.TProgressbar',
                        troughcolor='#e2e8f0',
                        background=self.ACCENT,
                        lightcolor=self.ACCENT_LIGHT,
                        darkcolor=self.ACCENT,
                        bordercolor=self.ACCENT)

        style.configure('TCombobox',
                        fieldbackground='white',
                        background=self.ACCENT,
                        foreground=self.TEXT_PRIMARY,
                        arrowcolor='white',
                        font=(self._current_font, 10))
        style.map('TCombobox',
                  fieldbackground=[('readonly', 'white')],
                  foreground=[('readonly', self.TEXT_PRIMARY)],
                  selectbackground=[('readonly', self.ACCENT_LIGHT)],
                  selectforeground=[('readonly', self.TEXT_PRIMARY)])

        style.configure('TEntry', fieldbackground='white',
                        foreground=self.TEXT_PRIMARY)
        style.configure('TScrollbar',
                        gripcount=0,
                        background='#cbd5e1',
                        darkcolor='#cbd5e1',
                        lightcolor='#cbd5e1',
                        troughcolor=self.BG_LIGHT,
                        bordercolor=self.BG_LIGHT,
                        arrowcolor='#64748b')

    def _on_close(self):
        if self.running:
            if messagebox.askyesno(self._tr('quit_title'), self._tr('quit_msg')):
                self._cancel_translation()
                self.destroy()
        else:
            self.destroy()

    def _build_ui(self):
        main = ttk.Frame(self, padding=self.PADDING)
        main.pack(fill=tk.BOTH, expand=True)

        header_frame = ttk.Frame(main)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text="\U0001f310").pack(side=tk.LEFT, padx=(0, 3))
        lang_names = [UI_LANG_NAMES[code] for code in UI_LANGUAGES]
        self._ui_lang_combo = ttk.Combobox(
            header_frame, values=lang_names,
            state='readonly', width=14
        )
        self._ui_lang_combo.set(UI_LANG_NAMES[self._current_lang])
        self._ui_lang_combo.pack(side=tk.LEFT)
        self._ui_lang_combo.bind('<<ComboboxSelected>>', self._on_ui_lang_change)

        ttk.Label(header_frame, text='\U0001f4d6').pack(side=tk.LEFT, padx=(8, 3))
        font_names = FONT_FAMILIES
        self._font_combo = ttk.Combobox(
            header_frame, values=font_names,
            state='readonly', width=14
        )
        self._font_combo.set(self._current_font)
        self._font_combo.pack(side=tk.LEFT)
        self._font_combo.bind('<<ComboboxSelected>>', self._on_font_change)

        self._header_icon = ttk.Label(header_frame, text='\U0001f3ac', font=(self._current_font, 18))
        self._header_icon.pack(side=tk.LEFT, padx=(0, 4))

        self._header_label = ttk.Label(
            header_frame, text=self._tr('app_title'),
            style='Header.TLabel'
        )
        self._header_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

        accent_bar = tk.Frame(main, height=4, bg='#4338ca')
        accent_bar.pack(fill=tk.X, pady=(0, 0))
        accent_glow = tk.Frame(main, height=1, bg='#818cf8')
        accent_glow.pack(fill=tk.X, pady=(0, 10))

        scroll_canvas = tk.Canvas(main, highlightthickness=0, bd=0, bg=self.BG_LIGHT)
        scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(main, orient=tk.VERTICAL, command=scroll_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_canvas.config(yscrollcommand=scrollbar.set)

        scrollable = ttk.Frame(scroll_canvas)
        scrollable.bind('<Configure>', lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox('all')))
        scroll_canvas.create_window((0, 0), window=scrollable, anchor='nw', tags='inner')
        scroll_canvas.bind('<Configure>', lambda e: scroll_canvas.itemconfig('inner', width=e.width))
        scroll_canvas.bind('<Enter>', lambda e: scroll_canvas.bind_all('<MouseWheel>',
                           lambda e: scroll_canvas.yview_scroll(int(-1*(e.delta/120)), 'units')))
        scroll_canvas.bind('<Leave>', lambda e: scroll_canvas.unbind_all('<MouseWheel>'))

        scrollable.columnconfigure(0, weight=3, minsize=400)
        scrollable.columnconfigure(1, weight=1)
        scrollable.rowconfigure(0, weight=1)

        left_col = ttk.Frame(scrollable)
        left_col.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        right_col = ttk.Frame(scrollable)
        right_col.grid(row=0, column=1, sticky='nsew', padx=(5, 0))

        self._build_file_section(left_col)
        self._build_language_section(left_col)
        self._build_output_section(left_col)
        self._build_engine_section(left_col)
        self._build_style_section(left_col)

        self._build_control_section(right_col)
        self._build_progress_section(right_col)
        self._build_simple_mux_section(right_col)
        self._build_batch_translate_section(right_col)
        self._build_mux_section(right_col)

        log_frame = ttk.Frame(scrollable)
        log_frame.grid(row=1, column=0, columnspan=2, sticky='nsew', pady=(5, 0))
        self._build_log_section(log_frame)

    def _build_file_section(self, parent):
        card = CardFrame(parent, title=self._tr('file_section'), font_family=self._current_font)
        card.pack(fill=tk.X, pady=5)
        self._file_card = card
        content = card.content

        dir_row = ttk.Frame(content)
        dir_row.pack(fill=tk.X, pady=4)
        self._dir_label = ttk.Label(dir_row, text=self._tr('dir_label'))
        self._dir_label.pack(side=tk.LEFT)
        self.dir_var = tk.StringVar(value='.')
        dir_entry = ttk.Entry(dir_row, textvariable=self.dir_var, width=30)
        dir_entry.pack(side=tk.LEFT, padx=6)
        self._browse_btn = tk.Button(dir_row, text=self._tr('browse'), command=self._browse_dir,
                                      width=10, cursor='hand2',
                                      bg=self.ACCENT, fg='white', relief='flat',
                                      font=(self._current_font, 10), bd=0)
        self._browse_btn.pack(side=tk.LEFT, padx=3)
        self._scan_btn = ttk.Button(dir_row, text=self._tr('scan'), command=self._scan_files, width=8, cursor='hand2')
        self._scan_btn.pack(side=tk.LEFT, padx=3)

        file_list_frame = ttk.Frame(content)
        file_list_frame.pack(fill=tk.X, pady=6)
        list_inner = ttk.Frame(file_list_frame)
        list_inner.pack(fill=tk.X, expand=True)
        self.file_listbox = tk.Listbox(list_inner, height=10, selectmode=tk.SINGLE,
                                       font=(self._current_font, 10),
                                       bg='white', fg=self.TEXT_PRIMARY,
                                       selectbackground=self.ACCENT_LIGHT,
                                       selectforeground=self.TEXT_PRIMARY,
                                       relief='flat', highlightthickness=1,
                                       highlightcolor=self.CARD_BORDER,
                                       highlightbackground=self.CARD_BORDER)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scrollbar = ttk.Scrollbar(list_inner, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        hscroll = ttk.Scrollbar(file_list_frame, orient=tk.HORIZONTAL, command=self.file_listbox.xview)
        hscroll.pack(fill=tk.X)
        self.file_listbox.config(xscrollcommand=hscroll.set)
        self.file_listbox.bind('<<ListboxSelect>>', self._on_file_select)

        btn_row = ttk.Frame(content)
        btn_row.pack(fill=tk.X)
        self._extract_btn = ttk.Button(btn_row, text=self._tr('extract_btn'),
                                       command=self._extract_subtitle, width=16, cursor='hand2')
        self._extract_btn.pack(side=tk.LEFT)
        self._extract_btn.config(state=tk.DISABLED)

    def _build_language_section(self, parent):
        card = CardFrame(parent, title=self._tr('lang_section'), font_family=self._current_font)
        card.pack(fill=tk.X, pady=5)
        self._lang_card = card
        content = card.content

        row = ttk.Frame(content)
        row.pack(fill=tk.X, pady=4)

        self._src_label = ttk.Label(row, text=self._tr('source'))
        self._src_label.pack(side=tk.LEFT)
        self.src_lang = ttk.Combobox(
            row, values=get_lang_choices(),
            state='readonly', width=18
        )
        self.src_lang.set('English')
        self.src_lang.pack(side=tk.LEFT, padx=6)

        self._swap_btn = ttk.Button(row, text=self._tr('swap'), command=self._swap_languages,
                                     width=6, cursor='hand2')
        self._swap_btn.pack(side=tk.LEFT, padx=6)

        self._target_label = ttk.Label(row, text=self._tr('target'))
        self._target_label.pack(side=tk.LEFT)
        self.dest_lang = ttk.Combobox(
            row, values=get_lang_choices(),
            state='readonly', width=18
        )
        self.dest_lang.set('Vietnamese')
        self.dest_lang.pack(side=tk.LEFT, padx=6)
        self.dest_lang.bind('<<ComboboxSelected>>', self._update_output_name)

    def _swap_languages(self):
        src = self.src_lang.get()
        dest = self.dest_lang.get()
        self.src_lang.set(dest)
        self.dest_lang.set(src)
        self._update_output_name()

    def _update_output_name(self, event=None):
        sel = self.file_listbox.curselection()
        if not sel or not self.scanned_files:
            return
        idx = sel[0]
        if idx >= len(self.scanned_files):
            return
        filepath = self.scanned_files[idx]
        if not os.path.isfile(filepath):
            return
        ext = os.path.splitext(filepath)[1].lower()
        if is_video_file(filepath):
            return
        out_name = f'{self.dest_lang.get()}_{LANGUAGES[self.dest_lang.get()]}'
        new_out = filepath.replace(ext, f'_{out_name}{ext}')
        self.out_var.set(new_out)

    def _build_output_section(self, parent):
        card = CardFrame(parent, title=self._tr('output_section'), font_family=self._current_font)
        card.pack(fill=tk.X, pady=5)
        self._out_card = card
        content = card.content

        row = ttk.Frame(content)
        row.pack(fill=tk.X, pady=4)
        self.out_var = tk.StringVar()
        out_entry = ttk.Entry(row, textvariable=self.out_var)
        out_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self._out_browse_btn = ttk.Button(row, text=self._tr('browse'), command=self._browse_output, width=10, cursor='hand2')
        self._out_browse_btn.pack(side=tk.RIGHT)

    def _build_engine_section(self, parent):
        card = CardFrame(parent, title=self._tr('engine_section'), font_family=self._current_font)
        card.pack(fill=tk.X, pady=5)
        self._engine_card = card
        content = card.content

        row = ttk.Frame(content)
        row.pack(fill=tk.X, pady=4)

        self._engine_label = ttk.Label(row, text=self._tr('engine_label'))
        self._engine_label.pack(side=tk.LEFT)
        self.engine_var = tk.StringVar(value=self._tr('google_engine'))
        self._engine_cb = ttk.Combobox(
            row, values=[self._tr('google_engine'), self._tr('llm_engine')],
            state='readonly', width=18, textvariable=self.engine_var
        )
        self._engine_cb.pack(side=tk.LEFT, padx=6)
        self._engine_cb.bind('<<ComboboxSelected>>', self._on_engine_change)

        self.llm_warning = ttk.Label(row, text='', foreground='red')
        self.llm_warning.pack(side=tk.LEFT, padx=6)
        if not HAS_OPENAI:
            self.llm_warning.config(text=self._tr('llm_warning'))

        self.llm_frame = ttk.Frame(content)

        api_row = ttk.Frame(self.llm_frame)
        api_row.pack(fill=tk.X, pady=4)
        self._api_key_label = ttk.Label(api_row, text=self._tr('api_key'))
        self._api_key_label.pack(side=tk.LEFT)
        self.api_key_var = tk.StringVar()
        api_entry = ttk.Entry(api_row, textvariable=self.api_key_var, width=40, show='*')
        api_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        self.show_key_btn = ttk.Button(api_row, text='\U0001f441', width=3, command=self._toggle_api_key, cursor='hand2')
        self.show_key_btn.pack(side=tk.LEFT)

        url_row = ttk.Frame(self.llm_frame)
        url_row.pack(fill=tk.X, pady=4)
        self._base_url_label = ttk.Label(url_row, text=self._tr('base_url'))
        self._base_url_label.pack(side=tk.LEFT)
        self.base_url_var = tk.StringVar(value=DEFAULT_LLM_BASE_URL)
        url_entry = ttk.Entry(url_row, textvariable=self.base_url_var)
        url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

        model_row = ttk.Frame(self.llm_frame)
        model_row.pack(fill=tk.X, pady=4)
        self._model_label = ttk.Label(model_row, text=self._tr('model'))
        self._model_label.pack(side=tk.LEFT)
        self.model_var = tk.StringVar(value=DEFAULT_LLM_MODEL)
        model_entry = ttk.Entry(model_row, textvariable=self.model_var)
        model_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        self._deepseek_btn = ttk.Button(model_row, text=self._tr('deepseek'), command=self._set_deepseek, width=9, cursor='hand2')
        self._deepseek_btn.pack(side=tk.RIGHT, padx=3)
        self._test_btn = ttk.Button(model_row, text=self._tr('test'), command=self._test_llm, width=8, cursor='hand2')
        self._test_btn.pack(side=tk.RIGHT)

        prompt_row = ttk.Frame(self.llm_frame)
        prompt_row.pack(fill=tk.X, pady=4)
        self._prompt_label = ttk.Label(prompt_row, text=self._tr('sys_prompt'))
        self._prompt_label.pack(anchor=tk.W)
        self.prompt_text = tk.Text(self.llm_frame, height=3, wrap=tk.WORD)
        self.prompt_text.insert('1.0', DEFAULT_SYSTEM_PROMPT)
        self.prompt_text.pack(fill=tk.X, pady=(0, 4))

        status_row = ttk.Frame(self.llm_frame)
        status_row.pack(fill=tk.X)
        self.llm_status_var = tk.StringVar()
        self._llm_status_label = ttk.Label(status_row, textvariable=self.llm_status_var,
                                           font=(self._current_font, 8))
        self._llm_status_label.pack(side=tk.LEFT)

    def _build_style_section(self, parent):
        self._style_frame = ttk.LabelFrame(parent, text=self._tr('style_section'), padding=10)
        self._style_inner = ttk.Frame(self._style_frame)
        self._style_inner.pack(fill=tk.BOTH, expand=True)
        self._style_canvas = tk.Canvas(self._style_inner, height=120, highlightthickness=0)
        self._style_scroll = ttk.Scrollbar(self._style_inner, orient=tk.VERTICAL, command=self._style_canvas.yview)
        self._style_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._style_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._style_scrollable = ttk.Frame(self._style_canvas)
        self._style_scrollable.bind('<Configure>',
                                    lambda e: self._style_canvas.configure(scrollregion=self._style_canvas.bbox('all')))
        self._style_canvas.create_window((0, 0), window=self._style_scrollable, anchor='nw')
        self._style_canvas.configure(yscrollcommand=self._style_scroll.set)

    def _build_control_section(self, parent):
        self._ctrl_frame = ttk.Frame(parent)
        self._ctrl_frame.pack(fill=tk.X, pady=5)

        self._start_btn = ttk.Button(
            self._ctrl_frame, text=self._tr('start'),
            command=self._start_translation, width=24, cursor='hand2'
        )
        self._start_btn.pack(side=tk.LEFT, padx=(0, 10))

        self._cancel_btn = ttk.Button(
            self._ctrl_frame, text=self._tr('cancel'),
            command=self._cancel_translation, width=12,
            state=tk.DISABLED, style='Cancel.TButton', cursor='hand2'
        )
        self._cancel_btn.pack(side=tk.LEFT)

        mux_frame = tk.Frame(self._ctrl_frame, bg=self.BG_LIGHT)
        mux_frame.pack(side=tk.LEFT, padx=(16, 0))
        self._mux_checkbox_icon = tk.Label(
            mux_frame, text='\u2610', font=(self._current_font, 14),
            bg=self.BG_LIGHT, fg=self.TEXT_SECONDARY, cursor='hand2'
        )
        self._mux_checkbox_icon.pack(side=tk.LEFT)
        self._mux_checkbox_icon.bind('<Button-1>', self._toggle_mux)
        self._mux_cb = tk.Label(
            mux_frame, text=self._tr('mux_checkbox'),
            font=(self._current_font, 10),
            bg=self.BG_LIGHT, fg=self.TEXT_PRIMARY, cursor='hand2'
        )
        self._mux_cb.pack(side=tk.LEFT, padx=(4, 0))
        self._mux_cb.bind('<Button-1>', self._toggle_mux)

    def _build_progress_section(self, parent):
        card = CardFrame(parent, title=self._tr('progress_section'), font_family=self._current_font)
        card.pack(fill=tk.X, pady=5)
        self._prog_card = card
        content = card.content

        self.progress = ttk.Progressbar(content, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 6))

        status_row = ttk.Frame(content)
        status_row.pack(fill=tk.X, pady=(0, 4))
        self.status_var = tk.StringVar(value=self._tr('ready'))
        self._status_label = ttk.Label(status_row, textvariable=self.status_var)
        self._status_label.pack(side=tk.LEFT)
        self._spinner_label = ttk.Label(status_row, text='', font=(self._current_font, 12))
        self._spinner_label.pack(side=tk.LEFT, padx=(6, 0))
        self._spinner_frames = ['◐', '◓', '◑', '◒']
        self._spinner_idx = 0
        self._spinner_id = None

        self._help_label = ttk.Label(content, text=self._tr('help_text'),
                                     font=(self._current_font, 10, 'bold'),
                                     foreground=self.ACCENT_DARK,
                                     justify=tk.LEFT)
        self._help_label.pack(anchor=tk.W)

    def _build_mux_section(self, parent):
        card = CardFrame(parent, title=self._tr('mux_section'), font_family=self._current_font)
        self._mux_card = card
        content = card.content

        row = ttk.Frame(content)
        row.pack(fill=tk.X, pady=3)
        ttk.Label(row, text='\U0001f3ac', font=(self._current_font, 12)).pack(side=tk.LEFT)
        self._mux_video_var = tk.StringVar()
        self._mux_video_combo = ttk.Combobox(row, textvariable=self._mux_video_var,
                                              state='readonly', width=25)
        self._mux_video_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

        row2 = ttk.Frame(content)
        row2.pack(fill=tk.X, pady=3)
        ttk.Label(row2, text='\U0001f4c4', font=(self._current_font, 12)).pack(side=tk.LEFT)
        self._mux_sub_var = tk.StringVar()
        self._mux_sub_combo = ttk.Combobox(row2, textvariable=self._mux_sub_var,
                                            state='readonly', width=25)
        self._mux_sub_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

        btn_row = ttk.Frame(content)
        btn_row.pack(fill=tk.X, pady=(3, 0))
        self._mux_btn = ttk.Button(btn_row, text=self._tr('mux_ok'),
                                   command=self._mux_selected, width=12, cursor='hand2')
        self._mux_btn.pack(side=tk.RIGHT)

    def _build_simple_mux_section(self, parent):
        card = CardFrame(parent, title=self._tr('simple_mux_title'), font_family=self._current_font)
        card.pack(fill=tk.X, pady=5)
        self._simple_mux_card = card
        content = card.content

        vr = ttk.Frame(content)
        vr.pack(fill=tk.X, pady=2)
        ttk.Label(vr, text='\U0001f3ac', font=(self._current_font, 10)).pack(side=tk.LEFT)
        self._mux_video_var2 = tk.StringVar()
        self._mux_video_entry = ttk.Entry(vr, textvariable=self._mux_video_var2)
        self._mux_video_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        ttk.Button(vr, text=self._tr('browse'), command=self._browse_mux_video, width=8, cursor='hand2').pack(side=tk.LEFT)
        vsb = ttk.Scrollbar(vr, orient=tk.HORIZONTAL, command=self._mux_video_entry.xview)
        vsb.pack(side=tk.BOTTOM, fill=tk.X)
        self._mux_video_entry.config(xscrollcommand=vsb.set)

        sr = ttk.Frame(content)
        sr.pack(fill=tk.X, pady=2)
        ttk.Label(sr, text='\U0001f4c4', font=(self._current_font, 10)).pack(side=tk.LEFT)
        self._mux_sub_var2 = tk.StringVar()
        self._mux_sub_entry = ttk.Entry(sr, textvariable=self._mux_sub_var2)
        self._mux_sub_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        ttk.Button(sr, text=self._tr('browse'), command=self._browse_mux_sub, width=8, cursor='hand2').pack(side=tk.LEFT)
        ssb = ttk.Scrollbar(sr, orient=tk.HORIZONTAL, command=self._mux_sub_entry.xview)
        ssb.pack(side=tk.BOTTOM, fill=tk.X)
        self._mux_sub_entry.config(xscrollcommand=ssb.set)

        btn_row = ttk.Frame(content)
        btn_row.pack(fill=tk.X, pady=(4, 0))
        self._simple_mux_btn = ttk.Button(btn_row, text='\u25b6 Start Mux', command=self._start_simple_mux, width=14, cursor='hand2')
        self._simple_mux_btn.pack(side=tk.RIGHT)

    def _build_batch_translate_section(self, parent):
        card = CardFrame(parent, title=self._tr('batch_translate_title'), font_family=self._current_font)
        card.pack(fill=tk.X, pady=5)
        self._batch_translate_card = card
        content = card.content

        self._batch_translate_desc = ttk.Label(content, text=self._tr('batch_translate_desc'),
                                                font=(self._current_font, 9), foreground=self.TEXT_SECONDARY)
        self._batch_translate_desc.pack(anchor=tk.W, pady=(0, 4))

        btn_row = ttk.Frame(content)
        btn_row.pack(fill=tk.X, pady=(0, 2))

        self._batch_translate_btn = ttk.Button(
            btn_row, text=self._tr('batch_translate_btn'),
            command=self._start_batch_videos, width=14, cursor='hand2'
        )
        self._batch_translate_btn.pack(side=tk.LEFT)

        self._batch_mux_var = tk.BooleanVar(value=True)
        self._batch_mux_cb = ttk.Checkbutton(
            btn_row, text='Mux', variable=self._batch_mux_var
        )
        self._batch_mux_cb.pack(side=tk.LEFT, padx=(8, 0))

    def _browse_mux_video(self):
        f = filedialog.askopenfilename(
            title='Select Video',
            filetypes=[('Video files', '*.mkv *.mp4'), ('All files', '*.*')]
        )
        if f:
            self._mux_video_var2.set(f)

    def _browse_mux_sub(self):
        f = filedialog.askopenfilename(
            title='Select Subtitle',
            filetypes=[('Subtitle files', '*.srt *.ass'), ('All files', '*.*')]
        )
        if f:
            self._mux_sub_var2.set(f)

    def _start_simple_mux(self):
        v = self._mux_video_var2.get().strip()
        s = self._mux_sub_var2.get().strip()
        if not v or not s:
            return
        self._simple_mux_btn.config(state=tk.DISABLED)
        thread = threading.Thread(target=self._simple_mux_thread, args=(v, s), daemon=True)
        thread.start()

    def _simple_mux_thread(self, video, sub):
        if not os.path.isfile(video) or not os.path.isfile(sub):
            self.after(0, lambda: self._log(f'\u274c File not found'))
            self.after(0, lambda: self._simple_mux_btn.config(state=tk.NORMAL))
            return
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            result = Mux_Subtitle.mux_subtitle_to_video(video, sub)
        output = buf.getvalue()
        if output:
            self.after(0, lambda o=output: self._log(o.strip()))
        if result:
            self.after(0, lambda r=result: self._log(f'\u2705 Muxed: {os.path.basename(r)}'))
        else:
            self.after(0, lambda: self._log(f'\u274c Mux failed'))
        self.after(0, lambda: self._simple_mux_btn.config(state=tk.NORMAL))

    def _mux_selected(self):
        disp_video = self._mux_video_var.get()
        disp_sub = self._mux_sub_var.get()
        if not disp_video or not disp_sub:
            return
        video = next((p for p in self._mux_video_paths if os.path.basename(p) == disp_video), None)
        sub = next((p for p in self._mux_sub_paths if os.path.basename(p) == disp_sub), None)
        if not video or not sub or not os.path.isfile(video) or not os.path.isfile(sub):
            return
        self._log(self._tr('mux_muxing'))
        self._mux_btn.config(state=tk.DISABLED)
        thread = threading.Thread(target=self._mux_thread, args=(video, sub), daemon=True)
        thread.start()

    def _populate_mux_selectors(self):
        vids = []
        subs = []

        for f in self.scanned_files:
            if is_video_file(f):
                vids.append(f)
            elif f.endswith(('.ass', '.srt')):
                subs.append(f)

        if self._current_output_path and os.path.isfile(self._current_output_path):
            if self._current_output_path not in subs:
                subs.insert(0, self._current_output_path)

        if vids:
            display_vids = [os.path.basename(v) for v in vids]
            self._mux_video_combo.config(values=display_vids)
            if self._original_video_path and self._original_video_path in vids:
                idx = vids.index(self._original_video_path)
                self._mux_video_combo.current(idx)
            else:
                self._mux_video_combo.current(0)
        else:
            self._mux_video_combo.config(values=[])

        if subs:
            display_subs = [os.path.basename(s) for s in subs]
            self._mux_sub_combo.config(values=display_subs)
            if self._current_output_path and self._current_output_path in subs:
                idx = subs.index(self._current_output_path)
                self._mux_sub_combo.current(idx)
            else:
                self._mux_sub_combo.current(0)
        else:
            self._mux_sub_combo.config(values=[])

        if vids and subs:
            self._mux_btn.config(state=tk.NORMAL)
        else:
            self._mux_btn.config(state=tk.DISABLED)

        self._mux_video_paths = vids
        self._mux_sub_paths = subs

    def _build_log_section(self, parent):
        self._log_frame = ttk.LabelFrame(parent, text=self._tr('log_section'), padding=8)
        self._log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = tk.Text(self._log_frame, height=10, wrap=tk.WORD, state=tk.DISABLED,
                                font=(self._current_font, 9),
                                bg=self.CARD_BG, fg=self.TEXT_SECONDARY,
                                relief='flat', highlightthickness=1,
                                highlightcolor=self.CARD_BORDER,
                                highlightbackground=self.CARD_BORDER)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        log_scroll = ttk.Scrollbar(self.log_text, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scroll.set)

    def _on_ui_lang_change(self, event=None):
        selected_name = self._ui_lang_combo.get()
        for code, name in UI_LANG_NAMES.items():
            if name == selected_name:
                self._current_lang = code
                break
        self._update_ui_language()

    def _on_font_change(self, event=None):
        selected_font = self._font_combo.get()
        if selected_font in FONT_FAMILIES:
            self._current_font = selected_font
            self._apply_font()

    def _update_ui_language(self):
        self.title(UI_STRINGS[self._current_lang]['app_title'])
        self._header_label.config(text=self._tr('app_title'))

        self._file_card.set_title(self._tr('file_section'))
        self._dir_label.config(text=self._tr('dir_label'))
        self._browse_btn.config(text=self._tr('browse'))
        self._scan_btn.config(text=self._tr('scan'))

        self._lang_card.set_title(self._tr('lang_section'))
        self._src_label.config(text=self._tr('source'))
        self._target_label.config(text=self._tr('target'))
        self._swap_btn.config(text=self._tr('swap'))

        self._out_card.set_title(self._tr('output_section'))
        self._out_browse_btn.config(text=self._tr('browse'))

        self._engine_card.set_title(self._tr('engine_section'))
        self._engine_label.config(text=self._tr('engine_label'))
        eng_values = [self._tr('google_engine'), self._tr('llm_engine')]
        self._engine_cb.config(values=eng_values)
        current_eng = self.engine_var.get()
        if current_eng not in eng_values:
            self.engine_var.set(eng_values[0])
        self._api_key_label.config(text=self._tr('api_key'))
        self._base_url_label.config(text=self._tr('base_url'))
        self._model_label.config(text=self._tr('model'))
        self._test_btn.config(text=self._tr('test'))
        self._deepseek_btn.config(text=self._tr('deepseek'))
        self._prompt_label.config(text=self._tr('sys_prompt'))
        if not HAS_OPENAI:
            self.llm_warning.config(text=self._tr('llm_warning'))

        self._style_frame.config(text=self._tr('style_section'))
        if self._cached_styles_path is not None:
            self._rebuild_style_checkboxes()

        self._start_btn.config(text=self._tr('start'))
        self._cancel_btn.config(text=self._tr('cancel'))
        self._extract_btn.config(text=self._tr('extract_btn'))
        self._mux_cb.config(text=self._tr('mux_checkbox'))

        self._prog_card.set_title(self._tr('progress_section'))
        self._help_label.config(text=self._tr('help_text'))
        saved_status = self.status_var.get()
        if saved_status and 'Cancelled' in saved_status:
            self.status_var.set(self._tr('cancelled_status'))
        elif saved_status and 'Ready' in saved_status:
            self.status_var.set(self._tr('ready'))

        self._log_frame.config(text=self._tr('log_section'))
        self._simple_mux_card.set_title(self._tr('simple_mux_title'))
        self._mux_card.set_title(self._tr('mux_section'))
        self._batch_translate_card.set_title(self._tr('batch_translate_title'))
        self._batch_translate_desc.config(text=self._tr('batch_translate_desc'))
        self._batch_translate_btn.config(text=self._tr('batch_translate_btn'))

    def _rebuild_style_checkboxes(self):
        for w in self._style_scrollable.winfo_children():
            w.destroy()
        self.style_vars = {}

        if not self._cached_styles_info:
            return

        default = [
            s for s, i in self._cached_styles_info.items()
            if i['text'] > 0 and i['drawing'] < i['total'] * 0.5
        ]

        self._style_header_label = ttk.Label(
            self._style_scrollable, text=self._tr('select_styles'),
            font=(self._current_font, 9, 'bold')
        )
        self._style_header_label.pack(anchor=tk.W, pady=(0, 5))

        for style, info in self._cached_styles_info.items():
            var = tk.BooleanVar(value=(style in default))
            self.style_vars[style] = var
            cb_text = self._tr('style_item').format(
                style=style,
                text=info['text'],
                drawing=info['drawing'],
                total=self._tr('total_label'),
                count=info['total']
            )
            cb = ttk.Checkbutton(
                self._style_scrollable,
                text=cb_text,
                variable=var
            )
            cb.pack(anchor=tk.W, pady=1)

        self._style_frame.pack(fill=tk.BOTH, expand=True, pady=3)
        self.update_idletasks()

    def _log(self, msg):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + '\n')
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _browse_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.dir_var.set(d)
            self._scan_files()

    def _scan_files(self):
        self.file_listbox.delete(0, tk.END)
        self.scanned_files = []
        self._original_video_path = None
        self._extract_btn.config(state=tk.DISABLED)
        scan_dir = self.dir_var.get() or '.'
        for ext in ('*.ass', '*.srt'):
            self.scanned_files += glob.glob(os.path.join(scan_dir, ext))
            self.scanned_files += glob.glob(os.path.join(scan_dir, '**', ext), recursive=True)
        for ext in ('*.mkv', '*.mp4', '*.avi', '*.mov'):
            self.scanned_files += glob.glob(os.path.join(scan_dir, ext))
            self.scanned_files += glob.glob(os.path.join(scan_dir, '**', ext), recursive=True)
        self.scanned_files = list(set(self.scanned_files))
        self.scanned_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        if not self.scanned_files:
            self.file_listbox.insert(tk.END, self._tr('no_files'))
            self._log(self._tr('no_files_log'))
            return
        for f in self.scanned_files:
            size = os.path.getsize(f)
            mtime = time.strftime('%H:%M %d/%m', time.localtime(os.path.getmtime(f)))
            prefix = '🎬 ' if is_video_file(f) else '   '
            display = f"{prefix}{os.path.basename(f):45s} {size:>8,}B  {mtime}"
            self.file_listbox.insert(tk.END, display)
        self._log(self._tr('found_files').format(count=len(self.scanned_files)))

    def _on_file_select(self, event):
        sel = self.file_listbox.curselection()
        if not sel or not self.scanned_files:
            return
        idx = sel[0]
        if idx >= len(self.scanned_files):
            return
        filepath = self.scanned_files[idx]
        if not os.path.isfile(filepath):
            return
        ext = os.path.splitext(filepath)[1].lower()

        self._style_frame.pack_forget()
        self._cached_styles_path = None
        self._cached_styles_info = None

        if is_video_file(filepath):
            self._extract_btn.config(state=tk.NORMAL)
            self._original_video_path = filepath
            self._log(self._tr('video_selected_log'))
            extracted = self._handle_video_file(filepath)
            if extracted is None:
                self._original_video_path = None
                return
            filepath = extracted
            ext = os.path.splitext(filepath)[1].lower()
            self.scanned_files.insert(0, filepath)
            self.file_listbox.delete(0, tk.END)
            for f in self.scanned_files:
                size = os.path.getsize(f)
                mtime = time.strftime('%H:%M %d/%m', time.localtime(os.path.getmtime(f)))
                prefix = '🎬 ' if is_video_file(f) else '   '
                display = f"{prefix}{os.path.basename(f):45s} {size:>8,}B  {mtime}"
                self.file_listbox.insert(tk.END, display)
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(0)
            self.file_listbox.activate(0)
            out_name = f'{self.dest_lang.get()}_{LANGUAGES[self.dest_lang.get()]}'
            self.out_var.set(filepath.replace(ext, f'_{out_name}{ext}'))
            self._log(self._tr('selected_log').format(name=os.path.basename(filepath)))
            if ext == '.ass':
                self._analyze_ass_styles(filepath)
            return

        self._original_video_path = None
        self._extract_btn.config(state=tk.DISABLED)

        out_name = f'{self.dest_lang.get()}_{LANGUAGES[self.dest_lang.get()]}'
        self.out_var.set(filepath.replace(ext, f'_{out_name}{ext}'))
        if ext == '.ass':
            self._analyze_ass_styles(filepath)
        self._log(self._tr('selected_log').format(name=os.path.basename(filepath)))

    def _handle_video_file(self, video_path):
        self._log(f"🔍 Scanning subtitle streams in {os.path.basename(video_path)}...")
        streams = get_subtitle_streams(video_path)
        if not streams:
            messagebox.showerror(self._tr('select_track_error'), self._tr('select_track_error'))
            self._log(self._tr('select_track_error_log'))
            return None

        dialog = tk.Toplevel(self, bg=self.BG_LIGHT)
        dialog.title(self._tr('select_track_title'))
        dialog.geometry("600x420")
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 600) // 2
        y = (dialog.winfo_screenheight() - 420) // 2
        dialog.geometry(f"+{x}+{y}")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(True, True)

        ttk.Label(dialog, text=self._tr('select_track_header').format(name=os.path.basename(video_path)),
                  font=(self._current_font, 11, 'bold'),
                  foreground=self.ACCENT_DARK).pack(pady=12)

        frame = ttk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=8)

        listbox = tk.Listbox(frame, font=(self._current_font, 11),
                             bg='white', fg=self.TEXT_PRIMARY,
                             selectbackground=self.ACCENT_LIGHT,
                             selectforeground=self.TEXT_PRIMARY,
                             relief='flat', highlightthickness=1,
                             highlightcolor=self.CARD_BORDER,
                             highlightbackground=self.CARD_BORDER)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scroll.set)

        for idx, s in enumerate(streams):
            lang = s['language']
            title = f" - {s['title']}" if s['title'] else ""
            label = f"[{idx+1}] [{s['codec']}] {lang}{title}"
            listbox.insert(tk.END, label)

        result = {'value': None}

        def on_ok():
            sel = listbox.curselection()
            if not sel:
                return
            result['value'] = streams[sel[0]]
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, pady=12, padx=15)

        ttk.Button(btn_frame, text=self._tr('select_track_ok'), command=on_ok, width=14, cursor='hand2').pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text=self._tr('select_track_cancel'), command=on_cancel, width=14, cursor='hand2').pack(side=tk.RIGHT, padx=10)

        self.wait_window(dialog)

        selected = result['value']
        if selected is None:
            self._log("❌ No track selected.")
            return None

        out_ext = '.ass' if selected['codec'] in ('ass', 'ssa') else '.srt'
        extracted_path = video_path.rsplit('.', 1)[0] + f'_track{selected["index"]}_{selected["language"]}{out_ext}'

        self._log(f"📤 Extracting {out_ext} track #{selected['index']}...")
        self.update_idletasks()

        if not extract_subtitle(video_path, selected['index'], extracted_path):
            messagebox.showerror("Error", "Failed to extract subtitle!")
            self._log("❌ Extract failed.")
            return None

        self._log(f"✅ Extracted: {os.path.basename(extracted_path)}")
        return extracted_path

    def _extract_subtitle(self):
        sel = self.file_listbox.curselection()
        if not sel or not self.scanned_files:
            return
        idx = sel[0]
        if idx >= len(self.scanned_files):
            return
        filepath = self.scanned_files[idx]
        if not is_video_file(filepath):
            return
        self._original_video_path = filepath
        self._log(self._tr('video_selected_log'))
        extracted = self._handle_video_file(filepath)
        if extracted is None:
            self._original_video_path = None
            return
        ext = os.path.splitext(extracted)[1].lower()
        self.scanned_files.insert(0, extracted)
        self.file_listbox.delete(0, tk.END)
        for f in self.scanned_files:
            size = os.path.getsize(f)
            mtime = time.strftime('%H:%M %d/%m', time.localtime(os.path.getmtime(f)))
            prefix = '🎬 ' if is_video_file(f) else '   '
            display = f"{prefix}{os.path.basename(f):45s} {size:>8,}B  {mtime}"
            self.file_listbox.insert(tk.END, display)
        self.file_listbox.selection_clear(0, tk.END)
        self.file_listbox.selection_set(0)
        self.file_listbox.activate(0)
        out_name = f'{self.dest_lang.get()}_{LANGUAGES[self.dest_lang.get()]}'
        self.out_var.set(extracted.replace(ext, f'_{out_name}{ext}'))
        self._log(self._tr('selected_log').format(name=os.path.basename(extracted)))
        if ext == '.ass':
            self._analyze_ass_styles(extracted)

    def _analyze_ass_styles(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
        except Exception as e:
            self._log(self._tr('cannot_read_log').format(name=e))
            return

        styles_info = {}
        for line in lines:
            if not line.strip().startswith('Dialogue:'):
                continue
            prefix, text = self._parse_ass_line(line)
            if not prefix:
                continue
            style_match = re.search(r'Dialogue:\s*\d+,[^,]*,[^,]*,([^,]*),', prefix)
            style = style_match.group(1) if style_match else '(unknown)'
            if style not in styles_info:
                styles_info[style] = {'total': 0, 'drawing': 0, 'text': 0}
            styles_info[style]['total'] += 1
            if self._is_drawing(text):
                styles_info[style]['drawing'] += 1
            else:
                clean = self._clean_ass_text(text)
                if clean:
                    styles_info[style]['text'] += 1

        for w in self._style_scrollable.winfo_children():
            w.destroy()
        self.style_vars = {}

        if not styles_info:
            self._cached_styles_path = filepath
            self._cached_styles_info = None
            return

        self._cached_styles_path = filepath
        self._cached_styles_info = styles_info

        default = [
            s for s, i in styles_info.items()
            if i['text'] > 0 and i['drawing'] < i['total'] * 0.5
        ]

        self._style_header_label = ttk.Label(
            self._style_scrollable, text=self._tr('select_styles'),
            font=(self._current_font, 9, 'bold')
        )
        self._style_header_label.pack(anchor=tk.W, pady=(0, 5))

        for style, info in styles_info.items():
            var = tk.BooleanVar(value=(style in default))
            self.style_vars[style] = var
            cb_text = self._tr('style_item').format(
                style=style,
                text=info['text'],
                drawing=info['drawing'],
                total=self._tr('total_label'),
                count=info['total']
            )
            cb = ttk.Checkbutton(
                self._style_scrollable,
                text=cb_text,
                variable=var
            )
            cb.pack(anchor=tk.W, pady=1)

        self._style_frame.pack(fill=tk.BOTH, expand=True, pady=3)
        self.update_idletasks()

    def _parse_ass_line(self, line):
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

    def _is_drawing(self, text):
        stripped = text.strip()
        clean = re.sub(r'\{[^}]*\}', '', stripped).strip()
        if re.match(r'^[mblspcn]\s', clean):
            return True
        if re.search(r'\{.*\\p\d+.*\}', stripped):
            return True
        if re.match(r'^[\d\s,.\-lmbnspc]+$', clean):
            return True
        nums = len(re.findall(r'[\d\-]+', clean))
        words = len(re.findall(r'[a-zA-Z]{2,}', clean))
        if nums > 10 and (words == 0 or nums / max(words, 1) > 3):
            return True
        return False

    def _clean_ass_text(self, text):
        clean = re.sub(r'\{\\[^}]*\}', '', text)
        clean = re.sub(r'\{[^}]*\}', '', clean)
        clean = clean.replace('\\N', ' ').replace('\\n', ' ')
        return clean.strip()

    def _browse_output(self):
        f = filedialog.asksaveasfilename(
            defaultextension='.srt',
            filetypes=[('Subtitle files', '*.ass *.srt'), ('All files', '*.*')]
        )
        if f:
            self.out_var.set(f)

    def _spinner_start(self):
        self._spinner_label.config(text='')
        self._spinner_idx = 0
        self._spinner_tick()

    def _spinner_tick(self):
        if not self.running:
            return
        self._spinner_label.config(text=self._spinner_frames[self._spinner_idx])
        self._spinner_idx = (self._spinner_idx + 1) % len(self._spinner_frames)
        self._spinner_id = self.after(200, self._spinner_tick)

    def _spinner_stop(self):
        if self._spinner_id:
            self.after_cancel(self._spinner_id)
            self._spinner_id = None
        self._spinner_label.config(text='')

    def _callback(self, event, **kwargs):
        self.after(0, self._handle_event, event, kwargs)

    def _handle_event(self, event, kwargs):
        if event == 'plan':
            total = kwargs.get('total', 0)
            if total > 0:
                self.progress['maximum'] = total
            self.status_var.set(self._tr('planned').format(total=total))
            self._log(self._tr('translating_log').format(total=total))
            self._spinner_start()
        elif event == 'progress':
            current = kwargs.get('current', 0)
            total = kwargs.get('total', 0)
            start_time = kwargs.get('start_time', time.time())
            self.progress['value'] = current
            elapsed = time.time() - start_time
            if current > 0 and current < total:
                eta_secs = (elapsed / current) * (total - current)
                eta_min = int(eta_secs // 60)
                eta_sec = int(eta_secs % 60)
                eta = f"{eta_min:02d}:{eta_sec:02d}"
            else:
                eta = "00:00"
            speed = current / elapsed if elapsed > 0 else 0
            self.status_var.set(
                self._tr('progress_fmt').format(current=current, total=total, eta=eta, speed=speed)
            )
        elif event == 'done':
            total = kwargs.get('total', 0)
            elapsed = kwargs.get('elapsed', 0)
            self.progress['value'] = total
            elapsed_min = int(elapsed // 60)
            elapsed_sec = int(elapsed % 60)
            self.status_var.set(
                self._tr('complete_status').format(total=total, min=elapsed_min, sec=elapsed_sec)
            )
            self._log(
                self._tr('done_log').format(total=total, min=elapsed_min, sec=elapsed_sec)
            )
            self._finish()
            if self._mux_var.get() and self._current_output_path and os.path.isfile(self._current_output_path):
                self._start_mux()
        elif event == 'error':
            msg = kwargs.get('message', 'Unknown error')
            self.status_var.set(self._tr('error_status').format(msg=msg))
            self._log(self._tr('error_log').format(msg=msg))
            messagebox.showerror('Error', msg)
            self._finish()

    def _finish(self):
        self.running = False
        self._start_btn.config(state=tk.NORMAL)
        self._cancel_btn.config(state=tk.DISABLED)
        self._batch_translate_btn.config(state=tk.NORMAL)
        self._spinner_stop()
        self._populate_mux_selectors()

    def _start_batch_videos(self):
        scan_dir = self.dir_var.get() or '.'
        vids = []
        for ext in ('*.mkv', '*.mp4', '*.avi', '*.mov'):
            vids += glob.glob(os.path.join(scan_dir, ext))
            vids += glob.glob(os.path.join(scan_dir, '**', ext), recursive=True)
        vids = list(set(vids))
        if not vids:
            messagebox.showwarning('Batch', 'No video files found!')
            return

        valid = []
        for v in vids:
            streams = get_subtitle_streams(v)
            if streams:
                valid.append((v, streams))
        if not valid:
            messagebox.showwarning('Batch', 'No videos with subtitle streams found!')
            return

        src = LANGUAGES.get(self.src_lang.get(), 'en')
        dest = LANGUAGES.get(self.dest_lang.get(), 'vi')
        if src == dest:
            messagebox.showwarning('Batch', 'Source and target languages are the same.')
            return

        use_llm = self.engine_var.get() == self._tr('llm_engine')
        if use_llm and not self.api_key_var.get().strip():
            messagebox.showwarning('Batch', 'Enter API key for LLM mode.')
            return

        # Confirm with user
        msg = f'Found {len(valid)} videos with subtitles.\n\n'
        for idx, (v, _) in enumerate(valid, 1):
            msg += f'  {idx}. {os.path.basename(v)}\n'
        msg += f'\nTranslate {src} → {dest}'
        if not messagebox.askyesno('Batch Translate Videos', msg):
            return

        self.running = True
        self._start_btn.config(state=tk.DISABLED)
        self._cancel_btn.config(state=tk.NORMAL)
        self._batch_translate_btn.config(state=tk.DISABLED)
        self.progress['value'] = 0
        self.progress['maximum'] = len(valid)
        self.status_var.set(f'Batch: 0/{len(valid)} videos')
        self._log(f'🎬 Batch translate: {len(valid)} videos, {src} → {dest}')
        self._spinner_start()

        thread = threading.Thread(
            target=self._batch_videos_thread,
            args=(valid, src, dest, use_llm),
            daemon=True
        )
        thread.start()

    def _batch_videos_thread(self, valid, src, dest, use_llm):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            import shutil
            success = 0
            total_videos = len(valid)
            for idx, (video_path, streams) in enumerate(valid, 1):
                vname = os.path.basename(video_path)
                self.after(0, lambda i=idx, t=total_videos: self.progress.configure(value=i, maximum=t))
                self.after(0, lambda i=idx, t=total_videos, n=vname:
                    self.status_var.set(f'Batch: {i}/{t} — {n}'))

                sel_stream = streams[0]
                out_ext = '.ass' if sel_stream['codec'] in ('ass', 'ssa') else '.srt'
                extracted_path = video_path.rsplit('.', 1)[0] + f'_batch{sel_stream["index"]}_{sel_stream["language"]}{out_ext}'

                self.after(0, lambda n=vname: self._log(f'📤 Extracting subtitles from {n}...'))
                if not extract_subtitle(video_path, sel_stream['index'], extracted_path):
                    self.after(0, lambda n=vname: self._log(f'❌ Extract failed: {n}'))
                    continue

                self.after(0, lambda n=vname: self._log(f'🌐 Translating {n}...'))

                if out_ext == '.ass':
                    total, elapsed = loop.run_until_complete(
                        Subtitle_Translator.translate_ass(
                            extracted_path, extracted_path, src, dest,
                            batch_idx=idx, batch_total=total_videos,
                            translate_styles=[]
                        )
                    )
                else:
                    total, elapsed = loop.run_until_complete(
                        Subtitle_Translator.translate_srt(
                            extracted_path, extracted_path, src, dest,
                            batch_idx=idx, batch_total=total_videos
                        )
                    )

                do_mux = self._batch_mux_var.get()
                if do_mux:
                    self.after(0, lambda n=vname: self._log(f'🎬 Muxing subtitle into {n}...'))
                    lang_name = LANG_NAMES.get(dest, dest)
                    muxed = Mux_Subtitle.mux_subtitle_to_video(video_path, extracted_path, lang_code=dest, lang_name=lang_name)
                    if muxed:
                        success += 1
                        self.after(0, lambda n=vname: self._log(f'✅ Done: {n}'))
                    else:
                        self.after(0, lambda n=vname: self._log(f'❌ Mux failed: {n}'))
                    if os.path.isfile(extracted_path):
                        try:
                            os.remove(extracted_path)
                        except OSError:
                            pass
                else:
                    lang_name = LANG_NAMES.get(dest, dest)
                    saved_path = video_path.rsplit('.', 1)[0] + f'_{lang_name}_{dest}.{out_ext}'
                    try:
                        shutil.copy2(extracted_path, saved_path)
                        os.remove(extracted_path)
                        self.after(0, lambda n=os.path.basename(saved_path):
                            self._log(f'✅ Saved: {n}'))
                    except OSError:
                        self.after(0, lambda n=vname:
                            self._log(f'❌ Failed to save subtitle: {n}'))
                    success += 1

                self.after(0, lambda i=idx, t=total_videos:
                    self.progress.configure(value=i, maximum=t))
                self.after(0, lambda s=success, i=idx, t=total_videos:
                    self.status_var.set(f'✅ Batch: {s}/{t} videos done'))

            self.after(0, lambda s=success, t=total_videos: self._log(f'✅ Batch complete: {s}/{t} videos'))
            self.after(0, lambda s=success, t=total_videos:
                messagebox.showinfo('Batch Complete', f'✅ Finished!\n\nSuccess: {s}/{t} videos'))
            self.after(0, lambda: self._finish())
        except Exception as e:
            self.after(0, lambda e=e: self._log(f'❌ Batch error: {e}'))
            self.after(0, lambda: self._finish())
        finally:
            loop.close()

    def _toggle_mux(self, event=None):
        self._mux_var.set(not self._mux_var.get())
        self._mux_checkbox_icon.config(
            text='\u2611' if self._mux_var.get() else '\u2610',
            fg=self.ACCENT if self._mux_var.get() else self.TEXT_SECONDARY
        )

    def _start_mux(self):
        video_path = self._original_video_path
        subtitle_path = self._current_output_path
        if subtitle_path and os.path.isfile(subtitle_path):
            lang_name = self.dest_lang.get()
            lang_code = LANGUAGES.get(lang_name, 'vi')
            if video_path and os.path.isfile(video_path):
                self._log(self._tr('mux_muxing'))
                thread = threading.Thread(target=self._mux_thread, args=(video_path, subtitle_path, lang_code, lang_name), daemon=True)
                thread.start()
            else:
                self.after(0, lambda: self._show_mux_video_dialog(subtitle_path, lang_code, lang_name))

    def _mux_thread(self, video_path, subtitle_path, lang_code='vi', lang_name='Vietnamese'):
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            result = Mux_Subtitle.mux_subtitle_to_video(video_path, subtitle_path, lang_code=lang_code, lang_name=lang_name)
        output = buf.getvalue()
        if output:
            self.after(0, lambda: self._log(output.strip()))
        if result:
            self.after(0, lambda: self._log(self._tr('mux_success').format(name=os.path.basename(result))))
            self.after(0, self._populate_mux_selectors)
        else:
            self.after(0, lambda: self._log(self._tr('mux_fail')))
            self.after(0, lambda: self._mux_btn.config(state=tk.NORMAL))

    def _show_mux_video_dialog(self, subtitle_path, lang_code='vi', lang_name='Vietnamese'):
        vids = Mux_Subtitle.scan_video_files(self.dir_var.get() or '.')
        if not vids:
            messagebox.showinfo(self._tr('mux_choose_title'), self._tr('mux_no_video'))
            self._log(self._tr('mux_no_video_log'))
            return

        dialog = tk.Toplevel(self, bg=self.BG_LIGHT)
        dialog.title(self._tr('mux_choose_title'))
        dialog.geometry("500x350")
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 500) // 2
        y = (dialog.winfo_screenheight() - 350) // 2
        dialog.geometry(f"+{x}+{y}")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(True, True)

        ttk.Label(dialog, text=self._tr('mux_choose_header'),
                  font=(self._current_font, 11, 'bold'),
                  foreground=self.ACCENT_DARK).pack(pady=12)

        frame = ttk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=8)

        listbox = tk.Listbox(frame, font=(self._current_font, 11),
                             bg='white', fg=self.TEXT_PRIMARY,
                             selectbackground=self.ACCENT_LIGHT,
                             selectforeground=self.TEXT_PRIMARY,
                             relief='flat', highlightthickness=1,
                             highlightcolor=self.CARD_BORDER,
                             highlightbackground=self.CARD_BORDER)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scroll.set)

        for idx, v in enumerate(vids):
            listbox.insert(tk.END, f"[{idx+1}] {os.path.basename(v)}")

        result = {'value': None}

        def on_ok():
            sel = listbox.curselection()
            if not sel:
                return
            result['value'] = vids[sel[0]]
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, pady=12, padx=15)

        ttk.Button(btn_frame, text=self._tr('mux_ok'), command=on_ok, width=14, cursor='hand2').pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text=self._tr('mux_cancel'), command=on_cancel, width=14, cursor='hand2').pack(side=tk.RIGHT, padx=10)

        self.wait_window(dialog)

        selected = result['value']
        if selected is None:
            self._log(self._tr('mux_cancelled_log'))
            return

        self._log(self._tr('mux_muxing'))
        thread = threading.Thread(target=self._mux_thread, args=(selected, subtitle_path, lang_code, lang_name), daemon=True)
        thread.start()

    def _start_translation(self):
        sel = self.file_listbox.curselection()
        if not sel or not self.scanned_files:
            messagebox.showwarning(self._tr('no_file_title'), self._tr('no_file_msg'))
            return
        idx = sel[0]
        if idx >= len(self.scanned_files):
            return
        input_file = self.scanned_files[idx]
        ext = os.path.splitext(input_file)[1].lower()

        src = LANGUAGES.get(self.src_lang.get(), 'en')
        dest = LANGUAGES.get(self.dest_lang.get(), 'vi')

        if src == dest:
            messagebox.showwarning(
                self._tr('swap'),
                self._tr('same_lang_msg').format(lang=self.src_lang.get())
            )
            return

        out = self.out_var.get().strip()
        if not out:
            out_name = f'{self.dest_lang.get()}_{dest}'
            out = input_file.replace(ext, f'_{out_name}{ext}')
            self.out_var.set(out)

        if os.path.exists(out):
            if not messagebox.askyesno(
                self._tr('overwrite_title'),
                self._tr('overwrite_msg').format(name=os.path.basename(out))
            ):
                return

        selected_styles = None
        if ext == '.ass' and self.style_vars:
            selected_styles = [s for s, v in self.style_vars.items() if v.get()]
            if not selected_styles:
                messagebox.showwarning(self._tr('no_style_title'), self._tr('no_style_msg'))
                return

        use_llm = self.engine_var.get() == self._tr('llm_engine')
        llm_config = None
        if use_llm:
            api_key = self.api_key_var.get().strip()
            if not api_key:
                messagebox.showwarning(self._tr('missing_key_title'), self._tr('missing_key_msg'))
                return
            llm_config = {
                'api_key': api_key,
                'base_url': self.base_url_var.get().strip() or DEFAULT_LLM_BASE_URL,
                'model': self.model_var.get().strip() or DEFAULT_LLM_MODEL,
                'system_prompt': self.prompt_text.get('1.0', 'end-1c').strip() or DEFAULT_SYSTEM_PROMPT,
            }

        self.running = True
        self._start_btn.config(state=tk.DISABLED)
        self._cancel_btn.config(state=tk.NORMAL)
        self._mux_btn.config(state=tk.DISABLED)
        self.progress['value'] = 0
        self._current_output_path = out
        engine_name = self._tr('llm_engine') if use_llm else self._tr('google_engine')
        self.status_var.set(self._tr('starting_fmt').format(engine=engine_name))
        self._log(self._tr('engine_log').format(engine=engine_name))
        self._log(self._tr('translating_log_fmt').format(name=os.path.basename(input_file)))
        self._log(
            self._tr('format_log_fmt').format(
                ext=ext.upper(),
                src=self.src_lang.get(),
                dest=self.dest_lang.get()
            )
        )
        self._log(self._tr('output_log_fmt').format(name=os.path.basename(out)))

        self.translator = AsyncTranslator(self._callback, use_llm=use_llm, llm_config=llm_config)
        self.translator.run_translate(input_file, out, src, dest, selected_styles)

    def _cancel_translation(self):
        if self.translator:
            self.translator.cancel()
        self.status_var.set(self._tr('cancelled_status'))
        self._log(self._tr('cancelled_log'))
        self._finish()

    def _on_engine_change(self, event=None):
        if self.engine_var.get() == self._tr('llm_engine'):
            if not HAS_OPENAI:
                messagebox.showwarning(
                    self._tr('missing_dep_title'),
                    self._tr('missing_dep_msg')
                )
                self.engine_var.set(self._tr('google_engine'))
                return
            self.llm_frame.pack(fill=tk.X, pady=(5, 0))
        else:
            self.llm_frame.pack_forget()

    def _toggle_api_key(self):
        for w in self.llm_frame.winfo_children():
            for child in w.winfo_children():
                if isinstance(child, ttk.Entry) and child.cget('show') == '*':
                    child.config(show='')
                    self.show_key_btn.config(text='\U0001f648')
                    return
                elif isinstance(child, ttk.Entry) and child.cget('show') == '':
                    child.config(show='*')
                    self.show_key_btn.config(text='\U0001f441')
                    return

    async def _test_llm_async(self, client, model):
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Reply with just: OK"}],
            max_tokens=10
        )
        return response.choices[0].message.content.strip()

    def _test_llm(self):
        api_key = self.api_key_var.get().strip()
        base_url = self.base_url_var.get().strip()
        model = self.model_var.get().strip()

        if not api_key:
            self.llm_status_var.set(self._tr('llm_enter_key'))
            return
        if not model:
            self.llm_status_var.set(self._tr('llm_enter_model'))
            return

        self.llm_status_var.set(self._tr('llm_testing'))
        self.update_idletasks()

        def test_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                client = openai.AsyncClient(api_key=api_key, base_url=base_url)
                result = loop.run_until_complete(self._test_llm_async(client, model))
                self.after(0, lambda: self.llm_status_var.set(
                    self._tr('llm_connected').format(response=result)
                ))
            except openai.AuthenticationError:
                self.after(0, lambda: self.llm_status_var.set(self._tr('llm_invalid_key')))
            except openai.NotFoundError:
                self.after(0, lambda: self.llm_status_var.set(
                    self._tr('llm_model_not_found').format(model=model)
                ))
            except Exception as e:
                msg = str(e)[:60]
                self.after(0, lambda: self.llm_status_var.set(
                    self._tr('llm_error').format(msg=msg)
                ))
            finally:
                loop.close()

        thread = threading.Thread(target=test_thread, daemon=True)
        thread.start()

    def _set_deepseek(self):
        self.base_url_var.set("https://api.deepseek.com/v1")
        self.model_var.set("deepseek-chat")
        self.engine_var.set(self._tr('llm_engine'))
        self._on_engine_change()
        self.llm_status_var.set(self._tr('llm_deepseek_applied'))


if __name__ == '__main__':
    app = SubtitleTranslatorGUI()
    app.mainloop()
