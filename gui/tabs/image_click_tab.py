"""
Image Click tab for the Auto Clicker GUI.
Handles image template matching and clicking functionality.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
from typing import TYPE_CHECKING, Optional, List, Dict, Any

from gui.tabs.base_tab import BaseTab

if TYPE_CHECKING:
    from gui.main_window import AutoClickerGUI


class ImageClickTab(BaseTab):
    """Tab for finding and clicking on screen elements using template images."""
    
    def __init__(self, notebook: ttk.Notebook, main_window: 'AutoClickerGUI') -> None:
        """Initialize the image click tab."""
        super().__init__(notebook, main_window)
        
    def create(self) -> None:
        """Create the image template matching tab."""
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

        self.main_window.start_img_click_btn = tk.Button(
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
        self.main_window.start_img_click_btn.pack(side=tk.LEFT, padx=3)

        self.main_window.stop_img_click_btn = tk.Button(
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
        self.main_window.stop_img_click_btn.pack(side=tk.LEFT, padx=3)

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

        self.main_window.template_image_var = tk.StringVar()
        filename_entry = tk.Entry(
            file_frame,
            textvariable=self.main_window.template_image_var,
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

        self.main_window.confidence_var = tk.DoubleVar(value=0.8)
        confidence_scale = tk.Scale(
            conf_slider_frame,
            from_=0.5,
            to=1.0,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            variable=self.main_window.confidence_var,
            length=200
        )
        confidence_scale.pack(side=tk.LEFT, padx=10)

        self.confidence_label = tk.Label(
            conf_slider_frame,
            text="0.80",
            font=("Arial", 10, "bold")
        )
        self.confidence_label.pack(side=tk.LEFT)

        self.main_window.confidence_var.trace('w', lambda *args: self.confidence_label.config(
            text=f"{self.main_window.confidence_var.get():.2f}"
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
            monitors = self.main_window.analyzer.get_monitors()
            monitor_count = len(monitors)
        except:
            monitor_count = 1

        monitor_select_frame = tk.Frame(img_monitor_frame)
        monitor_select_frame.pack(fill=tk.X, pady=5)

        self.main_window.img_monitor_var = tk.IntVar(value=0)

        tk.Radiobutton(
            monitor_select_frame,
            text="All Monitors",
            variable=self.main_window.img_monitor_var,
            value=0,
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=5)

        for i in range(monitor_count):
            tk.Radiobutton(
                monitor_select_frame,
                text=f"Monitor {i + 1}",
                variable=self.main_window.img_monitor_var,
                value=i + 1,
                font=("Arial", 9)
            ).pack(side=tk.LEFT, padx=5)

        # Preview button
        if monitor_count > 1:
            preview_btn = tk.Button(
                monitor_select_frame,
                text="👁 Preview Monitors",
                command=self.main_window.show_monitor_preview,
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

        self.main_window.img_action_mode_var = tk.StringVar(value="click")

        # Create playback variables here so they exist before update_img_action_controls is called
        self.main_window.img_playback_file_var = tk.StringVar()
        self.main_window.img_playback_speed_var = tk.DoubleVar(value=1.0)

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
            variable=self.main_window.img_action_mode_var,
            value="click",
            font=("Arial", 9),
            command=self.update_img_action_controls
        ).pack(side=tk.LEFT, padx=5)

        tk.Radiobutton(
            mode_buttons_frame,
            text="Play Recording",
            variable=self.main_window.img_action_mode_var,
            value="playback",
            font=("Arial", 9),
            command=self.update_img_action_controls
        ).pack(side=tk.LEFT, padx=5)

        # Container for dynamic controls
        self.main_window.img_action_controls_frame = tk.Frame(action_mode_frame)
        self.main_window.img_action_controls_frame.pack(fill=tk.X, pady=10)

        # Repeat/Interval settings (for both modes)
        repeat_frame = tk.LabelFrame(content, text="Repeat Settings", padx=12, pady=12, font=("Segoe UI", 9))
        repeat_frame.pack(fill=tk.X, padx=15, pady=8)

        tk.Label(
            repeat_frame,
            text="Configure how many times to repeat and interval before each search:",
            font=("Arial", 9)
        ).pack(anchor=tk.W, pady=(0, 5))

        # Unlimited checkbox
        self.main_window.img_unlimited_var = tk.BooleanVar(value=False)
        unlimited_check = tk.Checkbutton(
            repeat_frame,
            text="♾️ Unlimited Repeats (runs until stopped or image not found)",
            variable=self.main_window.img_unlimited_var,
            font=("Arial", 9, "bold"),
            fg="#e74c3c",
            command=self.toggle_img_repeat_count
        )
        unlimited_check.pack(anchor=tk.W, pady=5)

        # Keep retrying checkbox
        self.main_window.img_retry_on_not_found_var = tk.BooleanVar(value=False)
        retry_check = tk.Checkbutton(
            repeat_frame,
            text="🔄 Keep Retrying if Image Not Found (doesn't stop, waits and retries)",
            variable=self.main_window.img_retry_on_not_found_var,
            font=("Arial", 9, "bold"),
            fg="#3498db"
        )
        retry_check.pack(anchor=tk.W, pady=5)

        repeat_controls = tk.Frame(repeat_frame)
        repeat_controls.pack(fill=tk.X, pady=5)

        # Repeat count
        tk.Label(repeat_controls, text="Repeat Count:", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.main_window.img_repeat_var = tk.IntVar(value=1)
        self.main_window.img_repeat_spinbox = tk.Spinbox(
            repeat_controls,
            from_=1,
            to=10000,
            textvariable=self.main_window.img_repeat_var,
            width=8,
            font=("Arial", 9)
        )
        self.main_window.img_repeat_spinbox.pack(side=tk.LEFT, padx=5)

        # Interval
        tk.Label(repeat_controls, text="Interval (seconds):", font=("Arial", 9)).pack(side=tk.LEFT, padx=(20, 5))
        self.main_window.img_interval_var = tk.DoubleVar(value=0.0)
        tk.Spinbox(
            repeat_controls,
            from_=0.0,
            to=300.0,
            increment=0.5,
            textvariable=self.main_window.img_interval_var,
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

    def browse_template_image(self) -> None:
        """Browse for template image."""
        filename = filedialog.askopenfilename(
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.main_window.template_image_var.set(filename)

    def update_img_action_controls(self) -> None:
        """Update the action controls based on selected mode."""
        # Clear existing controls
        for widget in self.main_window.img_action_controls_frame.winfo_children():
            widget.destroy()

        mode = self.main_window.img_action_mode_var.get()

        if mode == "playback":
            # Show recording file selection
            tk.Label(
                self.main_window.img_action_controls_frame,
                text="Select recording to play when image is found:",
                font=("Arial", 9)
            ).pack(anchor=tk.W, pady=(0, 5))

            file_frame = tk.Frame(self.main_window.img_action_controls_frame)
            file_frame.pack(fill=tk.X, pady=5)

            filename_entry = tk.Entry(
                file_frame,
                textvariable=self.main_window.img_playback_file_var,
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
            speed_frame = tk.Frame(self.main_window.img_action_controls_frame)
            speed_frame.pack(fill=tk.X, pady=5)

            tk.Label(speed_frame, text="Playback Speed:", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
            tk.Spinbox(
                speed_frame,
                from_=0.1,
                to=5.0,
                increment=0.1,
                textvariable=self.main_window.img_playback_speed_var,
                width=8,
                font=("Arial", 9)
            ).pack(side=tk.LEFT, padx=5)
            tk.Label(speed_frame, text="x", font=("Arial", 9)).pack(side=tk.LEFT)

    def browse_playback_file_for_image(self) -> None:
        """Browse for recording file to play when image is found."""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.main_window.img_playback_file_var.set(filename)

    def toggle_img_repeat_count(self) -> None:
        """Enable/disable repeat count spinbox based on unlimited checkbox."""
        if self.main_window.img_unlimited_var.get():
            self.main_window.img_repeat_spinbox.config(state='disabled')
        else:
            self.main_window.img_repeat_spinbox.config(state='normal')

    def start_image_click(self) -> None:
        """Start finding and clicking on template image."""
        image_path = self.main_window.template_image_var.get()
        if not image_path:
            messagebox.showwarning("Input Required", "Please select a template image")
            return

        # Disable start button, enable stop button
        self.main_window.start_img_click_btn.config(state=tk.DISABLED)
        self.main_window.stop_img_click_btn.config(state=tk.NORMAL)
        self.main_window.img_click_running = True

        confidence = self.main_window.confidence_var.get()

        # Get monitor selection
        monitor: Optional[int] = self.main_window.img_monitor_var.get()
        if monitor == 0:
            monitor = None  # None means all monitors

        # Get repeat/interval settings
        unlimited = self.main_window.img_unlimited_var.get()
        repeat_count = self.main_window.img_repeat_var.get()
        interval = self.main_window.img_interval_var.get()
        retry_on_not_found = self.main_window.img_retry_on_not_found_var.get()

        # Get action mode
        action_mode = self.main_window.img_action_mode_var.get()
        playback_events: Optional[List[Dict[str, Any]]] = None
        playback_speed = 1.0

        if action_mode == "playback":
            # Load recording file
            playback_file = self.main_window.img_playback_file_var.get()
            if not playback_file:
                messagebox.showwarning("Input Required", "Please select a recording file for playback mode")
                self.main_window.start_img_click_btn.config(state=tk.NORMAL)
                self.main_window.stop_img_click_btn.config(state=tk.DISABLED)
                self.main_window.img_click_running = False
                return

            try:
                with open(playback_file, 'r') as f:
                    data = json.load(f)
                    playback_events = data['events']
                    playback_speed = self.main_window.img_playback_speed_var.get()
                    self.log(f"Loaded {len(playback_events)} events from {playback_file}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load recording: {e}")
                self.main_window.start_img_click_btn.config(state=tk.NORMAL)
                self.main_window.stop_img_click_btn.config(state=tk.DISABLED)
                self.main_window.img_click_running = False
                return

        def image_click_thread() -> None:
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

                success = self.main_window.clicker.click_on_image(
                    image_path,
                    confidence=confidence,
                    monitor=monitor,
                    repeat_count=repeat_count,
                    interval=interval,
                    playback_events=playback_events,
                    playback_speed=playback_speed,
                    unlimited=unlimited,
                    retry_on_not_found=retry_on_not_found,
                    stop_flag=lambda: not self.main_window.img_click_running,
                    log_callback=self.log
                )

                # Check if stopped by user before showing results
                if not self.main_window.img_click_running:
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
                self.main_window.img_click_running = False
                self.main_window.start_img_click_btn.config(state=tk.NORMAL)
                self.main_window.stop_img_click_btn.config(state=tk.DISABLED)

        threading.Thread(target=image_click_thread, daemon=True).start()

    def stop_image_click(self) -> None:
        """Stop the image click process."""
        self.main_window.img_click_running = False
        self.log("Stopping image click...")
        self.update_status("Image click stopped by user")

        # Re-enable buttons
        self.main_window.start_img_click_btn.config(state=tk.NORMAL)
        self.main_window.stop_img_click_btn.config(state=tk.DISABLED)
