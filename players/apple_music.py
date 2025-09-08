"""
Apple Music player implementation - FIXED STATUS HANDLING
"""
import asyncio
import threading
import time
import winrt.windows.media.control as wmc
from players.base_player import BasePlayer
from utils.time_utils import timespan_to_seconds
from config.settings import PROGRESS_UPDATE_INTERVAL, APPLE_MUSIC_POLLING_INTERVAL

class AppleMusicPlayer(BasePlayer):
    def __init__(self, file_manager, progress_tracker, artwork_manager):
        super().__init__("Apple Music", file_manager, progress_tracker, artwork_manager)
        self.loop = None
        self.session = None
        self.progress_task = None
        self._shutdown_lock = threading.Lock()
        self.current_track_id = None  # Track unique identifier
    
    def is_available(self):
        """Check if Apple Music is available"""
        try:
            return True  # Apple Music WinRT APIs are generally available on Windows 10+
        except Exception:
            return False
    
    def start_monitoring(self):
        """Start monitoring Apple Music"""
        if self.is_running:
            print("Apple Music monitoring already running")
            return
        
        self.is_running = True
        self.stop_event.clear()
        
        # Start monitoring in separate thread
        monitoring_thread = threading.Thread(target=self._run_monitoring_loop, daemon=True)
        monitoring_thread.start()
        print("Started Apple Music monitoring")
    
    def stop_monitoring(self):
        """Stop monitoring Apple Music"""
        with self._shutdown_lock:
            if not self.is_running:
                return
            
            print("Stopping Apple Music monitoring...")
            self.stop_event.set()
            self.is_running = False
            
            # Cancel progress task
            if self.progress_task and self.loop and not self.loop.is_closed():
                try:
                    self.loop.call_soon_threadsafe(self.progress_task.cancel)
                except:
                    pass
            
            # Remove event handlers BEFORE stopping loop
            if self.session:
                try:
                    self.session.remove_media_properties_changed(self._on_media_changed)
                    self.session.remove_playback_info_changed(self._on_playback_changed)
                    self.session = None
                except:
                    pass
            
            # Stop event loop
            if self.loop and self.loop.is_running():
                try:
                    self.loop.call_soon_threadsafe(self.loop.stop)
                except:
                    pass
            
            # Clear data
            self.clear_all_data()
            self.loop = None
            self.current_track_id = None
            print("Apple Music monitoring stopped")
    
    def _run_monitoring_loop(self):
        """Run the asyncio monitoring loop"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._monitor_apple_music())
        except Exception as e:
            print(f"Apple Music monitoring error: {e}")
        finally:
            try:
                if not self.loop.is_closed():
                    self.loop.close()
            except:
                pass
    
    async def _get_apple_music_session(self):
        """Get the Apple Music session"""
        try:
            manager = await wmc.GlobalSystemMediaTransportControlsSessionManager.request_async()
            sessions = manager.get_sessions()
            for session in sessions:
                if "applemusic" in session.source_app_user_model_id.lower():
                    return session
            return None
        except Exception as e:
            print(f"Error getting Apple Music session: {e}")
            return None
    
    async def _monitor_apple_music(self):
        """Main Apple Music monitoring loop"""
        try:
            self.session = await self._get_apple_music_session()
            if not self.session:
                print("Apple Music session not found")
                self.clear_all_data()
                return
            
            # Set up event handlers
            self.session.add_media_properties_changed(self._on_media_changed)
            self.session.add_playback_info_changed(self._on_playback_changed)
            
            # Initial update
            await self._handle_track_change()
            
            # Start continuous progress updates
            self.progress_task = asyncio.create_task(self._continuous_progress_update())
            
            # Keep monitoring until stopped
            while not self.stop_event.is_set() and self.is_running:
                await asyncio.sleep(APPLE_MUSIC_POLLING_INTERVAL)
        
        except Exception as e:
            print(f"Apple Music monitoring loop error: {e}")
        
        finally:
            # Cleanup
            if self.progress_task:
                self.progress_task.cancel()
                try:
                    await self.progress_task
                except asyncio.CancelledError:
                    pass
    
    def _on_media_changed(self, session, args):
        """Handle media property changes - FIXED RACE CONDITION"""
        with self._shutdown_lock:
            if self.loop and not self.loop.is_closed() and self.is_running:
                try:
                    asyncio.run_coroutine_threadsafe(self._handle_track_change(), self.loop)
                except Exception:
                    pass  # Silently ignore if loop is shutting down
    
    def _on_playback_changed(self, session, args):
        """Handle playback state changes - FIXED RACE CONDITION"""
        with self._shutdown_lock:
            if self.loop and not self.loop.is_closed() and self.is_running:
                try:
                    asyncio.run_coroutine_threadsafe(self._update_progress_only(), self.loop)
                except Exception:
                    pass  # Silently ignore if loop is shutting down
    
    def _create_track_id(self, title, artist, album, duration=0):
        """Create a unique track identifier"""
        return f"{artist}::{title}::{album}::{duration}"
    
    def _get_status_name(self, status):
        """Safely get status name - handles both enum and int"""
        try:
            if hasattr(status, 'name'):
                return status.name.lower()
            else:
                # Handle integer status codes
                status_map = {
                    0: "closed",
                    1: "opened", 
                    2: "changing",
                    3: "stopped",
                    4: "playing",
                    5: "paused"
                }
                return status_map.get(int(status), f"unknown({status})")
        except:
            return f"unknown({status})"
    
    async def _handle_track_change(self):
        """Handle track changes and artwork updates - FIXED STATUS HANDLING"""
        try:
            if not self.session or not self.is_running:
                return
            
            status = self.session.get_playback_info()
            current_status = status.playback_status
            
            # Get status name safely
            status_name = self._get_status_name(current_status)
            
            # Check for stopped/paused states
            if current_status in (
                wmc.GlobalSystemMediaTransportControlsSessionPlaybackStatus.STOPPED,
                wmc.GlobalSystemMediaTransportControlsSessionPlaybackStatus.PAUSED,
            ):
                print(f"Apple Music {status_name} - clearing files")
                self.clear_all_data()
                self.current_track_id = None
                return
            
            # Must be playing
            if current_status != wmc.GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING:
                print(f"Apple Music not playing (status: {status_name}) - clearing files")
                self.clear_all_data()
                self.current_track_id = None
                return
            
            # Get media info
            info = await self.session.try_get_media_properties_async()
            if not info or (not info.title and not info.artist and not info.album_title):
                print("No valid Apple Music media info - clearing files")
                self.clear_all_data()
                self.current_track_id = None
                return
            
            # Parse track info
            full_artist = info.artist or ""
            album = info.album_title or "Unknown Album"
            title = info.title or "Unknown Title"
            
            # Handle artist/album parsing (Apple Music sometimes puts album in artist field)
            if "—" in full_artist:
                artist, album_candidate = map(str.strip, full_artist.split("—", 1))
                if album_candidate:
                    album = album_candidate
            else:
                artist = full_artist or "Unknown Artist"
            
            # Get duration for unique track ID
            timeline = self.session.get_timeline_properties()
            duration = 0
            if timeline:
                duration = timespan_to_seconds(timeline.end_time)
            
            # Create unique track identifier
            track_id = self._create_track_id(title, artist, album, duration)
            
            # Check if this is truly a new track
            if track_id != self.current_track_id:
                print(f"New Apple Music track detected: {artist} - {title}")
                self.current_track_id = track_id
                
                # Clear old track data first
                self.clear_all_data()
                
                # Wait a moment for any pending operations
                await asyncio.sleep(0.2)
                
                # Handle artwork BEFORE writing track info
                print("Processing artwork...")
                artwork_success = await self.artwork_manager.handle_apple_music_artwork(self.session, artist, album, title)
                
                if artwork_success:
                    print("Artwork processed successfully")
                else:
                    print("Artwork processing failed")
                
                # Wait for artwork processing to complete
                await asyncio.sleep(0.5)
                
                # Now write track info
                print("Writing track info...")
                self.update_track_info(title, artist, album)
                
                # Reset artwork flag
                self.artwork_updated = True
            
            # Update progress regardless of track change
            await self._update_progress_data(title, artist, album)
        
        except Exception as e:
            if self.is_running:  # Only log if we're still supposed to be running
                print(f"Apple Music track change error: {e}")
                import traceback
                traceback.print_exc()
                self.clear_all_data()
                self.current_track_id = None
    
    async def _update_progress_only(self):
        """Handle playback state changes (just progress updates)"""
        if self.current_track_id and self.last_track_info and self.is_running:
            title, artist, album = self.last_track_info
            await self._update_progress_data(title, artist, album)
    
    async def _update_progress_data(self, title, artist, album):
        """Update progress data - THREAD SAFE"""
        try:
            if not self.session or not self.is_running:
                return
            
            status = self.session.get_playback_info()
            if status.playback_status != wmc.GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING:
                return
            
            timeline = self.session.get_timeline_properties()
            if timeline:
                position_seconds = timespan_to_seconds(timeline.position)
                duration_seconds = timespan_to_seconds(timeline.end_time)
            else:
                position_seconds = 0
                duration_seconds = 0
            
            # Update progress in a thread-safe way
            try:
                self.update_progress(title, artist, album, position_seconds, duration_seconds, True)
            except Exception as progress_error:
                if self.is_running:
                    print(f"Progress update error: {progress_error}")
        
        except Exception as e:
            if self.is_running:  # Only log if we're still supposed to be running
                print(f"Error updating Apple Music progress: {e}")
    
    async def _continuous_progress_update(self):
        """Continuously update progress every second"""
        while not self.stop_event.is_set() and self.is_running:
            try:
                if self.session and self.current_track_id and self.last_track_info and self.is_running:
                    title, artist, album = self.last_track_info
                    await self._update_progress_data(title, artist, album)
                
                await asyncio.sleep(PROGRESS_UPDATE_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.is_running:  # Only log if we're still supposed to be running
                    print(f"Continuous progress update error: {e}")
                await asyncio.sleep(PROGRESS_UPDATE_INTERVAL)