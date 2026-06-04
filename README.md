# 🎬 Subtitle Translator

Công cụ dịch phụ đề `.ass` / `.srt` tự động — hỗ trợ Google Dịch và các engine LLM (OpenAI, DeepSeek).  
Giao diện đồ họa (GUI) đa ngôn ngữ: 🇬🇧 English, 🇻🇳 Tiếng Việt, 🇨🇳 中文, 🇯🇵 日本語, 🇰🇷 한국어.

---

## ✨ Tính năng

- Dịch phụ đề `.ass` và `.srt` qua **Google Translate** hoặc **LLM (AI)**
- Chọn **Style** ASS để chỉ dịch các dòng thuộc kiểu mong muốn
- Giao diện **đa ngôn ngữ** (En / Vi / 中文 / 日本語 / 한국어)
- Hỗ trợ nhiều engine dịch: Google Translate, OpenAI, DeepSeek, API tương thích OpenAI
- Theme hiện đại, bo góc, dễ sử dụng
- Chạy CLI cho xử lý hàng loạt

---

## 📦 Yêu cầu

- **Python 3.8+** ([tải tại python.org](https://python.org))
- Các thư viện Python trong `requirements.txt`

## 🚀 Cài đặt

```bash
# Clone repo
git clone https://github.com/Bkhangg/Subtitle_Translator_by_google.git
cd Subtitle_Translator_by_google

# Cài thư viện
pip install -r requirements.txt
```

## ▶️ Cách chạy

**GUI** (khuyên dùng):
```bash
python subtitle_translator_gui.py
```

**CLI**:
```bash
python Subtitle_Translator.py
```

## 🖥️ Hướng dẫn sử dụng GUI

1. **Chọn thư mục** chứa file phụ đề → nhấn **Scan**
2. **Chọn file** từ danh sách
3. **Chọn ngôn ngữ nguồn và đích**
4. **Chọn engine** dịch:
   - **Google Dịch**: dùng ngay, không cần cấu hình
   - **LLM (AI)**: cần nhập API Key (OpenAI / DeepSeek / tương thích OpenAI)
5. Nhấn **🚀 Start Translation**
6. Theo dõi tiến trình ở cột phải

## 🧩 Cấu trúc project

```
├── subtitle_translator_gui.py     # Giao diện đồ họa (GUI)
├── Subtitle_Translator.py         # Giao diện dòng lệnh (CLI)
├── requirements.txt               # Thư viện Python cần thiết
├── screenshots/                   # Ảnh minh họa
│   ├── Subtitle_Translator_GUI_OaWy1SFhoj.png
│   └── WindowsTerminal_iNt0DTeF8E.png
└── README.md
```

## 📸 Ảnh minh họa

![Giao diện GUI](screenshots/python_poqiwX0XHZ.png)  
*Giao diện GUI chính*

![Dịch CLI](screenshots/WindowsTerminal_iNt0DTeF8E.png)  
*Quá trình dịch bằng CLI*

---

## 🔑 API Keys (cho LLM)

Tạo file `api.txt` trong thư mục gốc, mỗi dòng một key:

```
sk-your-openai-key-here
sk-your-deepseek-key-here
```

Hoặc nhập trực tiếp trong GUI.

## 📄 Giấy phép

MIT
