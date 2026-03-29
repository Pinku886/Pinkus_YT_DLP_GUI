import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import threading
import os
import sys
import re
import urllib.request
import zipfile
import shutil
import json
from error_tracker import ErrorTracker
from config_manager import ConfigManager
import re

# Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class YtDlpGui(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Pinku's YT-DLP GUI")
        self.geometry("900x700")

        # Data
        self.output_dir = ctk.StringVar(value=os.path.expanduser("~\\Downloads"))
        self.browsers = ["None", "chrome", "firefox", "edge", "opera", "brave", "vivaldi", "chromium"]
        self.video_qualities = ["None", "Best", "4K (2160p)", "2K (1440p)", "1080p", "720p", "480p", "360p", "Audio Only"]
        self.file_formats = ["None", "mp4", "mkv", "webm", "flv", "avi"]
        self.subtitle_options = ["None", "Original Only", "Auto-Generated Only", "Both"]
        self.thumbnail_options = ["None", "webp", "jpg", "png"]
        self.cookies_file_path = ctk.StringVar(value="")
        
        # Time Range Variables
        self.time_range_active = ctk.BooleanVar(value=False)
        self.start_h = ctk.StringVar(value="00")
        self.start_m = ctk.StringVar(value="00")
        self.start_s = ctk.StringVar(value="00")
        self.end_h = ctk.StringVar(value="00")
        self.end_m = ctk.StringVar(value="00")
        self.end_s = ctk.StringVar(value="00")
        
        # Batch download tracking
        self.batch_urls = []
        self.batch_current_index = 0
        self.batch_in_progress = False
        
        # Error tracker
        self.error_tracker = ErrorTracker()
        
        # Process tracking
        self.current_process = None
        self.skip_requested = False
        
        # Configuration & Session Manager
        self.config_manager = ConfigManager()
        
        # Help messages list
        self.help_labels = []

        # Load persisted settings
        self.load_settings()

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Tabview should expand, not top frame
        self.grid_rowconfigure(0, weight=0)

        self._create_widgets()
        
        # Check for portable binaries AFTER widgets are created
        self.after(500, self.check_and_install_binaries)
        
        # Maximize window after everything is loaded
        self.after(100, lambda: self.state('zoomed'))
        
        # Save settings on close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Load last session logs
        self.after(1000, self.load_last_session_logs)

    def check_and_install_binaries(self):
        """Check for local binaries and download if missing"""
        # Portable mode: Binaries in the same folder as the script/exe
        app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        ytdlp_path = os.path.join(app_dir, "yt-dlp.exe")
        ffmpeg_path = os.path.join(app_dir, "ffmpeg.exe")
        
        missing = []
        if not os.path.exists(ytdlp_path): missing.append("yt-dlp")
        if not os.path.exists(ffmpeg_path): missing.append("ffmpeg")
        
        if not missing:
            return # All good
            
        # Ask user to download
        msg = "Missing portable binaries:\n" + "\n".join(missing) + "\n\nDownload them now for a fully portable experience?"
        if not messagebox.askyesno("Portable Binaries", msg):
            return

        # Progress Window
        progress_win = ctk.CTkToplevel(self)
        progress_win.title("Downloading Binaries...")
        progress_win.geometry("400x150")
        progress_win.attributes("-topmost", True)
        
        lbl = ctk.CTkLabel(progress_win, text="Starting download...", font=("Roboto", 13))
        lbl.pack(pady=20)
        
        bar = ctk.CTkProgressBar(progress_win, width=300)
        bar.pack(pady=10)
        bar.set(0)
        
        def download_thread():
            try:
                def report_progress(count, block_size, total_size):
                    if total_size > 0:
                        percent = (count * block_size) / total_size
                        if percent > 1.0: percent = 1.0
                        self.after(0, lambda p=percent: bar.set(p))
                
                # 1. yt-dlp
                if "yt-dlp" in missing:
                    self.after(0, lambda: [lbl.configure(text="Downloading yt-dlp.exe..."), bar.set(0)])
                    url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
                    urllib.request.urlretrieve(url, ytdlp_path, reporthook=report_progress)
                
                # 2. ffmpeg
                if "ffmpeg" in missing:
                    self.after(0, lambda: [lbl.configure(text="Downloading FFmpeg (Large file)..."), bar.set(0)])
                    # Use a reliable build (gyan.dev)
                    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
                    zip_path = os.path.join(app_dir, "ffmpeg.zip")
                    
                    urllib.request.urlretrieve(url, zip_path, reporthook=report_progress)
                    
                    self.after(0, lambda: [lbl.configure(text="Extracting FFmpeg..."), bar.configure(mode="indeterminate"), bar.start()])
                    
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        # Find the ffmpeg.exe inside the zip (it's usually in a subfolder)
                        for file in zip_ref.namelist():
                            if file.endswith("bin/ffmpeg.exe"):
                                target = open(ffmpeg_path, "wb")
                                target.write(zip_ref.read(file))
                                target.close()
                            elif file.endswith("bin/ffprobe.exe"):
                                target = open(os.path.join(app_dir, "ffprobe.exe"), "wb")
                                target.write(zip_ref.read(file))
                                target.close()
                                
                    try: os.remove(zip_path)
                    except: pass

                self.after(0, lambda: [progress_win.destroy(), messagebox.showinfo("Success", "Binaries downloaded successfully!")])
                
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda: [progress_win.destroy(), messagebox.showerror("Download Error", err_msg)])
        
        threading.Thread(target=download_thread, daemon=True).start()

    def _create_widgets(self):
        # Top frame for title and error/info buttons
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="ew")
        top_frame.grid_columnconfigure(0, weight=1)
        
        # Main Title in Top Frame
        self.main_title = ctk.CTkLabel(top_frame, text="Pinku's YT-DLP GUI", 
                                       font=("Roboto", 24, "bold"))
        self.main_title.grid(row=0, column=0, sticky="w")
        
        # Top Row Buttons
        self.update_btn = ctk.CTkButton(top_frame, text="🚀 Update Tool", 
                                   command=self.update_tools, width=120, height=32,
                                   fg_color="#059669", hover_color="#047857")
        self.update_btn.grid(row=0, column=1, padx=(0, 10))
        
        self.clear_cache_btn = ctk.CTkButton(top_frame, text="🧹 Clear Cache", 
                                        command=self.clear_ytdlp_cache, width=120, height=32,
                                        fg_color="#334155", hover_color="#475569")
        self.clear_cache_btn.grid(row=0, column=2, padx=(0, 10))
        
        self.error_btn = ctk.CTkButton(top_frame, text="🔴 Errors (0)", 
                                       command=self.show_error_dialog, width=120, height=32,
                                       fg_color="#dc2626", hover_color="#991b1b")
        self.error_btn.grid(row=0, column=3, padx=(0, 10))
        self.update_error_button() # Sync with tracker immediately
        
        self.history_btn = ctk.CTkButton(top_frame, text="📜 History", 
                                         command=self.show_history_window, width=120, height=32,
                                         fg_color="#334155", hover_color="#475569")
        self.history_btn.grid(row=0, column=4, padx=(0, 10))
        
        # 5. About
        self.about_btn = ctk.CTkButton(top_frame, text="👤 About", 
                                  command=self.show_about_window, width=120, height=32,
                                  fg_color="#3b82f6", hover_color="#2563eb")
        self.about_btn.grid(row=0, column=6)
        
        # Separator line
        separator = ctk.CTkFrame(self, height=2, fg_color="gray30")
        separator.grid(row=1, column=0, padx=20, pady=(5, 0), sticky="ew")
        
        # Adjust row configuration
        self.grid_rowconfigure(0, weight=0) # Top frame
        self.grid_rowconfigure(1, weight=0) # Separator
        self.grid_rowconfigure(2, weight=0) # Custom Tab Buttons
        self.grid_rowconfigure(3, weight=1) # Tabview expands
        
        # Custom Tab Buttons Frame
        self.tab_btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.tab_btn_frame.grid(row=2, column=0, padx=20, pady=(10, 0), sticky="ew")
        self.tab_btn_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Main Tab Button (Blue)
        self.tab_btn_main = ctk.CTkButton(
            self.tab_btn_frame, 
            text="Main Download",
            command=lambda: self.set_active_tab("Main Download"),
            fg_color="#3b82f6", hover_color="#2563eb",
            height=35, font=("Roboto", 14, "bold")
        )
        self.tab_btn_main.grid(row=0, column=0, padx=(0, 5), sticky="e")
        
        # Batch Tab Button (Orange)
        self.tab_btn_batch = ctk.CTkButton(
            self.tab_btn_frame, 
            text="Batch Download",
            command=lambda: self.set_active_tab("Batch Download"),
            fg_color="#374151", border_width=0, text_color="#9ca3af", # Default inactive style (Grey)
            hover_color="#4b5563",
            height=35, font=("Roboto", 14, "bold")
        )
        self.tab_btn_batch.grid(row=0, column=1, padx=(5, 0), sticky="w")

        # Create tabbed interface (Hidden Header)
        self.tabview = ctk.CTkTabview(self, width=850, height=650)
        self.tabview.grid(row=3, column=0, padx=20, pady=(5, 20), sticky="nsew")
        
        # Create tabs
        self.tab_main = self.tabview.add("Main Download")
        self.tab_batch = self.tabview.add("Batch Download")
        
        # Set distinct colors
        # Main: Zinc 900 (Professional Dark Grey)
        # Batch: Zinc 950 (Deep Professional Dark)
        self.tab_main.configure(fg_color="#18181b")
        self.tab_batch.configure(fg_color="#09090b")
        
        # Configure tabs
        self.tab_main.grid_columnconfigure(1, weight=1)
        self.tab_main.grid_rowconfigure(9, weight=1) # Log row should expand
        
        self.tab_batch.grid_columnconfigure(0, weight=1)
        self.tab_batch.grid_rowconfigure(1, weight=1)
        
        self._create_main_tab()
        self._create_batch_tab()
        
        # Restore session data to widgets
        self.restore_session_data()
        
        # Real-time Metadata State
        self.metadata_timer = None
        self.current_video_metadata = None
        self.flash_timer = None
        
        # Bind URL entry events for auto-fetch
        # Note: Binding to internal entry widget for better event handling
        self.url_entry.bind("<KeyRelease>", self.on_url_input)
        self.url_entry.bind("<FocusOut>", self.on_url_input)
        self.url_entry.bind("<Button-1>", self.on_url_input) # Catch clicks/paste via mouse
        
        # Hide default tab header (After adding tabs to ensure it stays hidden)
        self.tabview._segmented_button.grid_remove()

    def set_active_tab(self, tab_name):
        """Switch tab and update custom buttons"""
        self.tabview.set(tab_name)
        
        if tab_name == "Main Download":
            # Active Main (Blue), Inactive Batch (Grey)
            self.tab_btn_main.configure(fg_color="#3b82f6", text_color="white", border_width=0)
            self.tab_btn_batch.configure(fg_color="#374151", text_color="#9ca3af", border_width=0)
        else:
            # Inactive Main (Grey), Active Batch (Orange)
            self.tab_btn_main.configure(fg_color="#374151", text_color="#9ca3af", border_width=0)
            self.tab_btn_batch.configure(fg_color="#f59e0b", text_color="white", border_width=0)

    def on_closing(self):
        """Save settings and close the app"""
        self.save_settings()
        self.destroy()

    def load_settings(self):
        """Load persistent settings into variables"""
        config = self.config_manager.load_config()
        self.output_dir.set(config.get("output_dir", os.path.expanduser("~\\Downloads")))
        self.cookies_file_path.set(config.get("cookies_file_path", ""))
        
        # These will be set to widgets after they are created in _create_widgets
        self.initial_config = config

    def restore_session_data(self):
        """Apply loaded config to widgets after they are created"""
        config = self.initial_config
        self.cookies_option.set(config.get("cookies_browser", "None"))
        self.quality_option.set(config.get("quality", "None"))
        self.format_option.set(config.get("format", "None"))
        self.subtitle_option.set(config.get("subtitle_option", "None"))
        
        self.batch_quality_option.set(config.get("batch_quality", "None"))
        self.batch_format_option.set(config.get("batch_format", "None"))
        if config.get("batch_audio_only", False):
            self.batch_audio_only.select()
        else:
            self.batch_audio_only.deselect()
        self.batch_audio_format.set(config.get("batch_audio_format", "None"))
        self.batch_subtitle_option.set(config.get("batch_subtitle", "None"))
        self.thumbnail_option.set(config.get("thumbnail_option", "None"))
        self.batch_thumbnail_option.set(config.get("batch_thumbnail", "None"))

        # Restore batch URLs
        batch_urls = config.get("batch_urls", "")
        if batch_urls:
            self.batch_textbox.insert("1.0", batch_urls)
            # Hide help message if content exists
            if hasattr(self, 'batch_url_help'):
                self._remove_help(self.batch_url_help)

    def save_settings(self):
        """Save current widget states to config"""
        config = {
            "output_dir": self.output_dir.get(),
            "quality": self.quality_option.get(),
            "format": self.format_option.get(),
            "cookies_browser": self.cookies_option.get(),
            "cookies_file_path": self.cookies_file_path.get(),
            "subtitle_option": self.subtitle_option.get(),
            "batch_quality": self.batch_quality_option.get(),
            "batch_format": self.batch_format_option.get(),
            "batch_audio_only": self.batch_audio_only.get(),
            "batch_audio_format": self.batch_audio_format.get(),
            "batch_audio_only": self.batch_audio_only.get(),
            "batch_audio_format": self.batch_audio_format.get(),
            "batch_subtitle": self.batch_subtitle_option.get(),
            "thumbnail_option": self.thumbnail_option.get(),
            "batch_thumbnail": self.batch_thumbnail_option.get(),
            "batch_urls": self.batch_textbox.get("1.0", "end-1c")
        }
        self.config_manager.save_config(config)

    def load_last_session_logs(self):
        """Load last session's logs into the UI"""
        logs = self.config_manager.get_last_logs(30)
        if logs:
            self.log("\n--- Previous Session Logs ---")
            for line in logs.splitlines():
                if line.strip():
                    self.log(line)
            self.log("--- End of Previous Logs ---\n")
            
            # Same for batch log
            self.batch_log_msg("\n--- Previous Session Logs ---")
            for line in logs.splitlines():
                if line.strip():
                    self.batch_log_msg(line)
            self.batch_log_msg("--- End of Previous Logs ---\n")

    def _create_main_tab(self):
        """Create main download tab"""
        # Header is now in the top frame, but we can keep a sub-header if needed
        # Or just start with URL input to save vertical space
        # ctk.CTkLabel(self.tab_main, text="YouTube Downloader (yt-dlp)", font=("Roboto", 24, "bold")).grid(row=0, column=0, columnspan=3, padx=20, pady=(10, 5), sticky="w")

        # URL Input with copy/paste buttons
        url_label = ctk.CTkLabel(self.tab_main, text="Video URL:", font=("Roboto", 14))
        url_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        
        # Create frame for URL entry and buttons
        url_frame = ctk.CTkFrame(self.tab_main, fg_color="transparent")
        url_frame.grid(row=1, column=1, columnspan=2, padx=(0, 20), pady=10, sticky="ew")
        url_frame.grid_columnconfigure(0, weight=1)
        
        self.url_entry = ctk.CTkEntry(url_frame, placeholder_text="Paste link here...")
        self.url_entry.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        # Overlay instruction for Main URL
        self.main_url_help = self._add_disappearing_msg(
            self.url_entry, 
            "Paste a video or playlist URL here and click 'Start Download'."
        )
        
        paste_btn = ctk.CTkButton(url_frame, text="📋 Paste", width=60, command=self.paste_url)
        paste_btn.grid(row=0, column=1, padx=(10, 2))
        
        copy_btn = ctk.CTkButton(url_frame, text="📄 Copy", width=70, command=self.copy_url)
        copy_btn.grid(row=0, column=2, padx=2)
        
        fmt_btn = ctk.CTkButton(url_frame, text="📋 Formats", width=80, fg_color="#8b5cf6", hover_color="#7c3aed",
                                command=self.show_main_formats)
        fmt_btn.grid(row=0, column=3, padx=2)

        # Output Directory
        dir_label = ctk.CTkLabel(self.tab_main, text="Save to:", font=("Roboto", 14))
        dir_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")

        dir_entry = ctk.CTkEntry(self.tab_main, textvariable=self.output_dir)
        dir_entry.grid(row=2, column=1, padx=(0, 10), pady=10, sticky="ew")

        browse_btn = ctk.CTkButton(self.tab_main, text="Browse", width=100, height=32,
                                   command=self.browse_folder,
                                   fg_color="#334155", hover_color="#475569")
        browse_btn.grid(row=2, column=2, padx=(0, 20), pady=10)

        # Settings Row 1 (Browser & Quality)
        settings_frame1 = ctk.CTkFrame(self.tab_main, fg_color="transparent")
        settings_frame1.grid(row=3, column=0, columnspan=3, padx=20, pady=5, sticky="ew")
        
        # Browser Cookies
        cookies_label = ctk.CTkLabel(settings_frame1, text="Browser Cookies:", font=("Roboto", 14))
        cookies_label.pack(side="left", padx=(0, 10))
        
        self.cookies_option = ctk.CTkOptionMenu(settings_frame1, values=self.browsers)
        self.cookies_option.set("None")  # Default to None due to Chrome DPAPI issues
        self.cookies_option.pack(side="left", padx=(0, 10))
        
        # Fix Config button for DPAPI issues
        fix_config_btn = ctk.CTkButton(settings_frame1, text="🔧 Fix Config", 
                                       width=100, height=32, command=self.fix_config_file,
                                       fg_color="#d97706", hover_color="#b45309")
        fix_config_btn.pack(side="left", padx=(0, 5))
        
        # Create Config button
        create_config_btn = ctk.CTkButton(settings_frame1, text="➕ Create Config", 
                                         width=110, height=32, command=self.create_config_file,
                                         fg_color="#059669", hover_color="#047857")
        create_config_btn.pack(side="left", padx=(0, 20))

        # Quality
        quality_label = ctk.CTkLabel(settings_frame1, text="Quality:", font=("Roboto", 14))
        quality_label.pack(side="left", padx=(0, 10))
        
        self.quality_option = ctk.CTkOptionMenu(settings_frame1, values=self.video_qualities, command=self.on_quality_change)
        self.quality_option.pack(side="left")

        # File Format (Moved here)
        format_label = ctk.CTkLabel(settings_frame1, text="File Format:", font=("Roboto", 14))
        format_label.pack(side="left", padx=(20, 10))
        
        self.format_option = ctk.CTkOptionMenu(settings_frame1, values=self.file_formats, width=100, command=self.on_format_change)
        self.format_option.set("None")
        self.format_option.pack(side="left")

        # Settings Row 2 (Format & Subtitles)
        settings_frame2 = ctk.CTkFrame(self.tab_main, fg_color="transparent")
        settings_frame2.grid(row=4, column=0, columnspan=3, padx=20, pady=5, sticky="ew")
        
        # Subtitles (Now First)
        subtitle_label = ctk.CTkLabel(settings_frame2, text="Subtitle:", font=("Roboto", 14))
        subtitle_label.pack(side="left", padx=(0, 10))

        self.subtitle_option = ctk.CTkOptionMenu(settings_frame2, values=self.subtitle_options)
        self.subtitle_option.pack(side="left", padx=(0, 20))

        # Thumbnails
        thumbnail_label = ctk.CTkLabel(settings_frame2, text="Thumbnail:", font=("Roboto", 14))
        thumbnail_label.pack(side="left", padx=(0, 10))

        self.thumbnail_option = ctk.CTkOptionMenu(settings_frame2, values=self.thumbnail_options, width=100)
        self.thumbnail_option.set("None")
        self.thumbnail_option.pack(side="left")

        # Settings Row 3 (Custom Cookies)
        settings_frame3 = ctk.CTkFrame(self.tab_main, fg_color="transparent")
        settings_frame3.grid(row=5, column=0, columnspan=3, padx=20, pady=5, sticky="ew")
        
        cookie_file_label = ctk.CTkLabel(settings_frame3, text="Custom Cookies.txt:", font=("Roboto", 14))
        cookie_file_label.pack(side="left", padx=(0, 10))
        
        self.cookies_file_entry = ctk.CTkEntry(settings_frame3, textvariable=self.cookies_file_path, 
                                               width=420, placeholder_text="Select a netscape format cookies.txt file...")
        self.cookies_file_entry.pack(side="left", padx=(0, 10))
        
        browse_cookies_btn = ctk.CTkButton(settings_frame3, text="📂 Browse", width=80, height=32,
                                           command=self.browse_cookies_file,
                                           fg_color="#334155", hover_color="#475569")
        browse_cookies_btn.pack(side="left", padx=(0, 5))
        
        clear_cookies_btn = ctk.CTkButton(settings_frame3, text="❌", width=40, height=32,
                                          fg_color="#334155", hover_color="#ef4444", 
                                          command=lambda: self.cookies_file_path.set(""))
        clear_cookies_btn.pack(side="left")

        # Time Range Selection
        time_range_frame = ctk.CTkFrame(self.tab_main, fg_color="transparent")
        time_range_frame.grid(row=6, column=0, columnspan=3, padx=20, pady=5, sticky="ew")
        
        self.time_range_cb = ctk.CTkCheckBox(time_range_frame, text="Download Specific Time Range", 
                                             variable=self.time_range_active, command=self.toggle_time_range)
        self.time_range_cb.pack(side="left", padx=(0, 15))
        
        ctk.CTkLabel(time_range_frame, text="Start:").pack(side="left", padx=(0, 5))
        self.start_h_entry = ctk.CTkEntry(time_range_frame, textvariable=self.start_h, width=30)
        self.start_h_entry.pack(side="left")
        ctk.CTkLabel(time_range_frame, text=":").pack(side="left")
        self.start_m_entry = ctk.CTkEntry(time_range_frame, textvariable=self.start_m, width=30)
        self.start_m_entry.pack(side="left")
        ctk.CTkLabel(time_range_frame, text=":").pack(side="left")
        self.start_s_entry = ctk.CTkEntry(time_range_frame, textvariable=self.start_s, width=30)
        self.start_s_entry.pack(side="left", padx=(0, 15))
        
        ctk.CTkLabel(time_range_frame, text="End:").pack(side="left", padx=(0, 5))
        self.end_h_entry = ctk.CTkEntry(time_range_frame, textvariable=self.end_h, width=30)
        self.end_h_entry.pack(side="left")
        ctk.CTkLabel(time_range_frame, text=":").pack(side="left")
        self.end_m_entry = ctk.CTkEntry(time_range_frame, textvariable=self.end_m, width=30)
        self.end_m_entry.pack(side="left")
        ctk.CTkLabel(time_range_frame, text=":").pack(side="left")
        self.end_s_entry = ctk.CTkEntry(time_range_frame, textvariable=self.end_s, width=30)
        self.end_s_entry.pack(side="left")
        
        # Initial State
        self.toggle_time_range()

        # File info display (filename and size)
        self.file_info_label = ctk.CTkLabel(self.tab_main, text="Ready to fetch info...", 
                                            font=("Roboto", 16, "bold"), text_color="#9ca3af")
        self.file_info_label.grid(row=7, column=0, columnspan=3, padx=20, pady=(5, 10), sticky="w")
        
        # Ensure row has height
        self.tab_main.grid_rowconfigure(7, minsize=30)

        # Download & Stop Buttons Frame
        btn_row_frame = ctk.CTkFrame(self.tab_main, fg_color="transparent")
        btn_row_frame.grid(row=8, column=0, columnspan=3, padx=20, pady=15, sticky="ew")
        btn_row_frame.grid_columnconfigure(0, weight=1)
        
        self.download_btn = ctk.CTkButton(btn_row_frame, text="Start Download", 
                                          font=("Roboto", 16, "bold"), height=40, 
                                          command=self.start_download_thread,
                                          fg_color="#3b82f6", hover_color="#2563eb")
        self.download_btn.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        self.stop_btn = ctk.CTkButton(btn_row_frame, text="🛑 Stop", 
                                       font=("Roboto", 16, "bold"), height=40, width=120,
                                       command=self.stop_all_downloads,
                                       fg_color="#ef4444", hover_color="#dc2626",
                                       state="disabled")
        self.stop_btn.grid(row=0, column=1)
        
        self.clear_log_btn = ctk.CTkButton(btn_row_frame, text="🧹 Clear Log", 
                                           font=("Roboto", 14), height=40, width=120,
                                           command=self.clear_main_log,
                                           fg_color="#4b5563", hover_color="#64748b")
        self.clear_log_btn.grid(row=0, column=2, padx=(10, 0))

        # Log Output
        self.log_textbox = ctk.CTkTextbox(self.tab_main, font=("Consolas", 11))
        self.log_textbox.grid(row=9, column=0, columnspan=3, padx=20, pady=(0, 15), sticky="nsew")
        self.log_textbox.insert("0.0", "Ready to download...\n")
        self.log_textbox.configure(state="disabled")
        
        # Overlay instruction for Activity Log
        self.main_log_help = self._add_disappearing_msg(
            self.log_textbox,
            "Download progress and system messages will appear here."
        )

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self.tab_main)
        self.progress_bar.grid(row=10, column=0, columnspan=3, padx=20, pady=(0, 15), sticky="ew")
        self.progress_bar.set(0)

    def _create_batch_tab(self):
        """Create batch download tab"""
        # Header
        header_label = ctk.CTkLabel(self.tab_batch, text="Batch Download", 
                                     font=("Roboto", 24, "bold"))
        header_label.grid(row=0, column=0, columnspan=3, padx=20, pady=(20, 10), sticky="w")

        # Batch settings frame (Quality, Format, Audio)
        batch_settings_frame = ctk.CTkFrame(self.tab_batch, fg_color="transparent")
        batch_settings_frame.grid(row=1, column=0, columnspan=3, padx=20, pady=(5, 10), sticky="ew")
        
        # Configure grid columns
        batch_settings_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=0)
        
        # Row 1: Video Quality & Format
        ctk.CTkLabel(batch_settings_frame, text="Video Quality:", font=("Roboto", 12)).grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.batch_quality_option = ctk.CTkOptionMenu(batch_settings_frame, values=self.video_qualities, width=120)
        self.batch_quality_option.set("None")
        self.batch_quality_option.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(batch_settings_frame, text="Format:", font=("Roboto", 12)).grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.batch_format_option = ctk.CTkOptionMenu(batch_settings_frame, values=self.file_formats, width=80)
        self.batch_format_option.set("None")
        self.batch_format_option.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(batch_settings_frame, text="Subtitles:", font=("Roboto", 12)).grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.batch_subtitle_option = ctk.CTkOptionMenu(batch_settings_frame, values=self.subtitle_options, width=140)
        self.batch_subtitle_option.set("None")
        self.batch_subtitle_option.grid(row=0, column=5, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(batch_settings_frame, text="Thumbnail:", font=("Roboto", 12)).grid(row=0, column=6, padx=5, pady=5, sticky="e")
        self.batch_thumbnail_option = ctk.CTkOptionMenu(batch_settings_frame, values=self.thumbnail_options, width=100)
        self.batch_thumbnail_option.set("None")
        self.batch_thumbnail_option.grid(row=0, column=7, padx=5, pady=5, sticky="w")

        # Row 2: Audio Only & Format
        ctk.CTkLabel(batch_settings_frame, text="Audio Mode:", font=("Roboto", 12, "bold")).grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.batch_audio_only = ctk.CTkCheckBox(batch_settings_frame, text="Audio Only")
        self.batch_audio_only.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(batch_settings_frame, text="Audio Format:", font=("Roboto", 12)).grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.batch_audio_format = ctk.CTkOptionMenu(batch_settings_frame, values=["mp3", "m4a", "opus", "flac"], width=100)
        self.batch_audio_format.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        # URL Text Area with scrollbars
        self.batch_textbox = ctk.CTkTextbox(self.tab_batch, font=("Consolas", 11), 
                                            wrap="none")
        self.batch_textbox.grid(row=2, column=0, columnspan=3, padx=20, pady=(0, 15), sticky="nsew")

        # Overlay instruction for Batch URL box
        self.batch_url_help = self._add_disappearing_msg(
            self.batch_textbox,
            "Type or paste URLs here (one per line).\n"
            "You can also import a .txt file. Format: one URL per line.\n"
            "Playlists are also supported!"
        )

        # Buttons frame
        buttons_frame = ctk.CTkFrame(self.tab_batch, fg_color="transparent")
        buttons_frame.grid(row=3, column=0, columnspan=3, padx=20, pady=(0, 10), sticky="ew")
        
        import_btn = ctk.CTkButton(buttons_frame, text="Import from File", 
                                   command=self.import_urls_from_file, width=150, height=32,
                                   fg_color="#334155", hover_color="#475569")
        import_btn.pack(side="left", padx=(0, 10))
        
        paste_batch_btn = ctk.CTkButton(buttons_frame, text="📋 Paste URL", 
                                        command=self.paste_batch_url, width=120, height=32,
                                        fg_color="#6366f1", hover_color="#4f46e5")
        paste_batch_btn.pack(side="left", padx=(0, 10))
        
        clear_btn = ctk.CTkButton(buttons_frame, text="Clear All", 
                                  command=self.clear_batch_urls, width=100, height=32,
                                  fg_color="#334155", hover_color="#475569")
        clear_btn.pack(side="left", padx=(0, 10))
        
        self.expand_playlist_var = ctk.BooleanVar(value=True)
        expand_cb = ctk.CTkCheckBox(buttons_frame, text="Expand Playlists", variable=self.expand_playlist_var)
        expand_cb.pack(side="left", padx=(5, 10))
        
        self.batch_start_btn = ctk.CTkButton(buttons_frame, text="Start Batch Download", 
                                             font=("Roboto", 14, "bold"),
                                             command=self.start_batch_download, width=200,
                                             fg_color="#f59e0b", hover_color="#d97706")
        self.batch_start_btn.pack(side="right")
        
        self.batch_stop_btn = ctk.CTkButton(buttons_frame, text="🛑 Stop All", 
                                             font=("Roboto", 12, "bold"), height=32,
                                             command=self.stop_all_downloads,
                                             fg_color="#ef4444", hover_color="#dc2626",
                                             width=100, state="disabled")
        self.batch_stop_btn.pack(side="right", padx=(0, 10))
        
        self.batch_skip_btn = ctk.CTkButton(buttons_frame, text="⏭️ Skip Current", 
                                            command=self.skip_current_download, height=32,
                                            width=120, fg_color="#6366f1", hover_color="#4f46e5",
                                            state="disabled")
        self.batch_skip_btn.pack(side="right", padx=(0, 10))

        # Remove old clear button from buttons_frame if it exists there
        if hasattr(self, 'batch_clear_log_btn'):
             try: self.batch_clear_log_btn.pack_forget()
             except: pass

        # File info for batch (green)
        self.batch_file_info_label = ctk.CTkLabel(self.tab_batch, text="", 
                                                  font=("Roboto", 11), text_color="#10b981")
        self.batch_file_info_label.grid(row=4, column=0, columnspan=3, padx=20, pady=(0, 5), sticky="w")

        # Progress info
        self.batch_progress_label = ctk.CTkLabel(self.tab_batch, text="", 
                                                  font=("Roboto", 13))
        self.batch_progress_label.grid(row=5, column=0, columnspan=3, padx=20, pady=(0, 5), sticky="w")

        # Log Header with Clear Button
        log_header = ctk.CTkFrame(self.tab_batch, fg_color="transparent", height=30)
        log_header.grid(row=6, column=0, columnspan=3, padx=20, pady=(10, 0), sticky="ew")
        
        ctk.CTkLabel(log_header, text="Activity Log", font=("Roboto", 12, "bold")).pack(side="left")
        
        self.batch_clear_log_btn = ctk.CTkButton(log_header, text="🧹 Clear Log", 
                                           font=("Roboto", 11), height=24, width=80,
                                           command=self.clear_batch_log,
                                           fg_color="#4b5563", hover_color="#64748b")
        self.batch_clear_log_btn.pack(side="right")

        # Batch log
        self.batch_log = ctk.CTkTextbox(self.tab_batch, font=("Consolas", 11), height=150)
        self.batch_log.grid(row=7, column=0, columnspan=3, padx=20, pady=(5, 15), sticky="nsew")
        self.batch_log.insert("0.0", "Ready for batch download...\n")
        self.batch_log.configure(state="disabled")
        
        # Overlay instruction for Batch Log
        self.batch_log_help = self._add_disappearing_msg(
            self.batch_log,
            "Batch processing status will be shown here."
        )

        # Batch progress bar
        self.batch_progress_bar = ctk.CTkProgressBar(self.tab_batch)
        self.batch_progress_bar.grid(row=8, column=0, columnspan=3, padx=20, pady=(0, 15), sticky="ew")
        self.batch_progress_bar.set(0)

    def _add_disappearing_msg(self, widget, message):
        """Add a disappearing instructions label over a widget"""
        # Create a label that looks like a ghost overlay
        label = ctk.CTkLabel(
            self, # Parent to the main window for absolute placement
            text=message,
            text_color="gray70",
            font=("Roboto", 12, "italic"),
            justify="center",
            cursor="hand2",
            bg_color="transparent"
        )
        
        # Position it centered inside the target widget
        label.place(in_=widget, relx=0.5, rely=0.5, anchor="center")
        
        # Bind click to disappear
        label.bind("<Button-1>", lambda e: self._remove_help(label))
        widget.bind("<Button-1>", lambda e: self._remove_help(label), add="+")
        widget.bind("<Key>", lambda e: self._remove_help(label), add="+")
        
        self.help_labels.append(label)
        return label

    def _remove_help(self, label):
        """Remove a specific help label"""
        try:
            if label in self.help_labels:
                label.place_forget()
                self.help_labels.remove(label)
        except:
            pass

    def _clear_all_help(self):
        """Clear all visible help messages"""
        for label in list(self.help_labels):
            self._remove_help(label)

    # show_app_info removed - merged into AboutWindow

    def skip_current_download(self):
        """Skip the currently running download in batch"""
        if self.current_process:
            self.skip_requested = True
            try:
                # On Windows, taskkill is more reliable for children
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.current_process.pid)], 
                             capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            except:
                self.current_process.kill()
            self.batch_log_msg("⏭️ Skip requested: Moving to next item...")

    def stop_all_downloads(self):
        """Stop any running download in main or batch mode"""
        self.skip_requested = True # For batch
        
        if getattr(self, 'batch_in_progress', False):
            self.batch_log_msg("🛑 Batch stopped by user.")
            self.batch_in_progress = False
            
        if hasattr(self, 'current_duplicate_dialog') and self.current_duplicate_dialog:
            try:
                self.current_duplicate_dialog.set_result(None)
            except:
                pass
                
        if self.current_process:
            try:
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.current_process.pid)], 
                             capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
                self.log("\n🛑 Download stopped by user.")
            except:
                self.current_process.kill()
            
            self.reset_ui()
            
        self.after(0, self.update_batch_ui_state)

    def paste_url(self):
        """Paste from clipboard to URL entry and trigger fetch"""
        try:
            if hasattr(self, 'main_url_help'):
                self._remove_help(self.main_url_help)

            self.url_entry.delete(0, 'end')
            self.url_entry.insert(0, self.clipboard_get())
            self.on_url_input() # Trigger fetch
        except:
            pass

    def paste_batch_url(self):
        """Paste URL from clipboard into batch textbox on a new line"""
        try:
            clipboard_text = self.clipboard_get().strip()
            if not clipboard_text:
                return
            
            # Remove help overlay if visible
            if hasattr(self, 'batch_url_help'):
                self._remove_help(self.batch_url_help)
            
            # Get current content and ensure we add on a new line
            current = self.batch_textbox.get("1.0", "end-1c")
            if current and not current.endswith("\n"):
                self.batch_textbox.insert("end", "\n")
            
            self.batch_textbox.insert("end", clipboard_text)
            self.batch_textbox.see("end")
        except:
            pass

    def show_main_formats(self):
        """Show formats for the URL in main window"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Please enter a valid URL first.")
            return
        FormatsWindow(self, url)

    def copy_url(self):
        """Copy URL to clipboard"""
        url = self.url_entry.get()
        if url:
            self.clipboard_clear()
            self.clipboard_append(url)
            self.log("URL copied to clipboard")
        else:
            messagebox.showwarning("No URL", "No URL to copy")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_dir.set(folder)

    def log(self, message):
        """Display message in UI log and write to persistent log"""
        self.after(0, lambda: self._log_to_widget(self.log_textbox, message))
        # Persist to file
        self.config_manager.append_log(f"[Main] {message}")

    def clear_main_log(self):
        """Clear the main log textbox"""
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.insert("0.0", "Log cleared.\n")
        self.log_textbox.configure(state="disabled")

    def batch_log_msg(self, message):
        """Display message in Batch log and write to persistent log"""
        self.after(0, lambda: self._log_to_widget(self.batch_log, message))
        # Persist to file
        self.config_manager.append_log(f"[Batch] {message}")

    def clear_batch_log(self):
        """Clear the batch log textbox"""
        self.batch_log.configure(state="normal")
        self.batch_log.delete("1.0", "end")
        self.batch_log.insert("0.0", "Batch log cleared.\n")
        self.batch_log.configure(state="disabled")

    def _log_to_widget(self, widget, message):
        """Helper to append log to a specific textbox widget"""
        if hasattr(self, 'main_log_help') and widget == self.log_textbox:
            self._remove_help(self.main_log_help)
        if hasattr(self, 'batch_log_help') and widget == self.batch_log:
            self._remove_help(self.batch_log_help)
            
        widget.configure(state="normal")
        widget.insert("end", str(message) + "\n")
        widget.see("end")
        widget.configure(state="disabled")

    def fix_config_file(self):
        """Fix config file by removing/commenting out Chrome cookie line"""
        config_path = os.path.join(os.getenv('APPDATA'), 'yt-dlp', 'config.txt')
        
        if not os.path.exists(config_path):
            messagebox.showinfo(
                "Config Not Found",
                "No config file found at:\n" + config_path + "\n\n"
                "The config file will be created when you run setup."
            )
            return
        
        try:
            # Read current config
            with open(config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Track if we made changes
            changes_made = False
            new_lines = []
            
            for line in lines:
                # Check if line contains cookies-from-browser (and not already commented)
                if '--cookies-from-browser' in line and not line.strip().startswith('#'):
                    # Comment it out
                    new_lines.append('# ' + line)
                    changes_made = True
                else:
                    new_lines.append(line)
            
            if changes_made:
                # Write back to file
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                
                messagebox.showinfo(
                    "Config Fixed!",
                    "Successfully disabled browser cookie extraction in config file.\n\n"
                    "The Chrome DPAPI error should now be resolved.\n\n"
                    "Config location:\n" + config_path
                )
                self.log("Config file fixed: Chrome cookie line disabled")
            else:
                messagebox.showinfo(
                    "Already Fixed",
                    "Config file doesn't have any active cookie extraction lines.\n\n"
                    "Your config is already correct!"
                )
        
        except Exception as e:
            messagebox.showerror(
                "Error Fixing Config",
                f"Could not modify config file:\n{e}\n\n"
                f"You can manually edit:\n{config_path}"
            )

    def create_config_file(self):
        """Create config file from scratch with correct settings"""
        config_folder = os.path.join(os.getenv('APPDATA'), 'yt-dlp')
        config_path = os.path.join(config_folder, 'config.txt')
        
        # Check if file already exists
        if os.path.exists(config_path):
            result = messagebox.askyesno(
                "Config Already Exists",
                "A config file already exists at:\n" + config_path + "\n\n"
                "Do you want to overwrite it with a fresh config?\n\n"
                "Warning: This will replace any custom settings!",
                icon='warning'
            )
            if not result:
                return
        
        try:
            # Create folder if it doesn't exist
            if not os.path.exists(config_folder):
                os.makedirs(config_folder)
                self.log(f"Created folder: {config_folder}")
            
            # Config content without Chrome cookies
            config_content = """# --- Authentication ---
