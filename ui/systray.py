"""
System tray management for ANP Tray App - FIXED BLOCKING ISSUE
"""
import time
import threading
import tkinter as tk
from tkinter import messagebox
import webbrowser
import os
from config.settings import ICON_DEFAULT, ICON_APPLE, ICON_ITUNES, PLAYER_APPLE_MUSIC, PLAYER_ITUNES, APP_NAME, APP_AUTHOR, APP_WEBSITE, APP_DESCRIPTION

class SystemTrayManager:
    def __init__(self, player_manager, about_dialog):
        self.player_manager = player_manager
        self.about_dialog = about_dialog
        self.current_info = {"track": "(waiting...)", "player": "None"}
        self.running = False
        self.systray = None
        self.fallback_mode = False
        self.quit_requested = False
        self._lock = threading.Lock()
    
    def start(self):
        """Start the system tray with fallback to console mode"""
        # First, check if icon files exist
        self._ensure_icon_files()
        
        try:
            print("Attempting to start system tray...")
            self._start_systray_blocking()
        except Exception as tray_error:
            print(f"System tray failed to start: {tray_error}")
            print("Falling back to console mode...")
            self._start_console_mode()
    
    def _ensure_icon_files(self):
        """Ensure icon files exist or create fallback"""
        icon_files = [ICON_DEFAULT, ICON_APPLE, ICON_ITUNES]
        
        for icon_path in icon_files:
            abs_path = os.path.abspath(icon_path)
            if not os.path.exists(abs_path):
                print(f"Icon file missing: {abs_path}")
                # Create a simple fallback icon file
                self._create_fallback_icon(abs_path)
    
    def _create_fallback_icon(self, icon_path):
        """Create a simple fallback .ico file"""
        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(icon_path), exist_ok=True)
            
            # Create a minimal 16x16 ICO file (basic format)
            ico_header = (
                b'\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00\x20\x00'
                b'\x68\x04\x00\x00\x16\x00\x00\x00'
            )
            
            bitmap_header = (
                b'\x28\x00\x00\x00\x10\x00\x00\x00\x20\x00\x00\x00\x01\x00'
                b'\x20\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            )
            
            # Create blue pixels (BGRA format)
            pixel_data = b'\xFF\x80\x00\xFF' * 256  # 16x16 orange pixels
            
            # AND mask (transparency mask - all opaque)
            and_mask = b'\x00' * 32  # 16x16 bits = 32 bytes
            
            ico_data = ico_header + bitmap_header + pixel_data + and_mask
            
            with open(icon_path, 'wb') as f:
                f.write(ico_data)
            
            print(f"Created fallback icon: {icon_path}")
        except Exception as e:
            print(f"Failed to create fallback icon {icon_path}: {e}")
    
    def _start_systray_blocking(self):
        """Start the system tray with proper blocking"""
        try:
            from infi.systray import SysTrayIcon
            
            # Verify icon file exists
            icon_path = os.path.abspath(ICON_DEFAULT)
            if not os.path.exists(icon_path):
                print(f"Icon file not found: {icon_path}")
                raise FileNotFoundError(f"Icon file missing: {icon_path}")
            
            menu_options = (
                (f"Use {PLAYER_APPLE_MUSIC}", None, self._switch_to_apple_music),
                (f"Use {PLAYER_ITUNES}", None, self._switch_to_itunes),
                ("Show Status", None, self._show_status_popup),
                ("About", None, self._show_about),
            )
            
            print(f"Creating system tray with icon: {icon_path}")
            self.systray = SysTrayIcon(
                icon_path,
                "ANP - Now Playing", 
                menu_options, 
                on_quit=self._on_quit
            )
            
            # Update initial state
            self._update_display()
            
            print("✅ System tray created successfully")
            print("Right-click the system tray icon to access menu")
            
            # Start the system tray in a separate thread
            self.running = True
            self.quit_requested = False
            
            # Start systray in background thread
            tray_thread = threading.Thread(target=self._systray_thread, daemon=False)
            tray_thread.start()
            
            # Custom blocking loop - wait until quit is requested
            print("System tray is now active. Monitoring music...")
            last_status_time = 0
            
            while self.running and not self.quit_requested:
                current_time = time.time()
                
                # Show periodic status
                if current_time - last_status_time >= 60:  # Every minute
                    current_player = self.player_manager.get_current_player_name()
                    print(f"[{time.strftime('%H:%M:%S')}] System tray active - {current_player} monitoring")
                    last_status_time = current_time
                
                time.sleep(1)
            
            print("System tray shutdown requested")
            
        except ImportError as e:
            print(f"System tray library not available: {e}")
            print("Install with: pip install infi.systray")
            raise
        except Exception as e:
            print(f"System tray initialization failed: {e}")
            raise
    
    def _systray_thread(self):
        """Run system tray in separate thread"""
        try:
            if self.systray:
                print("Starting system tray thread...")
                self.systray.start()
                print("System tray thread ended")
        except Exception as e:
            print(f"System tray thread error: {e}")
    
    def _start_console_mode(self):
        """Run in console mode as fallback"""
        self.fallback_mode = True
        self.running = True
        
        print("\n" + "="*60)
        print("ANP TRAY APP - CONSOLE MODE")
        print("="*60)
        print("System tray not available. Running in console mode.")
        print("")
        print("Commands:")
        print("  1 - Switch to Apple Music")
        print("  2 - Switch to iTunes") 
        print("  s - Show current status")
        print("  c - Clear screen")
        print("  q - Quit")
        print("  h - Show this help")
        print("="*60)
        print("App is now monitoring music and writing files...")
        print("="*60)
        
        # Start input handler in separate thread
        input_thread = threading.Thread(target=self._handle_console_input, daemon=True)
        input_thread.start()
        
        # Main console loop
        last_status_time = 0
        try:
            while self.running and not self.quit_requested:
                current_time = time.time()
                
                # Show status every 30 seconds
                if current_time - last_status_time >= 30:
                    current_player = self.player_manager.get_current_player_name()
                    print(f"[{time.strftime('%H:%M:%S')}] ♪ Console mode - {current_player} active")
                    last_status_time = current_time
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nReceived Ctrl+C")
            self.quit_requested = True
        finally:
            self.running = False
            print("Console mode ended")
    
    def _handle_console_input(self):
        """Handle console input in separate thread"""
        while self.running and not self.quit_requested:
            try:
                print(f"\n[{time.strftime('%H:%M:%S')}] Current Player: {self.player_manager.get_current_player_name()}")
                print("Command (1/2/s/c/q/h): ", end="", flush=True)
                
                cmd = input().strip().lower()
                
                if cmd == 'q':
                    print("Quitting...")
                    self.quit_requested = True
                    self.running = False
                    break
                elif cmd == '1':
                    print("Switching to Apple Music...")
                    success = self.player_manager.switch_to_player(PLAYER_APPLE_MUSIC)
                    print(f"✅ Switch {'successful' if success else 'failed'}")
                elif cmd == '2':
                    print("Switching to iTunes...")
                    success = self.player_manager.switch_to_player(PLAYER_ITUNES)
                    print(f"✅ Switch {'successful' if success else 'failed'}")
                elif cmd == 's':
                    self._show_detailed_status()
                elif cmd == 'c':
                    import os
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print("ANP TRAY APP - Music monitoring active")
                elif cmd == 'h':
                    self._show_help()
                else:
                    if cmd:  # Only show error for non-empty commands
                        print(f"❌ Unknown command: '{cmd}'. Type 'h' for help.")
                    
            except (EOFError, KeyboardInterrupt):
                print("\nInput thread ending...")
                self.quit_requested = True
                self.running = False
                break
            except Exception as e:
                print(f"Input error: {e}")
    
    def _show_detailed_status(self):
        """Show detailed status"""
        import os
        from config.settings import OUTPUT_FILE, ARTWORK_FILE, PROGRESS_FILE
        
        print("\n" + "="*50)
        print("DETAILED STATUS")
        print("="*50)
        print(f"Current Player: {self.player_manager.get_current_player_name()}")
        print(f"Available Players: {', '.join(self.player_manager.get_available_players())}")
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"System Tray Mode: {'Console' if self.fallback_mode else 'GUI'}")
        
        # Check file status
        files_to_check = [
            ("Now Playing", OUTPUT_FILE),
            ("Artwork", ARTWORK_FILE), 
            ("Progress", PROGRESS_FILE)
        ]
        
        print("\nFile Status:")
        for name, filepath in files_to_check:
            abs_path = os.path.abspath(filepath)
            if os.path.exists(abs_path):
                size = os.path.getsize(abs_path)
                mtime = os.path.getmtime(abs_path)
                mtime_str = time.strftime('%H:%M:%S', time.localtime(mtime))
                print(f"  {name}: ✅ EXISTS ({size} bytes, updated {mtime_str})")
                
                # Show content for small text files
                if name == "Now Playing" and size < 500:
                    try:
                        with open(abs_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        if content:
                            lines = content.split('\n')
                            if len(lines) >= 2:
                                print(f"    ♪ Playing: {lines[0]} - {lines[1]}")
                    except:
                        pass
            else:
                print(f"  {name}: ❌ MISSING ({abs_path})")
        
        print("="*50)
    
    def _show_help(self):
        """Show help"""
        print("\n" + "="*50)
        print("ANP TRAY APP - HELP")
        print("="*50)
        print("Commands:")
        print("  1 - Switch to Apple Music player")
        print("  2 - Switch to iTunes player") 
        print("  s - Show detailed status and file info")
        print("  c - Clear screen")
        print("  q - Quit application")
        print("  h - Show this help")
        print("\nThe app continuously monitors your music player and writes:")
        print("  - nowplaying.txt (artist, title, album)")
        print("  - anp_cover.png (album artwork)")
        print("  - track_progress.json (detailed progress info)")
        print("="*50)
    
    def _show_status_popup(self, _=None):
        """Show status in a popup (for system tray)"""
        if self.fallback_mode:
            self._show_detailed_status()
        else:
            try:
                current_player = self.player_manager.get_current_player_name()
                track_info = self.current_info.get("track", "No track")
                
                message = f"Current Player: {current_player}\nNow Playing: {track_info}"
                messagebox.showinfo("ANP Status", message)
            except Exception as e:
                print(f"Status popup error: {e}")
    
    def stop(self):
        """Stop the system tray"""
        with self._lock:
            print("Stopping system tray manager...")
            self.running = False
            self.quit_requested = True
            
            if self.systray and not self.fallback_mode:
                try:
                    self.systray.shutdown()
                except Exception as e:
                    print(f"Error shutting down system tray: {e}")
                self.systray = None
            
            print("System tray manager stopped")
    
    def update_track_info(self, track_info):
        """Update the track information display"""
        self.current_info["track"] = track_info
        if not self.fallback_mode and self.systray:
            self._update_tooltip()
        print(f"♪ Now Playing: {track_info}")
    
    def update_player_info(self, player_name):
        """Update the current player information"""
        self.current_info["player"] = player_name
        if not self.fallback_mode:
            self._update_display()
        print(f"🎵 Active Player: {player_name}")
    
    def _update_display(self):
        """Update the system tray icon and tooltip"""
        if not self.systray or self.fallback_mode:
            return
        
        try:
            # Update icon based on current player
            current_player = self.player_manager.get_current_player_name()
            
            icon_path = ICON_DEFAULT
            if current_player == PLAYER_APPLE_MUSIC:
                icon_path = ICON_APPLE
            elif current_player == PLAYER_ITUNES:
                icon_path = ICON_ITUNES
            
            # Check if icon exists
            abs_icon_path = os.path.abspath(icon_path)
            if os.path.exists(abs_icon_path):
                self.systray.update(icon=abs_icon_path)
            
            self.current_info["player"] = current_player
            self._update_tooltip()
        except Exception as e:
            print(f"Error updating system tray display: {e}")
    
    def _update_tooltip(self):
        """Update the system tray tooltip"""
        if self.systray and not self.fallback_mode:
            try:
                tooltip = f"ANP - {self.current_info['player']}: {self.current_info['track']}"
                self.systray.update(hover_text=tooltip)
            except Exception as e:
                print(f"Error updating tooltip: {e}")
    
    def _switch_to_apple_music(self, _=None):
        """Switch to Apple Music"""
        print("Switching to Apple Music...")
        success = self.player_manager.switch_to_player(PLAYER_APPLE_MUSIC)
        if not self.fallback_mode:
            self._update_display()
        print(f"Switch to Apple Music: {'✅ Success' if success else '❌ Failed'}")
    
    def _switch_to_itunes(self, _=None):
        """Switch to iTunes"""
        print("Switching to iTunes...")
        success = self.player_manager.switch_to_player(PLAYER_ITUNES)
        if not self.fallback_mode:
            self._update_display()
        print(f"Switch to iTunes: {'✅ Success' if success else '❌ Failed'}")
    
    def _show_about(self, _=None):
        """Show the about dialog"""
        if not self.fallback_mode:
            try:
                self.about_dialog.show()
            except:
                # Fallback to console about
                self._console_about()
        else:
            self._console_about()
    
    def _console_about(self):
        """Show about info in console"""
        print(f"\n{APP_NAME} - Modular Edition")
        print(f"by {APP_AUTHOR}")
        print(f"Website: {APP_WEBSITE}")
        print("\nDisplays info from Apple Music or iTunes")
        print("and saves it to nowplaying.txt with artwork.")
    
    def _on_quit(self, _=None):
        """Handle quit event"""
        print("System tray quit requested...")
        self.quit_requested = True
        self.running = False
        if hasattr(self, 'player_manager'):
            self.player_manager.shutdown()