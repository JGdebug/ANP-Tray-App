"""
Artwork management for music players - RESTORED WORKING V1
"""
import os
import tempfile
from core.file_manager import FileManager
from utils.lastfm_api import LastFmClient
from config.settings import ARTWORK_FILE

class ArtworkManager:
    def __init__(self):
        self.file_manager = FileManager()
        self.lastfm_client = LastFmClient()
        self.artwork_file = ARTWORK_FILE
    
    async def save_apple_music_artwork(self, session):
        """Save artwork directly from Apple Music session - WORKING V1 METHOD"""
        try:
            import winrt.windows.storage.streams as streams
            import winrt.windows.storage as storage
            
            # Get media properties which includes thumbnail
            info = await session.try_get_media_properties_async()
            if not info or not info.thumbnail:
                return False
            
            # Open the thumbnail stream
            input_stream = await info.thumbnail.open_read_async()
            if not input_stream:
                return False
            
            # Create temp file in the same directory as the target to avoid cross-drive issues
            target_dir = os.path.dirname(os.path.abspath(self.artwork_file))
            temp_file_path = os.path.join(target_dir, "anp_cover_temp.png")
            
            try:
                # Remove existing temp file if it exists
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                
                # Create temp file through Windows Storage API in the target directory
                folder = await storage.StorageFolder.get_folder_from_path_async(target_dir)
                temp_file = await folder.create_file_async(
                    os.path.basename(temp_file_path), 
                    storage.CreationCollisionOption.REPLACE_EXISTING
                )
                
                # Open output stream to temp file
                output_stream = await temp_file.open_async(storage.FileAccessMode.READ_WRITE)
                output_stream_writer = output_stream.get_output_stream_at(0)
                
                # Copy stream directly
                bytes_copied = await streams.RandomAccessStream.copy_async(input_stream, output_stream_writer)
                
                # Flush and close streams properly
                await output_stream_writer.flush_async()
                output_stream_writer.close()
                output_stream.close()
                input_stream.close()
                
                # Now move temp file to final location using safe cross-drive method
                if os.path.exists(temp_file_path) and os.path.getsize(temp_file_path) > 0:
                    if self.file_manager.safe_move_file(temp_file_path, self.artwork_file):
                        print(f"Apple Music artwork saved: {os.path.getsize(self.artwork_file)} bytes")
                        return True
                    else:
                        return False
                else:
                    return False
                    
            except Exception as direct_e:
                # Clean up streams
                try:
                    input_stream.close()
                except:
                    pass
                
                # Try simpler approach using Python file operations
                return await self._save_apple_music_artwork_fallback(session)
                
            finally:
                # Clean up temp file if it still exists
                try:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                except:
                    pass
            
        except Exception as e:
            print(f"Apple Music artwork error: {e}")
            return False
    
    async def _save_apple_music_artwork_fallback(self, session):
        """Fallback method for Apple Music artwork using Python file operations - WORKING V1"""
        try:
            import winrt.windows.storage.streams as streams
            
            info = await session.try_get_media_properties_async()
            if not info or not info.thumbnail:
                return False

            stream = await info.thumbnail.open_read_async()
            if not stream:
                return False

            # Create temporary file in same directory as target to avoid cross-drive issues
            target_dir = os.path.dirname(os.path.abspath(self.artwork_file))
            temp_path = os.path.join(target_dir, "anp_temp_artwork.tmp")
            
            try:
                artwork_data = bytearray()
                chunk_size = 1024
                total_size = stream.size
                
                while len(artwork_data) < total_size:
                    remaining = total_size - len(artwork_data)
                    current_chunk_size = min(chunk_size, remaining)
                    
                    try:
                        buffer = streams.Buffer(current_chunk_size)
                        result = await stream.read_async(buffer, current_chunk_size, streams.InputStreamOptions.READ_AHEAD)
                        
                        if not result or result.length == 0:
                            break
                        
                        # Use different approach to extract bytes from buffer
                        chunk_bytes = await self._buffer_to_bytes_alternative(result)
                        if chunk_bytes:
                            artwork_data.extend(chunk_bytes)
                        else:
                            break
                            
                    except Exception as chunk_e:
                        break
                
                stream.close()
                
                if artwork_data and len(artwork_data) > 1000:
                    # Write to temp file first
                    with open(temp_path, 'wb') as f:
                        f.write(artwork_data)
                    
                    # Use safe cross-drive move
                    if self.file_manager.safe_move_file(temp_path, self.artwork_file):
                        print(f"Apple Music artwork saved (fallback method): {len(artwork_data)} bytes")
                        return True
                    else:
                        return False
                else:
                    return False
                    
            finally:
                # Clean up temp file
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except:
                    pass
            
        except Exception as e:
            print(f"Apple Music artwork fallback error: {e}")
            return False

    async def _buffer_to_bytes_alternative(self, buffer):
        """Alternative method to extract bytes from WinRT buffer - WORKING V1"""
        try:
            # Method 1: Try using DataReader
            import winrt.windows.storage.streams as streams
            
            # Create a DataReader from the buffer
            data_reader = streams.DataReader.from_buffer(buffer)
            
            # Read bytes using DataReader
            byte_array = bytearray()
            for i in range(buffer.length):
                byte_val = data_reader.read_byte()
                byte_array.append(byte_val)
            
            return bytes(byte_array)
            
        except Exception as e1:
            try:
                # Method 2: Use buffer conversion utilities if available
                import array
                byte_array = array.array('B')
                
                # Try to iterate through buffer content
                for i in range(buffer.length):
                    try:
                        # Different ways to access buffer elements
                        byte_val = buffer.get_byte(i) if hasattr(buffer, 'get_byte') else None
                        if byte_val is not None:
                            byte_array.append(byte_val)
                        else:
                            return None
                    except:
                        return None
                        
                return byte_array.tobytes()
                
            except Exception as e2:
                return None
    
    def save_itunes_artwork(self, track):
        """Save artwork from iTunes track - WORKING V1"""
        try:
            if track.Artwork.Count > 0:
                art = track.Artwork.Item(1)
                if art:
                    art.SaveArtworkToFile(self.artwork_file)
                    artwork_saved = os.path.isfile(self.artwork_file)
                    if artwork_saved:
                        print(f"iTunes artwork saved: {os.path.getsize(self.artwork_file)} bytes")
                        return True
        except Exception as e:
            print(f"iTunes artwork error: {e}")
        return False
    
    def save_artwork_with_fallback(self, artist, album, title=None):
        """Try to save artwork using Last.fm API with fallback chain"""
        # Try album first
        url = self.lastfm_client.get_album_artwork_url(artist, album)
        
        # If no album artwork and we have a title, try title as album
        if not url and title:
            url = self.lastfm_client.get_track_artwork_url(artist, title)
        
        if url:
            if self.file_manager.save_artwork_from_url(url):
                print("Last.fm artwork saved successfully")
                return True
            else:
                print("Last.fm artwork URL found but save failed")
        else:
            print("No Last.fm artwork found")
        
        # Fall back to default artwork
        print("Using default artwork")
        return self.file_manager.save_default_artwork()
    
    async def handle_apple_music_artwork(self, session, artist, album, title=None):
        """Complete artwork handling chain for Apple Music - WORKING V1"""
        # Try Apple Music direct artwork first
        if await self.save_apple_music_artwork(session):
            return True
        
        # Fallback to Last.fm and default
        print("Apple Music artwork failed, trying fallback...")
        return self.save_artwork_with_fallback(artist, album, title)
    
    def handle_itunes_artwork(self, track, artist, album, title=None):
        """Complete artwork handling chain for iTunes - WORKING V1"""
        # Try iTunes direct artwork first
        if self.save_itunes_artwork(track):
            return True
        
        # Fallback to Last.fm and default
        print("iTunes artwork failed, trying fallback...")
        return self.save_artwork_with_fallback(artist, album, title)