import json
import os

class ConfigManager:
    def __init__(self):
        self.config_dir = os.path.join(os.getenv('APPDATA'), 'yt-dlp')
        self.config_file = os.path.join(self.config_dir, 'app_config.json')
        self.log_file = os.path.join(self.config_dir, 'app.log')
        self.history_file = os.path.join(self.config_dir, 'history.json')
        self._ensure_dir_exists()
        self.defaults = {
            "output_dir": os.path.expanduser("~\\Downloads"),
            "quality": "Best",
            "format": "mp4",
            "cookies_browser": "None",
            "cookies_file_path": "",
            "subtitle_option": "None",
            "batch_quality": "Best",
            "batch_format": "mp4",
            "batch_audio_only": False,
            "batch_audio_format": "mp3",
            "batch_urls": ""
        }

    def _ensure_dir_exists(self):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

    def load_config(self):
        """Load configuration from JSON file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return {**self.defaults, **json.load(f)}
            except:
                return self.defaults
        return self.defaults

    def save_config(self, config_data):
        """Save configuration to JSON file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def append_log(self, message):
        """Append a message to the persistent log file"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(message + "\n")
        except:
            pass

    def get_last_logs(self, lines=50):
        """Get the last N lines from the log file"""
        if not os.path.exists(self.log_file):
            return ""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                content = f.readlines()
                return "".join(content[-lines:])
        except:
            return ""

    def add_to_history(self, title, url, path):
        """Save a new successful download to history.json"""
        import datetime
        history = self.get_history()
        entry = {
            "title": title,
            "url": url,
            "path": path,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        history.insert(0, entry) # Add to top
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history[:500], f, indent=4) # Keep last 500
        except:
            pass

    def get_history(self):
        """Load history from JSON file"""
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def clear_history(self):
        """Wipe the history file"""
        try:
            if os.path.exists(self.history_file):
                os.remove(self.history_file)
        except:
            pass
