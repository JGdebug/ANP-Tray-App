"""
Configuration settings and constants for ANP Tray App - DEBUG VERSION
"""
import os

# API Keys
LASTFM_API_KEY = "37e1a3e278de6ebe3df20c425da7d3a2"

# File paths - Make sure these are correct!
OUTPUT_FILE = "../NPlaying/nowplaying.txt"
ARTWORK_FILE = os.path.abspath("../NPlaying/anp_cover.png")
PROGRESS_FILE = "../NPlaying/track_progress.json"
DEFAULT_ARTWORK = os.path.abspath("media/npdf.bmp")

# Debug: Print resolved paths at startup
print("=== FILE PATHS DEBUG ===")
print(f"Current working directory: {os.getcwd()}")
print(f"OUTPUT_FILE: {os.path.abspath(OUTPUT_FILE)}")
print(f"ARTWORK_FILE: {ARTWORK_FILE}")
print(f"PROGRESS_FILE: {os.path.abspath(PROGRESS_FILE)}")
print(f"DEFAULT_ARTWORK: {DEFAULT_ARTWORK}")
print("========================")

# Icons
ICON_DEFAULT = "media/npdf.ico"
ICON_APPLE = "media/npam.ico"
ICON_ITUNES = "media/npit.ico"

# Timing
PROGRESS_UPDATE_INTERVAL = 1.0  # seconds
APPLE_MUSIC_POLLING_INTERVAL = 2.0  # seconds
ITUNES_POLLING_INTERVAL = 1.0  # seconds

# Application info
APP_NAME = "ANP Tray App"
APP_AUTHOR = "KronosRazer"
APP_WEBSITE = "http://www.kronoskrew.com"
APP_DESCRIPTION = ("Displays info from Apple Music or iTunes\n"
                  "and saves it to nowplaying.txt.\n"
                  "Artwork saved as anp_cover.png.\n\n"
                  "Now with direct Apple Music artwork\n"
                  "and continuous progress tracking!")

# Player types
PLAYER_APPLE_MUSIC = "Apple Music"
PLAYER_ITUNES = "iTunes"