"""
File I/O operations for ANP Tray App - ENHANCED URL DOWNLOADING
"""
import os
import shutil
import time
import threading
from config.settings import OUTPUT_FILE, ARTWORK_FILE, PROGRESS_FILE, DEFAULT_ARTWORK

class FileManager:
    def __init__(self):
        self.output_file = OUTPUT_FILE
        self.artwork_file = ARTWORK_FILE
        self.progress_file = PROGRESS_FILE
        self.default_artwork = DEFAULT_ARTWORK
        self._write_lock = threading.Lock()
        
        # Debug: Show resolved paths
        print(f"FileManager initialized:")
        print(f"  Output file: {os.path.abspath(self.output_file)}")
        print(f"  Artwork file: {os.path.abspath(self.artwork_file)}")
        print(f"  Progress file: {os.path.abspath(self.progress_file)}")
    
    def write_now_playing(self, title="", artist="", album=""):
        """Write current track info to nowplaying.txt - THREAD SAFE"""
        with self._write_lock:
            try:
                output_path = os.path.abspath(self.output_file)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Write to temp file first, then rename for atomic operation
                temp_path = output_path + ".tmp"
                
                with open(temp_path, "w", encoding="utf-8") as f:
                    if title or artist or album:
                        content = f"{artist}\n{title}\n{album}"
                        f.write(content)
                        print(f"Writing nowplaying: {artist} - {title}")
                    else:
                        f.write("")
                        print("Clearing nowplaying.txt")
                
                # Atomic rename
                if os.path.exists(output_path):
                    os.remove(output_path)
                os.rename(temp_path, output_path)
                
                return True
            except Exception as e:
                print(f"ERROR writing now playing file: {e}")
                # Clean up temp file
                temp_path = output_path + ".tmp"
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except:
                    pass
                return False
    
    def clear_now_playing(self):
        """Clear the now playing file"""
        return self.write_now_playing()
    
    def safe_move_file(self, src_path, dst_path):
        """Safely move a file across drives or within same drive - THREAD SAFE"""
        with self._write_lock:
            try:
                print(f"Moving file: {src_path} -> {dst_path}")
                
                # Remove destination if it exists
                if os.path.exists(dst_path):
                    os.remove(dst_path)
                    print(f"Removed existing destination: {dst_path}")
                
                # Try rename first (fastest, works within same drive)
                try:
                    os.rename(src_path, dst_path)
                    print(f"Renamed successfully: {dst_path}")
                    return True
                except OSError:
                    # Rename failed (probably cross-drive), use copy + delete
                    shutil.copy2(src_path, dst_path)
                    os.remove(src_path)
                    print(f"Copy+delete successful: {dst_path}")
                    return True
                    
            except Exception as e:
                print(f"ERROR moving file from {src_path} to {dst_path}: {e}")
                return False
    
    def save_artwork_from_url(self, url):
        """Save artwork from URL - ENHANCED"""
        try:
            print(f"Downloading artwork from: {url}")
            
            import requests
            
            # Enhanced headers to avoid blocking
            headers = {
                'User-Agent': 'ANP-TrayApp/1.0 (Windows; Music Player Integration)',
                'Accept': 'image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(url, headers=headers, timeout=15, stream=True)
            
            if response.status_code == 200:
                artwork_path = os.path.abspath(self.artwork_file)
                os.makedirs(os.path.dirname(artwork_path), exist_ok=True)
                
                # Write to temp file first
                temp_path = artwork_path + ".tmp"
                
                with open(temp_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Verify file size
                file_size = os.path.getsize(temp_path)
                if file_size > 0:
                    # Atomic move
                    success = self.safe_move_file(temp_path, artwork_path)
                    if success:
                        print(f"URL artwork saved: {artwork_path} ({file_size} bytes)")
                        return True
                    else:
                        print("Failed to move downloaded artwork")
                        return False
                else:
                    print("Downloaded file is empty")
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                    return False
            else:
                print(f"HTTP error {response.status_code} downloading artwork")
                return False
                
        except Exception as e:
            print(f"ERROR saving artwork from URL: {e}")
            return False
    
    def save_default_artwork(self):
        """Copy default artwork as fallback"""
        try:
            print("Applying default artwork...")
            artwork_path = os.path.abspath(self.artwork_file)
            default_path = os.path.abspath(self.default_artwork)
            
            if not os.path.exists(default_path):
                print(f"Default artwork not found: {default_path}")
                return False
            
            os.makedirs(os.path.dirname(artwork_path), exist_ok=True)
            
            # Read default artwork
            with open(default_path, 'rb') as src:
                data = src.read()
            
            if not data:
                print("Default artwork file is empty")
                return False
            
            # Write to temp file first
            temp_path = artwork_path + ".tmp"
            with open(temp_path, 'wb') as dst:
                dst.write(data)
            
            # Atomic move
            success = self.safe_move_file(temp_path, artwork_path)
            if success:
                print(f"Default artwork saved: {artwork_path} ({len(data)} bytes)")
                return True
            else:
                print("Failed to save default artwork")
                return False
                
        except Exception as e:
            print(f"ERROR copying default artwork: {e}")
            return False
    
    def ensure_directories_exist(self):
        """Ensure all required directories exist"""
        try:
            # Create directories for all output files
            for file_path in [self.output_file, self.artwork_file, self.progress_file]:
                abs_path = os.path.abspath(file_path)
                dir_path = os.path.dirname(abs_path)
                os.makedirs(dir_path, exist_ok=True)
            return True
        except Exception as e:
            print(f"ERROR creating directories: {e}")
            return False