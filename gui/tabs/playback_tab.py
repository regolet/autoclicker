"""
Playback tab for the Auto Clicker GUI.
Handles playing back recorded mouse actions.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from typing import TYPE_CHECKING

from gui.tabs.base_tab import BaseTab

if TYPE_CHECKING:
    from gui.main_window import AutoClickerGUI


class PlaybackTab(BaseTab):
    """Tab for playing back recorded mouse actions."""
    
    def __init__(self, notebook: ttk.Notebook, main_window: 'AutoClickerGUI') -> None:
        """Initialize the playback tab."""
        super().__init__(notebook, main_window)
        
    def create(self) -> None:
        """Create the playback tab."""
        tab, content = self.create_scrollable_tab("▶ Playback")

        # Instructions
        instructions = tk.Label(
            content,
            text="Load and replay recorded mouse actions",
            font=("Segoe UI", 9),
            pady=5
        )
        instructions.pack()

        # Load recording frame
        load_frame = tk.LabelFrame(content, text="Load Recording", padx=8, pady=6, font=("Segoe UI", 9))
        load_frame.pack(fill=tk.X, padx=12, pady=5)

        tk.Label(load_frame, text="Recording file:", font=("Segoe UI", 9)).pack(anchor=tk.W)

        file_frame = tk.Frame(load_frame)
        file_frame.pack(fill=tk.X, pady=3)

        self.main_window.playback_filename_var = tk.StringVar()
        filename_entry = tk.Entry(
            file_frame,
            textvariable=self.main_window.playback_filename_var,
            font=("Segoe UI", 9),
            state='readonly'
        )
        filename_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_btn = tk.Button(
            file_frame,
            text="Browse...",
            command=self.browse_load_file,
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            cursor="hand2"
        )
        browse_btn.pack(side=tk.LEFT)

        load_btn = tk.Button(
            load_frame,
            text="📂 Load Recording",
            command=self.load_recording,
            bg="#3498db",
            fg="white",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2"
        )
        load_btn.pack(pady=5)

        self.main_window.loaded_info_label = tk.Label(
            load_frame,
            text="No recording loaded",
            font=("Segoe UI", 8),
            fg="gray"
        )
        self.main_window.loaded_info_label.pack()

        # Playback controls
        playback_frame = tk.LabelFrame(content, text="Playback Controls", padx=8, pady=6, font=("Segoe UI", 9))
        playback_frame.pack(fill=tk.X, padx=12, pady=5)

        # Speed control
        speed_frame = tk.Frame(playback_frame)
        speed_frame.pack(fill=tk.X, pady=5)

        tk.Label(speed_frame, text="Playback Speed:", font=("Segoe UI", 9)).pack(side=tk.LEFT)

        self.main_window.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = tk.Scale(
            speed_frame,
            from_=0.1,
            to=5.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.main_window.speed_var,
            length=180
        )
        speed_scale.pack(side=tk.LEFT, padx=8)

        self.speed_label = tk.Label(speed_frame, text="1.0x", font=("Segoe UI", 9, "bold"))
        self.speed_label.pack(side=tk.LEFT)

        self.main_window.speed_var.trace('w', lambda *args: self.speed_label.config(text=f"{self.main_window.speed_var.get():.1f}x"))

        # Play button
        play_btn = tk.Button(
            playback_frame,
            text="▶ Play Recording",
            command=self.play_recording,
            bg="#27ae60",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        play_btn.pack(pady=10)

        # Warning
        warning_label = tk.Label(
            playback_frame,
            text="⚠ Move mouse to top-left corner to abort playback",
            font=("Segoe UI", 8),
            fg="#e74c3c"
        )
        warning_label.pack()

    def browse_load_file(self) -> None:
        """Browse for recording file."""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.main_window.playback_filename_var.set(filename)

    def load_recording(self) -> None:
        """Load a recording file."""
        filename = self.main_window.playback_filename_var.get()
        if not filename:
            messagebox.showerror("Error", "Please select a file first")
            return

        try:
            self.main_window.loaded_events = self.main_window.recorder.load_recording(filename)
            self.main_window.loaded_info_label.config(
                text=f"Loaded {len(self.main_window.loaded_events)} events"
            )
            self.log(f"Loaded recording from {filename}")
        except Exception as e:
            self.log(f"Error loading recording: {e}")
            messagebox.showerror("Error", f"Failed to load recording: {e}")

    def play_recording(self) -> None:
        """Play back the loaded recording."""
        if not self.main_window.loaded_events:
            messagebox.showwarning("No Recording", "Please load a recording first")
            return

        speed = self.main_window.speed_var.get()
        self.log(f"Starting playback at {speed}x speed...")
        self.update_status("Playing back recording...")

        def playback_thread() -> None:
            try:
                self.main_window.clicker.play_recording(self.main_window.loaded_events, speed=speed)
                self.root.after(0, lambda: self.log("Playback completed"))
                self.root.after(0, lambda: self.update_status("Ready"))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Playback error: {e}"))
                self.root.after(0, lambda: self.update_status("Ready"))

        thread = threading.Thread(target=playback_thread, daemon=True)
        thread.start()
