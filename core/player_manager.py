"""
Player management and orchestration
"""
from players.apple_music import AppleMusicPlayer
from config.settings import PLAYER_APPLE_MUSIC, PLAYER_ITUNES

# Try to import iTunes player, but handle COM conflicts gracefully
try:
    from players.itunes import iTunesPlayer
    ITUNES_AVAILABLE = True
    print("iTunes player module loaded successfully")
except (ImportError, OSError) as e:
    print(f"iTunes player not available: {e}")
    ITUNES_AVAILABLE = False
    iTunesPlayer = None

class PlayerManager:
    def __init__(self, file_manager, progress_tracker, artwork_manager):
        self.file_manager = file_manager
        self.progress_tracker = progress_tracker
        self.artwork_manager = artwork_manager
        
        # Initialize players
        print("Initializing Apple Music player...")
        self.players = {
            PLAYER_APPLE_MUSIC: AppleMusicPlayer(file_manager, progress_tracker, artwork_manager)
        }
        
        # Only add iTunes if available
        if ITUNES_AVAILABLE and iTunesPlayer:
            print("Initializing iTunes player...")
            self.players[PLAYER_ITUNES] = iTunesPlayer(file_manager, progress_tracker, artwork_manager)
        
        self.current_player = None
        self.current_player_name = PLAYER_APPLE_MUSIC  # Default
        
        print(f"Player manager initialized with players: {list(self.players.keys())}")
    
    def get_available_players(self):
        """Get list of available players"""
        return list(self.players.keys())
    
    def is_player_available(self, player_name):
        """Check if a specific player is available"""
        return player_name in self.players
    
    def get_current_player_name(self):
        """Get the name of the current player"""
        return self.current_player_name
    
    def get_current_player(self):
        """Get the current player instance"""
        return self.current_player
    
    def switch_to_player(self, player_name):
        """Switch to a specific player"""
        print(f"Attempting to switch to player: {player_name}")
        
        if player_name not in self.players:
            print(f"Player not available: {player_name}")
            return False
        
        # Stop current player if running
        if self.current_player:
            print(f"Stopping current player: {self.current_player_name}")
            self.current_player.stop_monitoring()
        
        # Switch to new player
        self.current_player_name = player_name
        self.current_player = self.players[player_name]
        
        # Check if player is available
        print(f"Checking if {player_name} is available...")
        if not self.current_player.is_available():
            print(f"Player {player_name} is not available on this system")
            self.current_player.clear_all_data()
            return False
        
        # Start monitoring new player
        print(f"Starting monitoring for {player_name}")
        self.current_player.start_monitoring()
        print(f"Successfully switched to {player_name}")
        return True
    
    def start_default_player(self):
        """Start the default player"""
        return self.switch_to_player(self.current_player_name)
    
    def shutdown(self):
        """Shutdown all players"""
        print("Shutting down player manager...")
        if self.current_player:
            print(f"Stopping current player: {self.current_player_name}")
            self.current_player.stop_monitoring()
        
        # Clear all data
        self.file_manager.clear_now_playing()
        self.progress_tracker.clear_progress()
        
        print("All players shut down")