"""
Artwork management - SIMPLE FALLBACK VERSION
"""
import os
import tempfile
from config.settings import LASTFM_API_KEY

class ArtworkManager:
    def __init__(self):
        self.lastfm_api_key = LASTFM_API_KEY
    
    async def handle_apple_music_artwork(self, session, artist, album, title):
        """Handle Apple Music artwork - SIMPLE FALLBACK"""
        try:
            print("Apple Music direct artwork not available, using Last.fm...")
            return self._get_lastfm_artwork(artist, album, title)
        except Exception as e:
            print(f"Apple Music artwork error: {e}")
            return self._get_lastfm_artwork(artist, album, title)
    
    def handle_itunes_artwork(self, track_com_object, artist, album, title):
        """Handle iTunes artwork"""
        try:
            print("Getting iTunes artwork...")
            itunes_success = self._get_itunes_artwork_safe(track_com_object, artist, album, title)
            
            if itunes_success:
                return True
            else:
                return self._get_lastfm_artwork(artist, album, title)
        except Exception as e:
            print(f"iTunes artwork error: {e}")
            return self._get_lastfm_artwork(artist, album, title)
    
    def _get_itunes_artwork_safe(self, track_com_object, artist, album, title):
        """Safely get artwork from iTunes COM object"""
        try:
            if not track_com_object:
                return False
            
            artworks = track_com_object.Artwork
            if not artworks or artworks.Count == 0:
                print("No iTunes artwork available")
                return False
            
            artwork = artworks.Item(1)
            if not artwork:
                return False
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                artwork.SaveArtworkToFile(temp_path)
                
                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                    from config.settings import ARTWORK_FILE
                    from core.file_manager import FileManager
                    
                    file_manager = FileManager()
                    success = file_manager.safe_move_file(temp_path, os.path.abspath(ARTWORK_FILE))
                    
                    if success:
                        file_size = os.path.getsize(os.path.abspath(ARTWORK_FILE))
                        print(f"iTunes artwork saved: {file_size} bytes")
                        return True
                
                return False
            finally:
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except:
                    pass
        
        except Exception as e:
            print(f"Error accessing iTunes artwork: {e}")
            return False
    
    def _get_lastfm_artwork(self, artist, album, title):
        """Get artwork from Last.fm API with fallback to default"""
        try:
            print(f"Fetching artwork from Last.fm for: {artist} - {album}")
            
            import requests
            
            url = "http://ws.audioscrobbler.com/2.0/"
            params = {
                'method': 'album.getinfo',
                'api_key': self.lastfm_api_key,
                'artist': artist,
                'album': album,
                'format': 'json'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'album' in data and 'image' in data['album']:
                    images = data['album']['image']
                    
                    image_url = None
                    for img in reversed(images):
                        if img.get('#text'):
                            image_url = img['#text']
                            break
                    
                    if image_url:
                        print(f"Found Last.fm artwork: {image_url}")
                        from core.file_manager import FileManager
                        file_manager = FileManager()
                        if file_manager.save_artwork_from_url(image_url):
                            return True
            
            print("No Last.fm artwork found, using default")
            from core.file_manager import FileManager
            file_manager = FileManager()
            return file_manager.save_default_artwork()
            
        except Exception as e:
            print(f"Last.fm artwork error: {e}")
            try:
                from core.file_manager import FileManager
                file_manager = FileManager()
                return file_manager.save_default_artwork()
            except:
                return False