"""
ANP Tray App - Main Entry Point - ENHANCED ERROR HANDLING
"""
import sys
import os
import time

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.file_manager import FileManager
from core.progress_tracker import ProgressTracker
from core.artwork_manager import ArtworkManager
from core.player_manager import PlayerManager
from ui.systray import SystemTrayManager
from ui.about_dialog import AboutDialog

class ANPTrayApp:
    def __init__(self):
        # Initialize core components
        self.file_manager = FileManager()
        self.progress_tracker = ProgressTracker()
        self.artwork_manager = ArtworkManager()
        
        # Initialize player manager
        self.player_manager = PlayerManager(
            self.file_manager,
            self.progress_tracker, 
            self.artwork_manager
        )
        
        # Initialize UI components
        self.about_dialog = AboutDialog()
        self.systray_manager = SystemTrayManager(self.player_manager, self.about_dialog)
    
    def initialize(self):
        """Initialize the application"""
        print("Initializing ANP Tray App...")
        
        # Ensure directories exist
        if not self.file_manager.ensure_directories_exist():
            print("Failed to create required directories")
            return False
        
        # Clear any existing data
        self.file_manager.clear_now_playing()
        self.progress_tracker.clear_progress()
        
        # Show available players
        available_players = self.player_manager.get_available_players()
        print(f"Available players: {available_players}")
        
        print("ANP Tray App initialized successfully")
        return True
    
    def run(self):
        """Run the application"""
        if not self.initialize():
            print("Failed to initialize application")
            return False
        
        try:
            # Start default player
            print("Starting default player...")
            if not self.player_manager.start_default_player():
                print("Warning: Default player failed to start")
            else:
                print("Default player started successfully")
            
            # Give player a moment to initialize and detect music
            print("Waiting for player to initialize...")
            time.sleep(3)
            
            # Start system tray with fallback (this blocks until quit)
            print("Starting user interface...")
            self.systray_manager.start()
            
        except KeyboardInterrupt:
            print("\nReceived interrupt signal")
        except Exception as e:
            print(f"Application error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.shutdown()
        
        return True
    
    def shutdown(self):
        """Shutdown the application"""
        print("Shutting down ANP Tray App...")
        
        # Stop system tray
        self.systray_manager.stop()
        
        # Shutdown player manager
        self.player_manager.shutdown()
        
        print("ANP Tray App shutdown complete")

def main():
    """Main entry point"""
    print("=== ANP Tray App - Modular Edition ===")
    print("by KronosRazer")
    print("==========================================")
    
    app = ANPTrayApp()
    success = app.run()
    
    print(f"Application finished")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())