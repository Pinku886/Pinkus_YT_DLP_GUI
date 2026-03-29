# 🔴 Troubleshooting Guide - Pinkus YT-DLP GUI

This guide summarizes common errors and their solutions for the **Pinkus YT-DLP GUI**.

---

## 🕒 Table of Contents
1.  [403 Forbidden / Bot Detection](#-403-forbidden--bot-detection)
2.  [Sign-in to confirm you're not a bot](#-sign-in-to-confirm-youre-not-a-bot)
3.  [FFmpeg Missing / Not Found](#-ffmpeg-missing--not-found)
4.  [Slow Download Speeds](#-slow-download-speeds)
5.  [Age-Restricted Content](#-age-restricted-content)

---

## 🚫 403 Forbidden / Bot Detection
**Problem**: You get an error stating `ERROR: [youtube] 403: Forbidden`.

**Solutions**:
1.  **Browser Cookies**: Select `chrome` or `firefox` from the **Browser Cookies** dropdown. The app will extract your session cookies to prove you are a human.
2.  **Toggle VPN/Proxy**: Sometimes YouTube blocks specific IP ranges. Try switching your VPN server.
3.  **Update Tool**: Click **"🚀 Update Tool"** to ensure your `yt-dlp.exe` is the latest version. YouTube often changes its encryption, and the update fixes it.

---

## 🛡️ Sign-in to confirm you're not a bot
**Problem**: The log states `ERROR: [youtube] Sign in to confirm you're not a bot`.

**Solutions**:
1.  **Manual Cookies**: 
    - Install the [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) extension for Chrome/Edge.
    - Go to YouTube, login, and export `cookies.txt`.
    - In the GUI, browse and select this file in the **Custom Cookies.txt** field.
2.  **Clear Cache**: Click **"🧹 Clear Cache"** to remove any old session data.

---

## 📦 FFmpeg Missing / Not Found
**Problem**: High-quality 4K/1080p downloads fail, or merging doesn't work.

**Solutions**:
1.  **The Fix**: On first run, the app asks to download FFmpeg. If you missed it, delete `ffmpeg.exe` and `ffprobe.exe` from the folder and restart the app.
2.  **Manual Download**: If auto-download fails, download [**FFmpeg Essentials**](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip) and place `ffmpeg.exe` in the same folder as the GUI.

---

## ⚡ Slow Download Speeds
**Problem**: Downloads are stuck at KB/s or very low speeds.

**Solutions**:
1.  **DASH Formats**: Ensure **"Advanced Formats"** are used. `yt-dlp` works best when combining video and audio streams rather than downloading single-file formats.
2.  **Region**: Some regions have throttled traffic. Use a VPN to a closer server.
3.  **Clear Cache**: Use the **"🧹 Clear Cache"** button.

---

## 📵 Age-Restricted Content
**Problem**: You cannot download videos marked as 18+.

**Solutions**:
1.  **Must Use Cookies**: You *must* use cookies (Browser or File) to download age-restricted content. The app can only see what you can see in your browser.
2.  **Verified Account**: Ensure you are logged into a YouTube account that has verified its age.

---

### Need Further Help?
- Refer to [**User Guide**](USER_GUIDE.md) for feature explanations.
- Refer to [**Developer Guide**](DEVELOPER_GUIDE.md) for technical setup.
