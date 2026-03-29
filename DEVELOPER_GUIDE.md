# 🛠️ Developer Guide - Pinkus YT-DLP GUI

This guide provides technical instructions for setting up the development environment, modifying the code, and packaging the application for Windows.

---

## 🏗️ Project Architecture Overview

| File | Description |
| :--- | :--- |
| **`yt_dlp_gui.py`** | The main application logic and UI (CustomTkinter). Handles threading, downloads, and events. |
| **`config_manager.py`** | Manages `app_config.json`, project settings, and the download history (`history.json`). |
| **`error_tracker.py`** | Intelligent error parsing. Maps raw `yt-dlp` errors to human-readable suggestions. |
| **`Pinkus_YT_DLP_GUI.spec`** | The PyInstaller configuration file used to bundle the app into an `.exe`. |

---

## 🛠️ Environment Setup

### 1. Requirements
- **Python 3.10+** (Recommend 3.11 for performance)
- **Pip** (Standard Python package manager)

### 2. Install Dependencies
The GUI requires `customtkinter` for its modern theme.
```powershell
pip install customtkinter
```

### 3. External Binaries
The app manages its own binaries (`yt-dlp.exe` and `ffmpeg.exe`). 
- On development runs: If not present, the app will download them to its root directory.
- For packaging: These binaries are usually *not* bundled inside the EXE (to keep the size small), but rather downloaded on the user's first run.

---

## 📦 Packaging to Windows (.exe)

Use **PyInstaller** to create a standalone executable.

### 1. Install PyInstaller
```powershell
pip install pyinstaller
```

### 2. Identify CustomTkinter Path
`customtkinter` requires its theme files to be included. Find the installation path:
- **Typical Path**: `C:\Users\<User>\AppData\Local\Programs\Python\Python31x\Lib\site-packages\customtkinter`

### 3. Build Command
Run the following from the project root. **Replace the path** with your actual `customtkinter` folder.

```powershell
pyinstaller --noconfirm --onefile --windowed --add-data "C:/Users/%USERNAME%/AppData/Local/Programs/Python/Python311/Lib/site-packages/customtkinter;customtkinter/" --name "Pinkus_YT_DLP_GUI" --icon "app_icon.ico" yt_dlp_gui.py
```

- `--onefile`: Bundles everything into a single `.exe`.
- `--windowed`: Suppresses the command prompt window.
- `--add-data`: Vital for carrying over the `customtkinter` theme.

---

## 🔄 Updating Source
- **Dependency Management**: If you add new Python libraries, update the README's installation section.
- **Binary Updates**: The app's built-in `Update Tool` button handles fetching the latest `yt-dlp.exe` without needing a re-build.

---

### Need Further Assistance?
- Refer to [**User Guide**](USER_GUIDE.md) for feature explanations.
- Refer to [**Troubleshooting**](TROUBLESHOOTING.md) for known bugs and fixes.
