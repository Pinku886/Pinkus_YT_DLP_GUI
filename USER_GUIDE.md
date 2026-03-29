# 📖 User Guide - Pinkus YT-DLP GUI

Welcome to the definitive manual for the **Pinkus YT-DLP GUI**. This guide covers everything from basic downloads to advanced batch processing.

---

## 🕒 Table of Contents
1.  [Single Video Download](#-single-video-download)
2.  [Batch Video Download](#-batch-video-download)
3.  [Manual Format Selection](#-manual-format-selection)
4.  [Time Range Trimming](#-time-range-trimming)
5.  [Metadata Caching & History](#-metadata-caching--history)

---

## 🎯 Single Video Download
The **Main Download** tab is designed for quick, high-quality fetches.

1.  **Paste URL**: Insert your video link (Youtube, Twitch, Vimeo, etc.).
2.  **Select Quality**: Choose from `Best (Auto)`, `4K`, `1080p`, etc. 
    *   *Note: Real-time file size estimates will appear next to the resolution.*
3.  **Choose Output**: Browse and select where to save your file.
4.  **Download Specific Format**: Select `mp4` or `mkv` for video, or `mp3` for audio-only.
5.  **Click Start Download**: Watch the progress bar and real-time logs.

---

## 📦 Batch Video Download
Download hundreds of videos at once with total control.

1.  **Paste Bulk URLs**: Insert multiple URLs into the large text area (one per line).
2.  **Review Metadata**: Click **"Start Batch"**. The app will fetch info for *every* video first.
3.  **The Review Window**: A popup will appear showing all items.
    *   **Edit**: Click to change the quality for *that specific* video only.
    *   **Expand Playlists**: If a link is a playlist, the app will offer to expand it into individual videos.
4.  **Process**: Click "Start Processing" to begin the sequential download.

---

## 🎬 Manual Format Selection
Sometimes you want a specific video and audio stream (e.g., AV1 video + Opus audio).

1.  Paste your URL in the **Main Download** tab.
2.  Click the **"📋 Formats"** button.
3.  A window will open listing *all* available streams from the site's server.
4.  Pick precisely what you want and click "Download Selection".

---

## ✂️ Time Range Trimming
Need only a 30-second clip from a 2-hour livestream?

1.  Enable the **"Download Specific Time Range"** checkbox.
2.  Enter the **Start** and **End** times (HH:MM:SS format).
3.  Start the download. **Note**: This requires **FFmpeg** (installed automatically).
    *   *Tip: This is extremely fast and lossless for most formats.*

---

## 🛡️ Anti-Bot & Cookies
If you encounter **"Sign in to confirm you're not a bot"** or **"403 Forbidden"**:

1.  **Browser Cookies**: From the dropdown, select the browser you normally use (e.g., `chrome`, `firefox`). The app will securely extract your session cookies.
2.  **Custom Cookies**: If you have a `cookies.txt` file (Netscape format), browse and select it manually.
3.  **Update Tool**: Click the **"🚀 Update Tool"** button to ensure you have the latest `yt-dlp` fixes.

---

## 📜 Metadata Caching & History
- **Caching**: The app caches video info locally. If you re-add the same URL (even in a batch), it loads *instantly* without a second network trip.
- **History**: Click the **"📜 History"** button at the top to see your last 500 successful downloads. Clicking "Open Folder" takes you directly to the file.

---

### Need Help?
- Check the [**Troubleshooting Guide**](TROUBLESHOOTING.md) for error fixes.
- Refer to [**Developer Guide**](DEVELOPER_GUIDE.md) for technical setup.
