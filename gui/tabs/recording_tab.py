"""
Recording tab for the Auto Clicker GUI.
Handles mouse recording functionality.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import TYPE_CHECKING

from gui.tabs.base_tab import BaseTab

if TYPE_CHECKING:
    from gui.main_window import AutoClickerGUI


class RecordingTab(BaseTab):
    """Tab for recording mouse movements, clicks, and scrolls."""
    
    def __init__(self, notebook: ttk.Notebook, main_window: 'AutoClickerGUI') -> None:
        """Initialize the recording tab."""
        super().__init__(notebook, main_window)
        
    def create(self) -> None:
        """Create the mouse recorder tab."""
        tab, content = self.create_scrollable_tab("📹 Record")

        # Instructions
        instructions = tk.Label(
            content,
            text="Record your mouse movements, clicks, and scrolls",
            font=("Segoe UI", 9),
            pady=5
        )
        instructions.pack()

        # Recording controls frame
        controls_frame = tk.LabelFrame(content, text="Recording Controls", padx=8, pady=6, font=("Segoe UI", 9))
        controls_frame.pack(fill=tk.X, padx=12, pady=5)

        # Status indicator
        self.main_window.record_status_label = tk.Label(
            controls_frame,
            text="⚫ Not Recording",
            font=("Segoe UI", 10, "bold"),
            fg="gray"
        )
        self.main_window.record_status_label.pack(pady=4)

        # Buttons frame
        buttons_frame = tk.Frame(controls_frame)
        buttons_frame.pack(pady=4)

        self.main_window.start_record_btn = tk.Button(
            buttons_frame,
            text="▶ Start Recording",
            command=self.start_recording,
            bg="#27ae60",
            fg="white",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2"
        )
        self.main_window.start_record_btn.pack(side=tk.LEFT, padx=3)

        self.main_window.stop_record_btn = tk.Button(
            buttons_frame,
            text="⏹ Stop Recording",
            command=self.stop_recording,
            bg="#e74c3c",
            fg="white",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=12,
            pady=6,
            state=tk.DISABLED,
            cursor="hand2"
        )
        self.main_window.stop_record_btn.pack(side=tk.LEFT, padx=3)

        # Event counter
        self.main_window.event_count_label = tk.Label(
            controls_frame,
            text="Events recorded: 0",
            font=("Segoe UI", 9)
        )
        self.main_window.event_count_label.pack(pady=4)

        # Hotkey info
        hotkey_info = tk.Label(
            controls_frame,
            text="⌨ Hotkeys: F9 = Start | F10 = Stop",
            font=("Segoe UI", 8),
            fg="#3498db",
            bg="#ecf0f1",
            padx=8,
            pady=4
        )
        hotkey_info.pack(pady=3)

        # Save options
        save_frame = tk.LabelFrame(content, text="Save Recording", padx=8, pady=6, font=("Segoe UI", 9))
        save_frame.pack(fill=tk.X, padx=12, pady=5)

        tk.Label(save_frame, text="Filename:", font=("Segoe UI", 9)).pack(anchor=tk.W)

        filename_frame = tk.Frame(save_frame)
        filename_frame.pack(fill=tk.X, pady=3)

        self.main_window.record_filename_var = tk.StringVar(value="recording.json")
        filename_entry = tk.Entry(
            filename_frame,
            textvariable=self.main_window.record_filename_var,
            font=("Segoe UI", 9)
        )
        filename_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_btn = tk.Button(
            filename_frame,
            text="Browse...",
            command=self.browse_save_location,
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            cursor="hand2"
        )
        browse_btn.pack(side=tk.LEFT)

        save_btn = tk.Button(
            save_frame,
            text="💾 Save Recording",
            command=self.save_recording,
            bg="#3498db",
            fg="white",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2"
        )
        save_btn.pack(pady=5)

    def start_recording(self) -> None:
        """Start recording mouse events."""
        self.main_window.is_recording = True
        self.main_window.recorder.start_recording()

        self.main_window.start_record_btn.config(state=tk.DISABLED)
        self.main_window.stop_record_btn.config(state=tk.NORMAL)
        self.main_window.record_status_label.config(text="🔴 Recording...", fg="#e74c3c")

        self.log("Recording started")
        self.update_status("Recording in progress...")

        # Update event count periodically
        self.update_event_count()

    def stop_recording(self) -> None:
        """Stop recording mouse events."""
        self.main_window.is_recording = False
        events = self.main_window.recorder.stop_recording()

        self.main_window.start_record_btn.config(state=tk.NORMAL)
        self.main_window.stop_record_btn.config(state=tk.DISABLED)
        self.main_window.record_status_label.config(text="⚫ Not Recording", fg="gray")

        self.log(f"Recording stopped. Captured {len(events)} events")
        self.update_status("Recording stopped")

    def update_event_count(self) -> None:
        """Update the event count label."""
        if self.main_window.is_recording:
            count = len(self.main_window.recorder.events)
            self.main_window.event_count_label.config(text=f"Events recorded: {count}")
            self.root.after(100, self.update_event_count)
        else:
            count = len(self.main_window.recorder.events)
            self.main_window.event_count_label.config(text=f"Events recorded: {count}")

    def save_recording(self) -> None:
        """Save the current recording."""
        if not self.main_window.recorder.events:
            messagebox.showwarning("No Recording", "No events to save. Please record something first.")
            return

        filename = self.main_window.record_filename_var.get()
        if not filename:
            messagebox.showerror("Error", "Please specify a filename")
            return

        try:
            # Save with all events - no optimization needed since timing is preserved
            self.main_window.recorder.save_recording(filename, optimize=False)
            self.log(f"Recording saved to {filename} ({len(self.main_window.recorder.events)} events)")
            messagebox.showinfo("Success", f"Recording saved to {filename}")
        except Exception as e:
            self.log(f"Error saving recording: {e}")
            messagebox.showerror("Error", f"Failed to save recording: {e}")

    def browse_save_location(self) -> None:
        """Browse for save location."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.main_window.record_filename_var.set(filename)
