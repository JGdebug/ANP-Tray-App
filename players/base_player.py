"""
Base player class for music player implementations - OPTIMIZED CLEARING
"""
import threading
from abc import ABC, abstractmethod

# Player state constants
class PlayerState:
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2

class BasePlayer(ABC):
    def __init__(self, name, file_manager, progress_tracker, artwork_manager):
        self.name = name
        self.file_manager = file_manager
        self.progress_tracker = progress_tracker
        self.artwork_manager = artwork_manager
        
        # State tracking
        self.is_running = False
        self.stop_event = threading.Event()
        self.last_track_info = None
        self.artwork_updated = False
        self.last_clear_time = 0
    
    @abstractmethod
    def is_available(self):
        """Check if this player is available on the system"""
        pass
    
    @abstractmethod
    def start_monitoring(self):
        """Start monitoring this player"""
        pass
    
    @abstractmethod
    def stop_monitoring(self):
        """Stop monitoring this player"""
        pass
    
    def track_changed(self, current_track_info):
        """Check if the track has changed"""
        if self.last_track_info != current_track_info:
            return True
        return False
    
    def update_track_info(self, title, artist, album):
        """Update track information and write to files"""
        self.last_track_info = (title, artist, album)
        
        # Write to nowplaying.txt
        self.file_manager.write_now_playing(title, artist, album)
        
        # Reset artwork flag
        self.artwork_updated = False
    
    def update_progress(self, title, artist, album, position_seconds, duration_seconds, is_playing=True):
        """Update progress information"""
        self.progress_tracker.update_progress(
            title, artist, album, position_seconds, 
            duration_seconds, is_playing, self.name
        )
    
    def clear_all_data(self):
        """Clear all player data - RATE LIMITED"""
        import time
        current_time = time.time()
        
        # Rate limit clearing to once per 2 seconds
        if current_time - self.last_clear_time < 2.0:
            return
        
        self.last_clear_time = current_time
        self.last_track_info = None
        self.artwork_updated = False
        
        # Clear files
        self.file_manager.clear_now_playing()
        self.progress_tracker.clear_progress()