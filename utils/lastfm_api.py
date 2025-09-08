"""
Last.fm API client for artwork fallback
"""
import requests
from config.settings import LASTFM_API_KEY

class LastFmClient:
    def __init__(self):
        self.api_key = LASTFM_API_KEY
        self.base_url = "http://ws.audioscrobbler.com/2.0/"
    
    def get_album_artwork_url(self, artist, album):
        """Get artwork URL for album from Last.fm"""
        try:
            params = {
                "method": "album.getinfo",
                "api_key": self.api_key,
                "artist": artist,
                "album": album,
                "format": "json"
            }
            response = requests.get(self.base_url, params=params, timeout=5)
            data = response.json()
            
            if "album" in data and "image" in data["album"]:
                images = data["album"]["image"]
                for img in reversed(images):  # Get largest image
                    if img.get("#text"):
                        return img["#text"]
            return None
            
        except Exception as e:
            print(f"Last.fm artwork fetch failed: {e}")
            return None
    
    def get_track_artwork_url(self, artist, track):
        """Get artwork URL for track from Last.fm (fallback method)"""
        return self.get_album_artwork_url(artist, track)