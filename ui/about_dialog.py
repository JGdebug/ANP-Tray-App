"""
About dialog for ANP Tray App
"""
import tkinter as tk
import webbrowser
from config.settings import APP_NAME, APP_AUTHOR, APP_WEBSITE, APP_DESCRIPTION

class AboutDialog:
    def __init__(self):
        self.window = None
    
    def show(self):
        """Show the about dialog"""
        if self.window and self.window.winfo_exists():
            # Dialog already open, bring to front
            self.window.lift()
            self.window.focus_force()
            return
        
        self._create_dialog()
    
    def _create_dialog(self):
        """Create the about dialog window"""
        self.window = tk.Tk()
        self.window.title(f"About {APP_NAME}")
        self.window.resizable(False, False)
        self.window.geometry("300x200")
        self.window.attributes("-topmost", True)
        
        # Main title
        tk.Label(
            self.window,
            text=f"{APP_NAME}\nby {APP_AUTHOR}",
            font=("Segoe UI", 11, "bold"),
            pady=10
        ).pack()
        
        # Description
        tk.Label(
            self.window,
            text=APP_DESCRIPTION,
            font=("Segoe UI", 9),
            justify="center",
            wraplength=280
        ).pack(pady=(0, 10))
        
        # Website button
        tk.Button(
            self.window,
            text="Visit Website",
            command=self._open_website,
            width=20
        ).pack()
        
        # Close button
        tk.Button(
            self.window,
            text="Close",
            command=self._close_dialog,
            width=20
        ).pack(pady=5)
        
        # Handle window close event
        self.window.protocol("WM_DELETE_WINDOW", self._close_dialog)
        
        # Start the dialog
        self.window.mainloop()
    
    def _open_website(self):
        """Open the website and close dialog"""
        webbrowser.open(APP_WEBSITE)
        self._close_dialog()
    
    def _close_dialog(self):
        """Close the dialog"""
        if self.window:
            self.window.destroy()
            self.window = None