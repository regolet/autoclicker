"""
Main window for the Auto Clicker GUI.
This is the central orchestrator that composes all tab components.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from PIL import Image, ImageTk
import keyboard
import pyautogui

from mouse_recorder import MouseRecorder
from auto_clicker import AutoClicker
from screenshot_analyzer import ScreenshotAnalyzer
from logging_config import get_logger

# Import tab components
from gui.tabs.recording_tab import RecordingTab
from gui.tabs.playback_tab import PlaybackTab
from gui.tabs.alarm_tab import AlarmTab

# Module logger
logger = get_logger("gui")


class AutoClickerGUI:
    """Main GUI application with modular tab components."""
    
    def __init__(self, root: tk.Tk) -> None:
        """Initialize the main window."""
        self.root = root
        self.root.title("Auto Clicker with Image Matching")
        self.root.geometry("900x750")
        self.root.resizable(True, True)

        # Set minimum window size
        self.root.minsize(800, 600)

        # Initialize components
        self.recorder = MouseRecorder()
        self.clicker = AutoClicker()
        self.analyzer = ScreenshotAnalyzer()

        # State variables
        self.is_recording: bool = False
        self.current_recording_file: Optional[str] = None
        self.loaded_events: List[Dict[str, Any]] = []
        self.img_click_running: bool = False
        self.alarms: List[Dict[str, Any]] = []
        self.alarm_monitor_running: bool = False
        self.alarm_monitor_thread: Optional[threading.Thread] = None
        self.alarms_file: str = "alarms.json"

        # Setup GUI
        self.setup_gui()

    def setup_gui(self) -> None:
        """Setup the GUI layout."""
        # Title - more compact
        title_frame = tk.Frame(self.root, bg="#34495e", height=45)
        title_frame.pack(fill=tk.X, side=tk.TOP)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="🖱️ Auto Clicker",
            font=("Segoe UI", 14, "bold"),
            bg="#34495e",
            fg="white"
        )
        title_label.pack(pady=10)

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Create tabs using modular components
        self.image_click_tab = ImageClickTab(self.notebook, self)
        self.image_click_tab.create()
        
        self.recording_tab = RecordingTab(self.notebook, self)
        self.recording_tab.create()
        
        self.playback_tab = PlaybackTab(self.notebook, self)
        self.playback_tab.create()
        
        self.alarm_tab = AlarmTab(self.notebook, self)
        self.alarm_tab.create()

        # Status bar with save/load buttons
        status_frame = tk.Frame(self.root, bg="#ecf0f1")
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Load settings button
        load_settings_btn = tk.Button(
            status_frame,
            text="📂 Load Settings",
            command=self.manual_load_settings,
            bg="#27ae60",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=10,
            pady=2,
            cursor="hand2",
            relief=tk.FLAT
        )
        load_settings_btn.pack(side=tk.RIGHT, padx=2, pady=2)

        # Save settings button
        save_settings_btn = tk.Button(
            status_frame,
            text="💾 Save Settings",
            command=self.manual_save_settings,
            bg="#3498db",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=10,
            pady=2,
            cursor="hand2",
            relief=tk.FLAT
        )
        save_settings_btn.pack(side=tk.RIGHT, padx=2, pady=2)

        # Status label
        self.status_bar = tk.Label(
            status_frame,
            text="Ready",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#ecf0f1"
        )
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Log area
        log_frame = tk.LabelFrame(self.root, text="Activity Log", padx=3, pady=3, font=("Segoe UI", 9))
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=6,
            state=tk.DISABLED,
            bg="#ffffff",
            font=("Consolas", 8),
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Settings file path
        self.settings_file = "app_settings.json"

        # Load saved settings
        self.load_settings()
        self.load_alarms()

        # Apply saved settings after all UI elements are created
        self.apply_saved_settings()

        # Auto-start alarm monitoring if there are enabled alarms
        self.auto_start_alarm_monitoring()

        # Setup global hotkeys
        self.setup_hotkeys()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_hotkeys(self) -> None:
        """Setup global keyboard shortcuts."""
        try:
            keyboard.add_hotkey('f11', self.hotkey_start_image_click, suppress=False)
            keyboard.add_hotkey('f12', self.hotkey_stop_image_click, suppress=False)
            self.log("Hotkeys enabled: F11=Start Image Click, F12=Stop Image Click")
        except Exception as e:
            self.log(f"Warning: Could not setup hotkeys: {e}")

    def hotkey_start_image_click(self) -> None:
        """Hotkey handler for starting image click."""
        if not self.img_click_running:
            self.root.after(0, self.image_click_tab.start_image_click)

    def hotkey_stop_image_click(self) -> None:
        """Hotkey handler for stopping image click."""
        if self.img_click_running:
            self.root.after(0, self.image_click_tab.stop_image_click)

    def manual_save_settings(self) -> None:
        """Manually save settings with user feedback."""
        self.save_settings()
        self.log("Settings saved successfully!")
        self.update_status("Settings saved")
        self.root.after(2000, lambda: self.update_status("Ready"))

    def manual_load_settings(self) -> None:
        """Manually load settings with user feedback."""
        self.load_settings()
        self.apply_saved_settings()
        self.log("Settings reloaded from file!")
        self.update_status("Settings loaded")
        self.root.after(2000, lambda: self.update_status("Ready"))

    def save_settings(self) -> None:
        """Save current settings to file."""
        settings: Dict[str, Any] = {
            "last_playback_file": self.playback_filename_var.get() if hasattr(self, 'playback_filename_var') else "",
            "playback_speed": self.speed_var.get() if hasattr(self, 'speed_var') else 1.0,
            "template_image": self.template_image_var.get() if hasattr(self, 'template_image_var') else "",
            "confidence": self.confidence_var.get() if hasattr(self, 'confidence_var') else 0.8,
            "img_monitor": self.img_monitor_var.get() if hasattr(self, 'img_monitor_var') else 0,
            "img_action_mode": self.img_action_mode_var.get() if hasattr(self, 'img_action_mode_var') else "click",
            "img_repeat": self.img_repeat_var.get() if hasattr(self, 'img_repeat_var') else 1,
            "img_interval": self.img_interval_var.get() if hasattr(self, 'img_interval_var') else 0.0,
            "img_unlimited": self.img_unlimited_var.get() if hasattr(self, 'img_unlimited_var') else False,
            "img_retry_on_not_found": self.img_retry_on_not_found_var.get() if hasattr(self, 'img_retry_on_not_found_var') else False,
            "img_playback_file": self.img_playback_file_var.get() if hasattr(self, 'img_playback_file_var') else "",
            "img_playback_speed": self.img_playback_speed_var.get() if hasattr(self, 'img_playback_speed_var') else 1.0,
            "record_filename": self.record_filename_var.get() if hasattr(self, 'record_filename_var') else "recording.json",
        }

        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving settings: {e}")

    def load_settings(self) -> None:
        """Load settings from file."""
        if not os.path.exists(self.settings_file):
            return

        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
            self.saved_settings = settings
            logger.info("Settings loaded from file")
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            self.saved_settings = {}

    def apply_saved_settings(self) -> None:
        """Apply saved settings to UI elements."""
        if not hasattr(self, 'saved_settings') or not self.saved_settings:
            return

        settings = self.saved_settings

        try:
            if "last_playback_file" in settings and hasattr(self, 'playback_filename_var'):
                self.playback_filename_var.set(settings["last_playback_file"])
            if "playback_speed" in settings and hasattr(self, 'speed_var'):
                self.speed_var.set(settings["playback_speed"])
            if "template_image" in settings and hasattr(self, 'template_image_var'):
                self.template_image_var.set(settings["template_image"])
            if "confidence" in settings and hasattr(self, 'confidence_var'):
                self.confidence_var.set(settings["confidence"])
            if "img_monitor" in settings and hasattr(self, 'img_monitor_var'):
                self.img_monitor_var.set(settings["img_monitor"])
            if "img_action_mode" in settings and hasattr(self, 'img_action_mode_var'):
                self.img_action_mode_var.set(settings["img_action_mode"])
            if "img_repeat" in settings and hasattr(self, 'img_repeat_var'):
                self.img_repeat_var.set(settings["img_repeat"])
            if "img_interval" in settings and hasattr(self, 'img_interval_var'):
                self.img_interval_var.set(settings["img_interval"])
            if "img_unlimited" in settings and hasattr(self, 'img_unlimited_var'):
                self.img_unlimited_var.set(settings["img_unlimited"])
                if hasattr(self, 'image_click_tab'):
                    self.image_click_tab.toggle_img_repeat_count()
            if "img_retry_on_not_found" in settings and hasattr(self, 'img_retry_on_not_found_var'):
                self.img_retry_on_not_found_var.set(settings["img_retry_on_not_found"])
            if "img_playback_file" in settings and hasattr(self, 'img_playback_file_var'):
                self.img_playback_file_var.set(settings["img_playback_file"])
            if "img_playback_speed" in settings and hasattr(self, 'img_playback_speed_var'):
                self.img_playback_speed_var.set(settings["img_playback_speed"])
            if "record_filename" in settings and hasattr(self, 'record_filename_var'):
                self.record_filename_var.set(settings["record_filename"])

            if hasattr(self, 'image_click_tab'):
                self.image_click_tab.update_img_action_controls()

            if hasattr(self, 'log_text'):
                self.log("Settings loaded from previous session")

        except Exception as e:
            import traceback
            logger.error(f"Error applying settings: {e}")
            traceback.print_exc()

    def load_alarms(self) -> None:
        """Load alarms from separate alarms.json file."""
        if not os.path.exists(self.alarms_file):
            self.alarms = []
            return

        try:
            with open(self.alarms_file, 'r') as f:
                self.alarms = json.load(f)
            logger.info(f"Loaded {len(self.alarms)} alarms from {self.alarms_file}")
            if hasattr(self, 'alarm_listbox'):
                self.refresh_alarm_list()
        except Exception as e:
            logger.error(f"Error loading alarms: {e}")
            self.alarms = []

    def save_alarms(self) -> None:
        """Save alarms to separate alarms.json file."""
        try:
            with open(self.alarms_file, 'w') as f:
                json.dump(self.alarms, f, indent=2)
            logger.info(f"Saved {len(self.alarms)} alarms to {self.alarms_file}")
        except Exception as e:
            logger.error(f"Error saving alarms: {e}")

    def auto_start_alarm_monitoring(self) -> None:
        """Automatically start alarm monitoring if there are enabled alarms."""
        if not self.alarms:
            return

        enabled_count = sum(1 for alarm in self.alarms if alarm['enabled'])
        if enabled_count > 0:
            self.start_alarm_monitor()
            logger.info(f"Auto-started alarm monitoring with {enabled_count} enabled alarms")

    def refresh_alarm_list(self) -> None:
        """Refresh the alarm list display."""
        self.alarm_listbox.delete(0, tk.END)
        for alarm in self.alarms:
            status = "✓ ON" if alarm['enabled'] else "✗ OFF"
            hour = alarm['hour']
            minute = alarm['minute']
            am_pm = alarm.get('am_pm', 'AM')
            time_str = f"{hour}:{minute:02d} {am_pm}"

            actions = []
            if alarm.get('play_recording', False):
                actions.append("Rec")
            if alarm.get('play_mp3', False):
                actions.append("MP3")
            if alarm.get('pause_autoclicker', False):
                actions.append("Pause")
            if alarm.get('start_autoclicker', False):
                actions.append("Start")
            if alarm.get('click_image', False):
                actions.append("Img")
            action_text = "+".join(actions) if actions else "None"

            days = alarm.get('days', [])
            if len(days) == 7:
                days_text = "Every day"
            elif days:
                day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                days_text = ",".join([day_names[d] for d in sorted(days)])
            else:
                days_text = "No days"

            display_text = f"{status} | {time_str} | {days_text} | {action_text}"
            self.alarm_listbox.insert(tk.END, display_text)

    def show_alarm_dialog(self, mode: str = "add", alarm_index: Optional[int] = None) -> None:
        """Show dialog for adding or editing an alarm with enhanced features."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Alarm" if mode == "add" else "Edit Alarm")
        dialog.geometry("500x650")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()

        # If editing, load existing alarm data
        if mode == "edit" and alarm_index is not None:
            alarm = self.alarms[alarm_index]
        else:
            alarm = None

        # Create canvas with scrollbar for scrollable content
        canvas = tk.Canvas(dialog)
        scrollbar = tk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Make scrollable frame expand to fill canvas width
        def _configure_canvas(event: Any) -> None:
            canvas_width = event.width
            canvas.itemconfig(window_id, width=canvas_width)
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", _configure_canvas)

        # Enable mouse wheel scrolling
        def _on_mousewheel(event: Any) -> None:
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Time settings (12-hour format with AM/PM)
        time_frame = tk.LabelFrame(scrollable_frame, text="Time (12-hour format)", padx=15, pady=10)
        time_frame.pack(fill=tk.X, padx=15, pady=5)

        time_inputs = tk.Frame(time_frame)
        time_inputs.pack()

        tk.Label(time_inputs, text="Hour:", font=("Arial", 9)).pack(side=tk.LEFT, padx=3)
        hour_var = tk.IntVar(value=alarm.get('hour', 12) if alarm else 12)
        tk.Spinbox(
            time_inputs,
            from_=1,
            to=12,
            textvariable=hour_var,
            width=4,
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=3)

        tk.Label(time_inputs, text="Minute:", font=("Arial", 9)).pack(side=tk.LEFT, padx=(10, 3))
        minute_var = tk.IntVar(value=alarm.get('minute', 0) if alarm else 0)
        tk.Spinbox(
            time_inputs,
            from_=0,
            to=59,
            textvariable=minute_var,
            width=4,
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=3)

        am_pm_var = tk.StringVar(value=alarm.get('am_pm', 'AM') if alarm else 'AM')
        am_pm_combo = ttk.Combobox(
            time_inputs,
            textvariable=am_pm_var,
            values=["AM", "PM"],
            state="readonly",
            width=4,
            font=("Arial", 9)
        )
        am_pm_combo.pack(side=tk.LEFT, padx=(10, 3))

        # Day selection
        day_frame = tk.LabelFrame(scrollable_frame, text="Repeat on Days", padx=15, pady=10)
        day_frame.pack(fill=tk.X, padx=15, pady=5)

        day_vars: List[tk.BooleanVar] = []
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        days_grid = tk.Frame(day_frame)
        days_grid.pack()

        for i, day_name in enumerate(day_names):
            var = tk.BooleanVar(value=i in alarm.get('days', []) if alarm else False)
            day_vars.append(var)
            tk.Checkbutton(
                days_grid,
                text=day_name,
                variable=var,
                font=("Arial", 9)
            ).grid(row=i // 2, column=i % 2, sticky=tk.W, padx=10, pady=2)

        # Select all/none buttons
        select_btns = tk.Frame(day_frame)
        select_btns.pack(pady=5)

        def select_all_days() -> None:
            for var in day_vars:
                var.set(True)

        def select_no_days() -> None:
            for var in day_vars:
                var.set(False)

        tk.Button(select_btns, text="All", command=select_all_days, width=6, font=("Arial", 8)).pack(side=tk.LEFT, padx=3)
        tk.Button(select_btns, text="None", command=select_no_days, width=6, font=("Arial", 8)).pack(side=tk.LEFT, padx=3)

        # Actions (checkboxes for multiple actions)
        action_frame = tk.LabelFrame(scrollable_frame, text="Actions (Select one or more)", padx=15, pady=10)
        action_frame.pack(fill=tk.X, padx=15, pady=5)

        play_recording_var = tk.BooleanVar(value=alarm.get('play_recording', False) if alarm else False)
        play_mp3_var = tk.BooleanVar(value=alarm.get('play_mp3', False) if alarm else False)
        pause_autoclicker_var = tk.BooleanVar(value=alarm.get('pause_autoclicker', False) if alarm else False)
        start_autoclicker_var = tk.BooleanVar(value=alarm.get('start_autoclicker', False) if alarm else False)
        click_image_var = tk.BooleanVar(value=alarm.get('click_image', False) if alarm else False)

        tk.Checkbutton(action_frame, text="Play Recording", variable=play_recording_var, font=("Arial", 8)).pack(anchor=tk.W, pady=1)
        tk.Checkbutton(action_frame, text="Play MP3 File", variable=play_mp3_var, font=("Arial", 8)).pack(anchor=tk.W, pady=1)
        tk.Checkbutton(action_frame, text="Pause Autoclicker", variable=pause_autoclicker_var, font=("Arial", 8)).pack(anchor=tk.W, pady=1)
        tk.Checkbutton(action_frame, text="Start Autoclicker", variable=start_autoclicker_var, font=("Arial", 8)).pack(anchor=tk.W, pady=1)
        tk.Checkbutton(action_frame, text="Click on Image", variable=click_image_var, font=("Arial", 8)).pack(anchor=tk.W, pady=1)

        # Recording file selection
        recording_frame = tk.LabelFrame(scrollable_frame, text="Recording File", padx=15, pady=8)
        recording_frame.pack(fill=tk.X, padx=15, pady=3)

        recording_file_var = tk.StringVar(value=alarm.get('recording_file', '') if alarm else '')
        recording_entry_frame = tk.Frame(recording_frame)
        recording_entry_frame.pack(fill=tk.X, pady=3)

        tk.Entry(recording_entry_frame, textvariable=recording_file_var, font=("Arial", 8), state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))

        def browse_recording() -> None:
            filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
            if filename:
                recording_file_var.set(filename)

        tk.Button(recording_entry_frame, text="Browse...", command=browse_recording, font=("Arial", 8), cursor="hand2").pack(side=tk.LEFT)

        # MP3 file selection
        mp3_frame = tk.LabelFrame(scrollable_frame, text="MP3 File", padx=15, pady=8)
        mp3_frame.pack(fill=tk.X, padx=15, pady=3)

        mp3_file_var = tk.StringVar(value=alarm.get('mp3_file', '') if alarm else '')
        mp3_entry_frame = tk.Frame(mp3_frame)
        mp3_entry_frame.pack(fill=tk.X, pady=3)

        tk.Entry(mp3_entry_frame, textvariable=mp3_file_var, font=("Arial", 8), state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))

        def browse_mp3() -> None:
            filename = filedialog.askopenfilename(filetypes=[("MP3 files", "*.mp3"), ("All audio files", "*.mp3 *.wav *.ogg"), ("All files", "*.*")])
            if filename:
                mp3_file_var.set(filename)

        tk.Button(mp3_entry_frame, text="Browse...", command=browse_mp3, font=("Arial", 8), cursor="hand2").pack(side=tk.LEFT)

        # Image files selection (multiple images supported)
        image_frame = tk.LabelFrame(scrollable_frame, text="Image Files (for Click on Image)", padx=15, pady=8)
        image_frame.pack(fill=tk.X, padx=15, pady=3)

        # Initialize image_files list from alarm data
        image_files_list: List[Dict[str, Any]] = []
        if alarm:
            if 'image_file' in alarm and alarm['image_file']:
                image_files_list = [{'file': alarm['image_file'], 'monitor': alarm.get('image_monitor', 0)}]
            elif 'image_files' in alarm:
                image_files_list = alarm['image_files']

        images_container = tk.Frame(image_frame)
        images_container.pack(fill=tk.X, pady=3)

        image_entries: List[tuple] = []

        def add_image_entry(image_data: Optional[Dict[str, Any]] = None) -> None:
            entry_frame = tk.Frame(images_container, bd=1, relief=tk.GROOVE, padx=5, pady=5)
            entry_frame.pack(fill=tk.X, pady=2)

            file_var = tk.StringVar(value=image_data['file'] if image_data else '')
            monitor_var = tk.IntVar(value=image_data['monitor'] if image_data else 0)

            file_frame = tk.Frame(entry_frame)
            file_frame.pack(fill=tk.X)

            tk.Entry(file_frame, textvariable=file_var, font=("Arial", 8), state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))

            def browse_image() -> None:
                filename = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")])
                if filename:
                    file_var.set(filename)

            tk.Button(file_frame, text="Browse", command=browse_image, font=("Arial", 7), cursor="hand2", width=8).pack(side=tk.LEFT, padx=2)

            def remove_entry() -> None:
                entry_frame.destroy()
                image_entries.remove((file_var, monitor_var, entry_frame))

            tk.Button(file_frame, text="✕", command=remove_entry, font=("Arial", 8, "bold"), fg="red", cursor="hand2", width=2).pack(side=tk.LEFT)

            monitor_frame = tk.Frame(entry_frame)
            monitor_frame.pack(fill=tk.X, pady=(3, 0))

            tk.Label(monitor_frame, text="Monitor:", font=("Arial", 7)).pack(side=tk.LEFT, padx=(0, 5))

            monitor_options = ["All Monitors"] + [f"Monitor {i+1}" for i in range(len(self.analyzer.get_monitors()))]
            monitor_combo = ttk.Combobox(monitor_frame, values=monitor_options, state='readonly', font=("Arial", 7), width=13)
            monitor_combo.current(monitor_var.get())
            monitor_combo.pack(side=tk.LEFT)

            def on_monitor_change(event: Any) -> None:
                monitor_var.set(monitor_combo.current())

            monitor_combo.bind('<<ComboboxSelected>>', on_monitor_change)
            image_entries.append((file_var, monitor_var, entry_frame))

        if image_files_list:
            for img_data in image_files_list:
                add_image_entry(img_data)
        else:
            add_image_entry()

        add_btn_frame = tk.Frame(image_frame)
        add_btn_frame.pack(fill=tk.X, pady=(5, 0))

        tk.Button(add_btn_frame, text="+ Add Another Image", command=lambda: add_image_entry(), font=("Arial", 8), cursor="hand2", bg="#4CAF50", fg="white").pack()

        # Playback speed
        speed_frame = tk.LabelFrame(scrollable_frame, text="Recording Playback Speed", padx=15, pady=8)
        speed_frame.pack(fill=tk.X, padx=15, pady=3)

        speed_var = tk.DoubleVar(value=alarm.get('speed', 1.0) if alarm else 1.0)
        speed_inputs = tk.Frame(speed_frame)
        speed_inputs.pack()

        tk.Label(speed_inputs, text="Speed:", font=("Arial", 8)).pack(side=tk.LEFT, padx=3)
        tk.Spinbox(speed_inputs, from_=0.1, to=10.0, increment=0.1, textvariable=speed_var, width=6, font=("Arial", 8)).pack(side=tk.LEFT, padx=3)
        tk.Label(speed_inputs, text="x", font=("Arial", 8)).pack(side=tk.LEFT)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Save button
        def save_alarm() -> None:
            canvas.unbind_all("<MouseWheel>")

            if not (play_recording_var.get() or play_mp3_var.get() or pause_autoclicker_var.get() or start_autoclicker_var.get() or click_image_var.get()):
                messagebox.showwarning("No Action Selected", "Please select at least one action")
                return

            if play_recording_var.get() and not recording_file_var.get():
                messagebox.showwarning("Input Required", "Please select a recording file")
                return

            if play_mp3_var.get() and not mp3_file_var.get():
                messagebox.showwarning("Input Required", "Please select an MP3 file")
                return

            selected_days = [i for i, var in enumerate(day_vars) if var.get()]
            if not selected_days:
                messagebox.showwarning("No Days Selected", "Please select at least one day")
                return

            time_changed = False
            if alarm:
                if (alarm.get('hour') != hour_var.get() or alarm.get('minute') != minute_var.get() or alarm.get('am_pm') != am_pm_var.get()):
                    time_changed = True

            image_files = []
            for file_var_item, monitor_var_item, _ in image_entries:
                file_path = file_var_item.get()
                if file_path:
                    image_files.append({'file': file_path, 'monitor': monitor_var_item.get()})

            alarm_data = {
                'hour': hour_var.get(),
                'minute': minute_var.get(),
                'am_pm': am_pm_var.get(),
                'days': selected_days,
                'play_recording': play_recording_var.get(),
                'play_mp3': play_mp3_var.get(),
                'pause_autoclicker': pause_autoclicker_var.get(),
                'start_autoclicker': start_autoclicker_var.get(),
                'click_image': click_image_var.get(),
                'recording_file': recording_file_var.get(),
                'mp3_file': mp3_file_var.get(),
                'image_files': image_files,
                'speed': speed_var.get(),
                'enabled': alarm['enabled'] if alarm else True,
                'triggered_today': {} if time_changed else (alarm.get('triggered_today', {}) if alarm else {})
            }

            if mode == "add":
                self.alarms.append(alarm_data)
                self.log(f"Alarm added: {hour_var.get()}:{minute_var.get():02d} {am_pm_var.get()}")
            else:
                self.alarms[alarm_index] = alarm_data
                self.log(f"Alarm updated: {hour_var.get()}:{minute_var.get():02d} {am_pm_var.get()}")

            self.refresh_alarm_list()
            self.save_alarms()
            dialog.destroy()

        def cancel_dialog() -> None:
            canvas.unbind_all("<MouseWheel>")
            dialog.destroy()

        btn_frame = tk.Frame(scrollable_frame)
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="💾 Save Alarm", command=save_alarm, bg="#27ae60", fg="white", font=("Arial", 11, "bold"), padx=20, pady=10, cursor="hand2").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=cancel_dialog, bg="#95a5a6", fg="white", font=("Arial", 10, "bold"), padx=15, pady=8, cursor="hand2").pack(side=tk.LEFT, padx=5)

    def start_alarm_monitor(self) -> None:
        """Start monitoring all alarms."""
        if not self.alarms:
            messagebox.showwarning("No Alarms", "Please add at least one alarm first")
            return

        enabled_count = sum(1 for alarm in self.alarms if alarm['enabled'])
        if enabled_count == 0:
            messagebox.showwarning("No Enabled Alarms", "Please enable at least one alarm")
            return

        self.alarm_monitor_running = True
        self.start_monitor_btn.config(state=tk.DISABLED)
        self.stop_monitor_btn.config(state=tk.NORMAL)
        self.alarm_monitor_status_label.config(text=f"✓ Monitoring: ON ({enabled_count} active)", fg="#27ae60")

        self.log(f"Alarm monitoring started ({enabled_count} alarms active)")
        self.update_status(f"Monitoring {enabled_count} alarms")

        def monitor_thread_func() -> None:
            import time as time_module
            while self.alarm_monitor_running:
                now = datetime.now()
                current_hour_24 = now.hour
                current_minute = now.minute
                current_weekday = now.weekday()

                for alarm in self.alarms:
                    if not alarm['enabled']:
                        continue

                    if current_weekday not in alarm.get('days', []):
                        continue

                    alarm_hour_12 = alarm['hour']
                    am_pm = alarm.get('am_pm', 'AM')

                    if am_pm == 'PM' and alarm_hour_12 != 12:
                        alarm_hour_24 = alarm_hour_12 + 12
                    elif am_pm == 'AM' and alarm_hour_12 == 12:
                        alarm_hour_24 = 0
                    else:
                        alarm_hour_24 = alarm_hour_12

                    alarm_minute = alarm['minute']
                    trigger_key = f"{now.year}-{now.month}-{now.day}"

                    if 'triggered_today' not in alarm:
                        alarm['triggered_today'] = {}

                    if (current_hour_24 == alarm_hour_24 and
                        current_minute == alarm_minute and
                        alarm['triggered_today'].get(trigger_key, False) == False):

                        time_str = f"{alarm_hour_12}:{alarm_minute:02d} {am_pm}"
                        self.log(f"ALARM! Triggering: {time_str}")

                        if alarm.get('play_mp3', False):
                            self.play_mp3(alarm.get('mp3_file', ''))

                        if alarm.get('play_recording', False):
                            self.play_alarm_recording(
                                alarm.get('recording_file', ''),
                                alarm.get('speed', 1.0)
                            )

                        if alarm.get('click_image', False):
                            self._execute_alarm_image_clicks(alarm)

                        if alarm.get('pause_autoclicker', False):
                            if self.img_click_running:
                                self.image_click_tab.stop_image_click()
                                self.log("Image Click stopped by alarm")

                        if alarm.get('start_autoclicker', False):
                            if not self.img_click_running:
                                self.image_click_tab.start_image_click()
                                self.log("Image Click started by alarm")

                        alarm['triggered_today'][trigger_key] = True
                        self.save_alarms()

                time_module.sleep(1)

        self.alarm_monitor_thread = threading.Thread(target=monitor_thread_func, daemon=True)
        self.alarm_monitor_thread.start()

    def _execute_alarm_image_clicks(self, alarm: Dict[str, Any]) -> None:
        """Execute image click actions for an alarm."""
        import time as time_module
        
        image_files = []
        if 'image_files' in alarm and alarm['image_files']:
            image_files = alarm['image_files']
        elif 'image_file' in alarm and alarm['image_file']:
            image_files = [{
                'file': alarm['image_file'],
                'monitor': alarm.get('image_monitor', 0)
            }]

        if image_files:
            self.log(f"Alarm will search for {len(image_files)} image(s)...")
            for idx, img_data in enumerate(image_files, 1):
                image_file = img_data['file']
                monitor_index = img_data['monitor']
                monitor = None if monitor_index == 0 else monitor_index

                self.log(f"Searching for image {idx}/{len(image_files)}: {os.path.basename(image_file)}")
                found = self.find_and_click_image(image_file, 0.8, monitor, max_retries=5, retry_interval=2.0)

                if found:
                    self.log(f"Image {idx} found and clicked!")
                    if idx < len(image_files):
                        time_module.sleep(1.0)
                else:
                    self.log(f"Image {idx} not found after 5 attempts")

    def stop_alarm_monitor(self) -> None:
        """Stop monitoring all alarms."""
        self.alarm_monitor_running = False
        self.start_monitor_btn.config(state=tk.NORMAL)
        self.stop_monitor_btn.config(state=tk.DISABLED)
        self.alarm_monitor_status_label.config(text="⚫ Monitoring: OFF", fg="gray")

        self.log("Alarm monitoring stopped")
        self.update_status("Alarm monitoring stopped")

    def find_and_click_image(
        self,
        image_path: str,
        confidence: float = 0.8,
        monitor: Optional[int] = None,
        max_retries: int = -1,
        retry_interval: float = 2.0
    ) -> bool:
        """Find an image on screen and click on it."""
        try:
            if not os.path.exists(image_path):
                self.log(f"Image file not found: {image_path}")
                return False

            attempt = 0
            image_name = os.path.basename(image_path)
            self.log(f"Searching for image: {image_name}")

            while (max_retries == -1 or attempt < max_retries) and self.alarm_monitor_running:
                try:
                    result = self.analyzer.find_image_on_screen(image_path, confidence, monitor)

                    if result:
                        x, y, match_confidence = result

                        if monitor is not None:
                            monitors = self.analyzer.get_monitors()
                            if monitor > 0 and monitor <= len(monitors):
                                mon = monitors[monitor - 1]
                                x += mon['left']
                                y += mon['top']

                        pyautogui.moveTo(x, y, duration=0.2)
                        pyautogui.click()
                        self.log(f"Image found and clicked at ({x}, {y}) with confidence {match_confidence:.2f}")
                        return True
                    else:
                        attempt += 1
                        if attempt == 1:
                            self.log(f"Image not found, retrying every {retry_interval}s until found...")
                        
                        for _ in range(int(retry_interval * 10)):
                            if not self.alarm_monitor_running:
                                return False
                            time.sleep(0.1)

                except Exception as search_error:
                    self.log(f"Error during image search (attempt {attempt}): {search_error}")
                    time.sleep(retry_interval)
                    attempt += 1

            return False

        except Exception as e:
            self.log(f"Error finding/clicking image: {e}")
            return False

    def play_mp3(self, mp3_file: str) -> None:
        """Play an MP3 file."""
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(mp3_file)
            pygame.mixer.music.play()
            self.log(f"Playing MP3: {mp3_file}")
        except Exception as e:
            self.log(f"Error playing MP3: {e}")

    def play_alarm_recording(self, recording_file: str, speed: float = 1.0) -> None:
        """Play a recording file for alarm."""
        try:
            with open(recording_file, 'r') as f:
                data = json.load(f)
                events = data['events']

            self.log(f"Playing recording: {recording_file}")
            self.clicker.play_recording(events, speed=speed)
        except Exception as e:
            self.log(f"Error playing recording: {e}")

    def show_monitor_preview(self) -> None:
        """Show preview window with thumbnails of all monitors."""
        try:
            thumbnails = self.analyzer.get_monitor_thumbnails(max_width=300)

            preview_window = tk.Toplevel(self.root)
            preview_window.title("Monitor Preview")
            preview_window.geometry("700x600")

            tk.Label(
                preview_window,
                text="Monitor Previews - Click to refresh",
                font=("Arial", 14, "bold"),
                pady=10
            ).pack()

            canvas = tk.Canvas(preview_window)
            scrollbar = ttk.Scrollbar(preview_window, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            for i, thumbnail in enumerate(thumbnails):
                monitor_frame = tk.LabelFrame(
                    scrollable_frame,
                    text=f"Monitor {i + 1}",
                    padx=10,
                    pady=10,
                    font=("Arial", 11, "bold")
                )
                monitor_frame.pack(fill=tk.X, padx=15, pady=8)

                photo = ImageTk.PhotoImage(thumbnail)
                label = tk.Label(monitor_frame, image=photo)
                label.image = photo  # type: ignore
                label.pack()

                try:
                    monitors = self.analyzer.get_monitors()
                    mon = monitors[i]
                    info_text = f"Size: {mon['width']}x{mon['height']} | Position: ({mon['left']}, {mon['top']})"
                    tk.Label(
                        monitor_frame,
                        text=info_text,
                        font=("Arial", 9),
                        fg="gray"
                    ).pack(pady=5)
                except:
                    pass

            canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            scrollbar.pack(side="right", fill="y")

            refresh_btn = tk.Button(
                preview_window,
                text="🔄 Refresh Previews",
                command=lambda: [preview_window.destroy(), self.show_monitor_preview()],
                bg="#3498db",
                fg="white",
                font=("Arial", 10, "bold"),
                padx=20,
                pady=10,
                cursor="hand2"
            )
            refresh_btn.pack(pady=10)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create monitor preview: {e}")
            self.log(f"Error creating monitor preview: {e}")

    def log(self, message: str) -> None:
        """Add message to log and write to file."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"

        # Log to GUI
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, full_message)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

        # Log to file via logger
        logger.info(message)

    def update_status(self, message: str) -> None:
        """Update status bar."""
        self.status_bar.config(text=message)

    def on_closing(self) -> None:
        """Handle window closing."""
        self.save_settings()

        try:
            keyboard.unhook_all()
        except:
            pass
        self.root.destroy()


def main() -> None:
    """Main entry point."""
    root = tk.Tk()
    app = AutoClickerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
