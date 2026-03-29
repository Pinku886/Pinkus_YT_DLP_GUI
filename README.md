# <img src="app_logo.png" width="48" align="center"> Pinkus YT-DLP GUI

![Project Banner](project_banner.png)

A high-performance, **premium graphical interface** for `yt-dlp`, meticulously crafted for reliability, speed, and ease of use. This tool is designed to bypass modern bot detection, provide deep control over media streams, and offer a truly **portable, self-contained** experience.

---

## ✨ Features That Stand Out

*   **⚡ Smart Batch Engine**: Add hundreds of URLs. The app reviews metadata, caches results locally, and lets you customize *each* item before downloading.
*   **🛡️ Bot-Bypassing Logic**: Intelligent cookie management and client spoofing to avoid `403 Forbidden` and `Sign-in required` errors.
*   **📦 Zero-Install Portability**: Self-downloads its own `yt-dlp.exe` and `ffmpeg.exe` engines, making it run perfectly from a USB drive.
*   **🎬 Stream-Level Control**: Manually select specific video resolutions, audio codecs (AV1, VP9, H264), and bitrates.
*   **🖼️ Thumbnail Mastery**: Support for high-quality `WebP` thumbnails and automatic embedding.
*   **📜 History Tracking**: Keeps a searchable log of your last 500 downloads with direct "Open Folder" access.
*   **🔴 Smart Diagnosis**: Integrated error tracker that suggests specific fixes for common download failures.

---

## 🚀 Quick Start (Normal Usage)

1.  **Run the App**: Launch `Pinkus_YT_DLP_GUI.exe` (or run `yt_dlp_gui.py`).
2.  **Paste URL**: Drop your YouTube/Vimeo/Twitch link in the box.
3.  **Download**: Click **"Start Download"**.
    *   *Note: On the first run, the app will offer to download FFmpeg automatically. Say **Yes** for high-quality video merging.*

---

## 🛠️ Installation (Developers / Python Users)

**Requirements**:
- **Python 3.10+** (Recommend 3.11 for performance)
- **FFmpeg** (Managed automatically by the app)

**Setup**:
```powershell
# Clone the repository (or download source)
git clone https://github.com/Pinku886/Pinkus_YT_DLP_GUI.git

# Install one requirement
pip install customtkinter
```

**Run**:
```powershell
python yt_dlp_gui.py
```

---

## 📖 Detailed Guides

| Guide | Description |
| :--- | :--- |
| [**User Guide**](USER_GUIDE.md) | How to use Batch mode, Time Range, and Format selection. |
| [**Developer Guide**](DEVELOPER_GUIDE.md) | How to build the EXE and modify the code. |
| [**Troubleshooting**](TROUBLESHOOTING.md) | Fixing `403` errors, Cookies, and dependency issues. |

---

## 🛡️ License & Acknowledgements

Created with ❤️ by **Pinku**.  
Powered by the incredible [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter).

*Disclaimer: This tool is intended for personal use and downloading content you have the right to access. Please respect the terms of service of the content platforms you use.*
