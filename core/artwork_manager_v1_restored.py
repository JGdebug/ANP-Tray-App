"""
Artwork management - RESTORED V1 WORKING METHOD
"""
import os
import tempfile
from config.settings import LASTFM_API_KEY

class ArtworkManager:
    def __init__(self):
        self.lastfm_api_key = LASTFM_API_KEY
    
    async def handle_apple_music_artwork(self, session, artist, album, title):
        """Handle Apple Music artwork - V1 WORKING METHOD"""
        try:
            print("Getting Apple Music artwork...")
            
            # Get media properties
            info = await session.try_get_media_properties_async()
            if not info or not info.thumbnail:
                print("No Apple Music thumbnail available")
                return False
            
            # Open the thumbnail stream
            stream_ref = await info.thumbnail.open_read_async()
            if not stream_ref:
                print("Failed to open Apple Music thumbnail stream")
                return False
            
            try:
                # V1 METHOD - Simple byte reading
                stream_size = stream_ref.size
                if stream_size > 0:
                    # Read all bytes at once (V1 approach)
                    from winrt.windows.storage.streams import Buffer
                    buffer = Buffer(int(stream_size))
                    result = await stream_ref.read_async(buffer)
                    
                    if result and result.length > 0:
                        # Convert to bytes using the V1 method
                        import array
                        byte_array = array.array('B')
                        for i in range(result.length):
                            byte_array.append(result.get_byte(i))
                        
                        artwork_bytes = byte_array.tobytes()
                        
                        # Save artwork
                        from config.settings import ARTWORK_FILE
                        temp_path = os.path.abspath(ARTWORK_FILE + "_temp.png")
                        
                        with open(temp_path, 'wb') as f:
                            f.write(artwork_bytes)
                        
                        # Move to final location
                        from core.file_manager import FileManager
                        file_manager = FileManager()
                        success = file_manager.safe_move_file(temp_path, os.path.abspath(ARTWORK_FILE))
                        
                        if success:
                            print(f"Apple Music artwork saved: {len(artwork_bytes)} bytes")
                            return True
                
                return False
                
            finally:
                stream_ref.close()
                
        except Exception as e:
            print(f"Apple Music artwork error: {e}")
            return False