"""
iTunes player implementation - FIXED COM THREADING ISSUES
"""
import threading
import time
from players.base_player import BasePlayer, PlayerState
from config.settings import PROGRESS_UPDATE_INTERVAL, ITUNES_POLLING_INTERVAL

class iTunesPlayer(BasePlayer):
    def __init__(self, file_manager, progress_tracker, artwork_manager):
        super().__init__("iTunes", file_manager, progress_tracker, artwork_manager)
        self.itunes = None
        self.last_progress_update = 0
        self._com_initialized = False
        self.last_known_state = None
        self.consecutive_empty_checks = 0
        self._monitoring_thread = None
    
    def is_available(self):
        """Check if iTunes is available"""
        return self._test_itunes_availability()
    
    def _test_itunes_availability(self):
        """Test iTunes availability in a separate thread (COM-safe)"""
        result = [False]  # Use list to store result from thread
        
        def test_thread():
            try:
                import pythoncom
                import comtypes.client
                
                # Initialize COM properly for this thread
                pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
                
                try:
                    itunes = comtypes.client.CreateObject("iTunes.Application")
                    if itunes:
                        # Quick test - try to access a simple property
                        _ = itunes.Version
                        result[0] = True
                except Exception as e:
                    print(f"iTunes availability test failed: {e}")
                    result[0] = False
                finally:
                    pythoncom.CoUninitialize()
                    
            except Exception as e:
                print(f"COM initialization failed in test: {e}")
                result[0] = False
        
        # Run test in separate thread
        test_thread_obj = threading.Thread(target=test_thread, daemon=True)
        test_thread_obj.start()
        test_thread_obj.join(timeout=5.0)  # 5 second timeout
        
        return result[0]
    
    def start_monitoring(self):
        """Start monitoring iTunes"""
        if self.is_running:
            print("iTunes monitoring already running")
            return
        
        self.is_running = True
        self.stop_event.clear()
        self.consecutive_empty_checks = 0
        self.last_known_state = None
        
        # Start monitoring in separate thread with proper COM handling
        self._monitoring_thread = threading.Thread(target=self._safe_monitoring_wrapper, daemon=True)
        self._monitoring_thread.start()
        print("Started iTunes monitoring")
    
    def stop_monitoring(self):
        """Stop monitoring iTunes"""
        if not self.is_running:
            return
        
        print("Stopping iTunes monitoring...")
        self.stop_event.set()
        self.is_running = False
        
        # Wait for monitoring thread to finish (with timeout)
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=3.0)
        
        # Clear data ONCE on stop
        self.clear_all_data()
        print("iTunes monitoring stopped")
    
    def _safe_monitoring_wrapper(self):
        """Safe wrapper for monitoring with proper COM handling"""
        try:
            self._run_monitoring_loop()
        except Exception as e:
            print(f"iTunes monitoring wrapper error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Ensure COM is cleaned up
            try:
                if self._com_initialized:
                    import pythoncom
                    pythoncom.CoUninitialize()
                    self._com_initialized = False
            except:
                pass
    
    def _run_monitoring_loop(self):
        """Run the iTunes monitoring loop with proper COM initialization"""
        # Initialize COM in THIS thread
        try:
            import pythoncom
            import comtypes.client
            
            print("Initializing COM for iTunes monitoring...")
            pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
            self._com_initialized = True
            
            # Create iTunes COM object in this thread
            self.itunes = comtypes.client.CreateObject("iTunes.Application")
            if not self.itunes:
                print("Failed to create iTunes COM object")
                return
            
            print("iTunes COM object created successfully")
            
        except Exception as e:
            print(f"COM initialization error: {e}")
            self.clear_all_data()
            return
        
        # Main monitoring loop
        try:
            while not self.stop_event.is_set() and self.is_running:
                try:
                    self._check_itunes_status()
                    time.sleep(ITUNES_POLLING_INTERVAL)
                except Exception as e:
                    print(f"iTunes polling error: {e}")
                    self.consecutive_empty_checks += 1
                    if self.consecutive_empty_checks >= 3:
                        print("Multiple iTunes errors - clearing data")
                        self.clear_all_data()
                        self.consecutive_empty_checks = 0
                    time.sleep(ITUNES_POLLING_INTERVAL)
        
        except Exception as e:
            print(f"iTunes monitoring loop error: {e}")
            import traceback
            traceback.print_exc()
            self.clear_all_data()
        
        finally:
            # Cleanup COM - CRITICAL for preventing GIL issues
            self.itunes = None
            if self._com_initialized:
                try:
                    print("Cleaning up iTunes COM...")
                    pythoncom.CoUninitialize()
                    self._com_initialized = False
                    print("iTunes COM cleanup complete")
                except Exception as cleanup_error:
                    print(f"COM cleanup error: {cleanup_error}")
    
    def _check_itunes_status(self):
        """Check iTunes status and update accordingly - COM THREAD SAFE"""
        if not self.itunes or not self.is_running:
            return
        
        try:
            # Access iTunes properties in the same thread where COM was initialized
            track = self.itunes.CurrentTrack
            player_state = self.itunes.PlayerState
            
            # Handle no track case
            if not track:
                self.consecutive_empty_checks += 1
                if self.consecutive_empty_checks >= 5:
                    if self.last_known_state != "empty":
                        print("iTunes has no current track - clearing files")
                        self.clear_all_data()
                        self.last_known_state = "empty"
                    self.consecutive_empty_checks = 0
                return
            
            # Reset consecutive empty checks
            self.consecutive_empty_checks = 0
            
            # Get track info (all in same COM thread)
            title = track.Name or "Unknown Title"
            artist = track.Artist or "Unknown Artist"
            album = track.Album or "Unknown Album"
            
            # Handle different player states
            if player_state == PlayerState.STOPPED:
                if self.last_known_state != "stopped":
                    print("iTunes stopped - clearing files")
                    self.clear_all_data()
                    self.last_known_state = "stopped"
                return
            elif player_state == PlayerState.PAUSED:
                if self.last_known_state != "paused":
                    print("iTunes paused - clearing files")
                    self.clear_all_data()
                    self.last_known_state = "paused"
                return
            elif player_state == PlayerState.PLAYING:
                self._handle_playing_track(track, title, artist, album)
                self.last_known_state = "playing"
            else:
                if self.last_known_state == "playing":
                    print(f"iTunes unknown state ({player_state}) - clearing files")
                    self.clear_all_data()
                    self.last_known_state = "unknown"
        
        except Exception as e:
            print(f"iTunes status check error: {e}")
            self.consecutive_empty_checks += 1
            if self.consecutive_empty_checks >= 3:
                self.clear_all_data()
                self.consecutive_empty_checks = 0
    
    def _handle_playing_track(self, track, title, artist, album):
        """Handle a playing track - COM THREAD SAFE"""
        current_time = time.time()
        current_track_info = (title, artist, album)
        
        # Check if this is a new track
        if self.track_changed(current_track_info):
            print(f"New iTunes track detected: {artist} - {title}")
            
            # Handle artwork for new track (pass the COM track object)
            try:
                self.artwork_manager.handle_itunes_artwork(track, artist, album, title)
                self.artwork_updated = True
            except Exception as artwork_error:
                print(f"iTunes artwork error: {artwork_error}")
            
            # Small delay for artwork processing
            time.sleep(0.4)
            
            # Update track info
            self.update_track_info(title, artist, album)
        
        # Update progress every second
        if current_time - self.last_progress_update >= PROGRESS_UPDATE_INTERVAL:
            try:
                # Access COM properties in same thread
                position_seconds = self.itunes.PlayerPosition
                duration_seconds = track.Duration
                
                self.update_progress(title, artist, album, position_seconds, duration_seconds, True)
                self.last_progress_update = current_time
            
            except Exception as progress_e:
                print(f"Error getting iTunes progress: {progress_e}")