"""
Progress tracking functionality for music players - THREAD SAFE VERSION
"""
import json
import os
import time
import threading
from datetime import datetime
from utils.time_utils import format_time
from config.settings import PROGRESS_FILE

class ProgressTracker:
    def __init__(self):
        self.progress_file = PROGRESS_FILE
        self._write_lock = threading.Lock()
        print(f"ProgressTracker initialized: {os.path.abspath(self.progress_file)}")
    
    def save_progress_info(self, progress_data):
        """Save progress information to JSON file for web consumption - THREAD SAFE"""
        with self._write_lock:
            try:
                progress_path = os.path.abspath(self.progress_file)
                
                if progress_data:
                    # Add timestamp
                    progress_data["timestamp"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                    progress_data["timestamp_unix"] = time.time()
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(progress_path), exist_ok=True)
                
                # Write to temp file first, then rename for atomic operation
                temp_path = progress_path + ".tmp"
                
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(progress_data or {}, f, indent=2)
                
                # Atomic rename (Windows compatible)
                if os.path.exists(progress_path):
                    os.remove(progress_path)
                os.rename(temp_path, progress_path)
                
            except Exception as e:
                print(f"ERROR saving progress info: {e}")
                # Clean up temp file if it exists
                temp_path = progress_path + ".tmp"
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except:
                    pass
    
    def clear_progress(self):
        """Clear progress information"""
        self.save_progress_info(None)
    
    def create_progress_data(self, title, artist, album, position_seconds=0, 
                           duration_seconds=0, is_playing=True, player="Unknown"):
        """Create standardized progress data structure"""
        return {
            "title": title,
            "artist": artist,
            "album": album,
            "position_seconds": position_seconds,
            "duration_seconds": duration_seconds,
            "position_formatted": format_time(position_seconds),
            "duration_formatted": format_time(duration_seconds),
            "progress_percentage": (position_seconds / duration_seconds * 100) if duration_seconds > 0 else 0,
            "is_playing": is_playing,
            "player": player
        }
    
    def update_progress(self, title, artist, album, position_seconds, 
                       duration_seconds, is_playing=True, player="Unknown"):
        """Update progress with new timing information"""
        progress_data = self.create_progress_data(
            title, artist, album, position_seconds, 
            duration_seconds, is_playing, player
        )
        self.save_progress_info(progress_data)
        return progress_data