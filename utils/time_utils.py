"""
Time formatting utilities
"""

def format_time(seconds):
    """Format seconds as MM:SS or HH:MM:SS"""
    if seconds <= 0:
        return "0:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def timespan_to_seconds(timespan):
    """Convert WinRT TimeSpan to seconds"""
    try:
        if timespan is None:
            return 0
        # WinRT TimeSpan has ticks property (100-nanosecond intervals)
        # 1 second = 10,000,000 ticks
        if hasattr(timespan, 'ticks'):
            return timespan.ticks / 10000000.0
        # Alternative: check for total_milliseconds
        elif hasattr(timespan, 'total_milliseconds'):
            return timespan.total_milliseconds / 1000.0
        # Alternative: check for duration property
        elif hasattr(timespan, 'duration'):
            return timespan.duration / 10000000.0
        else:
            # Try direct conversion if it's already a number
            return float(timespan) if timespan else 0
    except Exception as e:
        print(f"TimeSpan conversion error: {e}")
        return 0