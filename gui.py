"""
GUI Application for AI-Powered Auto Clicker
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import json
from datetime import datetime
from mouse_recorder import MouseRecorder
from auto_clicker import AutoClicker
from screenshot_analyzer import ScreenshotAnalyzer
from dotenv import load_dotenv


class AutoClickerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI-Powered Auto Clicker")
        self.root.geometry("800x700")
        self.root.resizable(True, True)

        # Load environment variables
        load_dotenv()
        self.api_key = os.getenv('OPENAI_API_KEY')

        # Initialize components
        self.recorder = MouseRecorder()
        self.clicker = AutoClicker(api_key=self.api_key)
        self.analyzer = ScreenshotAnalyzer(api_key=self.api_key)

        # State variables
        self.is_recording = False
        self.current_recording_file = None
        self.loaded_events = []

        # Setup GUI
        self.setup_gui()

    def setup_gui(self):
        """Setup the GUI layout"""
        # Title
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        title_frame.pack(fill=tk.X, side=tk.TOP)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="🤖 AI-Powered Auto Clicker",
            font=("Arial", 18, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=15)

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self.create_recorder_tab()
        self.create_playback_tab()
        self.create_ai_click_tab()
        self.create_image_click_tab()
        self.create_screenshot_tab()

        # Status bar
        self.status_bar = tk.Label(
            self.root,
            text="Ready",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#ecf0f1"
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Log area
        log_frame = tk.LabelFrame(self.root, text="Activity Log", padx=5, pady=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            state=tk.DISABLED,
            bg="#f8f9fa",
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def create_recorder_tab(self):
        """Create the mouse recorder tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📹 Record")

        # Instructions
        instructions = tk.Label(
            tab,
            text="Record your mouse movements, clicks, and scrolls",
            font=("Arial", 11),
            pady=10
        )
        instructions.pack()

        # Recording controls frame
        controls_frame = tk.LabelFrame(tab, text="Recording Controls", padx=20, pady=20)
        controls_frame.pack(fill=tk.X, padx=20, pady=10)

        # Status indicator
        self.record_status_label = tk.Label(
            controls_frame,
            text="⚫ Not Recording",
            font=("Arial", 12, "bold"),
            fg="gray"
        )
        self.record_status_label.pack(pady=10)

        # Buttons frame
        buttons_frame = tk.Frame(controls_frame)
        buttons_frame.pack(pady=10)

        self.start_record_btn = tk.Button(
            buttons_frame,
            text="▶ Start Recording",
            command=self.start_recording,
            bg="#27ae60",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.start_record_btn.pack(side=tk.LEFT, padx=5)

        self.stop_record_btn = tk.Button(
            buttons_frame,
            text="⏹ Stop Recording",
            command=self.stop_recording,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=10,
            state=tk.DISABLED,
            cursor="hand2"
        )
        self.stop_record_btn.pack(side=tk.LEFT, padx=5)

        # Event counter
        self.event_count_label = tk.Label(
            controls_frame,
            text="Events recorded: 0",
            font=("Arial", 10)
        )
        self.event_count_label.pack(pady=10)

        # Save options
        save_frame = tk.LabelFrame(tab, text="Save Recording", padx=20, pady=20)
        save_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(save_frame, text="Filename:", font=("Arial", 10)).pack(anchor=tk.W)

        filename_frame = tk.Frame(save_frame)
        filename_frame.pack(fill=tk.X, pady=5)

        self.record_filename_var = tk.StringVar(value="recording.json")
        filename_entry = tk.Entry(
            filename_frame,
            textvariable=self.record_filename_var,
            font=("Arial", 10)
        )
        filename_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_btn = tk.Button(
            filename_frame,
            text="Browse...",
            command=self.browse_save_location,
            cursor="hand2"
        )
        browse_btn.pack(side=tk.LEFT)

        save_btn = tk.Button(
            save_frame,
            text="💾 Save Recording",
            command=self.save_recording,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=8,
            cursor="hand2"
        )
        save_btn.pack(pady=10)

    def create_playback_tab(self):
        """Create the playback tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="▶ Playback")

        # Instructions
        instructions = tk.Label(
            tab,
            text="Load and replay recorded mouse actions",
            font=("Arial", 11),
            pady=10
        )
        instructions.pack()

        # Load recording frame
        load_frame = tk.LabelFrame(tab, text="Load Recording", padx=20, pady=20)
        load_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(load_frame, text="Recording file:", font=("Arial", 10)).pack(anchor=tk.W)

        file_frame = tk.Frame(load_frame)
        file_frame.pack(fill=tk.X, pady=5)

        self.playback_filename_var = tk.StringVar()
        filename_entry = tk.Entry(
            file_frame,
            textvariable=self.playback_filename_var,
            font=("Arial", 10),
            state='readonly'
        )
        filename_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_btn = tk.Button(
            file_frame,
            text="Browse...",
            command=self.browse_load_file,
            cursor="hand2"
        )
        browse_btn.pack(side=tk.LEFT)

        load_btn = tk.Button(
            load_frame,
            text="📂 Load Recording",
            command=self.load_recording,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=8,
            cursor="hand2"
        )
        load_btn.pack(pady=10)

        self.loaded_info_label = tk.Label(
            load_frame,
            text="No recording loaded",
            font=("Arial", 9),
            fg="gray"
        )
        self.loaded_info_label.pack()

        # Playback controls
        playback_frame = tk.LabelFrame(tab, text="Playback Controls", padx=20, pady=20)
        playback_frame.pack(fill=tk.X, padx=20, pady=10)

        # Speed control
        speed_frame = tk.Frame(playback_frame)
        speed_frame.pack(fill=tk.X, pady=10)

        tk.Label(speed_frame, text="Playback Speed:", font=("Arial", 10)).pack(side=tk.LEFT)

        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = tk.Scale(
            speed_frame,
            from_=0.1,
            to=5.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.speed_var,
            length=200
        )
        speed_scale.pack(side=tk.LEFT, padx=10)

        self.speed_label = tk.Label(speed_frame, text="1.0x", font=("Arial", 10, "bold"))
        self.speed_label.pack(side=tk.LEFT)

        self.speed_var.trace('w', lambda *args: self.speed_label.config(text=f"{self.speed_var.get():.1f}x"))

        # Play button
        play_btn = tk.Button(
            playback_frame,
            text="▶ Play Recording",
            command=self.play_recording,
            bg="#27ae60",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=30,
            pady=15,
            cursor="hand2"
        )
        play_btn.pack(pady=20)

        # Warning
        warning_label = tk.Label(
            playback_frame,
            text="⚠ Move mouse to top-left corner to abort playback",
            font=("Arial", 9),
            fg="#e74c3c"
        )
        warning_label.pack()

    def create_ai_click_tab(self):
        """Create the AI click tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🤖 AI Click")

        # Instructions
        instructions = tk.Label(
            tab,
            text="Use AI to analyze screenshots and click on described elements",
            font=("Arial", 11),
            pady=10
        )
        instructions.pack()

        # API Key status
        api_status_frame = tk.Frame(tab, bg="#ecf0f1")
        api_status_frame.pack(fill=tk.X, padx=20, pady=5)

        if self.api_key:
            status_text = "✅ OpenAI API Key: Configured"
            status_color = "#27ae60"
        else:
            status_text = "❌ OpenAI API Key: Not configured (check .env file)"
            status_color = "#e74c3c"

        tk.Label(
            api_status_frame,
            text=status_text,
            font=("Arial", 9),
            fg=status_color,
            bg="#ecf0f1"
        ).pack(pady=5)

        # Target description
        target_frame = tk.LabelFrame(tab, text="Target Description", padx=20, pady=20)
        target_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(
            target_frame,
            text="Describe what to click (e.g., 'the blue submit button', 'the search icon'):",
            font=("Arial", 10)
        ).pack(anchor=tk.W, pady=(0, 5))

        self.ai_target_var = tk.StringVar()
        target_entry = tk.Entry(
            target_frame,
            textvariable=self.ai_target_var,
            font=("Arial", 11)
        )
        target_entry.pack(fill=tk.X, pady=5)

        # Region selection (optional)
        region_frame = tk.LabelFrame(tab, text="Search Region (Optional)", padx=20, pady=20)
        region_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(
            region_frame,
            text="Leave empty to search entire screen, or specify region:",
            font=("Arial", 9)
        ).pack(anchor=tk.W)

        region_inputs = tk.Frame(region_frame)
        region_inputs.pack(fill=tk.X, pady=5)

        self.region_x_var = tk.StringVar()
        self.region_y_var = tk.StringVar()
        self.region_w_var = tk.StringVar()
        self.region_h_var = tk.StringVar()

        for label, var in [("X:", self.region_x_var), ("Y:", self.region_y_var),
                           ("Width:", self.region_w_var), ("Height:", self.region_h_var)]:
            frame = tk.Frame(region_inputs)
            frame.pack(side=tk.LEFT, padx=5)
            tk.Label(frame, text=label, font=("Arial", 9)).pack(side=tk.LEFT)
            tk.Entry(frame, textvariable=var, width=8, font=("Arial", 9)).pack(side=tk.LEFT)

        # Monitor selection
        monitor_frame = tk.LabelFrame(tab, text="Monitor Selection", padx=20, pady=20)
        monitor_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(
            monitor_frame,
            text="Select which monitor to capture (useful for dual/multi-monitor setups):",
            font=("Arial", 9)
        ).pack(anchor=tk.W, pady=(0, 5))

        # Get available monitors
        try:
            monitors = self.analyzer.get_monitors()
            monitor_count = len(monitors)
        except:
            monitor_count = 1

        monitor_select_frame = tk.Frame(monitor_frame)
        monitor_select_frame.pack(fill=tk.X, pady=5)

        self.monitor_var = tk.IntVar(value=0)

        tk.Radiobutton(
            monitor_select_frame,
            text="All Monitors (Default)",
            variable=self.monitor_var,
            value=0,
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=5)

        for i in range(monitor_count):
            tk.Radiobutton(
                monitor_select_frame,
                text=f"Monitor {i + 1}",
                variable=self.monitor_var,
                value=i + 1,
                font=("Arial", 9)
            ).pack(side=tk.LEFT, padx=5)

        # Repeat/Interval settings
        repeat_frame = tk.LabelFrame(tab, text="Repeat Settings", padx=20, pady=20)
        repeat_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(
            repeat_frame,
            text="Configure how many times to click and the interval between clicks:",
            font=("Arial", 9)
        ).pack(anchor=tk.W, pady=(0, 5))

        repeat_controls = tk.Frame(repeat_frame)
        repeat_controls.pack(fill=tk.X, pady=5)

        # Repeat count
        tk.Label(repeat_controls, text="Repeat Count:", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.ai_repeat_var = tk.IntVar(value=1)
        tk.Spinbox(
            repeat_controls,
            from_=1,
            to=1000,
            textvariable=self.ai_repeat_var,
            width=8,
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=5)

        # Interval
        tk.Label(repeat_controls, text="Interval (seconds):", font=("Arial", 9)).pack(side=tk.LEFT, padx=(20, 5))
        self.ai_interval_var = tk.DoubleVar(value=0.0)
        tk.Spinbox(
            repeat_controls,
            from_=0.0,
            to=60.0,
            increment=0.5,
            textvariable=self.ai_interval_var,
            width=8,
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=5)

        tk.Label(
            repeat_frame,
            text="Example: Repeat=5, Interval=2.0 will click 5 times with 2 seconds between each click",
            font=("Arial", 8),
            fg="gray"
        ).pack(anchor=tk.W, pady=5)

        # Action button
        action_frame = tk.Frame(tab)
        action_frame.pack(pady=20)

        ai_click_btn = tk.Button(
            action_frame,
            text="🎯 Analyze & Click",
            command=self.ai_click,
            bg="#9b59b6",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=30,
            pady=15,
            cursor="hand2"
        )
        ai_click_btn.pack()

    def create_image_click_tab(self):
        """Create the image template matching tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🖼 Image Click")

        # Instructions
        instructions = tk.Label(
            tab,
            text="Find and click on screen elements using template images",
            font=("Arial", 11),
            pady=10
        )
        instructions.pack()

        # Image selection
        image_frame = tk.LabelFrame(tab, text="Template Image", padx=20, pady=20)
        image_frame.pack(fill=tk.X, padx=20, pady=10)

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

        # Confidence threshold
        confidence_frame = tk.LabelFrame(tab, text="Matching Settings", padx=20, pady=20)
        confidence_frame.pack(fill=tk.X, padx=20, pady=10)

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

        # Action button
        action_frame = tk.Frame(tab)
        action_frame.pack(pady=20)

        image_click_btn = tk.Button(
            action_frame,
            text="🔍 Find & Click",
            command=self.image_click,
            bg="#e67e22",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=30,
            pady=15,
            cursor="hand2"
        )
        image_click_btn.pack()

    def create_screenshot_tab(self):
        """Create the screenshot tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📸 Screenshot")

        # Instructions
        instructions = tk.Label(
            tab,
            text="Capture screenshots of your screen",
            font=("Arial", 11),
            pady=10
        )
        instructions.pack()

        # Screenshot options
        options_frame = tk.LabelFrame(tab, text="Screenshot Options", padx=20, pady=20)
        options_frame.pack(fill=tk.X, padx=20, pady=10)

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
        save_frame = tk.LabelFrame(tab, text="Save Location", padx=20, pady=20)
        save_frame.pack(fill=tk.X, padx=20, pady=10)

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
        action_frame = tk.Frame(tab)
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
            self.recorder.save_recording(filename)
            self.log(f"Recording saved to {filename}")
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

    # AI Click methods
    def ai_click(self):
        """Use AI to find and click on target"""
        if not self.api_key:
            messagebox.showerror(
                "API Key Missing",
                "OpenAI API key not configured. Please add it to your .env file."
            )
            return

        target = self.ai_target_var.get().strip()
        if not target:
            messagebox.showwarning("Input Required", "Please describe what to click")
            return

        # Parse region if specified
        region = None
        try:
            if all([self.region_x_var.get(), self.region_y_var.get(),
                   self.region_w_var.get(), self.region_h_var.get()]):
                region = (
                    int(self.region_x_var.get()),
                    int(self.region_y_var.get()),
                    int(self.region_w_var.get()),
                    int(self.region_h_var.get())
                )
        except ValueError:
            messagebox.showerror("Invalid Input", "Region values must be integers")
            return

        # Get monitor selection
        monitor = self.monitor_var.get()
        if monitor == 0:
            monitor = None  # None means all monitors

        # Get repeat/interval settings
        repeat_count = self.ai_repeat_var.get()
        interval = self.ai_interval_var.get()

        def ai_click_thread():
            try:
                self.log(f"Analyzing screen for: {target}")
                if monitor:
                    self.log(f"Using Monitor {monitor}")
                if repeat_count > 1:
                    self.log(f"Will click {repeat_count} times with {interval}s interval")
                self.update_status("Analyzing screenshot with AI...")

                success = self.clicker.click_on_ai_target(
                    target,
                    region=region,
                    monitor=monitor,
                    repeat_count=repeat_count,
                    interval=interval
                )

                if success:
                    self.log("Target found and clicked!")
                    self.update_status("AI click successful")
                    messagebox.showinfo("Success", "Target found and clicked!")
                else:
                    self.log("Target not found")
                    self.update_status("Target not found")
                    messagebox.showwarning("Not Found", "Could not find the target")
            except Exception as e:
                self.log(f"Error during AI click: {e}")
                messagebox.showerror("Error", f"AI click failed: {e}")

        threading.Thread(target=ai_click_thread, daemon=True).start()

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

    def image_click(self):
        """Find and click on template image"""
        image_path = self.template_image_var.get()
        if not image_path:
            messagebox.showwarning("Input Required", "Please select a template image")
            return

        confidence = self.confidence_var.get()

        def image_click_thread():
            try:
                self.log(f"Searching for image: {image_path}")
                self.update_status("Searching for template image...")

                success = self.clicker.click_on_image(image_path, confidence=confidence)

                if success:
                    self.log("Image found and clicked!")
                    self.update_status("Image click successful")
                    messagebox.showinfo("Success", "Image found and clicked!")
                else:
                    self.log("Image not found")
                    self.update_status("Image not found")
                    messagebox.showwarning("Not Found", "Could not find the image on screen")
            except Exception as e:
                self.log(f"Error during image click: {e}")
                messagebox.showerror("Error", f"Image click failed: {e}")

        threading.Thread(target=image_click_thread, daemon=True).start()

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

    # Utility methods
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

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
