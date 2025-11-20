"""
GUI Application for Auto Clicker with Image Template Matching
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import json
import time
from datetime import datetime
from PIL import Image, ImageTk
import keyboard
import pyautogui
from mouse_recorder import MouseRecorder
from auto_clicker import AutoClicker
from screenshot_analyzer import ScreenshotAnalyzer


class AutoClickerGUI:
    def __init__(self, root):
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
        self.is_recording = False
        self.current_recording_file = None
        self.loaded_events = []
        self.img_click_running = False  # Flag for stopping image click
        self.alarms = []  # List of alarm dictionaries
        self.alarm_monitor_running = False  # Flag for alarm monitoring thread
        self.alarm_monitor_thread = None  # Thread for monitoring all alarms
        self.alarms_file = "alarms.json"  # Separate file for alarms

        # Setup GUI
        self.setup_gui()

    def setup_gui(self):
        """Setup the GUI layout"""
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

        # Create notebook (tabs) - reduced padding
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Create tabs
        self.create_image_click_tab()
        self.create_recorder_tab()
        self.create_playback_tab()
        self.create_alarm_tab()

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

        # Log area - more compact
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

    def setup_hotkeys(self):
        """Setup global keyboard shortcuts"""
        try:
            # F11 to start image click
            keyboard.add_hotkey('f11', self.hotkey_start_image_click, suppress=False)
            # F12 to stop image click
            keyboard.add_hotkey('f12', self.hotkey_stop_image_click, suppress=False)
            self.log("Hotkeys enabled: F11=Start Image Click, F12=Stop Image Click")
        except Exception as e:
            self.log(f"Warning: Could not setup hotkeys: {e}")

    def hotkey_start_recording(self):
        """Hotkey handler for starting recording"""
        if not self.is_recording:
            self.root.after(0, self.start_recording)

    def hotkey_stop_recording(self):
        """Hotkey handler for stopping recording"""
        if self.is_recording:
            self.root.after(0, self.stop_recording)

    def hotkey_start_image_click(self):
        """Hotkey handler for starting image click"""
        if not self.img_click_running:
            self.root.after(0, self.start_image_click)

    def hotkey_stop_image_click(self):
        """Hotkey handler for stopping image click"""
        if self.img_click_running:
            self.root.after(0, self.stop_image_click)

    def manual_save_settings(self):
        """Manually save settings with user feedback"""
        self.save_settings()
        self.log("Settings saved successfully!")
        self.update_status("Settings saved")
        # Brief visual feedback
        self.root.after(2000, lambda: self.update_status("Ready"))

    def manual_load_settings(self):
        """Manually load settings with user feedback"""
        self.load_settings()
        self.apply_saved_settings()
        self.log("Settings reloaded from file!")
        self.update_status("Settings loaded")
        # Brief visual feedback
        self.root.after(2000, lambda: self.update_status("Ready"))

    def save_settings(self):
        """Save current settings to file"""
        settings = {
            # Playback settings
            "last_playback_file": self.playback_filename_var.get() if hasattr(self, 'playback_filename_var') else "",
            "playback_speed": self.speed_var.get() if hasattr(self, 'speed_var') else 1.0,

            # Image Click settings
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

            # Recording settings
            "record_filename": self.record_filename_var.get() if hasattr(self, 'record_filename_var') else "recording.json",

            # Screenshot settings
            "screenshot_mode": self.screenshot_mode_var.get() if hasattr(self, 'screenshot_mode_var') else "full",
            "ss_region_x": self.ss_region_x_var.get() if hasattr(self, 'ss_region_x_var') else "",
            "ss_region_y": self.ss_region_y_var.get() if hasattr(self, 'ss_region_y_var') else "",
            "ss_region_w": self.ss_region_w_var.get() if hasattr(self, 'ss_region_w_var') else "",
            "ss_region_h": self.ss_region_h_var.get() if hasattr(self, 'ss_region_h_var') else "",
            "screenshot_filename": self.screenshot_filename_var.get() if hasattr(self, 'screenshot_filename_var') else ""
        }

        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_settings(self):
        """Load settings from file"""
        if not os.path.exists(self.settings_file):
            return

        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)

            # Store settings to apply after UI is created
            self.saved_settings = settings
            # Don't log here - log widget doesn't exist yet
            print("Settings loaded from file")
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.saved_settings = {}

    def apply_saved_settings(self):
        """Apply saved settings to UI elements"""
        if not hasattr(self, 'saved_settings') or not self.saved_settings:
            return

        settings = self.saved_settings

        try:
            # Apply playback settings
            if "last_playback_file" in settings and hasattr(self, 'playback_filename_var'):
                self.playback_filename_var.set(settings["last_playback_file"])
            if "playback_speed" in settings and hasattr(self, 'speed_var'):
                self.speed_var.set(settings["playback_speed"])

            # Apply Image Click settings
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
                if hasattr(self, 'toggle_img_repeat_count'):
                    self.toggle_img_repeat_count()
            if "img_retry_on_not_found" in settings and hasattr(self, 'img_retry_on_not_found_var'):
                self.img_retry_on_not_found_var.set(settings["img_retry_on_not_found"])
            if "img_playback_file" in settings and hasattr(self, 'img_playback_file_var'):
                self.img_playback_file_var.set(settings["img_playback_file"])
            if "img_playback_speed" in settings and hasattr(self, 'img_playback_speed_var'):
                self.img_playback_speed_var.set(settings["img_playback_speed"])

            # Apply recording settings
            if "record_filename" in settings and hasattr(self, 'record_filename_var'):
                self.record_filename_var.set(settings["record_filename"])

            # Apply screenshot settings
            if "screenshot_mode" in settings and hasattr(self, 'screenshot_mode_var'):
                self.screenshot_mode_var.set(settings["screenshot_mode"])
            if "ss_region_x" in settings and hasattr(self, 'ss_region_x_var'):
                self.ss_region_x_var.set(settings["ss_region_x"])
            if "ss_region_y" in settings and hasattr(self, 'ss_region_y_var'):
                self.ss_region_y_var.set(settings["ss_region_y"])
            if "ss_region_w" in settings and hasattr(self, 'ss_region_w_var'):
                self.ss_region_w_var.set(settings["ss_region_w"])
            if "ss_region_h" in settings and hasattr(self, 'ss_region_h_var'):
                self.ss_region_h_var.set(settings["ss_region_h"])
            if "screenshot_filename" in settings and hasattr(self, 'screenshot_filename_var'):
                self.screenshot_filename_var.set(settings["screenshot_filename"])

            # Update UI based on loaded settings
            if hasattr(self, 'update_img_action_controls'):
                self.update_img_action_controls()

            # Log success after log widget exists
            if hasattr(self, 'log_text'):
                self.log("Settings loaded from previous session")

        except Exception as e:
            import traceback
            print(f"Error applying settings: {e}")
            traceback.print_exc()

    def load_alarms(self):
        """Load alarms from separate alarms.json file"""
        if not os.path.exists(self.alarms_file):
            self.alarms = []
            return

        try:
            with open(self.alarms_file, 'r') as f:
                self.alarms = json.load(f)
            print(f"Loaded {len(self.alarms)} alarms from {self.alarms_file}")
            # Refresh alarm list if widget exists
            if hasattr(self, 'alarm_listbox'):
                self.refresh_alarm_list()
        except Exception as e:
            print(f"Error loading alarms: {e}")
            self.alarms = []

    def save_alarms(self):
        """Save alarms to separate alarms.json file"""
        try:
            with open(self.alarms_file, 'w') as f:
                json.dump(self.alarms, f, indent=2)
            print(f"Saved {len(self.alarms)} alarms to {self.alarms_file}")
        except Exception as e:
            print(f"Error saving alarms: {e}")

    def auto_start_alarm_monitoring(self):
        """Automatically start alarm monitoring if there are enabled alarms"""
        if not self.alarms:
            return

        enabled_count = sum(1 for alarm in self.alarms if alarm['enabled'])
        if enabled_count > 0:
            # Start monitoring without showing any messages
            self.start_alarm_monitor()
            print(f"Auto-started alarm monitoring with {enabled_count} enabled alarms")

    def find_and_click_image(self, image_path, confidence=0.8, monitor=None, max_retries=-1, retry_interval=2.0):
        """
        Find an image on screen and click on it. Keeps retrying until found.

        Args:
            image_path: Path to the image file to find
            confidence: Confidence threshold (0-1) for matching
            monitor: Monitor number (1, 2, etc.) or None for all monitors
            max_retries: Maximum number of retries (-1 for unlimited)
            retry_interval: Time in seconds between retries

        Returns:
            True if image was found and clicked, False if max retries exceeded or file not found
        """
        try:
            if not os.path.exists(image_path):
                self.log(f"Image file not found: {image_path}")
                return False

            attempt = 0
            image_name = os.path.basename(image_path)
            self.log(f"Searching for image: {image_name}")

            while (max_retries == -1 or attempt < max_retries) and self.alarm_monitor_running:
                try:
                    # Find the image on screen
                    result = self.analyzer.find_image_on_screen(image_path, confidence, monitor)

                    if result:
                        x, y, match_confidence = result

                        # Adjust coordinates if monitor was specified
                        if monitor is not None:
                            monitors = self.analyzer.get_monitors()
                            if monitor > 0 and monitor <= len(monitors):
                                mon = monitors[monitor - 1]
                                x += mon['left']
                                y += mon['top']
                                self.log(f"Adjusted coordinates for monitor {monitor}: ({x}, {y})")

                        # Move mouse to the position and click
                        pyautogui.moveTo(x, y, duration=0.2)
                        pyautogui.click()
                        self.log(f"Image found and clicked at ({x}, {y}) with confidence {match_confidence:.2f}")
                        return True
                    else:
                        attempt += 1
                        if attempt == 1:
                            self.log(f"Image not found, retrying every {retry_interval}s until found...")
                        elif attempt % 10 == 0:  # Log every 10 attempts to avoid spam
                            self.log(f"Still searching for {image_name}... (attempt {attempt})")

                        # Wait before retrying (check alarm_monitor_running during sleep)
                        for _ in range(int(retry_interval * 10)):
                            if not self.alarm_monitor_running:
                                self.log(f"Image search stopped for: {image_name}")
                                return False
                            time.sleep(0.1)

                except Exception as search_error:
                    self.log(f"Error during image search (attempt {attempt}): {search_error}")
                    time.sleep(retry_interval)
                    attempt += 1

            self.log(f"Max retries ({max_retries}) reached for image: {image_name}")
            return False

        except Exception as e:
            self.log(f"Error finding/clicking image: {e}")
            return False

    def on_closing(self):
        """Handle window closing"""
        # Save settings before closing
        self.save_settings()

        try:
            # Unhook all keyboard hotkeys
            keyboard.unhook_all()
        except:
            pass
        self.root.destroy()

    def create_scrollable_tab(self, tab_name):
        """
        Create a scrollable tab frame

        Returns:
            Tuple of (tab_frame, scrollable_content_frame)
        """
        # Create the main tab frame
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=tab_name)

        # Create canvas and scrollbar
        canvas = tk.Canvas(tab, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)

        # Create scrollable frame
        scrollable_frame = ttk.Frame(canvas)

        # Update scroll region when frame changes
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # Create window in canvas and configure it to fill width
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        # Bind to enter/leave events to enable scrolling when mouse is over the tab
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")

        # Bind when mouse enters the canvas area
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)
        scrollable_frame.bind('<Enter>', _bind_to_mousewheel)
        scrollable_frame.bind('<Leave>', _unbind_from_mousewheel)

        # Make scrollable frame expand to fill canvas width
        def _configure_canvas(event):
            # Get the canvas width (subtract scrollbar if visible)
            canvas_width = event.width
            # Set the embedded window to fill the canvas width
            canvas.itemconfig(window_id, width=canvas_width)
            # Also update the scroll region
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", _configure_canvas)

        return tab, scrollable_frame

    def create_recorder_tab(self):
        """Create the mouse recorder tab"""
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
        self.record_status_label = tk.Label(
            controls_frame,
            text="⚫ Not Recording",
            font=("Segoe UI", 10, "bold"),
            fg="gray"
        )
        self.record_status_label.pack(pady=4)

        # Buttons frame
        buttons_frame = tk.Frame(controls_frame)
        buttons_frame.pack(pady=4)

        self.start_record_btn = tk.Button(
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
        self.start_record_btn.pack(side=tk.LEFT, padx=3)

        self.stop_record_btn = tk.Button(
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
        self.stop_record_btn.pack(side=tk.LEFT, padx=3)

        # Event counter
        self.event_count_label = tk.Label(
            controls_frame,
            text="Events recorded: 0",
            font=("Segoe UI", 9)
        )
        self.event_count_label.pack(pady=4)

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

        self.record_filename_var = tk.StringVar(value="recording.json")
        filename_entry = tk.Entry(
            filename_frame,
            textvariable=self.record_filename_var,
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

    def create_playback_tab(self):
        """Create the playback tab"""
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

        self.playback_filename_var = tk.StringVar()
        filename_entry = tk.Entry(
            file_frame,
            textvariable=self.playback_filename_var,
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

        self.loaded_info_label = tk.Label(
            load_frame,
            text="No recording loaded",
            font=("Segoe UI", 8),
            fg="gray"
        )
        self.loaded_info_label.pack()

        # Playback controls
        playback_frame = tk.LabelFrame(content, text="Playback Controls", padx=8, pady=6, font=("Segoe UI", 9))
        playback_frame.pack(fill=tk.X, padx=12, pady=5)

        # Speed control
        speed_frame = tk.Frame(playback_frame)
        speed_frame.pack(fill=tk.X, pady=5)

        tk.Label(speed_frame, text="Playback Speed:", font=("Segoe UI", 9)).pack(side=tk.LEFT)

        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = tk.Scale(
            speed_frame,
            from_=0.1,
            to=5.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.speed_var,
            length=180
        )
        speed_scale.pack(side=tk.LEFT, padx=8)

        self.speed_label = tk.Label(speed_frame, text="1.0x", font=("Segoe UI", 9, "bold"))
        self.speed_label.pack(side=tk.LEFT)

        self.speed_var.trace('w', lambda *args: self.speed_label.config(text=f"{self.speed_var.get():.1f}x"))

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

    def create_image_click_tab(self):
        """Create the image template matching tab"""
        tab, content = self.create_scrollable_tab("🖼 Image Click")

        # Instructions - inside scrollable content
        instructions = tk.Label(
            content,
            text="Find and click on screen elements using template images",
            font=("Segoe UI", 10),
            pady=8
        )
        instructions.pack()

        # Action buttons (at top) - more compact
        action_frame = tk.Frame(content)
        action_frame.pack(pady=12)

        self.start_img_click_btn = tk.Button(
            action_frame,
            text="▶ Start",
            command=self.start_image_click,
            bg="#27ae60",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=15,
            pady=6,
            cursor="hand2",
            relief=tk.FLAT
        )
        self.start_img_click_btn.pack(side=tk.LEFT, padx=3)

        self.stop_img_click_btn = tk.Button(
            action_frame,
            text="⏹ Stop",
            command=self.stop_image_click,
            bg="#e74c3c",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=15,
            pady=6,
            state=tk.DISABLED,
            cursor="hand2",
            relief=tk.FLAT
        )
        self.stop_img_click_btn.pack(side=tk.LEFT, padx=3)

        # Hotkey info - more compact
        hotkey_info = tk.Label(
            content,
            text="⌨ F11 = Start | F12 = Stop",
            font=("Segoe UI", 8),
            fg="#7f8c8d",
            bg="#ecf0f1",
            padx=8,
            pady=3
        )
        hotkey_info.pack(pady=3)

        # Image selection - more compact
        image_frame = tk.LabelFrame(content, text="Template Image", padx=12, pady=12, font=("Segoe UI", 9))
        image_frame.pack(fill=tk.X, padx=15, pady=8)

        tk.Label(
            image_frame,
            text="Select an image to find on screen:",
            font=("Arial", 10)
        ).pack(anchor=tk.W, pady=(0, 5))

        file_frame = tk.Frame(image_frame)
        file_frame.pack(fill=tk.X, pady=5)

        self.template_image_var = tk.StringVar()
        filename_entry = tk.Entry(
            file_frame,
            textvariable=self.template_image_var,
            font=("Arial", 10),
            state='readonly'
        )
        filename_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_btn = tk.Button(
            file_frame,
            text="Browse...",
            command=self.browse_template_image,
            cursor="hand2"
        )
        browse_btn.pack(side=tk.LEFT)

        # Confidence threshold - more compact
        confidence_frame = tk.LabelFrame(content, text="Matching Settings", padx=12, pady=12, font=("Segoe UI", 9))
        confidence_frame.pack(fill=tk.X, padx=15, pady=8)

        conf_slider_frame = tk.Frame(confidence_frame)
        conf_slider_frame.pack(fill=tk.X, pady=10)

        tk.Label(
            conf_slider_frame,
            text="Confidence Threshold:",
            font=("Arial", 10)
        ).pack(side=tk.LEFT)

        self.confidence_var = tk.DoubleVar(value=0.8)
        confidence_scale = tk.Scale(
            conf_slider_frame,
            from_=0.5,
            to=1.0,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            variable=self.confidence_var,
            length=200
        )
        confidence_scale.pack(side=tk.LEFT, padx=10)

        self.confidence_label = tk.Label(
            conf_slider_frame,
            text="0.80",
            font=("Arial", 10, "bold")
        )
        self.confidence_label.pack(side=tk.LEFT)

        self.confidence_var.trace('w', lambda *args: self.confidence_label.config(
            text=f"{self.confidence_var.get():.2f}"
        ))

        tk.Label(
            confidence_frame,
            text="Higher values = more strict matching (may miss variations)\nLower values = more lenient (may find false matches)",
            font=("Arial", 8),
            fg="gray",
            justify=tk.LEFT
        ).pack(pady=5)

        # Monitor selection
        img_monitor_frame = tk.LabelFrame(content, text="Monitor Selection", padx=12, pady=12, font=("Segoe UI", 9))
        img_monitor_frame.pack(fill=tk.X, padx=15, pady=8)

        tk.Label(
            img_monitor_frame,
            text="Select which monitor to search (for dual/multi-monitor setups):",
            font=("Arial", 9)
        ).pack(anchor=tk.W, pady=(0, 5))

        # Get available monitors
        try:
            monitors = self.analyzer.get_monitors()
            monitor_count = len(monitors)
        except:
            monitor_count = 1

        monitor_select_frame = tk.Frame(img_monitor_frame)
        monitor_select_frame.pack(fill=tk.X, pady=5)

        self.img_monitor_var = tk.IntVar(value=0)

        tk.Radiobutton(
            monitor_select_frame,
            text="All Monitors",
            variable=self.img_monitor_var,
            value=0,
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=5)

        for i in range(monitor_count):
            tk.Radiobutton(
                monitor_select_frame,
                text=f"Monitor {i + 1}",
                variable=self.img_monitor_var,
                value=i + 1,
                font=("Arial", 9)
            ).pack(side=tk.LEFT, padx=5)

        # Preview button
        if monitor_count > 1:
            preview_btn = tk.Button(
                monitor_select_frame,
                text="👁 Preview Monitors",
                command=self.show_monitor_preview,
                bg="#16a085",
                fg="white",
                font=("Arial", 9, "bold"),
                padx=10,
                pady=5,
                cursor="hand2"
            )
            preview_btn.pack(side=tk.LEFT, padx=10)

        # Action Mode Selection
        action_mode_frame = tk.LabelFrame(content, text="Action When Found", padx=12, pady=12, font=("Segoe UI", 9))
        action_mode_frame.pack(fill=tk.X, padx=15, pady=8)

        self.img_action_mode_var = tk.StringVar(value="click")

        # Create playback variables here so they exist before update_img_action_controls is called
        self.img_playback_file_var = tk.StringVar()
        self.img_playback_speed_var = tk.DoubleVar(value=1.0)

        tk.Label(
            action_mode_frame,
            text="Choose what to do when image is found:",
            font=("Arial", 9)
        ).pack(anchor=tk.W, pady=(0, 5))

        # Radio buttons for action mode
        mode_buttons_frame = tk.Frame(action_mode_frame)
        mode_buttons_frame.pack(fill=tk.X, pady=5)

        tk.Radiobutton(
            mode_buttons_frame,
            text="Simple Click",
            variable=self.img_action_mode_var,
            value="click",
            font=("Arial", 9),
            command=self.update_img_action_controls
        ).pack(side=tk.LEFT, padx=5)

        tk.Radiobutton(
            mode_buttons_frame,
            text="Play Recording",
            variable=self.img_action_mode_var,
            value="playback",
            font=("Arial", 9),
            command=self.update_img_action_controls
        ).pack(side=tk.LEFT, padx=5)

        # Container for dynamic controls
        self.img_action_controls_frame = tk.Frame(action_mode_frame)
        self.img_action_controls_frame.pack(fill=tk.X, pady=10)

        # Repeat/Interval settings (for both modes)
        repeat_frame = tk.LabelFrame(content, text="Repeat Settings", padx=12, pady=12, font=("Segoe UI", 9))
        repeat_frame.pack(fill=tk.X, padx=15, pady=8)

        tk.Label(
            repeat_frame,
            text="Configure how many times to repeat and interval before each search:",
            font=("Arial", 9)
        ).pack(anchor=tk.W, pady=(0, 5))

        # Unlimited checkbox
        self.img_unlimited_var = tk.BooleanVar(value=False)
        unlimited_check = tk.Checkbutton(
            repeat_frame,
            text="♾️ Unlimited Repeats (runs until stopped or image not found)",
            variable=self.img_unlimited_var,
            font=("Arial", 9, "bold"),
            fg="#e74c3c",
            command=self.toggle_img_repeat_count
        )
        unlimited_check.pack(anchor=tk.W, pady=5)

        # Keep retrying checkbox
        self.img_retry_on_not_found_var = tk.BooleanVar(value=False)
        retry_check = tk.Checkbutton(
            repeat_frame,
            text="🔄 Keep Retrying if Image Not Found (doesn't stop, waits and retries)",
            variable=self.img_retry_on_not_found_var,
            font=("Arial", 9, "bold"),
            fg="#3498db"
        )
        retry_check.pack(anchor=tk.W, pady=5)

        repeat_controls = tk.Frame(repeat_frame)
        repeat_controls.pack(fill=tk.X, pady=5)

        # Repeat count
        tk.Label(repeat_controls, text="Repeat Count:", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.img_repeat_var = tk.IntVar(value=1)
        self.img_repeat_spinbox = tk.Spinbox(
            repeat_controls,
            from_=1,
            to=10000,
            textvariable=self.img_repeat_var,
            width=8,
            font=("Arial", 9)
        )
        self.img_repeat_spinbox.pack(side=tk.LEFT, padx=5)

        # Interval
        tk.Label(repeat_controls, text="Interval (seconds):", font=("Arial", 9)).pack(side=tk.LEFT, padx=(20, 5))
        self.img_interval_var = tk.DoubleVar(value=0.0)
        tk.Spinbox(
            repeat_controls,
            from_=0.0,
            to=300.0,
            increment=0.5,
            textvariable=self.img_interval_var,
            width=8,
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=5)

        tk.Label(
            repeat_frame,
            text="Flow: Find image → Click/Playback → Wait interval → Repeat\nExample: Repeat=5, Interval=2 = Click every 2 seconds, 5 times total",
            font=("Arial", 8),
            fg="gray",
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=5)

        # Initialize action controls
        self.update_img_action_controls()

    def create_screenshot_tab(self):
        """Create the screenshot tab"""
        tab, content = self.create_scrollable_tab("📸 Screenshot")

        # Instructions
        instructions = tk.Label(
            content,
            text="Capture screenshots of your screen",
            font=("Arial", 11),
            pady=10
        )
        instructions.pack()

        # Screenshot options
        options_frame = tk.LabelFrame(content, text="Screenshot Options", padx=12, pady=12, font=("Segoe UI", 9))
        options_frame.pack(fill=tk.X, padx=15, pady=8)

        # Full screen or region
        self.screenshot_mode_var = tk.StringVar(value="full")

        tk.Radiobutton(
            options_frame,
            text="Full Screen",
            variable=self.screenshot_mode_var,
            value="full",
            font=("Arial", 10)
        ).pack(anchor=tk.W, pady=5)

        tk.Radiobutton(
            options_frame,
            text="Specific Region",
            variable=self.screenshot_mode_var,
            value="region",
            font=("Arial", 10)
        ).pack(anchor=tk.W)

        # Region inputs
        region_frame = tk.Frame(options_frame)
        region_frame.pack(fill=tk.X, pady=10)

        self.ss_region_x_var = tk.StringVar()
        self.ss_region_y_var = tk.StringVar()
        self.ss_region_w_var = tk.StringVar()
        self.ss_region_h_var = tk.StringVar()

        for label, var in [("X:", self.ss_region_x_var), ("Y:", self.ss_region_y_var),
                           ("Width:", self.ss_region_w_var), ("Height:", self.ss_region_h_var)]:
            frame = tk.Frame(region_frame)
            frame.pack(side=tk.LEFT, padx=5)
            tk.Label(frame, text=label, font=("Arial", 9)).pack(side=tk.LEFT)
            tk.Entry(frame, textvariable=var, width=8, font=("Arial", 9)).pack(side=tk.LEFT)

        # Save location
        save_frame = tk.LabelFrame(content, text="Save Location", padx=12, pady=12, font=("Segoe UI", 9))
        save_frame.pack(fill=tk.X, padx=15, pady=8)

        file_frame = tk.Frame(save_frame)
        file_frame.pack(fill=tk.X, pady=5)

        self.screenshot_filename_var = tk.StringVar(
            value=f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        filename_entry = tk.Entry(
            file_frame,
            textvariable=self.screenshot_filename_var,
            font=("Arial", 10)
        )
        filename_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_btn = tk.Button(
            file_frame,
            text="Browse...",
            command=self.browse_screenshot_location,
            cursor="hand2"
        )
        browse_btn.pack(side=tk.LEFT)

        # Capture button
        action_frame = tk.Frame(content)
        action_frame.pack(pady=20)

        screenshot_btn = tk.Button(
            action_frame,
            text="📸 Capture Screenshot",
            command=self.capture_screenshot,
            bg="#16a085",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=30,
            pady=15,
            cursor="hand2"
        )
        screenshot_btn.pack()

    # Recording methods
    def start_recording(self):
        """Start recording mouse events"""
        self.is_recording = True
        self.recorder.start_recording()

        self.start_record_btn.config(state=tk.DISABLED)
        self.stop_record_btn.config(state=tk.NORMAL)
        self.record_status_label.config(text="🔴 Recording...", fg="#e74c3c")

        self.log("Recording started")
        self.update_status("Recording in progress...")

        # Update event count periodically
        self.update_event_count()

    def stop_recording(self):
        """Stop recording mouse events"""
        self.is_recording = False
        events = self.recorder.stop_recording()

        self.start_record_btn.config(state=tk.NORMAL)
        self.stop_record_btn.config(state=tk.DISABLED)
        self.record_status_label.config(text="⚫ Not Recording", fg="gray")

        self.log(f"Recording stopped. Captured {len(events)} events")
        self.update_status("Recording stopped")

    def update_event_count(self):
        """Update the event count label"""
        if self.is_recording:
            count = len(self.recorder.events)
            self.event_count_label.config(text=f"Events recorded: {count}")
            self.root.after(100, self.update_event_count)
        else:
            count = len(self.recorder.events)
            self.event_count_label.config(text=f"Events recorded: {count}")

    def save_recording(self):
        """Save the current recording"""
        if not self.recorder.events:
            messagebox.showwarning("No Recording", "No events to save. Please record something first.")
            return

        filename = self.record_filename_var.get()
        if not filename:
            messagebox.showerror("Error", "Please specify a filename")
            return

        try:
            # Save with all events - no optimization needed since timing is preserved
            self.recorder.save_recording(filename, optimize=False)
            self.log(f"Recording saved to {filename} ({len(self.recorder.events)} events)")
            messagebox.showinfo("Success", f"Recording saved to {filename}")
        except Exception as e:
            self.log(f"Error saving recording: {e}")
            messagebox.showerror("Error", f"Failed to save recording: {e}")

    def browse_save_location(self):
        """Browse for save location"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.record_filename_var.set(filename)

    # Playback methods
    def browse_load_file(self):
        """Browse for recording file"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.playback_filename_var.set(filename)

    def load_recording(self):
        """Load a recording file"""
        filename = self.playback_filename_var.get()
        if not filename:
            messagebox.showerror("Error", "Please select a file")
            return

        try:
            self.loaded_events = self.recorder.load_recording(filename)
            self.loaded_info_label.config(
                text=f"✅ Loaded {len(self.loaded_events)} events",
                fg="#27ae60"
            )
            self.log(f"Loaded recording from {filename}")
        except Exception as e:
            self.log(f"Error loading recording: {e}")
            messagebox.showerror("Error", f"Failed to load recording: {e}")

    def play_recording(self):
        """Play back the loaded recording"""
        if not self.loaded_events:
            messagebox.showwarning("No Recording", "Please load a recording first")
            return

        speed = self.speed_var.get()

        def playback_thread():
            try:
                self.log(f"Starting playback at {speed}x speed...")
                self.update_status(f"Playing back recording at {speed}x speed...")
                self.clicker.play_recording(self.loaded_events, speed=speed)
                self.log("Playback completed")
                self.update_status("Playback completed")
            except Exception as e:
                self.log(f"Error during playback: {e}")
                messagebox.showerror("Error", f"Playback failed: {e}")

        threading.Thread(target=playback_thread, daemon=True).start()

    # Image Click methods
    def browse_template_image(self):
        """Browse for template image"""
        filename = filedialog.askopenfilename(
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.template_image_var.set(filename)

    def update_img_action_controls(self):
        """Update the action controls based on selected mode"""
        # Clear existing controls
        for widget in self.img_action_controls_frame.winfo_children():
            widget.destroy()

        mode = self.img_action_mode_var.get()

        if mode == "playback":
            # Show recording file selection
            tk.Label(
                self.img_action_controls_frame,
                text="Select recording to play when image is found:",
                font=("Arial", 9)
            ).pack(anchor=tk.W, pady=(0, 5))

            file_frame = tk.Frame(self.img_action_controls_frame)
            file_frame.pack(fill=tk.X, pady=5)

            # Use existing variable instead of creating new one
            filename_entry = tk.Entry(
                file_frame,
                textvariable=self.img_playback_file_var,
                font=("Arial", 9),
                state='readonly'
            )
            filename_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

            browse_btn = tk.Button(
                file_frame,
                text="Browse...",
                command=self.browse_playback_file_for_image,
                cursor="hand2"
            )
            browse_btn.pack(side=tk.LEFT)

            # Playback speed
            speed_frame = tk.Frame(self.img_action_controls_frame)
            speed_frame.pack(fill=tk.X, pady=5)

            tk.Label(speed_frame, text="Playback Speed:", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
            # Use existing variable instead of creating new one
            tk.Spinbox(
                speed_frame,
                from_=0.1,
                to=5.0,
                increment=0.1,
                textvariable=self.img_playback_speed_var,
                width=8,
                font=("Arial", 9)
            ).pack(side=tk.LEFT, padx=5)
            tk.Label(speed_frame, text="x", font=("Arial", 9)).pack(side=tk.LEFT)

    def browse_playback_file_for_image(self):
        """Browse for recording file to play when image is found"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.img_playback_file_var.set(filename)

    def toggle_img_repeat_count(self):
        """Enable/disable repeat count spinbox based on unlimited checkbox"""
        if self.img_unlimited_var.get():
            self.img_repeat_spinbox.config(state='disabled')
        else:
            self.img_repeat_spinbox.config(state='normal')

    def start_image_click(self):
        """Start finding and clicking on template image"""
        image_path = self.template_image_var.get()
        if not image_path:
            messagebox.showwarning("Input Required", "Please select a template image")
            return

        # Disable start button, enable stop button
        self.start_img_click_btn.config(state=tk.DISABLED)
        self.stop_img_click_btn.config(state=tk.NORMAL)
        self.img_click_running = True

        confidence = self.confidence_var.get()

        # Get monitor selection
        monitor = self.img_monitor_var.get()
        if monitor == 0:
            monitor = None  # None means all monitors

        # Get repeat/interval settings
        unlimited = self.img_unlimited_var.get()
        repeat_count = self.img_repeat_var.get()
        interval = self.img_interval_var.get()
        retry_on_not_found = self.img_retry_on_not_found_var.get()

        # Get action mode
        action_mode = self.img_action_mode_var.get()
        playback_events = None
        playback_speed = 1.0

        if action_mode == "playback":
            # Load recording file
            playback_file = self.img_playback_file_var.get()
            if not playback_file:
                messagebox.showwarning("Input Required", "Please select a recording file for playback mode")
                return

            try:
                with open(playback_file, 'r') as f:
                    data = json.load(f)
                    playback_events = data['events']
                    playback_speed = self.img_playback_speed_var.get()
                    self.log(f"Loaded {len(playback_events)} events from {playback_file}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load recording: {e}")
                return

        def image_click_thread():
            try:
                self.log(f"Searching for image: {image_path}")
                if monitor:
                    self.log(f"Using Monitor {monitor}")
                if action_mode == "playback":
                    self.log(f"Will play recording when found (speed: {playback_speed}x)")
                if unlimited:
                    self.log(f"Unlimited mode: Will repeat forever with {interval}s interval")
                elif repeat_count > 1:
                    self.log(f"Will repeat {repeat_count} times with {interval}s interval")
                if retry_on_not_found:
                    self.log(f"Retry mode: Will keep searching if image not found")

                self.update_status("Searching for template image...")

                success = self.clicker.click_on_image(
                    image_path,
                    confidence=confidence,
                    monitor=monitor,
                    repeat_count=repeat_count,
                    interval=interval,
                    playback_events=playback_events,
                    playback_speed=playback_speed,
                    unlimited=unlimited,
                    retry_on_not_found=retry_on_not_found,
                    stop_flag=lambda: not self.img_click_running,
                    log_callback=self.log
                )

                # Check if stopped by user before showing results
                if not self.img_click_running:
                    # User stopped it, don't show any message
                    self.log("Image click stopped by user")
                    self.update_status("Stopped")
                elif success:
                    if action_mode == "playback":
                        self.log("Image found and recording played!")
                        self.update_status("Image found and recording played")
                    else:
                        self.log("Image found and clicked!")
                        self.update_status("Image click successful")
                else:
                    self.log("Image not found")
                    self.update_status("Image not found")
            except Exception as e:
                self.log(f"Error during image click: {e}")
                self.update_status("Error during image click")
            finally:
                # Re-enable buttons when done
                self.img_click_running = False
                self.start_img_click_btn.config(state=tk.NORMAL)
                self.stop_img_click_btn.config(state=tk.DISABLED)

        threading.Thread(target=image_click_thread, daemon=True).start()

    def stop_image_click(self):
        """Stop the image click process"""
        self.img_click_running = False
        self.log("Stopping image click...")
        self.update_status("Image click stopped by user")

        # Re-enable buttons
        self.start_img_click_btn.config(state=tk.NORMAL)
        self.stop_img_click_btn.config(state=tk.DISABLED)

    # Screenshot methods
    def browse_screenshot_location(self):
        """Browse for screenshot save location"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )
        if filename:
            self.screenshot_filename_var.set(filename)

    def capture_screenshot(self):
        """Capture a screenshot"""
        mode = self.screenshot_mode_var.get()
        filename = self.screenshot_filename_var.get()

        if not filename:
            messagebox.showerror("Error", "Please specify a filename")
            return

        region = None
        if mode == "region":
            try:
                if all([self.ss_region_x_var.get(), self.ss_region_y_var.get(),
                       self.ss_region_w_var.get(), self.ss_region_h_var.get()]):
                    region = (
                        int(self.ss_region_x_var.get()),
                        int(self.ss_region_y_var.get()),
                        int(self.ss_region_w_var.get()),
                        int(self.ss_region_h_var.get())
                    )
                else:
                    messagebox.showwarning("Input Required", "Please specify region coordinates")
                    return
            except ValueError:
                messagebox.showerror("Invalid Input", "Region values must be integers")
                return

        try:
            self.log(f"Capturing screenshot...")
            screenshot = self.analyzer.capture_screenshot(region)
            self.analyzer.save_screenshot(screenshot, filename)
            self.log(f"Screenshot saved to {filename}")
            messagebox.showinfo("Success", f"Screenshot saved to {filename}")
        except Exception as e:
            self.log(f"Error capturing screenshot: {e}")
            messagebox.showerror("Error", f"Failed to capture screenshot: {e}")

    def create_alarm_tab(self):
        """Create the alarm clock tab with support for multiple alarms"""
        tab, content = self.create_scrollable_tab("⏰ Alarm Clock")

        # Instructions
        instructions = tk.Label(
            content,
            text="Create multiple alarms to play MP3 files or trigger recordings",
            font=("Segoe UI", 9),
            pady=5
        )
        instructions.pack()

        # Monitoring status (moved to top)
        status_frame = tk.LabelFrame(content, text="Monitor Status", padx=8, pady=6, font=("Segoe UI", 9))
        status_frame.pack(fill=tk.X, padx=12, pady=5)

        self.alarm_monitor_status_label = tk.Label(
            status_frame,
            text="⚫ Monitoring: OFF",
            font=("Segoe UI", 10, "bold"),
            fg="gray"
        )
        self.alarm_monitor_status_label.pack(pady=4)

        # Monitor control buttons
        monitor_btn_frame = tk.Frame(status_frame)
        monitor_btn_frame.pack(pady=4)

        self.start_monitor_btn = tk.Button(
            monitor_btn_frame,
            text="▶ Start Monitoring",
            command=self.start_alarm_monitor,
            bg="#27ae60",
            fg="white",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2"
        )
        self.start_monitor_btn.pack(side=tk.LEFT, padx=3)

        self.stop_monitor_btn = tk.Button(
            monitor_btn_frame,
            text="⏹ Stop Monitoring",
            command=self.stop_alarm_monitor,
            bg="#e74c3c",
            fg="white",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=12,
            pady=6,
            state=tk.DISABLED,
            cursor="hand2"
        )
        self.stop_monitor_btn.pack(side=tk.LEFT, padx=3)

        # Alarm list section
        list_frame = tk.LabelFrame(content, text="Alarms", padx=8, pady=6, font=("Segoe UI", 9))
        list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=5)

        # Alarm listbox with scrollbar
        listbox_frame = tk.Frame(list_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        alarm_scrollbar = tk.Scrollbar(listbox_frame)
        alarm_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.alarm_listbox = tk.Listbox(
            listbox_frame,
            yscrollcommand=alarm_scrollbar.set,
            font=("Segoe UI", 9),
            height=6,
            selectmode=tk.SINGLE
        )
        self.alarm_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        alarm_scrollbar.config(command=self.alarm_listbox.yview)

        # List action buttons
        list_btn_frame = tk.Frame(list_frame)
        list_btn_frame.pack(fill=tk.X, pady=3)

        tk.Button(
            list_btn_frame,
            text="➕ Add New Alarm",
            command=self.show_add_alarm_dialog,
            bg="#27ae60",
            fg="white",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            list_btn_frame,
            text="✏ Edit Selected",
            command=self.edit_selected_alarm,
            bg="#3498db",
            fg="white",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            list_btn_frame,
            text="🗑 Delete Selected",
            command=self.delete_selected_alarm,
            bg="#e74c3c",
            fg="white",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            list_btn_frame,
            text="🔄 Toggle On/Off",
            command=self.toggle_selected_alarm,
            bg="#f39c12",
            fg="white",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=3)

    def refresh_alarm_list(self):
        """Refresh the alarm list display"""
        self.alarm_listbox.delete(0, tk.END)
        for alarm in self.alarms:
            status = "✓ ON" if alarm['enabled'] else "✗ OFF"

            # Format time with AM/PM
            hour = alarm['hour']
            minute = alarm['minute']
            am_pm = alarm.get('am_pm', 'AM')
            time_str = f"{hour}:{minute:02d} {am_pm}"

            # Get actions
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

            # Get days
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

    def show_add_alarm_dialog(self):
        """Show dialog to add a new alarm"""
        self.show_alarm_dialog(mode="add")

    def edit_selected_alarm(self):
        """Edit the selected alarm"""
        selection = self.alarm_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an alarm to edit")
            return

        index = selection[0]
        self.show_alarm_dialog(mode="edit", alarm_index=index)

    def delete_selected_alarm(self):
        """Delete the selected alarm"""
        selection = self.alarm_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an alarm to delete")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this alarm?"):
            index = selection[0]
            del self.alarms[index]
            self.refresh_alarm_list()
            self.log("Alarm deleted")
            self.save_alarms()

    def toggle_selected_alarm(self):
        """Toggle the selected alarm on/off"""
        selection = self.alarm_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an alarm to toggle")
            return

        index = selection[0]
        self.alarms[index]['enabled'] = not self.alarms[index]['enabled']
        self.refresh_alarm_list()
        status = "enabled" if self.alarms[index]['enabled'] else "disabled"
        self.log(f"Alarm {status}")
        self.save_alarms()

    def show_alarm_dialog(self, mode="add", alarm_index=None):
        """Show dialog for adding or editing an alarm with enhanced features"""
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
        def _configure_canvas(event):
            # Get the canvas width (subtract scrollbar if visible)
            canvas_width = event.width
            # Set the embedded window to fill the canvas width
            canvas.itemconfig(window_id, width=canvas_width)
            # Also update the scroll region
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", _configure_canvas)

        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
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

        day_vars = []
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

        def select_all_days():
            for var in day_vars:
                var.set(True)

        def select_no_days():
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

        tk.Checkbutton(
            action_frame,
            text="Play Recording",
            variable=play_recording_var,
            font=("Arial", 8)
        ).pack(anchor=tk.W, pady=1)

        tk.Checkbutton(
            action_frame,
            text="Play MP3 File",
            variable=play_mp3_var,
            font=("Arial", 8)
        ).pack(anchor=tk.W, pady=1)

        tk.Checkbutton(
            action_frame,
            text="Pause Autoclicker",
            variable=pause_autoclicker_var,
            font=("Arial", 8)
        ).pack(anchor=tk.W, pady=1)

        tk.Checkbutton(
            action_frame,
            text="Start Autoclicker",
            variable=start_autoclicker_var,
            font=("Arial", 8)
        ).pack(anchor=tk.W, pady=1)

        tk.Checkbutton(
            action_frame,
            text="Click on Image",
            variable=click_image_var,
            font=("Arial", 8)
        ).pack(anchor=tk.W, pady=1)

        # Recording file selection
        recording_frame = tk.LabelFrame(scrollable_frame, text="Recording File", padx=15, pady=8)
        recording_frame.pack(fill=tk.X, padx=15, pady=3)

        recording_file_var = tk.StringVar(value=alarm.get('recording_file', '') if alarm else '')

        recording_entry_frame = tk.Frame(recording_frame)
        recording_entry_frame.pack(fill=tk.X, pady=3)

        tk.Entry(
            recording_entry_frame,
            textvariable=recording_file_var,
            font=("Arial", 8),
            state='readonly'
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))

        def browse_recording():
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                recording_file_var.set(filename)

        tk.Button(
            recording_entry_frame,
            text="Browse...",
            command=browse_recording,
            font=("Arial", 8),
            cursor="hand2"
        ).pack(side=tk.LEFT)

        # MP3 file selection
        mp3_frame = tk.LabelFrame(scrollable_frame, text="MP3 File", padx=15, pady=8)
        mp3_frame.pack(fill=tk.X, padx=15, pady=3)

        mp3_file_var = tk.StringVar(value=alarm.get('mp3_file', '') if alarm else '')

        mp3_entry_frame = tk.Frame(mp3_frame)
        mp3_entry_frame.pack(fill=tk.X, pady=3)

        tk.Entry(
            mp3_entry_frame,
            textvariable=mp3_file_var,
            font=("Arial", 8),
            state='readonly'
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))

        def browse_mp3():
            filename = filedialog.askopenfilename(
                filetypes=[
                    ("MP3 files", "*.mp3"),
                    ("All audio files", "*.mp3 *.wav *.ogg"),
                    ("All files", "*.*")
                ]
            )
            if filename:
                mp3_file_var.set(filename)

        tk.Button(
            mp3_entry_frame,
            text="Browse...",
            command=browse_mp3,
            font=("Arial", 8),
            cursor="hand2"
        ).pack(side=tk.LEFT)

        # Image files selection (multiple images supported)
        image_frame = tk.LabelFrame(scrollable_frame, text="Image Files (for Click on Image)", padx=15, pady=8)
        image_frame.pack(fill=tk.X, padx=15, pady=3)

        # Initialize image_files list from alarm data
        image_files_list = []
        if alarm:
            # Check if old format (single image)
            if 'image_file' in alarm and alarm['image_file']:
                # Convert old format to new format
                image_files_list = [{
                    'file': alarm['image_file'],
                    'monitor': alarm.get('image_monitor', 0)
                }]
            # Check if new format (multiple images)
            elif 'image_files' in alarm:
                image_files_list = alarm['image_files']

        # Container for image entries
        images_container = tk.Frame(image_frame)
        images_container.pack(fill=tk.X, pady=3)

        image_entries = []  # Store all image entry widgets

        def add_image_entry(image_data=None):
            entry_frame = tk.Frame(images_container, bd=1, relief=tk.GROOVE, padx=5, pady=5)
            entry_frame.pack(fill=tk.X, pady=2)

            file_var = tk.StringVar(value=image_data['file'] if image_data else '')
            monitor_var = tk.IntVar(value=image_data['monitor'] if image_data else 0)

            # File selection
            file_frame = tk.Frame(entry_frame)
            file_frame.pack(fill=tk.X)

            tk.Entry(
                file_frame,
                textvariable=file_var,
                font=("Arial", 8),
                state='readonly'
            ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))

            def browse_image():
                filename = filedialog.askopenfilename(
                    filetypes=[
                        ("Image files", "*.png *.jpg *.jpeg *.bmp"),
                        ("PNG files", "*.png"),
                        ("JPEG files", "*.jpg *.jpeg"),
                        ("All files", "*.*")
                    ]
                )
                if filename:
                    file_var.set(filename)

            tk.Button(
                file_frame,
                text="Browse",
                command=browse_image,
                font=("Arial", 7),
                cursor="hand2",
                width=8
            ).pack(side=tk.LEFT, padx=2)

            # Remove button
            def remove_entry():
                entry_frame.destroy()
                image_entries.remove((file_var, monitor_var, entry_frame))

            tk.Button(
                file_frame,
                text="✕",
                command=remove_entry,
                font=("Arial", 8, "bold"),
                fg="red",
                cursor="hand2",
                width=2
            ).pack(side=tk.LEFT)

            # Monitor selection
            monitor_frame = tk.Frame(entry_frame)
            monitor_frame.pack(fill=tk.X, pady=(3, 0))

            tk.Label(monitor_frame, text="Monitor:", font=("Arial", 7)).pack(side=tk.LEFT, padx=(0, 5))

            monitor_options = ["All Monitors"] + [f"Monitor {i+1}" for i in range(len(self.analyzer.get_monitors()))]
            monitor_combo = ttk.Combobox(
                monitor_frame,
                values=monitor_options,
                state='readonly',
                font=("Arial", 7),
                width=13
            )
            monitor_combo.current(monitor_var.get())
            monitor_combo.pack(side=tk.LEFT)

            def on_monitor_change(event):
                monitor_var.set(monitor_combo.current())

            monitor_combo.bind('<<ComboboxSelected>>', on_monitor_change)

            image_entries.append((file_var, monitor_var, entry_frame))

        # Add existing images
        if image_files_list:
            for img_data in image_files_list:
                add_image_entry(img_data)
        else:
            # Add one empty entry by default
            add_image_entry()

        # Add Image button
        add_btn_frame = tk.Frame(image_frame)
        add_btn_frame.pack(fill=tk.X, pady=(5, 0))

        tk.Button(
            add_btn_frame,
            text="+ Add Another Image",
            command=lambda: add_image_entry(),
            font=("Arial", 8),
            cursor="hand2",
            bg="#4CAF50",
            fg="white"
        ).pack()

        # Playback speed
        speed_frame = tk.LabelFrame(scrollable_frame, text="Recording Playback Speed", padx=15, pady=8)
        speed_frame.pack(fill=tk.X, padx=15, pady=3)

        speed_var = tk.DoubleVar(value=alarm.get('speed', 1.0) if alarm else 1.0)

        speed_inputs = tk.Frame(speed_frame)
        speed_inputs.pack()

        tk.Label(speed_inputs, text="Speed:", font=("Arial", 8)).pack(side=tk.LEFT, padx=3)
        tk.Spinbox(
            speed_inputs,
            from_=0.1,
            to=10.0,
            increment=0.1,
            textvariable=speed_var,
            width=6,
            font=("Arial", 8)
        ).pack(side=tk.LEFT, padx=3)
        tk.Label(speed_inputs, text="x", font=("Arial", 8)).pack(side=tk.LEFT)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Save button
        def save_alarm():
            # Unbind mousewheel before closing
            canvas.unbind_all("<MouseWheel>")

            # Validate that at least one action is selected
            if not (play_recording_var.get() or play_mp3_var.get() or pause_autoclicker_var.get() or start_autoclicker_var.get()):
                messagebox.showwarning("No Action Selected", "Please select at least one action")
                return

            # Validate files for selected actions
            if play_recording_var.get() and not recording_file_var.get():
                messagebox.showwarning("Input Required", "Please select a recording file")
                return

            if play_mp3_var.get() and not mp3_file_var.get():
                messagebox.showwarning("Input Required", "Please select an MP3 file")
                return

            # Get selected days
            selected_days = [i for i, var in enumerate(day_vars) if var.get()]
            if not selected_days:
                messagebox.showwarning("No Days Selected", "Please select at least one day")
                return

            # Check if time was changed when editing
            time_changed = False
            if alarm:
                old_hour = alarm.get('hour')
                old_minute = alarm.get('minute')
                old_am_pm = alarm.get('am_pm')
                new_hour = hour_var.get()
                new_minute = minute_var.get()
                new_am_pm = am_pm_var.get()

                if old_hour != new_hour or old_minute != new_minute or old_am_pm != new_am_pm:
                    time_changed = True

            # Collect all image files
            image_files = []
            for file_var, monitor_var, _ in image_entries:
                file_path = file_var.get()
                if file_path:  # Only add if file is selected
                    image_files.append({
                        'file': file_path,
                        'monitor': monitor_var.get()
                    })

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
                'image_files': image_files,  # Multiple images
                'speed': speed_var.get(),
                'enabled': alarm['enabled'] if alarm else True,
                # Clear triggered_today if time was changed, otherwise keep it
                'triggered_today': {} if time_changed else (alarm.get('triggered_today', {}) if alarm else {})
            }

            if mode == "add":
                self.alarms.append(alarm_data)
                self.log(f"Alarm added: {hour_var.get()}:{minute_var.get():02d} {am_pm_var.get()}")
            else:
                self.alarms[alarm_index] = alarm_data
                if time_changed:
                    self.log(f"Alarm updated: {hour_var.get()}:{minute_var.get():02d} {am_pm_var.get()} (trigger flag cleared)")
                else:
                    self.log(f"Alarm updated: {hour_var.get()}:{minute_var.get():02d} {am_pm_var.get()}")

            self.refresh_alarm_list()
            self.save_alarms()
            dialog.destroy()

        def cancel_dialog():
            canvas.unbind_all("<MouseWheel>")
            dialog.destroy()

        btn_frame = tk.Frame(scrollable_frame)
        btn_frame.pack(pady=15)

        tk.Button(
            btn_frame,
            text="💾 Save Alarm",
            command=save_alarm,
            bg="#27ae60",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=10,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="Cancel",
            command=cancel_dialog,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

    def start_alarm_monitor(self):
        """Start monitoring all alarms"""
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

        def monitor_thread_func():
            import time as time_module
            while self.alarm_monitor_running:
                now = datetime.now()
                current_hour_24 = now.hour
                current_minute = now.minute
                current_weekday = now.weekday()  # 0=Monday, 6=Sunday

                for alarm in self.alarms:
                    if not alarm['enabled']:
                        continue

                    # Check if today is a scheduled day
                    if current_weekday not in alarm.get('days', []):
                        continue

                    # Convert alarm time from 12-hour to 24-hour format
                    alarm_hour_12 = alarm['hour']
                    am_pm = alarm.get('am_pm', 'AM')

                    if am_pm == 'PM' and alarm_hour_12 != 12:
                        alarm_hour_24 = alarm_hour_12 + 12
                    elif am_pm == 'AM' and alarm_hour_12 == 12:
                        alarm_hour_24 = 0
                    else:
                        alarm_hour_24 = alarm_hour_12

                    alarm_minute = alarm['minute']

                    # Create unique trigger key for today
                    trigger_key = f"{now.year}-{now.month}-{now.day}"

                    # Get triggered_today dict (create if doesn't exist)
                    if 'triggered_today' not in alarm:
                        alarm['triggered_today'] = {}

                    # Check if it's time to trigger
                    if (current_hour_24 == alarm_hour_24 and
                        current_minute == alarm_minute and
                        alarm['triggered_today'].get(trigger_key, False) == False):

                        # Trigger alarm
                        time_str = f"{alarm_hour_12}:{alarm_minute:02d} {am_pm}"
                        self.log(f"ALARM! Triggering: {time_str}")

                        # Execute all selected actions
                        if alarm.get('play_mp3', False):
                            self.play_mp3(alarm.get('mp3_file', ''))

                        if alarm.get('play_recording', False):
                            self.play_alarm_recording(
                                alarm.get('recording_file', ''),
                                alarm.get('speed', 1.0)
                            )

                        # Execute Click on Image first (if enabled)
                        image_found = False
                        if alarm.get('click_image', False):
                            # Support both old and new format
                            image_files = []

                            # Check for new format (multiple images)
                            if 'image_files' in alarm and alarm['image_files']:
                                image_files = alarm['image_files']
                            # Fall back to old format (single image)
                            elif 'image_file' in alarm and alarm['image_file']:
                                image_files = [{
                                    'file': alarm['image_file'],
                                    'monitor': alarm.get('image_monitor', 0)
                                }]

                            if image_files:
                                self.log(f"Alarm will search for {len(image_files)} image(s)...")

                                # Try each image in order
                                for idx, img_data in enumerate(image_files, 1):
                                    image_file = img_data['file']
                                    monitor_index = img_data['monitor']
                                    monitor = None if monitor_index == 0 else monitor_index

                                    # Search for image with 5 attempts (not unlimited)
                                    self.log(f"Searching for image {idx}/{len(image_files)}: {os.path.basename(image_file)} (max 5 attempts)...")
                                    found = self.find_and_click_image(image_file, 0.8, monitor, max_retries=5, retry_interval=2.0)

                                    if found:
                                        self.log(f"Image {idx} found and clicked!")
                                        image_found = True
                                        # Add delay after clicking before searching for next image
                                        if idx < len(image_files):  # Not the last image
                                            self.log(f"Waiting 1 second before searching for next image...")
                                            time_module.sleep(1.0)
                                    else:
                                        self.log(f"Image {idx} not found after 5 attempts")

                                if not image_found:
                                    self.log("None of the images were found, alarm actions completed")
                                else:
                                    # Add delay after all images are clicked before pausing
                                    self.log(f"All images clicked, waiting 1 second before next action...")
                                    time_module.sleep(1.0)
                            else:
                                self.log("Click on Image action selected but no image files specified")

                        # Pause autoclicker AFTER clicking images (if enabled)
                        if alarm.get('pause_autoclicker', False):
                            if self.img_click_running:
                                self.stop_image_click()
                                self.log("Image Click stopped by alarm")

                        # Only start autoclicker if no click_image OR if image was found
                        if alarm.get('start_autoclicker', False):
                            # If click_image is enabled, only start if image was found
                            if alarm.get('click_image', False):
                                if image_found:
                                    if not self.img_click_running and hasattr(self, 'start_img_click_btn') and self.start_img_click_btn['state'] == tk.NORMAL:
                                        self.start_image_click()
                                        self.log("Image Click started by alarm (image was found)")
                                else:
                                    self.log("Skipping start autoclicker - image was not found")
                            else:
                                # No click_image action, start autoclicker normally
                                if not self.img_click_running and hasattr(self, 'start_img_click_btn') and self.start_img_click_btn['state'] == tk.NORMAL:
                                    self.start_image_click()
                                    self.log("Image Click started by alarm")

                        # Mark as triggered for today
                        alarm['triggered_today'][trigger_key] = True
                        self.save_alarms()  # Save trigger state

                    # Clean up old trigger keys (keep only last 2 days)
                    if alarm.get('triggered_today'):
                        keys_to_remove = []
                        for key in alarm['triggered_today']:
                            try:
                                year, month, day = map(int, key.split('-'))
                                trigger_date = datetime(year, month, day)
                                days_ago = (now - trigger_date).days
                                if days_ago > 1:
                                    keys_to_remove.append(key)
                            except:
                                pass
                        for key in keys_to_remove:
                            del alarm['triggered_today'][key]

                time_module.sleep(1)  # Check every second

        self.alarm_monitor_thread = threading.Thread(target=monitor_thread_func, daemon=True)
        self.alarm_monitor_thread.start()

    def stop_alarm_monitor(self):
        """Stop monitoring all alarms"""
        self.alarm_monitor_running = False
        self.start_monitor_btn.config(state=tk.NORMAL)
        self.stop_monitor_btn.config(state=tk.DISABLED)
        self.alarm_monitor_status_label.config(text="⚫ Monitoring: OFF", fg="gray")

        self.log("Alarm monitoring stopped")
        self.update_status("Alarm monitoring stopped")

    def play_mp3(self, mp3_file):
        """Play an MP3 file"""
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(mp3_file)
            pygame.mixer.music.play()
            self.log(f"Playing MP3: {mp3_file}")
        except Exception as e:
            self.log(f"Error playing MP3: {e}")

    def play_alarm_recording(self, recording_file, speed=1.0):
        """Play a recording file for alarm"""
        try:
            with open(recording_file, 'r') as f:
                data = json.load(f)
                events = data['events']

            self.log(f"Playing recording: {recording_file}")

            # Play the recording
            self.clicker.play_recording(events, speed=speed)
        except Exception as e:
            self.log(f"Error playing recording: {e}")

    # Utility methods
    def show_monitor_preview(self):
        """Show preview window with thumbnails of all monitors"""
        try:
            thumbnails = self.analyzer.get_monitor_thumbnails(max_width=300)

            # Create preview window
            preview_window = tk.Toplevel(self.root)
            preview_window.title("Monitor Preview")
            preview_window.geometry("700x600")

            tk.Label(
                preview_window,
                text="Monitor Previews - Click to refresh",
                font=("Arial", 14, "bold"),
                pady=10
            ).pack()

            # Create scrollable frame for thumbnails
            canvas = tk.Canvas(preview_window)
            scrollbar = ttk.Scrollbar(preview_window, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            # Display thumbnails
            for i, thumbnail in enumerate(thumbnails):
                monitor_frame = tk.LabelFrame(
                    scrollable_frame,
                    text=f"Monitor {i + 1}",
                    padx=10,
                    pady=10,
                    font=("Arial", 11, "bold")
                )
                monitor_frame.pack(fill=tk.X, padx=15, pady=8)

                # Convert PIL image to PhotoImage
                photo = ImageTk.PhotoImage(thumbnail)

                # Keep reference to prevent garbage collection
                label = tk.Label(monitor_frame, image=photo)
                label.image = photo
                label.pack()

                # Add monitor info
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

            # Refresh button
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

    def log(self, message):
        """Add message to log and write to file"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"

        # Log to GUI
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, full_message)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

        # Log to file
        try:
            with open("autoclicker_log.txt", "a", encoding="utf-8") as log_file:
                log_file.write(full_message)
        except Exception as e:
            print(f"Error writing to log file: {e}")

    def update_status(self, message):
        """Update status bar"""
        self.status_bar.config(text=message)


def main():
    """Main entry point"""
    root = tk.Tk()
    app = AutoClickerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