# Browser cookie extraction disabled due to DPAPI issues with Chrome
# Most videos work without cookies!
# Uncomment and change browser if needed (firefox works better):
# --cookies-from-browser firefox

# If you need cookies for age-restricted content, export cookies.txt
# from your browser and use this instead:
# --cookies "C:\\Users\\Pinku\\Downloads\\cookies.txt"

# --- Download Location ---
# Save files to your Windows "Downloads" folder automatically
-P "~/Downloads"

# --- Filename Format ---
# Save files as "Title.extension" (instead of the long default weird ID)
-o "%(title)s.%(ext)s"

# --- Quality ---
# Check for errors and ignore them if possible
--ignore-errors
"""
            
            # Write config file
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            messagebox.showinfo(
                "Config Created!",
                "Successfully created config file with optimal settings.\n\n"
                "Features:\n"
                "• No browser cookies (avoids DPAPI errors)\n"
                "• Downloads to ~/Downloads folder\n"
                "• Clean filenames\n"
                "• Error handling enabled\n\n"
                "Config location:\n" + config_path
            )
            self.log("Config file created successfully at: " + config_path)
        
        except Exception as e:
            messagebox.showerror(
                "Error Creating Config",
                f"Could not create config file:\n{e}\n\n"
                f"Target location:\n{config_path}"
            )

    def import_urls_from_file(self):
        """Import URLs from a text file"""
        file_path = filedialog.askopenfilename(
            title="Select URL List File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.batch_textbox.insert("end", content)
                self.batch_log_msg(f"Imported URLs from: {file_path}")
            except Exception as e:
                messagebox.showerror("Import Error", f"Could not import file:\n{e}")

    def clear_batch_urls(self):
        """Clear the batch URL text area"""
        self.batch_textbox.delete("1.0", "end")
        self.batch_log_msg("Cleared all URLs")

    def start_batch_download(self):
        """Redesigned start_batch_download: Step 1 - Show Setup Dialog"""
        self._clear_all_help()
        content = self.batch_textbox.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("No URLs", "Please enter at least one URL")
            return
        
        urls = [url.strip() for url in content.split('\n') if url.strip()]
        if not urls:
            messagebox.showwarning("No URLs", "No valid URLs found")
            return

        # Instead of fetching immediately, open the Batch Setup Dialog
        BatchSetupDialog(self, urls)

    def info_fetching_task(self, urls):
        """Expand playlists and fetch info for all URLs"""
        all_items = []
        total_urls = len(urls)
        
        self.skip_requested = False
        for i, url in enumerate(urls):
            if self.skip_requested:
                self.after(0, lambda: self.update_batch_ui_state())
                return
            
            self.after(0, lambda u=url, idx=i: self.batch_progress_label.configure(
                text=f"Fetching info {idx+1}/{total_urls}: {u[:50]}..."
            ))
            
            # Expand playlist or just get single info
            expand = self.expand_playlist_var.get()
            
            # Common flags
            cmd = ["yt-dlp", "--no-warnings"]
            cmd.extend(self.get_anti_bot_headers())
            
            # Cookies
            cookies_file = self.cookies_file_path.get()
            if cookies_file and os.path.exists(cookies_file):
                cmd.extend(["--cookies", cookies_file])
                self.after(0, lambda: self.batch_log_msg(f"Using cookies file for info: {os.path.basename(cookies_file)}"))
            else:
                browser = self.cookies_option.get()
                if browser != "None":
                    cmd.extend(["--cookies-from-browser", browser])
                    self.after(0, lambda: self.batch_log_msg(f"Using browser cookies for info: {browser}"))

            if expand:
                # Existing logic: Expand playlist into items
                cmd.extend([
                    "--flat-playlist", 
                    "--print", "%(webpage_url,original_url,url)s|||%(title)s|||%(filesize,filesize_approx)s|||%(duration_string)s"
                ])
                
                # Add quality selector for accurate size (only needed for individual items)
                b_quality = self.batch_quality_option.get()
                b_audio_only = self.batch_audio_only.get()
                
                if b_quality and b_quality != "Best" and not b_audio_only:
                    import re
                    height_match = re.search(r'(\d{3,4})p', b_quality)
                    if height_match:
                        height = height_match.group(1)
                        cmd.extend(["-f", f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"])
                    else:
                        numbers = "".join(filter(str.isdigit, b_quality))
                        if numbers:
                             cmd.extend(["-f", f"bestvideo[height<={numbers}]+bestaudio/best[height<={numbers}]/best"])
                elif b_audio_only:
                    cmd.extend(["-f", "bestaudio/best"])
                    
                cmd.append(url)
            else:
                # New logic: Get playlist/video metadata as single item
                cmd.extend(["-J", "--flat-playlist", url])

            # Try to fetch info with retries
            success = False
            fetch_retries = 2
            for attempt in range(fetch_retries):
                if self.skip_requested:
                    self.after(0, lambda: self.update_batch_ui_state())
                    return

                try:
                    process = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                        text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                    )
                    stdout, stderr = process.communicate()
                    
                    if process.returncode == 0:
                        if expand:
                            # Parse line-by-line output
                            for line in stdout.splitlines():
                                if '|||' in line:
                                    parts = line.split('|||')
                                    if len(parts) >= 2:
                                        item_url = parts[0]
                                        title = parts[1]
                                        size_raw = parts[2] if len(parts) > 2 else "NA"
                                        duration = parts[3] if len(parts) > 3 else "NA"
                                        
                                        all_items.append({
                                            'url': item_url,
                                            'title': title,
                                            'size_raw': size_raw,
                                            'size': self.format_size_raw(size_raw),
                                            'duration': duration,
                                            'quality': self.batch_quality_option.get(),
                                            'format': self.batch_format_option.get(),
                                            'audio_only': self.batch_audio_only.get(),
                                            'audio_format': self.batch_audio_format.get(),
                                            'subtitle': self.batch_subtitle_option.get(),
                                            'thumbnail': self.batch_thumbnail_option.get(),
                                            'selected': True,
                                            'is_playlist': False,
                                            'metadata': None # Loaded on demand for speed
                                        })
                        else:
                            # Parse JSON output
                            import json
                            try:
                                data = json.loads(stdout)
                                _type = data.get('_type', 'video')
                                
                                if _type == 'playlist':
                                    title = f"Playlist: {data.get('title', 'Unknown')} ({data.get('playlist_count', '?')} items)"
                                    is_playlist = True
                                else:
                                    title = data.get('title', 'Unknown')
                                    is_playlist = False
                                
                                all_items.append({
                                    'url': data.get('webpage_url', url),
                                    'title': title,
                                    'size_raw': 'NA', # Can't easily get total size of playlist without expansion
                                    'size': 'Unknown' if is_playlist else 'Calculated on fetch',
                                    'duration': 'N/A' if is_playlist else data.get('duration_string', 'N/A'),
                                    'quality': self.batch_quality_option.get(),
                                    'format': self.batch_format_option.get(),
                                    'audio_only': self.batch_audio_only.get(),
                                    'audio_format': self.batch_audio_format.get(),
                                    'subtitle': self.batch_subtitle_option.get(),
                                    'thumbnail': self.batch_thumbnail_option.get(),
                                    'selected': True,
                                    'is_playlist': is_playlist,
                                    'metadata': data if not is_playlist else None # Store metadata for single vids
                                })
                            except json.JSONDecodeError:
                                self.after(0, lambda: self.batch_log_msg(f"❌ Error parsing JSON for {url}"))
                                
                        success = True
                        break # Success!
                    else:
                        if attempt < fetch_retries - 1:
                            self.after(0, lambda u=url: self.batch_log_msg(f"🔄 Retrying info fetch for: {u}..."))
                        else:
                            if stderr:
                                self.after(0, lambda u=url, msg=stderr.strip(): self.batch_log_msg(f"⚠️ Failed info for {u}: {msg[:200]}..."))
                            else:
                                self.after(0, lambda u=url: self.batch_log_msg(f"⚠️ Failed to fetch info for: {u} (No detailed error)"))
                except Exception as e:
                    self.after(0, lambda e=e: self.batch_log_msg(f"❌ Error fetching info: {e}"))
                    break

        if not all_items:
            self.after(0, lambda: messagebox.showwarning("No Items", "Could not fetch information for any of the URLs."))
            self.after(0, lambda: self.batch_start_btn.configure(state="normal"))
            return

        self.after(0, lambda: self.open_review_window(all_items))

    def format_size_raw(self, size_str):
        """Convert raw size string to human readable"""
        if not size_str or size_str == 'NA':
            return "Unknown"
        try:
            size_bytes = int(float(size_str))
            if size_bytes > 1024*1024*1024:
                return f"{size_bytes/(1024*1024*1024):.2f} GB"
            elif size_bytes > 1024*1024:
                return f"{size_bytes/(1024*1024):.2f} MB"
            elif size_bytes > 1024:
                return f"{size_bytes/1024:.2f} KB"
            else:
                return f"{size_bytes} B"
        except:
            return "Unknown"

    def open_review_window(self, items):
        """Open the maximized review window with table"""
        self.batch_start_btn.configure(state="normal")
        self.batch_progress_label.configure(text="Reviewing batch items...")
        ReviewWindow(self, items)

    def start_batch_processing_loop(self, items):
        """Step 2 - Actually download the reviewed items"""
        self.batch_urls = items # Now it's a list of dicts
        self.batch_current_index = 0
        self.batch_in_progress = True
        self.batch_overwrite_all = False
        self.batch_skip_all = False
        self.after(0, self.update_batch_ui_state)
        
        self.batch_log_msg(f"\n{'='*50}")
        self.batch_log_msg(f"🚀 Starting batch download: {len(self.batch_urls)} selected items")
        self.batch_log_msg(f"{'='*50}\n")
        
        self.process_next_batch_item()

    def process_next_batch_item(self):
        """Process the next item from the reviewed list"""
        if not getattr(self, 'batch_in_progress', False):
            self.after(0, self.update_batch_ui_state)
            return
            
        if self.batch_current_index >= len(self.batch_urls):
            self.batch_in_progress = False
            self.after(0, self.update_batch_ui_state)
            self.batch_progress_bar.set(1.0)
            self.batch_log_msg(f"\n{'='*50}")
            self.batch_log_msg("✅ Batch download completed!")
            self.batch_log_msg(f"{'='*50}\n")
            self.batch_progress_label.configure(text="All downloads complete!")
            return
        
        item = self.batch_urls[self.batch_current_index]
        total = len(self.batch_urls)
        current_num = self.batch_current_index + 1
        
        progress = current_num / total
        self.batch_progress_bar.set(progress)
        self.batch_progress_label.configure(text=f"Downloading {current_num} of {total}: {item['title'][:60]}...")
        
        self.batch_log_msg(f"\n[{current_num}/{total}] Processing: {item['title']}")
        
        self.skip_requested = False
        thread = threading.Thread(
            target=self.run_yt_dlp_batch,
            args=(item,),
            daemon=True
        )
        thread.start()

    def run_yt_dlp_batch(self, item):
        """Run yt-dlp for batch item with item-specific settings and 3x retry"""
        url = item['url']
        title = item.get('title', 'Unknown Title')
        info_text = f"📹 {title}  |  📦 {item['size']}"
        self.after(0, lambda: self.batch_file_info_label.configure(text=info_text))
        
        # 1. Duplicate Check
        existing_file = self.check_for_duplicate(title, self.output_dir.get())
        if existing_file:
            if getattr(self, 'batch_skip_all', False):
                self.after(0, lambda: self.batch_log_msg(f"⏭️ Item skipped: File already exists ('{os.path.basename(existing_file)}')"))
                self.batch_current_index += 1
                self.after(0, self.process_next_batch_item)
                return
            elif not getattr(self, 'batch_overwrite_all', False):
                # Ask user for permission (needs to be thread-safe for batch)
                result = []
                def show_dialog():
                    dialog = FileExistsDialog(self, title, existing_file)
                    self.wait_window(dialog)
                    result.append(dialog.result)

                self.after(0, show_dialog)
                
                # Busy wait for user answer
                import time
                wait_start = time.time()
                while not result:
                    time.sleep(0.1)
                    if self.skip_requested: break
                    
                if result:
                    choice = result[0]
                    if choice == "yes_all":
                        self.batch_overwrite_all = True
                    elif choice == "no_all":
                        self.batch_skip_all = True
                        
                    if choice in ["no", "no_all", None]:
                        self.after(0, lambda: self.batch_log_msg(f"⏭️ Item skipped: File already exists ('{os.path.basename(existing_file)}')"))
                        self.batch_current_index += 1
                        self.after(0, self.process_next_batch_item)
                        return
                else:
                    # User clicked 'Skip Current' while dialog was open or closed it via X
                    if not self.skip_requested:
                        self.after(0, lambda: self.batch_log_msg(f"⏭️ Item skipped: File already exists ('{os.path.basename(existing_file)}')"))
                        self.batch_current_index += 1
                        self.after(0, self.process_next_batch_item)
                    return

        # Write JSON metadata to disk to bypass fetching if available
        json_path = None
        
        try:
            if item.get('metadata'):
                import json
                import tempfile
                quality_str = item.get('quality', 'Best')
                audio_only = item.get('audio_only', False)
                exact_format_id = self._get_exact_format_id(item['metadata'], quality_str, audio_only)
                item['exact_format_id'] = exact_format_id
                
                fd, json_path = tempfile.mkstemp(suffix=".json")
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(item['metadata'], f)
                item['info_json_path'] = json_path
        except Exception as e:
            self.after(0, lambda: self.batch_log_msg(f"Warning: Could not save metadata cache: {e}"))
            json_path = None

        retries = 0
        max_retries = 1
        last_error = ""
        success = False # Flag to track if download was successful
        
        while retries < max_retries:
            if retries > 0:
                self.after(0, lambda: self.batch_log_msg(f"🔄 Retry attempt {retries}/{max_retries} for: {item['title']}"))
            
            try:
                cmd = self.build_ytdlp_command_item(item)
                self.after(0, lambda: self.batch_log_msg(f"Running command: {' '.join(cmd)}"))
                
                self.current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )

                full_output = []
                for line in self.current_process.stdout:
                    line = line.strip()
                    if line:
                        self.after(0, lambda l=line: self.batch_log_msg(l))
                        full_output.append(line)
                
                self.current_process.wait()
                
                if self.skip_requested:
                    self.after(0, lambda: self.batch_log_msg("⏭️ Item skipped by user"))
                    break
                elif self.current_process.returncode == 0:
                    self.after(0, lambda: self.batch_log_msg("✓ Download successful"))
                    success = True # Set success flag
                    # Record in history
                    final_path = os.path.join(self.output_dir.get(), f"{title}.mp4")
                    self.config_manager.add_to_history(title, url, final_path)
                    break # Move to cleanup and next item
                else:
                    last_error = "\n".join(full_output[-10:])
                    retries += 1
            except Exception as e:
                last_error = str(e)
                retries += 1
        
        if not success and not self.skip_requested: # Only log failure if not successful and not skipped
            self.after(0, lambda: self.batch_log_msg(f"✗ Failed after {max_retries} attempts: {item['title']}"))
            diagnosis, solutions = self.diagnose_error(last_error)
            self.after(0, lambda: self.batch_log_msg(f"💡 Suggestion: {solutions[0]}"))
            
            # Add to persistent tracker
            self.error_tracker.add_error(url, diagnosis, "Batch Download")
            self.after(0, self.update_error_button)

        if json_path and os.path.exists(json_path):
            try: os.remove(json_path)
            except: pass

        self.current_process = None
        self.batch_current_index += 1
        self.after(0, self.process_next_batch_item)

    def on_quality_change(self, choice):
        """Handle quality change event - Instant update using cache"""
        # Dynamic Format Options
        if choice == "Audio Only":
             self.format_option.configure(values=["mp3", "m4a", "wav", "flac", "opus"])
             if self.format_option.get() not in ["mp3", "m4a", "wav", "flac", "opus"]:
                 self.format_option.set("mp3")
        else:
             self.format_option.configure(values=self.file_formats)
             if self.format_option.get() not in self.file_formats:
                 self.format_option.set("mp4")
                
        # Immediate update if we have metadata
        if self.current_video_metadata:
            self.update_file_info_from_metadata()

    def on_format_change(self, choice):
        """Handle format change event - Update size info only"""
        if self.current_video_metadata:
            self.update_file_info_from_metadata()

        url = self.url_entry.get().strip()
        if not url: return

        # If we have cached metadata for this URL, calculate size instantly
        if hasattr(self, 'current_video_metadata') and self.current_video_metadata and self.current_video_metadata.get('original_url') == url:
            self.update_file_info_from_cache()
        else:
            # Fallback to fetch if not cached (e.g. pasted new url but didn't wait)
            self.fetch_video_info_thread(url)

    def toggle_time_range(self):
        """Enable/disable time range inputs"""
        state = "normal" if self.time_range_active.get() else "disabled"
        for widget in [self.start_h_entry, self.start_m_entry, self.start_s_entry,
                       self.end_h_entry, self.end_m_entry, self.end_s_entry]:
            widget.configure(state=state)

    def fetch_video_info_thread(self, url):
        """Fetch full metadata once and cache it"""
        self.file_info_label.configure(text="Fetching video info...")
        self.current_video_title = None
        self.current_video_metadata = None # Clear old cache
        
        def run():
            metadata = self.fetch_metadata_json(url)
            if metadata:
                self.current_video_metadata = metadata
                self.current_video_metadata['original_url'] = url
                self.current_video_title = metadata.get('title', 'Unknown')
                
                # Update UI on main thread
                self.after(0, self.update_file_info_from_cache)
                
            else:
                self.after(0, lambda: self.file_info_label.configure(text="Could not fetch video info"))
        
        threading.Thread(target=run, daemon=True).start()

    def update_file_info_from_cache(self):
        """Calculate size from cached metadata based on current settings"""
        if not hasattr(self, 'current_video_metadata') or not self.current_video_metadata:
            return

        title = self.current_video_metadata.get('title', 'Unknown')
        quality = self.quality_option.get()
        # Calculate size locally
        size = self.calculate_size_from_metadata(self.current_video_metadata, quality)
        
        info_text = f"📹 {title}  |  📦 {size}"
        self.file_info_label.configure(text=info_text)

    def fetch_metadata_json(self, url):
        """Fetch full JSON metadata for a URL"""
        try:
            # Check for local binaries
            app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            local_ytdlp = os.path.join(app_dir, "yt-dlp.exe")
            
            exe = local_ytdlp if os.path.exists(local_ytdlp) else "yt-dlp"
            cmd = [exe, "-J", "--no-warnings", url]
            
            # Add ffmpeg location if present locally
            local_ffmpeg = os.path.join(app_dir, "ffmpeg.exe")
            if os.path.exists(local_ffmpeg):
                cmd.extend(["--ffmpeg-location", app_dir])

            cmd.extend(self.get_anti_bot_headers())
            
            # Cookies handling
            cookies_file = self.cookies_file_path.get()
            if cookies_file and os.path.exists(cookies_file):
                cmd.extend(["--cookies", cookies_file])
            else:
                browser = self.cookies_option.get()
                if browser != "None":
                    cmd.extend(["--cookies-from-browser", browser])
            
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            
            if result.returncode == 0:
                import json
                return json.loads(result.stdout)
            return None
        except:
            return None

    def calculate_size_from_metadata(self, metadata, quality):
        """Estimate file size from metadata formats based on quality selection"""
        if not metadata or 'formats' not in metadata:
            return "Unknown"
            
        formats = metadata.get('formats', [])
        
        # Logic matches yt-dlp selection behavior
        target_height = 0
        if "Audio Only" in quality:
            # Best audio
            best_audio = 0
            for f in formats:
                if f.get('vcodec') == 'none' and f.get('filesize'):
                    if f['filesize'] > best_audio: best_audio = f['filesize']
            return self.format_size_raw(best_audio) if best_audio > 0 else "Unknown"
            
        elif quality == "Best":
             target_height = 99999 # Unlimited
        else:
            # Parse height "1080p" -> 1080
            import re
            match = re.search(r'(\d{3,4})', quality)
            target_height = int(match.group(1)) if match else 1080
            
        # Find best video stream <= target_height
        best_video_size = 0
        best_audio_size = 0
        
        # 1. Find best audio size (approximate)
        for f in formats:
            if f.get('vcodec') == 'none' and f.get('filesize'):
                 best_audio_size = max(best_audio_size, f['filesize'])
        
        # 2. Find best video stream
        current_best_tbr = 0
        
        for f in formats:
            if f.get('vcodec') != 'none':
                h = f.get('height', 0)
                if h and h <= target_height:
                    # Check if this is better quality (using bitrate as proxy)
                    tbr = f.get('tbr', 0) or 0
                    if tbr > current_best_tbr:
                        current_best_tbr = tbr
                        # prefer filesize if available, else estimate from bitrate approx
                        size = f.get('filesize') or f.get('filesize_approx')
                        if size:
                             best_video_size = size
        
        if best_video_size == 0 and best_audio_size == 0:
            return "Unknown"
            
        total_size = best_video_size + best_audio_size
        return self.format_size_raw(total_size)

    def get_cookie_args(self):
        """Helper to get cookie arguments for yt-dlp"""
        args = []
        # Custom cookies file
        cookies_file = self.cookies_file_path.get()
        if cookies_file and os.path.exists(cookies_file):
            args.extend(["--cookies", cookies_file])
            return args
            
        # Cookies from browser
        browser = self.cookies_option.get()
        if browser != "None":
            args.extend(["--cookies-from-browser", browser])
            
        return args

    def get_time_range_args(self):
        """Get time range arguments if enabled"""
        if not self.time_range_active.get():
            return []
            
        # Helper to construct time string
        def get_time_str(h_var, m_var, s_var):
            h = h_var.get().strip() or "00"
            m = m_var.get().strip() or "00"
            s = s_var.get().strip() or "00"
            return f"{h.zfill(2)}:{m.zfill(2)}:{s.zfill(2)}"

        start = get_time_str(self.start_h, self.start_m, self.start_s)
        end = get_time_str(self.end_h, self.end_m, self.end_s)
        
        # Check if default (00:00:00) - treat as empty for logic if needed, 
        # but here we likely want specific ranges. 
        # However, to support open-ended ranges like "start from 10s to end",
        # we might need a way to indicate "no limit". 
        # For now, let's assume 00:00:00 is start, and if end is 00:00:00, maybe it means end?
        # Actually, simpler: if all are 0, it's 0.
        
        start_is_zero = (start == "00:00:00")
        end_is_zero = (end == "00:00:00")

        if start_is_zero and end_is_zero:
            return []
            
        section = "*"
        if not start_is_zero:
            section += start
            
        section += "-"
        
        if not end_is_zero:
            section += end
            
        if section != "*-": 
            self.log(f"Cut time range: {section}")
            return ["--download-sections", section, "--force-keyframes-at-cuts"]
            
        return []

    def on_url_input(self, event=None):
        """Handle URL input with debounce"""
        # Remove help text on any input
        if hasattr(self, 'main_url_help'):
            self._remove_help(self.main_url_help)

        # Ignore modifier keys to prevent spam
        if event and event.keysym in ("Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"):
            return

        # Reset timer
        if self.metadata_timer:
            self.after_cancel(self.metadata_timer)
            
        # Wait 800ms after last keystroke to fetch info
        self.metadata_timer = self.after(800, self.fetch_metadata_bg)

    def fetch_metadata_bg(self):
        """Fetch full metadata in background"""
        url = self.url_entry.get().strip()
        if not url:
            return

        print(f"Triggering metadata fetch for: {url}")
        
        # Stop flashing if running
        if self.flash_timer:
            self.after_cancel(self.flash_timer)
            self.flash_timer = None
            
        self.file_info_label.configure(text="🔍 Fetching info...", text_color="#fbbf24") # Amber for fetching
        
        def _fetch_task():
            try:
                cmd = ['yt-dlp', '--dump-json', '--no-playlist', url]
                cookie_args = self.get_cookie_args()
                if cookie_args:
                    cmd.extend(cookie_args)
                    
                # print(f"Command: {cmd}") 
                process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    metadata = json.loads(stdout.decode('utf-8', errors='ignore'))
                    self.current_video_metadata = metadata
                    print("Metadata fetch successful")
                    self.after(0, self.update_file_info_from_metadata)
                else:
                    err = stderr.decode()
                    print(f"Metadata fetch failed: {err}")
                    self.current_video_metadata = None
                    self.after(0, lambda: self.file_info_label.configure(text="❌ Info fetch failed", text_color="#ef4444"))
            except Exception as e:
                print(f"Metadata fetch exception: {e}")
                self.current_video_metadata = None
                self.after(0, lambda: self.file_info_label.configure(text="❌ Error fetching info", text_color="#ef4444"))
                
        threading.Thread(target=_fetch_task, daemon=True).start()

    def update_file_info_from_metadata(self):
        """Update UI with title and estimated size"""
        if not self.current_video_metadata:
            return
            
        title = self.current_video_metadata.get('title', 'Unknown')
        quality = self.quality_option.get()
        size = self.calculate_size_from_metadata(self.current_video_metadata, quality)
        
        self.file_info_label.configure(text=f"📹 {title}  |  📦 {size}", text_color="#10b981")
        self.flash_info_text()

    def flash_info_text(self):
        """Flash the file info text colors"""
        if self.flash_timer:
            self.after_cancel(self.flash_timer)
            
        current_color = self.file_info_label.cget("text_color")
        next_color = "#ffffff" if current_color == "#10b981" else "#10b981"
        
        self.file_info_label.configure(text_color=next_color)
        self.flash_timer = self.after(500, self.flash_info_text)

    def start_download_thread(self):
        self._clear_all_help()
        url = self.url_entry.get()
        if not url:
            self.log("Error: Please enter a URL.")
            return

        # Check browser for cookies
        browser = self.cookies_option.get()
        if browser != "None" and not self.cookies_file_path.get():
            if self.is_browser_running(browser):
                messagebox.showwarning(
                    "Browser Running", 
                    f"{browser.title()} seems to be running.\n"
                    "Please close it completely to allow cookie extraction."
                )
                return
        
        # UI state
        self.download_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        
        # Fetch and display video info in background
        self.file_info_label.configure(text="Fetching video info...")
        
        
        # Shared data between threads
        self.current_video_title = None
        
        # Get current settings
        quality = self.quality_option.get()
        fmt = self.format_option.get()
        
        def fetch_info():
            # If we already have metadata for this URL, just use it
            if self.current_video_metadata and self.current_video_metadata.get('webpage_url') == url:
                self.after(0, self.update_file_info_from_metadata)
                return

            # Otherwise fetch it (fallback)
            title, size = self.get_video_info(url, quality, fmt)
            if title:
                self.current_video_title = title
                info_text = f"📹 {title}  |  📦 {size}"
                self.after(0, lambda: self.file_info_label.configure(text=info_text))
            else:
                self.after(0, lambda: self.file_info_label.configure(text="Could not fetch video info"))
        
        threading.Thread(target=fetch_info, daemon=True).start()
        
        # Start download thread with UI reset callback
        def download_and_reset():
            self.run_yt_dlp_with_retry(url, title=self.current_video_title, quality=quality, file_format=fmt)
            self.after(0, self.reset_ui)
            
        thread = threading.Thread(target=download_and_reset, daemon=True)
        thread.start()

    def is_browser_running(self, browser_name):
        """Check if browser is running"""
        process_map = {
            "chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "opera": "opera.exe",
            "brave": "brave.exe",
            "vivaldi": "vivaldi.exe",
            "chromium": "chrome.exe"
        }
        
        exe_name = process_map.get(browser_name.lower())
        if not exe_name:
            return False

        try:
            output = subprocess.check_output(
                f'tasklist /FI "IMAGENAME eq {exe_name}"', 
                shell=True
            ).decode()
            if exe_name in output:
                return True
        except:
            pass
        return False

    def get_video_info(self, url, quality, fmt):
        """Fetch video title and estimated size"""
        try:
            # Prepare command to get JSON metadata
            cmd = [
                'yt-dlp',
                '--dump-json',
                '--no-playlist',
                url
            ]
            
            # Add cookie args if needed
            cookie_args = self.get_cookie_args()
            if cookie_args:
                cmd.extend(cookie_args)
                
            # Run command
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                print(f"Info fetch error: {stderr.decode()}")
                return None, None
                
            info = json.loads(stdout.decode())
            title = info.get('title', 'Unknown Title')
            filesize = info.get('filesize_approx') or info.get('filesize')
            
            # Format size
            if filesize:
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if filesize < 1024:
                        size_str = f"{filesize:.2f} {unit}"
                        break
                    filesize /= 1024
                else:
                    size_str = f"{filesize:.2f} PB"
            else:
                size_str = "Size Unknown"
                
            return title, size_str
            
        except Exception as e:
            print(f"Error fetching info: {e}")
            return None, None

    def get_anti_bot_headers(self):
        """Hardened bypass using mobile clients and ipv4 forcing"""
        return [
            "--force-ipv4",
            "--no-check-certificates",
            "--add-header", "Accept-Language: en-US,en;q=0.9",
        ]

    def _get_exact_format_id(self, metadata, quality, audio_only=False, audio_format='mp3'):
        """Extract exact format ID from metadata based on requested quality string"""
        if not metadata or 'formats' not in metadata: return None
        if quality == "None": return None
        
        if audio_only:
            # We want bestaudio
            return "bestaudio/best"
            
        if quality == "Best":
            return "bestvideo+bestaudio/best"
            
        # Parse requested height
        import re
        height_match = re.search(r'(\d{3,4})p', quality)
        target_height = 1080
        if height_match: target_height = int(height_match.group(1))
        elif "2160" in quality: target_height = 2160
        
        # Find best video format with height <= target_height
        best_v_fmt = None
        best_v_height = 0
        best_v_tbr = 0
        
        for f in metadata.get('formats', []):
            if f.get('vcodec') == 'none': continue # audio only
            h = f.get('height') or 0
            tbr = f.get('tbr') or 0
            if h <= target_height:
                if h > best_v_height or (h == best_v_height and tbr > best_v_tbr):
                    best_v_height = h
                    best_v_tbr = tbr
                    best_v_fmt = f.get('format_id')
                    
        if best_v_fmt:
            return f"{best_v_fmt}+bestaudio/best"
        return None

    def build_ytdlp_command(self, url, quality=None, file_format=None, exact_format_id=None, load_info_json=None):
        """Build yt-dlp command with all options"""
        # Check for local binaries
        app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        local_ytdlp = os.path.join(app_dir, "yt-dlp.exe")
        
        exe = local_ytdlp if os.path.exists(local_ytdlp) else "yt-dlp"
        cmd = [exe, "--newline", "--no-colors"]
        
        # Add ffmpeg location if present locally
        local_ffmpeg = os.path.join(app_dir, "ffmpeg.exe")
        if os.path.exists(local_ffmpeg):
            cmd.extend(["--ffmpeg-location", app_dir])
        cmd.extend(self.get_anti_bot_headers())
        
        out_path = os.path.join(self.output_dir.get(), "%(title)s.%(ext)s")
        cmd.extend(["-o", out_path])

        # Cookies handling (Manual file takes priority)
        cookies_file = self.cookies_file_path.get()
        if cookies_file and os.path.exists(cookies_file):
            cmd.extend(["--cookies", cookies_file])
            self.log(f"Using manual cookies file: {os.path.basename(cookies_file)}")
        else:
            browser = self.cookies_option.get()
            if browser != "None":
                cmd.extend(["--cookies-from-browser", browser])

        # Use provided args or fetch from UI
        if not quality: quality = self.quality_option.get()
        if not file_format: file_format = self.format_option.get()
        
        if load_info_json:
            cmd.extend(["--load-info-json", load_info_json])
            
        if exact_format_id:
            cmd.extend(["-f", exact_format_id])
            if "Audio Only" not in quality:
                 if file_format != "None":
                     cmd.extend(["--merge-output-format", file_format])
            elif "Audio Only" in quality:
                 if file_format != "None":
                     cmd.extend(["-x", "--audio-format", file_format, "--audio-quality", "0"])
                 else:
                     cmd.extend(["-x", "--audio-quality", "0"])
        else:
            if "Audio Only" in quality:
                cmd.extend(["-f", "bestaudio/best"])
                if file_format != "None":
                    cmd.extend(["-x", "--audio-format", file_format, "--audio-quality", "0"])
                else:
                    cmd.extend(["-x", "--audio-quality", "0"])
            elif quality == "None":
                cmd.extend(["--skip-download"])
            else:
                if quality == "Best":
                    format_str = f"bestvideo+bestaudio/best"
                else:
                    import re
                    height_match = re.search(r'(\d{3,4})p', quality)
                    if height_match:
                        height = height_match.group(1)
                    else:
                        numbers = "".join(filter(str.isdigit, quality))
                        if len(numbers) > 4: height = "2160"
                        elif numbers: height = numbers
                        else: height = "1080"
    
                    format_str = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
                
                cmd.extend(["-f", format_str])
            
            if "Audio Only" not in quality and quality != "None":
                if file_format != "None":
                    cmd.extend(["--merge-output-format", file_format])

        subtitle_choice = self.subtitle_option.get()
        if subtitle_choice == "Original Only":
            cmd.extend(["--write-subs", "--sub-langs", "all"])
        elif subtitle_choice == "Auto-Generated Only":
            cmd.extend(["--write-auto-subs", "--sub-langs", "en.*,en"])
        elif subtitle_choice == "Both":
            cmd.extend(["--write-subs", "--write-auto-subs", "--sub-langs", "en.*,en"])

        thumbnail_choice = self.thumbnail_option.get()
        if thumbnail_choice in ("webp", "jpg", "png"):
            cmd.extend(["--write-thumbnail"])
            cmd.extend(["--convert-thumbnails", thumbnail_choice])
            cmd.extend(["--ppa", "ThumbnailsConvertor+ffmpeg:-qscale:v 2"])

        # Time Range
        cmd.extend(self.get_time_range_args())

        cmd.append(url)
        return cmd

    def build_ytdlp_command_item(self, item):
        """Build command for a specific reviewed item"""
        url = item['url']
        # Check for local binaries
        app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        local_ytdlp = os.path.join(app_dir, "yt-dlp.exe")
        
        exe = local_ytdlp if os.path.exists(local_ytdlp) else "yt-dlp"
        cmd = [exe, "--newline", "--no-colors"]
        
        # Add ffmpeg location if present locally
        local_ffmpeg = os.path.join(app_dir, "ffmpeg.exe")
        if os.path.exists(local_ffmpeg):
            cmd.extend(["--ffmpeg-location", app_dir])
        
        cmd.extend(self.get_anti_bot_headers())
        
        if item.get('is_playlist'):
            # Playlist Mode: Create subfolder and number items
            out_path = os.path.join(self.output_dir.get(), "%(playlist_title)s", "%(playlist_index)s - %(title)s.%(ext)s")
            cmd.extend(["-o", out_path])
            cmd.append("--yes-playlist")
        else:
            # Single Video Mode
            out_path = os.path.join(self.output_dir.get(), "%(title)s.%(ext)s")
            cmd.extend(["-o", out_path])
            cmd.append("--no-playlist") # Ensure we only get the video if it's a mix


        # Cookies handling (Manual file takes priority)
        cookies_file = self.cookies_file_path.get()
        if cookies_file and os.path.exists(cookies_file):
            cmd.extend(["--cookies", cookies_file])
        else:
            browser = self.cookies_option.get()
            if browser != "None":
                cmd.extend(["--cookies-from-browser", browser])

        # Custom Format ID override or JSON exact format
        exact_format = item.get('exact_format_id')
        
        json_path = item.get('info_json_path')
        if json_path and os.path.exists(json_path):
            cmd.extend(["--load-info-json", json_path])

        if exact_format:
            cmd.extend(["-f", exact_format])
            if item.get('format') and not item.get('audio_only') and item.get('format') != "None":
                 cmd.extend(["--merge-output-format", item['format']])
            elif item.get('audio_only'):
                 audio_fmt = item.get('audio_format', 'mp3')
                 if audio_fmt != "None":
                     cmd.extend(["-x", "--audio-format", audio_fmt, "--audio-quality", "0"])
                 else:
                     cmd.extend(["-x", "--audio-quality", "0"])
        elif item['audio_only']:
            audio_fmt = item.get('audio_format', 'mp3')
            cmd.extend(["-f", "bestaudio/best"])
            if audio_fmt != "None":
                cmd.extend(["-x", "--audio-format", audio_fmt, "--audio-quality", "0"])
            else:
                cmd.extend(["-x", "--audio-quality", "0"])
        elif item['quality'] == "None":
            cmd.extend(["--skip-download"])
        else:
            quality = item['quality']
            file_format = item['format']
            
            if quality == "Best":
                format_str = f"bestvideo+bestaudio/best"
            else:
                import re
                height_match = re.search(r'(\d{3,4})p', quality)
                if height_match:
                    height = height_match.group(1)
                else:
                    numbers = "".join(filter(str.isdigit, quality))
                    if len(numbers) > 4: height = "2160"
                    elif numbers: height = numbers
                    else: height = "1080"
                format_str = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
            
            cmd.extend(["-f", format_str])
            if file_format != "None":
                cmd.extend(["--merge-output-format", file_format])

        # Subtitles for batch item
        subtitle_choice = item.get('subtitle', 'None')
        if subtitle_choice == "Original Only":
            cmd.extend(["--write-subs", "--sub-langs", "all"])
        elif subtitle_choice == "Auto-Generated Only":
            cmd.extend(["--write-auto-subs", "--sub-langs", "en.*,en"])
        elif subtitle_choice == "Both":
            cmd.extend(["--write-subs", "--write-auto-subs", "--sub-langs", "en.*,en"])

        # Thumbnails for batch item
        thumbnail_choice = item.get('thumbnail', 'None')
        if thumbnail_choice in ("webp", "jpg", "png"):
            cmd.extend(["--write-thumbnail"])
            cmd.extend(["--convert-thumbnails", thumbnail_choice])
            cmd.extend(["--ppa", "ThumbnailsConvertor+ffmpeg:-qscale:v 2"])

        cmd.extend(["--ignore-errors"]) # User requested robust download
        cmd.append(url)
        return cmd

    def run_yt_dlp_with_retry(self, url, max_retries=1, title=None, quality=None, file_format=None):
        """Run download with retry logic and error diagnosis"""
        # 1. Duplicate Check
        if title:
            existing_file = self.check_for_duplicate(title, self.output_dir.get())
            if existing_file:
                # Ask user for permission (on main thread because it's a dialog)
                result = []
                self.after(0, lambda: result.append(messagebox.askyesno(
                    "File Already Exists", 
                    f"A file that looks like this video already exists in your folder:\n\n"
                    f"'{existing_file}'\n\n"
                    "Do you want to download it anyway?"
                )))
                
                # Busy wait for user answer (max 1 minute)
                import time
                wait_start = time.time()
                while not result and time.time() - wait_start < 60:
                    time.sleep(0.1)
                
                if result and result[0] is False:
                    self.log(f"⏭️ Download skipped: File already exists ('{existing_file}')")
                    return True # Count as handled

        retries = 0
        last_error = ""
        self.skip_requested = False
        
        # Write JSON metadata to disk to bypass fetching if available
        json_path = None
        exact_format_id = None
        
        try:
            if hasattr(self, 'current_video_metadata') and self.current_video_metadata:
                import json
                import tempfile
                quality_str = quality or self.quality_option.get()
                audio_only = "Audio Only" in quality_str
                exact_format_id = self._get_exact_format_id(self.current_video_metadata, quality_str, audio_only)
                
                fd, json_path = tempfile.mkstemp(suffix=".json")
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(self.current_video_metadata, f)
        except Exception as e:
            self.log(f"Warning: Could not save metadata cache: {e}")
            json_path = None

        while retries < max_retries:
            if self.skip_requested:
                if json_path and os.path.exists(json_path): os.remove(json_path)
                return False
            if retries > 0:
                self.log(f"\n🔄 Retry attempt {retries}/{max_retries}...")
            
            try:
                cmd = self.build_ytdlp_command(url, quality=quality, file_format=file_format, exact_format_id=exact_format_id, load_info_json=json_path)
                self.log(f"Running command: {' '.join(cmd)}")

                self.current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, universal_newlines=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )

                progress_pattern = re.compile(r"\[download\]\s+(\d+\.?\d*)%")
                ffmpeg_time_pattern = re.compile(r"time=(\d{2}:\d{2}:\d{2}\.\d+)")
                
                # Calculate total duration if time range is active
                total_duration_sec = 0
                if self.time_range_active.get():
                    def parse_hms(h_s, m_s, s_s):
                        try:
                            return float(h_s.get() or 0)*3600 + float(m_s.get() or 0)*60 + float(s_s.get() or 0)
                        except: return 0
                    
                    start_sec = parse_hms(self.start_h, self.start_m, self.start_s)
                    end_sec = parse_hms(self.end_h, self.end_m, self.end_s)
                    if end_sec > start_sec:
                        total_duration_sec = end_sec - start_sec

                full_output = []
                for line in self.current_process.stdout:
                    line = line.strip()
                    if line:
                        self.log(line)
                        full_output.append(line)
                        
                        percent = None
                        match = progress_pattern.search(line)
                        if match:
                            percent = float(match.group(1))
                        
                        # Fallback for ffmpeg time-based progress
                        elif total_duration_sec > 0 and "time=" in line:
                            match_time = ffmpeg_time_pattern.search(line)
                            if match_time:
                                t_str = match_time.group(1)
                                try:
                                    parts = t_str.split(':')
                                    current_sec = float(parts[0])*3600 + float(parts[1])*60 + float(parts[2])
                                    percent = (current_sec / total_duration_sec) * 100
                                    # Cap at 99.9% until actual completion
                                    if percent > 100: percent = 99.9
                                except: pass

                        if percent is not None:
                            self.after(0, lambda p=percent: self.update_progress(p))
                
                self.current_process.wait()
                
                if self.current_process.returncode == 0:
                    self.log("\n✅ Download Completed Successfully!")
                    # Show BIG GREEN SUCCESS
                    self.file_info_label.configure(text="✅ DOWNLOAD COMPLETE", font=("Roboto", 24, "bold"), text_color="#10b981")
                    # Reset after 5 seconds
                    self.after(5000, lambda: self.file_info_label.configure(text="", font=("Roboto", 12), text_color="#10b981"))
                    # Record in history
                    if title:
                        # Construct a probable path (best effort)
                        final_path = os.path.join(self.output_dir.get(), f"{title}.mp4")
                        self.config_manager.add_to_history(title, url, final_path)
                        
                    # If it was in error tracker, remove it
                    self.error_tracker.remove_error(url)
                    self.after(0, self.update_error_button)
                    if json_path and os.path.exists(json_path):
                        try: os.remove(json_path)
                        except: pass
                    return True
                else:
                    last_error = "\n".join(full_output[-10:]) # Keep last few lines
                    retries += 1
                    
            except Exception as e:
                last_error = str(e)
                retries += 1
        
        # If we reach here, it failed after all retries
        if self.skip_requested: return False
        
        self.log(f"\n❌ Download failed after {max_retries} attempts.")
        diagnosis, solutions = self.diagnose_error(last_error)
        
        self.log("\n🛑 Error Diagnosis:")
        self.log(f"   {diagnosis}")
        self.log("\n💡 Possible Solutions:")
        for sol in solutions:
            self.log(f"   • {sol}")
            
        # Add to persistent error tracker
        self.error_tracker.add_error(url, diagnosis, "Main Download")
        self.after(0, self.update_error_button)
        if json_path and os.path.exists(json_path):
            try: os.remove(json_path)
            except: pass
        return False

    def diagnose_error(self, error_text):
        """Diagnose common yt-dlp errors and suggest fixes"""
        patterns = {
            r"403": ("Access Forbidden (403)", ["Clear cookies and try again", "Browser cookies may be expired", "Use a VPN if IP is flagged"]),
            r"410": ("Video Removed (410)", ["The video is no longer available"]),
            r"Sign in to confirm": ("Bot Detection / Login Required", 
                                    ["Select a 'Custom Cookies.txt' file in the GUI", 
                                     "Click the '🧹 Clear Cache' button at the top",
                                     "Use the 'Update Tool' button to update yt-dlp",
                                     "Extract cookies with 'Get cookies.txt' browser extension"]),
            r"Geo-restricted": ("Geographic Restriction", ["Use a VPN to change your location", "Try a proxy server"]),
            r"ffmpeg": ("FFmpeg Not Found", ["Click 'Create Config' to setup tool paths", "Install FFmpeg manually"]),
            r"DPAPI": ("Chrome Cookie Error", ["Select 'Guest' or use a 'Custom Cookies.txt' file", "Close Chrome completely before downloading"]),
            r"Outdated": ("Software Outdated", ["Click the '🚀 Update Tool' button", "Run update_tools.ps1"]),
            r"Incomplete YouTube ID": ("Invalid URL", ["Check if the URL is copied correctly"]),
        }
        
        for pattern, (diagnosis, solutions) in patterns.items():
            if re.search(pattern, error_text, re.IGNORECASE):
                return diagnosis, solutions
                
        return "Unknown Error", ["Check your internet connection", "Try updating yt-dlp", "View logs for more details"]

    def check_for_duplicate(self, title, directory):
        """Check if a file with a similar title already exists in the folder"""
        if not title or not os.path.exists(directory):
            return False
            
        # Clean title for comparison (remove special chars/spaces)
        clean_title = re.sub(r'[^\w\s]', '', title).lower().strip()
        if not clean_title: return False
        
        try:
            for filename in os.listdir(directory):
                # Clean filename
                clean_filename = re.sub(r'[^\w\s]', '', filename).lower()
                # If the title is a significant part of the filename
                if clean_title in clean_filename:
                    return filename
        except:
            pass
        return None

    def update_error_button(self):
        """Update the error button visibility and text"""
        count = self.error_tracker.get_error_count()
        if count > 0:
            self.error_btn.configure(text=f"🔴 Errors ({count})", 
                                     fg_color="#dc2626", hover_color="#991b1b")
        else:
            self.error_btn.configure(text="⚪ No Errors", 
                                     fg_color="#374151", hover_color="#4b5563")
        self.error_btn.grid() # Always show now

    def show_error_dialog(self):
        """Show dialog to manage failed downloads"""
        ErrorDialog(self)

    def show_history_window(self):
        """Open the persistent history window"""
        HistoryWindow(self)

    def show_about_window(self):
        """Open the professional About window"""
        AboutWindow(self)

    def update_progress(self, percent):
        """Update progress bar"""
        self.progress_bar.set(percent / 100)
        self.progress_bar.configure(mode="determinate")
        
        # Update text with percentage
        if hasattr(self, 'file_info_label'):
            # Keep title if available, assuming it was set before
            current_text = self.file_info_label.cget("text").split("|")[0].strip()
            # Avoid overwriting with just percentage if possible, but simplest is:
            if "|" in current_text: # Already has title
                 self.file_info_label.configure(text=f"{current_text} | ⏳ {percent:.1f}%")
            else:
                 # Start or just percentage
                 title = getattr(self, 'current_video_title', 'Downloading')
                 if not title: title = "Downloading"
                 self.file_info_label.configure(text=f"📹 {title} | ⏳ {percent:.1f}%")

    def reset_ui(self):
        """Reset UI after download"""
        self.download_btn.configure(state="normal")
        if hasattr(self, 'stop_btn'): self.stop_btn.configure(state="disabled")
        self.progress_bar.stop()
        self.progress_bar.set(0)
        self.progress_bar.configure(mode="determinate")
        self.current_process = None
        self.after(0, self.update_batch_ui_state)

    def update_batch_ui_state(self):
        """Update batch UI buttons based on progress"""
        if not hasattr(self, 'batch_start_btn'): return
        if self.batch_in_progress:
            self.batch_start_btn.configure(state="disabled")
            self.batch_stop_btn.configure(state="normal")
            self.batch_skip_btn.configure(state="normal")
        else:
            self.batch_start_btn.configure(state="normal")
            self.batch_stop_btn.configure(state="disabled")
            self.batch_skip_btn.configure(state="disabled")

    def browse_cookies_file(self):
        """Open file dialog to select cookies.txt"""
        file_path = filedialog.askopenfilename(
            title="Select cookies.txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            self.cookies_file_path.set(file_path)

    def update_tools(self):
        """Check for and run updates for both yt-dlp and ffmpeg"""
        self.log("\n🔄 Checking for tool updates...")
        
        # UI for progress
        progress_win = ctk.CTkToplevel(self)
        progress_win.title("Updating Tools...")
        progress_win.geometry("450x200")
        progress_win.attributes("-topmost", True)
        progress_win.transient(self)
        
        # Center the window
        self.update_idletasks()
        try:
            x = self.winfo_x() + (self.winfo_width() // 2) - 225
            y = self.winfo_y() + (self.winfo_height() // 2) - 100
            progress_win.geometry(f"+{x}+{y}")
        except:
            pass
        
        lbl = ctk.CTkLabel(progress_win, text="Initializing...", font=("Roboto", 13))
        lbl.pack(pady=(20, 10))
        
        bar = ctk.CTkProgressBar(progress_win, width=350)
        bar.pack(pady=10)
        bar.set(0)
        
        # Paths
        app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        local_ytdlp = os.path.join(app_dir, "yt-dlp.exe")
        ytdlp_exe = local_ytdlp if os.path.exists(local_ytdlp) else "yt-dlp"
        ffmpeg_exe = os.path.join(app_dir, "ffmpeg.exe")

        def run_updates():
            status_msgs = []
            
            # --- 1. Update yt-dlp ---
            self.after(0, lambda: [lbl.configure(text="Checking yt-dlp..."), bar.configure(mode="indeterminate"), bar.start()])
            try:
                result = subprocess.run([ytdlp_exe, "-U"], capture_output=True, text=True, 
                                       creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
                self.after(0, lambda: self.log(result.stdout.strip()[:100] + "..."))
                if "latest version" in result.stdout or "up-to-date" in result.stdout:
                    status_msgs.append("yt-dlp: Up to date")
                else:
                    status_msgs.append("yt-dlp: Updated successfully")
            except Exception as e:
                status_msgs.append(f"yt-dlp: Error ({str(e)[:30]})")
                
            # --- 2. Update ffmpeg ---
            self.after(0, lambda: [lbl.configure(text="Checking FFmpeg version..."), bar.stop(), bar.configure(mode="determinate"), bar.set(0)])
            try:
                # Get remote version
                req = urllib.request.Request("https://www.gyan.dev/ffmpeg/builds/release-version", headers={'User-Agent': 'Mozilla/5.0'})
                remote_ver = urllib.request.urlopen(req, timeout=10).read().decode('utf-8').strip()
                
                # Get local version
                local_ver = ""
                if os.path.exists(ffmpeg_exe):
                    result = subprocess.run([ffmpeg_exe, "-version"], capture_output=True, text=True,
                                          creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
                    # Extract version string
                    match = re.search(r'ffmpeg version ([\d\.]+)', result.stdout)
                    if match:
                        local_ver = match.group(1)
                
                if local_ver and local_ver == remote_ver:
                    status_msgs.append(f"FFmpeg: Up to date ({local_ver})")
                else:
                    # Needs update
                    self.after(0, lambda: [lbl.configure(text=f"Downloading FFmpeg {remote_ver} (~130MB)...")])
                    
                    def report_progress(count, block_size, total_size):
                        if total_size > 0:
                            percent = (count * block_size) / total_size
                            if percent > 1.0: percent = 1.0
                            self.after(0, lambda p=percent: bar.set(p))
                            
                    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
                    zip_path = os.path.join(app_dir, "ffmpeg.zip")
                    
                    urllib.request.urlretrieve(url, zip_path, reporthook=report_progress)
                    
                    self.after(0, lambda: [lbl.configure(text="Extracting FFmpeg binaries..."), bar.configure(mode="indeterminate"), bar.start()])
                    
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        for file in zip_ref.namelist():
                            if file.endswith("bin/ffmpeg.exe"):
                                with open(ffmpeg_exe, "wb") as target:
                                    target.write(zip_ref.read(file))
                            elif file.endswith("bin/ffprobe.exe"):
                                with open(os.path.join(app_dir, "ffprobe.exe"), "wb") as target:
                                    target.write(zip_ref.read(file))
                                    
                    try: os.remove(zip_path)
                    except: pass
                    
                    status_msgs.append(f"FFmpeg: Updated to {remote_ver}")
                    self.after(0, lambda: self.log(f"FFmpeg updated to {remote_ver}"))
                    
            except Exception as e:
                self.after(0, lambda: self.log(f"FFmpeg update error: {str(e)}"))
                status_msgs.append(f"FFmpeg: Error checking/updating")

            # Finalize
            summary = "\n".join(status_msgs)
            self.after(0, lambda: [progress_win.destroy(), messagebox.showinfo("Update Complete", summary)])

        threading.Thread(target=run_updates, daemon=True).start()

    def clear_ytdlp_cache(self):
        """Run yt-dlp --rm-cache-dir"""
        self.log("\n🧹 Clearing yt-dlp cache...")
        
        app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        local_ytdlp = os.path.join(app_dir, "yt-dlp.exe")
        exe = local_ytdlp if os.path.exists(local_ytdlp) else "yt-dlp"

        def run_clear():
            try:
                result = subprocess.run([exe, "--rm-cache-dir"], capture_output=True, text=True, 
                                       creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
                self.after(0, lambda: self.log(result.stdout))
                self.after(0, lambda: messagebox.showinfo("Cache Cleared", "yt-dlp cache has been cleared successfully."))
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda: self.log(f"Error clearing cache: {err_msg}"))
                self.after(0, lambda: messagebox.showerror("Error", f"Could not clear cache:\n{err_msg}"))
        
        threading.Thread(target=run_clear, daemon=True).start()

class ErrorDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Failed Downloads & Errors")
        self.geometry("700x500")
        self.transient(parent)
        self.grab_set()
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(self, text="⚠️ Failed Downloads History", font=("Roboto", 18, "bold")).grid(row=0, column=0, pady=20)
        
        # Scrollable list
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)
        
        self.refresh_list()
        
        # Clear Button
        ctk.CTkButton(self, text="🗑️ Clear All History", fg_color="#475569", 
                      command=self.clear_all).grid(row=2, column=0, pady=(0, 20))

    def refresh_list(self):
        # Clear frame
        for widget in self.scroll.winfo_children():
            widget.destroy()
            
        errors = self.parent.error_tracker.get_errors()
        if not errors:
            ctk.CTkLabel(self.scroll, text="No failed downloads logged.").pack(pady=50)
            return
            
        for err in errors:
            frame = ctk.CTkFrame(self.scroll)
            frame.pack(fill="x", padx=10, pady=5)
            
            # URL and Diagnosis
            text_frame = ctk.CTkFrame(frame, fg_color="transparent")
            text_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)
            
            url_lbl = ctk.CTkLabel(text_frame, text=err['url'], wraplength=400, justify="left", text_color="#3b82f6")
            url_lbl.pack(anchor="w")
            
            diag_lbl = ctk.CTkLabel(text_frame, text=f"Error: {err.get('error', 'Unknown')}", font=("Roboto", 11, "italic"), text_color="#ef4444")
            diag_lbl.pack(anchor="w")
            
            # Action Buttons
            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.pack(side="right", padx=10)
            
            ctk.CTkButton(btn_frame, text="🔄 Retry", width=60, height=24, 
                          command=lambda u=err['url']: self.retry(u)).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="📋 Copy", width=60, height=24,
                          command=lambda u=err['url']: self.copy(u)).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="❌", width=30, height=24, fg_color="#ef4444",
                          command=lambda u=err['url']: self.remove(u)).pack(side="left", padx=2)

    def retry(self, url):
        # Insert into entry and start download
        self.parent.tabview.set("Main Download")
        self.parent.url_entry.delete(0, tk.END)
        self.parent.url_entry.insert(0, url)
        self.parent.start_download_thread()
        self.destroy()

    def copy(self, url):
        self.clipboard_clear()
        self.clipboard_append(url)
        messagebox.showinfo("Copied", "URL copied to clipboard")

    def remove(self, url):
        self.parent.error_tracker.remove_error(url)
        self.parent.update_error_button()
        self.refresh_list()

    def clear_all(self):
        if messagebox.askyesno("Confirm Clear", "Clear all error history?"):
            self.parent.error_tracker.clear_all_errors()
            self.parent.update_error_button()
            self.refresh_list()

class FileExistsDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, existing_file):
        super().__init__(parent)
        self.parent = parent
        self.title("File Already Exists")
        self.geometry("600x250")
        self.resizable(False, False)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        try:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - 300
            y = parent.winfo_y() + (parent.winfo_height() // 2) - 125
            self.geometry(f"+{x}+{y}")
        except:
            pass

        self.result = "no" # Default to no if closed
        parent.current_duplicate_dialog = self

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Main container
        container = ctk.CTkFrame(self, fg_color=("gray95", "gray15"))
        container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        container.grid_columnconfigure(1, weight=1)
        
        # Icon (Using a label with a question mark similar to messagebox)
        icon_frame = ctk.CTkFrame(container, width=50, height=50, corner_radius=25, fg_color="#3b82f6")
        icon_frame.grid(row=0, column=0, padx=(15, 15), pady=15, sticky="nw")
        icon_label = ctk.CTkLabel(icon_frame, text="?", font=ctk.CTkFont(size=24, weight="bold"), text_color="white")
        icon_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Text
        text_frame = ctk.CTkFrame(container, fg_color="transparent")
        text_frame.grid(row=0, column=1, sticky="nsew", pady=15, padx=(0, 15))
        
        msg1 = f"Batch Item: '{title}'"
        lbl1 = ctk.CTkLabel(text_frame, text=msg1, justify="left", font=ctk.CTkFont(weight="bold"), wraplength=450)
        lbl1.pack(anchor="w", pady=(0, 10))
        
        msg2 = "A file that looks like this video already exists in your folder:"
        lbl2 = ctk.CTkLabel(text_frame, text=msg2, justify="left", wraplength=450)
        lbl2.pack(anchor="w")
        
        msg3 = f"'{os.path.basename(existing_file)}'"
        lbl3 = ctk.CTkLabel(text_frame, text=msg3, justify="left", font=ctk.CTkFont(weight="bold"), wraplength=450)
        lbl3.pack(anchor="w", pady=(5, 10))
        
        msg4 = "Do you want to download it anyway?"
        lbl4 = ctk.CTkLabel(text_frame, text=msg4, justify="left", wraplength=450)
        lbl4.pack(anchor="w")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        btn_frame.grid_columnconfigure((0,1,2,3), weight=1)
        
        btn_yes = ctk.CTkButton(btn_frame, text="Yes", width=100, command=lambda: self.set_result("yes"))
        btn_yes.grid(row=0, column=0, padx=5)
        
        btn_yes_all = ctk.CTkButton(btn_frame, text="Yes to All", width=100, fg_color="#22c55e", hover_color="#16a34a", command=lambda: self.set_result("yes_all"))
        btn_yes_all.grid(row=0, column=1, padx=5)
        
        btn_no = ctk.CTkButton(btn_frame, text="No", width=100, fg_color="transparent", border_width=1, text_color=("gray10", "#DCE4EE"), command=lambda: self.set_result("no"))
        btn_no.grid(row=0, column=2, padx=5)
        
        btn_no_all = ctk.CTkButton(btn_frame, text="No to All", width=100, fg_color="#ef4444", hover_color="#dc2626", command=lambda: self.set_result("no_all"))
        btn_no_all.grid(row=0, column=3, padx=5)

        self.protocol("WM_DELETE_WINDOW", lambda: self.set_result("no"))

    def set_result(self, choice):
        self.result = choice
        self.grab_release()
        try:
            self.parent.current_duplicate_dialog = None
        except:
            pass
        self.destroy()

class ReviewWindow(ctk.CTkToplevel):
    def __init__(self, parent, items):
        super().__init__(parent)
        self.parent = parent
        self.items = items
        
        self.title("Batch Download Review")
        self.geometry("1000x800")
        
        # Make window appear on top
        self.transient(parent)
        self.state('zoomed')
        self.lift()
        self.focus_force()
        self.grab_set()
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header with Total Size
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)
        
        self.total_size_label = ctk.CTkLabel(header_frame, text="Total Size: Calculating...", 
                                              font=("Roboto", 18, "bold"))
        self.total_size_label.grid(row=0, column=0, padx=20, pady=10)
        
        # Buttons on top
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=2, padx=20, pady=10)
        
        ctk.CTkButton(btn_frame, text="Select All", width=100, command=self.select_all).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Deselect All", width=100, command=self.deselect_all).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="✏️ Edit Selected", width=120, fg_color="#6366f1", hover_color="#4f46e5",
                      command=self.edit_selected).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🚀 Start Download", fg_color="#10b981", hover_color="#059669", 
                      font=("Roboto", 14, "bold"), command=self.start_download).pack(side="left", padx=15)

        # Table Frame (Scrollable)
        self.table_container = ctk.CTkScrollableFrame(self)
        self.table_container.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.table_container.grid_columnconfigure(1, weight=1) # Title column
        
        # Table Headers
        headers = ["✔", "File Name", "Duration", "Size", "Quality", "Subtitles", "Actions"]
        for col, h in enumerate(headers):
            lbl = ctk.CTkLabel(self.table_container, text=h, font=("Roboto", 13, "bold"))
            lbl.grid(row=0, column=col, padx=10, pady=5, sticky="w")
        
        self.row_widgets = []
        self.refresh_table()
        self.update_total_size()

    def refresh_table(self):
        # Clear existing
        for w in self.row_widgets:
            for item_key in w:
                if isinstance(w[item_key], (ctk.CTkLabel, ctk.CTkCheckBox, ctk.CTkFrame)):
                    w[item_key].destroy()
        self.row_widgets = []
        
        for i, item in enumerate(self.items):
            row = i + 1
            
            # Checkbox
            var = tk.BooleanVar(value=item['selected'])
            cb = ctk.CTkCheckBox(self.table_container, text="", variable=var, width=20,
                                 command=lambda idx=i, v=var: self.toggle_item(idx, v))
            cb.grid(row=row, column=0, padx=10, pady=5)
            
            # Title
            title_lbl = ctk.CTkLabel(self.table_container, text=item['title'], wraplength=400, justify="left")
            title_lbl.grid(row=row, column=1, padx=10, pady=5, sticky="w")
            
            # Duration
            dur_lbl = ctk.CTkLabel(self.table_container, text=item['duration'])
            dur_lbl.grid(row=row, column=2, padx=10, pady=5)
            
            # Size
            size_lbl = ctk.CTkLabel(self.table_container, text=item['size'], text_color="#10b981")
            size_lbl.grid(row=row, column=3, padx=10, pady=5)
            
            # Quality
            q_text = f"{item['quality']} ({item['format']})"
            if item['audio_only']: 
                audio_fmt = item.get('audio_format', 'mp3')
                q_text = f"Audio Only ({audio_fmt})"
            quality_lbl = ctk.CTkLabel(self.table_container, text=q_text)
            quality_lbl.grid(row=row, column=4, padx=10, pady=5)
            

            
            # Subtitles
            sub_text = item.get('subtitle', 'None')
            sub_lbl = ctk.CTkLabel(self.table_container, text=sub_text)
            sub_lbl.grid(row=row, column=5, padx=10, pady=5)
            
            # Actions
            act_frame = ctk.CTkFrame(self.table_container, fg_color="transparent")
            act_frame.grid(row=row, column=6, padx=10, pady=5)
            
            mod_btn = ctk.CTkButton(act_frame, text="Modify", width=70, height=24, 
                                    command=lambda idx=i: self.modify_item(idx))
            mod_btn.pack(side="left", padx=2)
            
            fetch_btn = ctk.CTkButton(act_frame, text="Fetch", width=70, height=24,
                                      command=lambda idx=i: self.fetch_item(idx))
            fetch_btn.pack(side="left", padx=2)
            
            fmt_btn = ctk.CTkButton(act_frame, text="Formats", width=70, height=24, fg_color="#8b5cf6", hover_color="#7c3aed",
                                    command=lambda idx=i: AdvancedFormatsWindow(self, self.items[idx]['url'], self.items[idx].get('metadata'), lambda fid, note: self.set_custom_format(idx, fid, note)))
            fmt_btn.pack(side="left", padx=2)
            
            self.row_widgets.append({
                'cb': cb, 'title': title_lbl, 'dur': dur_lbl, 
                'size': size_lbl, 'quality': quality_lbl, 'actions': act_frame
            })

    def toggle_item(self, idx, var):
        self.items[idx]['selected'] = var.get()
        self.update_total_size()

    def update_total_size(self):
        total_bytes = 0
        for item in self.items:
            if item['selected'] and item['size_raw'] != 'NA':
                try: total_bytes += int(float(item['size_raw']))
                except: pass
        
        size_str = self.parent.format_size_raw(total_bytes)
        self.total_size_label.configure(text=f"Total Selected Size: {size_str}")

    def select_all(self):
        for item in self.items: item['selected'] = True
        self.refresh_table()
        self.update_total_size()

    def deselect_all(self):
        for item in self.items: item['selected'] = False
        self.refresh_table()
        self.update_total_size()

    def modify_item(self, idx):
        ModifyDialog(self, idx)

    def edit_selected(self):
        selected_indices = [i for i, item in enumerate(self.items) if item['selected']]
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select items to edit.")
            return
        BatchEditDialog(self, selected_indices)

    def fetch_item(self, idx):
        threading.Thread(target=self._fetch_single, args=(idx,), daemon=True).start()

    def batch_fetch(self, indices):
        """Fetch info for multiple items in background"""
        def run_batch():
            for idx in indices:
                if not self.winfo_exists(): break
                self._fetch_single(idx)
        threading.Thread(target=run_batch, daemon=True).start()

    def set_custom_format(self, idx, fmt_id, note):
        self.items[idx]['custom_format_id'] = fmt_id
        self.items[idx]['quality'] = f"Custom: {note}"
        self.refresh_table()

    def recalculate_item(self, idx):
        """Update item size/title from cached metadata without re-fetching"""
        item = self.items[idx]
        if not item.get('metadata'):
            # No cache? Fetch it.
            threading.Thread(target=self._fetch_single, args=(idx,), daemon=True).start()
            return

        # Calculate locally
        new_size = self.parent.calculate_size_from_metadata(item['metadata'], item['quality'])
        self.items[idx]['size'] = new_size
        
        # Parse approximate size raw for total calc
        # This is a bit hacky but works for the total sum
        try:
             # simple heuristic: parse "123.45 MiB" -> bytes
             parts = new_size.split()
             if len(parts) >= 2:
                 val = float(parts[0])
                 unit = parts[1].lower()
                 mult = 1
                 if 'k' in unit: mult = 1024
                 elif 'm' in unit: mult = 1024**2
                 elif 'g' in unit: mult = 1024**3
                 self.items[idx]['size_raw'] = str(int(val * mult))
             else:
                 self.items[idx]['size_raw'] = '0'
        except:
             self.items[idx]['size_raw'] = '0'

        self.after(0, self.refresh_table)
        self.after(0, self.update_total_size)

    def _fetch_single(self, idx):
        item = self.items[idx]
        # Visual feedback
        self.after(0, lambda: self.update_item_status(idx, "Updating..."))
        
        is_playlist = item.get('is_playlist', False)
        
        if is_playlist:
            # Playlist metadata is small, we can just fetch it again or use what we have?
            # Actually for playlists we want the count/title, not really the size of all items (too slow)
            cmd = ["yt-dlp", "-J", "--flat-playlist", "--no-warnings"]
        else:
            # Single video: Get FULL JSON for caching
            cmd = ["yt-dlp", "-J", "--no-warnings"]
        
        # Add anti-bot headers from parent
        cmd.extend(self.parent.get_anti_bot_headers())
        
        # Cookies
        cookies_file = self.parent.cookies_file_path.get()
        if cookies_file and os.path.exists(cookies_file):
             cmd.extend(["--cookies", cookies_file])
        else:
             browser = self.parent.cookies_option.get()
             if browser != "None":
                 cmd.extend(["--cookies-from-browser", browser])

        cmd.append(item['url'])
            
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            if result.returncode == 0:
                import json
                try:
                    data = json.loads(result.stdout)
                    if is_playlist:
                        new_title = f"Playlist: {data.get('title', 'Unknown')} ({data.get('playlist_count', '?')} items)"
                        self.items[idx]['title'] = new_title
                        self.items[idx]['size'] = "Unknown"
                        # Playlists don't support quality changes in the same way, so no metadata cache needed for calc
                    else:
                        # Single Video
                        self.items[idx]['metadata'] = data
                        self.items[idx]['title'] = data.get('title', 'Unknown')
                        # Trigger local calc
                        self.after(0, lambda: self.recalculate_item(idx))
                        return # Recalculate will handle the UI refresh

                    self.after(0, self.refresh_table)
                    self.after(0, self.update_total_size)
                except:
                     self.after(0, lambda: self.update_item_status(idx, "Error"))
        except: pass

    def update_item_status(self, idx, msg):
        # Helper to update a specific row's size text temporarily
        # We need to find the widget. Since row_widgets matches items index...
        if idx < len(self.row_widgets):
             self.row_widgets[idx]['size'].configure(text=msg)

    def start_download(self):
        selected_items = [it for it in self.items if it['selected']]
        if not selected_items:
            messagebox.showwarning("No Items", "Please select at least one item to download.")
            return
        self.parent.start_batch_processing_loop(selected_items)
        self.destroy()

class ModifyDialog(ctk.CTkToplevel):
    def __init__(self, parent, idx):
        super().__init__(parent)
        self.parent_window = parent
        self.idx = idx
        item = parent.items[idx]
        
        self.title("Modify Quality")

        self.geometry("300x680")
        self.transient(parent)
        self.grab_set()
        
        ctk.CTkLabel(self, text="Select Quality:", font=("Roboto", 14, "bold")).pack(pady=10)
        self.q_opt = ctk.CTkOptionMenu(self, values=parent.parent.video_qualities)
        self.q_opt.set(item['quality'])
        self.q_opt.pack(pady=5)
        
        ctk.CTkLabel(self, text="Select Format:", font=("Roboto", 14, "bold")).pack(pady=10)
        self.f_opt = ctk.CTkOptionMenu(self, values=parent.parent.file_formats)
        self.f_opt.set(item['format'])
        self.f_opt.pack(pady=5)
        
        self.audio_var = tk.BooleanVar(value=item['audio_only'])
        ctk.CTkCheckBox(self, text="Audio Only", variable=self.audio_var).pack(pady=10)
        
        ctk.CTkLabel(self, text="Audio Format:", font=("Roboto", 14, "bold")).pack(pady=5)
        self.af_opt = ctk.CTkOptionMenu(self, values=["mp3", "m4a", "opus", "flac"])
        self.af_opt.set(item.get('audio_format', 'mp3'))
        self.af_opt.pack(pady=5)
        

        
        ctk.CTkLabel(self, text="Subtitles:", font=("Roboto", 14, "bold")).pack(pady=5)
        self.sub_opt = ctk.CTkOptionMenu(self, values=parent.parent.subtitle_options)
        self.sub_opt.set(item.get('subtitle', 'None'))
        self.sub_opt.pack(pady=5)
        
        ctk.CTkLabel(self, text="Thumbnail:", font=("Roboto", 14, "bold")).pack(pady=5)
        self.thumb_opt = ctk.CTkOptionMenu(self, values=parent.parent.thumbnail_options)
        self.thumb_opt.set(item.get('thumbnail', 'None'))
        self.thumb_opt.pack(pady=5)
        
        ctk.CTkButton(self, text="Apply Changes", command=self.apply).pack(pady=20)
        
    def apply(self):
        self.parent_window.items[self.idx]['quality'] = self.q_opt.get()
        self.parent_window.items[self.idx]['format'] = self.f_opt.get()
        self.parent_window.items[self.idx]['audio_only'] = self.audio_var.get()
        self.parent_window.items[self.idx]['audio_format'] = self.af_opt.get()
        self.parent_window.items[self.idx]['subtitle'] = self.sub_opt.get()
        self.parent_window.items[self.idx]['thumbnail'] = self.thumb_opt.get()
            
        # Recalculate size from cache (or fetch if missing)
        self.parent_window.recalculate_item(self.idx)
        self.destroy()

class BatchEditDialog(ctk.CTkToplevel):
    def __init__(self, parent, indices):
        super().__init__(parent)
        self.parent_window = parent
        self.indices = indices
        
        self.title(f"Batch Edit ({len(indices)} items)")
        self.geometry("300x650")
        self.transient(parent)
        self.grab_set()
        
        ctk.CTkLabel(self, text="New Quality:", font=("Roboto", 14, "bold")).pack(pady=5)
        self.q_opt = ctk.CTkOptionMenu(self, values=parent.parent.video_qualities)
        self.q_opt.pack(pady=5)
        
        ctk.CTkLabel(self, text="New Format:", font=("Roboto", 14, "bold")).pack(pady=5)
        self.f_opt = ctk.CTkOptionMenu(self, values=parent.parent.file_formats)
        self.f_opt.set("None")
        self.f_opt.pack(pady=5)
        
        self.audio_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(self, text="Audio Only", variable=self.audio_var).pack(pady=10)
        
        ctk.CTkLabel(self, text="Audio Format:", font=("Roboto", 14, "bold")).pack(pady=5)
        self.af_opt = ctk.CTkOptionMenu(self, values=["mp3", "m4a", "opus", "flac"])
        self.af_opt.pack(pady=5)
        
        ctk.CTkLabel(self, text="Subtitles:", font=("Roboto", 14, "bold")).pack(pady=5)
        self.sub_opt = ctk.CTkOptionMenu(self, values=parent.parent.subtitle_options)
        self.sub_opt.set("None")
        self.sub_opt.pack(pady=5)
        
        ctk.CTkLabel(self, text="Thumbnail:", font=("Roboto", 14, "bold")).pack(pady=5)
        self.thumb_opt = ctk.CTkOptionMenu(self, values=parent.parent.thumbnail_options)
        self.thumb_opt.set("None")
        self.thumb_opt.pack(pady=5)
        
        ctk.CTkLabel(self, text="Note: Updates all selected items", text_color="gray").pack(pady=10)
        
        ctk.CTkButton(self, text="Apply to All Selected", command=self.apply).pack(pady=10)
        
    def apply(self):
        new_q = self.q_opt.get()
        new_f = self.f_opt.get()
        new_audio = self.audio_var.get()
        new_af = self.af_opt.get()
        new_sub = self.sub_opt.get()
        new_thumb = self.thumb_opt.get()
        
        for idx in self.indices:
            self.parent_window.items[idx]['quality'] = new_q
            self.parent_window.items[idx]['format'] = new_f
            self.parent_window.items[idx]['audio_only'] = new_audio
            self.parent_window.items[idx]['audio_format'] = new_af
            self.parent_window.items[idx]['subtitle'] = new_sub
            self.parent_window.items[idx]['thumbnail'] = new_thumb
            
        # Recalculate all (instant if cached)
        for idx in self.indices:
            self.parent_window.recalculate_item(idx)
            
        self.destroy()

class BatchSetupDialog(ctk.CTkToplevel):
    def __init__(self, parent, urls):
        super().__init__(parent)
        self.parent_window = parent
        self.urls = urls
        
        self.title("Batch Setup (All Items)")
        
        # Maximize the window
        # ctk doesn't have a direct 'zoomed' state across all platforms, but state('zoomed') works on Windows
        try:
            self.after(200, lambda: self.state('zoomed'))
        except:
            # Fallback for non-Windows
            self.geometry("1000x800")
            
        self.transient(parent)
        self.grab_set()

        # Create a main frame to center content if maximized
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=50, pady=50)
        
        # ---------------- Directory Section ----------------
        dir_frame = ctk.CTkFrame(main_frame)
        dir_frame.pack(fill="x", pady=(0, 20), padx=20)
        
        ctk.CTkLabel(dir_frame, text="Save Batch To:", font=("Roboto", 16, "bold")).pack(side="left", padx=10, pady=15)
        
        self.dir_var = tk.StringVar(value=parent.output_dir.get())
        self.dir_entry = ctk.CTkEntry(dir_frame, textvariable=self.dir_var, width=400, font=("Roboto", 14))
        self.dir_entry.pack(side="left", padx=10, pady=15, expand=True, fill="x")
        
        dir_btn = ctk.CTkButton(dir_frame, text="Browse Folder", command=self.browse_folder, width=120)
        dir_btn.pack(side="left", padx=10, pady=15)
        
        # ---------------- Quality & Format Section ----------------
        settings_frame = ctk.CTkFrame(main_frame)
        settings_frame.pack(fill="x", pady=20, padx=20)
        
        # Left column (Video)
        left_col = ctk.CTkFrame(settings_frame, fg_color="transparent")
        left_col.pack(side="left", expand=True, fill="both", padx=20, pady=20)
        
        ctk.CTkLabel(left_col, text="Video Quality:", font=("Roboto", 14, "bold")).pack(pady=5, anchor="w")
        self.q_opt = ctk.CTkOptionMenu(left_col, values=parent.video_qualities, width=200)
        self.q_opt.set(parent.batch_quality_option.get())
        self.q_opt.pack(pady=(0, 15), anchor="w")
        
        ctk.CTkLabel(left_col, text="Video Format:", font=("Roboto", 14, "bold")).pack(pady=5, anchor="w")
        self.f_opt = ctk.CTkOptionMenu(left_col, values=parent.file_formats, width=200)
        self.f_opt.set(parent.batch_format_option.get())
        self.f_opt.pack(pady=(0, 15), anchor="w")
        
        ctk.CTkLabel(left_col, text="Subtitles:", font=("Roboto", 14, "bold")).pack(pady=5, anchor="w")
        self.sub_opt = ctk.CTkOptionMenu(left_col, values=parent.subtitle_options, width=200)
        self.sub_opt.set(parent.batch_subtitle_option.get())
        self.sub_opt.pack(pady=(0, 15), anchor="w")
        
        ctk.CTkLabel(left_col, text="Thumbnail:", font=("Roboto", 14, "bold")).pack(pady=5, anchor="w")
        self.thumb_opt = ctk.CTkOptionMenu(left_col, values=parent.thumbnail_options, width=200)
        self.thumb_opt.set(parent.batch_thumbnail_option.get())
        self.thumb_opt.pack(pady=(0, 15), anchor="w")
        
        # Right column (Audio)
        right_col = ctk.CTkFrame(settings_frame, fg_color="transparent")
        right_col.pack(side="left", expand=True, fill="both", padx=20, pady=20)
        
        self.audio_var = tk.BooleanVar(value=parent.batch_audio_only.get())
        ctk.CTkCheckBox(right_col, text="Audio Only Mode", variable=self.audio_var, font=("Roboto", 14, "bold")).pack(pady=(5, 15), anchor="w")
        
        ctk.CTkLabel(right_col, text="Audio Format:", font=("Roboto", 14, "bold")).pack(pady=5, anchor="w")
        self.af_opt = ctk.CTkOptionMenu(right_col, values=["mp3", "m4a", "opus", "flac"], width=200)
        self.af_opt.set(parent.batch_audio_format.get())
        self.af_opt.pack(pady=(0, 15), anchor="w")
        
        # ---------------- Actions ----------------
        action_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        action_frame.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkLabel(action_frame, text="Note: These settings will be applied to all items in the batch.", text_color="gray").pack(pady=10)
        
        btn = ctk.CTkButton(action_frame, text="Apply Settings & Fetch Details", font=("Roboto", 16, "bold"), 
                            command=self.apply, height=40, width=250, fg_color="#f59e0b", hover_color="#d97706")
        btn.pack(pady=10)

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.dir_var.get())
        if folder:
            self.dir_var.set(folder)
        
    def apply(self):
        # Update parent's output directory
        self.parent_window.output_dir.set(self.dir_var.get())
        
        # Update parent's batch options
        self.parent_window.batch_quality_option.set(self.q_opt.get())
        self.parent_window.batch_format_option.set(self.f_opt.get())
        
        if self.audio_var.get():
             self.parent_window.batch_audio_only.select()
        else:
             self.parent_window.batch_audio_only.deselect()

        self.parent_window.batch_audio_format.set(self.af_opt.get())
        self.parent_window.batch_subtitle_option.set(self.sub_opt.get())
        self.parent_window.batch_thumbnail_option.set(self.thumb_opt.get())
            
        self.parent_window.batch_start_btn.configure(state="disabled")
        self.parent_window.batch_stop_btn.configure(state="normal")
        self.parent_window.batch_log_msg("\n🔍 Fetching information for all URLs (this may take a moment)...")
        
        # Start info fetching thread
        threading.Thread(target=self.parent_window.info_fetching_task, args=(self.urls,), daemon=True).start()
            
        self.destroy()

class FormatsWindow(ctk.CTkToplevel):
    def __init__(self, parent, url):
        super().__init__(parent)
        self.parent = parent
        self.url = url
        
        self.title("Available Formats")
        self.geometry("800x600")
        
        # Make window appear on top
        self.transient(parent)
        self.lift()
        self.focus_force()
        self.grab_set() # Required because parent (ReviewWindow) is modal
        
        # ID Frame
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(top, text=f"Formats for: {url}", font=("Roboto", 12)).pack(side="left", expand=True, fill="x")
        
        # Text Area
        self.text_area = ctk.CTkTextbox(self, font=("Consolas", 11), wrap="none")
        self.text_area.pack(fill="both", expand=True, padx=10, pady=5)
        self.text_area.insert("0.0", "Fetching formats... please wait...")
        self.text_area.configure(state="disabled")
        
        # Close btn
        ctk.CTkButton(self, text="Close", command=self.destroy).pack(pady=10)
        
        self.after(100, self.fetch_formats)
        
    def fetch_formats(self):
        # Gather all needed info in Main Thread (Tkinter methods are not thread-safe)
        app = self.parent
        # Resolve actual app instance if parent is not it (unlikely here but keeping safeguard)
        if hasattr(app, 'parent') and hasattr(app.parent, 'get_anti_bot_headers'):
             app = app.parent
        
        cmd_base = ["yt-dlp", "--no-warnings", "-F"]
        
        # Get headers/cookies safely
        if hasattr(app, 'get_anti_bot_headers'):
            cmd_base.extend(app.get_anti_bot_headers())
            
            cookies_file = app.cookies_file_path.get()
            if cookies_file and os.path.exists(cookies_file):
                cmd_base.extend(["--cookies", cookies_file])
            else:
                browser = app.cookies_option.get()
                if browser != "None":
                    cmd_base.extend(["--cookies-from-browser", browser])
        
        target_url = self.url
        
        def run():
            cmd = cmd_base + [target_url]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
                output = result.stdout if result.returncode == 0 else result.stderr
            except Exception as e:
                output = f"Error running yt-dlp: {str(e)}"
                
            self.after(0, lambda: self.show_output(output))
            
        threading.Thread(target=run, daemon=True).start()
        
    def show_output(self, text):
        self.text_area.configure(state="normal")
        self.text_area.delete("1.0", "end")
        self.text_area.insert("0.0", text)
        self.text_area.configure(state="disabled")

class HistoryWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("📜 Download History")
        self.geometry("800x500")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        ctk.CTkLabel(header_frame, text="Recent Downloads", 
                     font=("Roboto", 20, "bold")).pack(side="left")
        
        ctk.CTkButton(header_frame, text="🧹 Clear History", 
                     fg_color="#ef4444", hover_color="#dc2626",
                     command=self.clear_history).pack(side="right")
        
        # Scrollable list
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        self.refresh_list()
        
        # Make it modal-ish
        self.grab_set()

    def refresh_list(self):
        """Clear and rebuild the history list"""
        for child in self.scroll_frame.winfo_children():
            child.destroy()
            
        history = self.parent.config_manager.get_history()
        if not history:
            ctk.CTkLabel(self.scroll_frame, text="No download history found.", 
                         font=("Roboto", 14, "italic")).pack(pady=40)
            return
            
        for i, entry in enumerate(history):
            item_frame = ctk.CTkFrame(self.scroll_frame)
            item_frame.pack(fill="x", padx=5, pady=5)
            
            # Title & Date
            text_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            text_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)
            
            ctk.CTkLabel(text_frame, text=entry['title'], font=("Roboto", 13, "bold"), 
                         wraplength=500, justify="left").pack(anchor="w")
            
            sub_text = f"📅 {entry['date']}  |  🔗 {entry['url'][:60]}..."
            ctk.CTkLabel(text_frame, text=sub_text, font=("Roboto", 11), 
                         text_color="gray").pack(anchor="w")
            
            # Action Buttons
            btn_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            btn_frame.pack(side="right", padx=10)
            
            ctk.CTkButton(btn_frame, text="� Copy URL", width=100,
                         command=lambda u=entry['url']: self.copy_url(u)).pack(side="left", padx=5)
            
            ctk.CTkButton(btn_frame, text="�📂 Open Folder", width=100,
                         command=lambda p=entry['path']: self.open_folder(p)).pack(side="left", padx=5)

    def copy_url(self, url):
        """Copy URL to clipboard"""
        self.clipboard_clear()
        self.clipboard_append(url)
        self.update() # Required on some systems
        messagebox.showinfo("Copied", "Link copied to clipboard!")

    def open_folder(self, path):
        """Open the containing folder of a file"""
        folder = os.path.dirname(path)
        if os.path.exists(folder):
            os.startfile(folder)
        else:
            messagebox.showerror("Error", f"Folder not found:\n{folder}")

    def clear_history(self):
        """Confirm and clear history"""
        if messagebox.askyesno("Clear History", "Are you sure you want to delete all download history?"):
            self.parent.config_manager.clear_history()
            self.refresh_list()

class AboutWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("About")
        self.geometry("600x650")
        self.resizable(False, False)
        
        # Center window
        self.update_idletasks()
        try:
            x = (self.winfo_screenwidth() // 2) - (600 // 2)
            y = (self.winfo_screenheight() // 2) - (650 // 2)
            self.geometry(f"+{x}+{y}")
        except: pass
        
        # Tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.tab_about = self.tabview.add("About")
        self.tab_guide = self.tabview.add("How to Use")
        
        self._setup_about_tab()
        self._setup_guide_tab()
        
        # Footer
        ctk.CTkLabel(self, text="© 2026 Pinku Maharana. All rights reserved.", 
                     font=("Roboto", 10), text_color="gray60").pack(side="bottom", pady=10)
        
        # Modal
        self.grab_set()
        
    def _setup_about_tab(self):
        container = ctk.CTkFrame(self.tab_about, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        ctk.CTkLabel(container, text="Pinku's YT-DLP GUI", 
                     font=("Roboto", 26, "bold"), text_color="#818cf8").pack(pady=(10, 5))
        
        ctk.CTkLabel(container, text="Version 2.7.0 Professional", 
                     font=("Roboto", 12, "italic"), text_color="gray").pack(pady=(0, 20))
        
        ctk.CTkFrame(container, height=2, fg_color="gray30").pack(fill="x", pady=10)
        
        # Info
        info_frame = ctk.CTkFrame(container, fg_color="transparent")
        info_frame.pack(fill="both", expand=True)
        
        self._add_info_row(info_frame, "👤 Author:", "Pinku Maharana")
        
        # Website
        website_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        website_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(website_frame, text="🌐 Website:", font=("Roboto", 13, "bold"), width=100, anchor="w").pack(side="left")
        link_lbl = ctk.CTkLabel(website_frame, text="https://github.com/Pinku886/Pinkus_YT_DLP_GUI", font=("Roboto", 13), 
                                text_color="#60a5fa", cursor="hand2")
        link_lbl.pack(side="left")
        link_lbl.bind("<Button-1>", lambda e: self.open_link("https://github.com/Pinku886/Pinkus_YT_DLP_GUI"))
        
        self._add_info_row(info_frame, "📄 License:", "Open Source (GPL-3.0)")
        
        ctk.CTkFrame(container, height=2, fg_color="gray30").pack(fill="x", pady=15)
        
        # Tools
        ctk.CTkLabel(container, text="🛠️ Built With:", font=("Roboto", 15, "bold")).pack(anchor="w", pady=(0, 10))
        
        tools_frame = ctk.CTkFrame(container, fg_color="gray20", corner_radius=10)
        tools_frame.pack(fill="x", padx=5, pady=5)
        
        tools = [
            ("Python 3.11", "Core Language"),
            ("yt-dlp", "Media Downloader"),
            ("CustomTkinter", "UI Framework"),
            ("FFmpeg", "Media Processor")
        ]
        
        for tool, desc in tools:
            t_frame = ctk.CTkFrame(tools_frame, fg_color="transparent")
            t_frame.pack(fill="x", padx=15, pady=5)
            ctk.CTkLabel(t_frame, text=f"• {tool}", font=("Roboto", 12, "bold"), text_color="#a5b4fc").pack(side="left")
            ctk.CTkLabel(t_frame, text=f" - {desc}", font=("Roboto", 11), text_color="gray").pack(side="left")

    def _setup_guide_tab(self):
        info_text = (
            "🚀 Pinku's YT-DLP GUI - User Guide\n\n"
            "--- 1. SINGLE DOWNLOAD ---\n"
            "• Paste a video URL.\n"
            "• Select Quality (Best, 4K, 1080p...) and Format.\n"
            "• Click 'Start Download'.\n"
            "• File Size is calculated in real-time based on your selection!\n\n"
            "--- 2. BATCH DOWNLOAD ---\n"
            "• Paste multiple URLs (one per line).\n"
            "• Toggle 'Expand Playlists':\n"
            "   - Checked: Downloads every video in the playlist as separate items.\n"
            "   - Unchecked: Downloads the whole playlist as one managed item.\n"
            "• Click 'Start Batch' to fetch metadata.\n"
            "• REVIEW WINDOW: \n"
            "   - Modify quality per item.\n"
            "   - Click 'Formats' for the ADVANCED SELECTOR.\n"
            "• Batch Metadata Caching: Metadata is cached locally to speed up subsequent batches.\n\n"
            "--- 3. ADVANCED FEATURES ---\n"
            "• Advanced Format Selector: In Batch Review, click 'Formats'.\n"
            "  - View detailed stream info (Resolution, Codec, Bitrate, Size).\n"
            "  - Select a Video stream and an Audio stream (Ctrl+Click) to combine them.\n"
            "• Real-time Metadata: Changing quality options updates expected file size instantly.\n"
            "• WebP Thumbnails: Select 'webp' in Thumbnail options for the highest quality image.\n\n"
            "--- TROUBLESHOOTING ---\n"
            "• Bot Detection? Use 'Cookies' option with your browser or a cookies.txt file.\n"
            "• 403 Forbidden? Check your IP/VPN.\n"
            "• FFmpeg Missing? Automatic check included. Use 'Fix Config' if needed.\n"
        )
        
        text_area = ctk.CTkTextbox(self.tab_guide, font=("Roboto", 13), wrap="word")
        text_area.pack(expand=True, fill="both", padx=10, pady=10)
        text_area.insert("0.0", info_text)
        text_area.configure(state="disabled")

    def _add_info_row(self, parent, label, value):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=5)
        ctk.CTkLabel(row, text=label, font=("Roboto", 13, "bold"), width=100, anchor="w").pack(side="left")
        ctk.CTkLabel(row, text=value, font=("Roboto", 13)).pack(side="left")

    def open_link(self, url):
        import webbrowser
        webbrowser.open(url)

    def get_video_info(self, url, quality, fmt):
        """Helper to get video info for simple download"""
        # Reuse fetch logic
        # For simple download, we just need metadata to estimate size
        # But wait, 'start_download_thread' calls this to get (title, size_str, duration)
        # We can implement a synchronous version or reuse the async fetch
        
        cmd = ["yt-dlp", "-J", "--no-warnings"]
        cmd.extend(self.get_anti_bot_headers())
        
        cookies_file = self.cookies_file_path.get()
        if cookies_file and os.path.exists(cookies_file):
             cmd.extend(["--cookies", cookies_file])
        else:
             browser = self.cookies_option.get()
             if browser != "None":
                 cmd.extend(["--cookies-from-browser", browser])
        
        cmd.append(url)
        
        title = "Unknown"
        size_str = "Calculating..."
        duration = "?"
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                title = data.get('title', 'Unknown')
                duration = self.format_seconds(data.get('duration', 0))
                
                # Calculate size
                size_str = self.calculate_size_from_metadata(data, quality)
        except: pass
        
        return title, size_str, duration

class AdvancedFormatsWindow(ctk.CTkToplevel):
    def __init__(self, parent, url, metadata, callback):
        super().__init__(parent)
        self.parent = parent
        self.url = url
        self.metadata = metadata
        self.callback = callback
        
        self.title("Advanced Format Selector")
        self.geometry("900x600")
        
        # Modal setup
        self.transient(parent)
        self.lift()
        self.focus_force()
        self.grab_set()
        
        # Header
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(top, text=f"Select Formats for: {url}", font=("Roboto", 14, "bold")).pack(side="left")
        
        # Instruction
        ctk.CTkLabel(self, text="Select 1 Video + 1 Audio stream (Ctrl+Click) to combine, or just 1 stream.", 
                     text_color="gray").pack(padx=10, pady=(0,5))
        
        # Table Frame
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Treeview Styles
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
                        background="#2b2b2b", 
                        foreground="white", 
                        fieldbackground="#2b2b2b",
                        rowheight=25)
        style.configure("Treeview.Heading", background="#3b3b3b", foreground="white", relief="flat")
        style.map("Treeview", background=[('selected', '#10b981')])
        
        # Columns
        cols = ("ID", "Ext", "Resolution", "FPS", "Bitrate", "Size", "Codec", "Proto", "Note")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="extended")
        
        # Headings
        for col in cols:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_column(c, False))
            self.tree.column(col, width=80 if col != "Note" else 150)
            
        self.tree.column("ID", width=50)
        self.tree.column("Ext", width=50)
        self.tree.column("FPS", width=50)
            
        # Scrollbar
        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(btn_frame, text="Apply Selection", fg_color="#10b981", hover_color="#059669",
                      command=self.apply_selection).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="#ef4444", hover_color="#dc2626",
                      command=self.destroy).pack(side="right", padx=5)
        
        # Tags for coloring
        self.tree.tag_configure("video", foreground="#60a5fa") # Blueish
        self.tree.tag_configure("audio", foreground="#facc15") # Yellowish
        self.tree.tag_configure("both", foreground="white")
        
        if self.metadata:
            self.populate_table(self.metadata.get('formats', []))
        else:
            self.fetch_metadata()
            
    def fetch_metadata(self):
        # Fetch generic metadata if missing
        def run():
            # Check for local binaries
            app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            local_ytdlp = os.path.join(app_dir, "yt-dlp.exe")
            
            exe = local_ytdlp if os.path.exists(local_ytdlp) else "yt-dlp"
            cmd = [exe, "-J", "--no-warnings"]
            # Add headers/cookies
            app = self.parent.parent # ReviewWindow -> YtDlpGui
            if hasattr(app, 'get_anti_bot_headers'):
                cmd.extend(app.get_anti_bot_headers())
                cookies_file = app.cookies_file_path.get()
                if cookies_file and os.path.exists(cookies_file):
                    cmd.extend(["--cookies", cookies_file])
                else:
                    browser = app.cookies_option.get()
                    if browser != "None":
                        cmd.extend(["--cookies-from-browser", browser])
            
            cmd.append(self.url)
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
                if res.returncode == 0:
                    import json
                    data = json.loads(res.stdout)
                    self.after(0, lambda: self.populate_table(data.get('formats', [])))
            except: pass
            
        threading.Thread(target=run, daemon=True).start()

    def populate_table(self, formats):
        for f in formats:
            fid = f.get('format_id', 'N/A')
            ext = f.get('ext', 'N/A')
            
            # Res
            w = f.get('width')
            h = f.get('height')
            res = f"{w}x{h}" if w and h else "N/A"
            if res == "N/A" and f.get('vcodec') != 'none': res = "Video"
            if f.get('vcodec') == 'none': res = "Audio"
            
            fps = f.get('fps', '')
            tbr = f.get('tbr', 0)
            filesize = f.get('filesize') or f.get('filesize_approx')
            size_str = self.parent.parent.format_size_raw(filesize) if filesize else "N/A"
            
            proto = f.get('protocol', '')
            vcodec = f.get('vcodec', 'none')
            acodec = f.get('acodec', 'none')
            note = f.get('format_note', '')
            
            # Determine type
            ftype = "both"
            if vcodec != 'none' and acodec == 'none': ftype = "video"
            elif vcodec == 'none' and acodec != 'none': ftype = "audio"
            
            values = (fid, ext, res, fps, f"{tbr}k" if tbr else "", size_str, f"{vcodec}/{acodec}", proto, note)
            self.tree.insert("", "end", values=values, tags=(ftype,))

    def sort_column(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        # Try numeric sort
        try:
            l.sort(key=lambda t: float(t[0].replace('k','').replace('x','').split()[0]), reverse=reverse)
        except:
            l.sort(reverse=reverse)
            
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)
            
        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    def apply_selection(self):
        selected = self.tree.selection()
        if not selected: return
        
        ids = []
        notes = []
        for item in selected:
            vals = self.tree.item(item)['values']
            ids.append(str(vals[0])) # ID
            notes.append(f"{vals[2]} ({vals[1]})")
            
        # Combine
        # yt-dlp expects video+audio or just single
        final_id = "+".join(ids)
        final_note = " + ".join(notes)
        
        if self.callback:
            self.callback(final_id, final_note)
            
        self.destroy()

if __name__ == "__main__":
    app = YtDlpGui()
    app.mainloop()
