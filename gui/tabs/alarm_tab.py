"""
Alarm tab for the Auto Clicker GUI.
Handles scheduled alarm functionality.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING

from gui.tabs.base_tab import BaseTab

if TYPE_CHECKING:
    from gui.main_window import AutoClickerGUI


class AlarmTab(BaseTab):
    """Tab for managing scheduled alarms."""
    
    def __init__(self, notebook: ttk.Notebook, main_window: 'AutoClickerGUI') -> None:
        """Initialize the alarm tab."""
        super().__init__(notebook, main_window)
        
    def create(self) -> None:
        """Create the alarm clock tab with support for multiple alarms."""
        tab, content = self.create_scrollable_tab("⏰ Alarm")

        # Instructions
        instructions = tk.Label(
            content,
            text="Schedule automated tasks at specific times",
            font=("Segoe UI", 9),
            pady=5
        )
        instructions.pack()

        # Monitoring status (moved to top)
        status_frame = tk.LabelFrame(content, text="Monitor Status", padx=8, pady=6, font=("Segoe UI", 9))
        status_frame.pack(fill=tk.X, padx=12, pady=5)

        self.main_window.alarm_monitor_status_label = tk.Label(
            status_frame,
            text="⚫ Monitoring: OFF",
            font=("Segoe UI", 10, "bold"),
            fg="gray"
        )
        self.main_window.alarm_monitor_status_label.pack(pady=4)

        # Monitor control buttons
        monitor_btn_frame = tk.Frame(status_frame)
        monitor_btn_frame.pack(pady=4)

        self.main_window.start_monitor_btn = tk.Button(
            monitor_btn_frame,
            text="▶ Start Monitoring",
            command=self.main_window.start_alarm_monitor,
            bg="#27ae60",
            fg="white",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2"
        )
        self.main_window.start_monitor_btn.pack(side=tk.LEFT, padx=3)

        self.main_window.stop_monitor_btn = tk.Button(
            monitor_btn_frame,
            text="⏹ Stop Monitoring",
            command=self.main_window.stop_alarm_monitor,
            bg="#e74c3c",
            fg="white",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=12,
            pady=6,
            state=tk.DISABLED,
            cursor="hand2"
        )
        self.main_window.stop_monitor_btn.pack(side=tk.LEFT, padx=3)

        # Alarm list section
        list_frame = tk.LabelFrame(content, text="Alarms", padx=8, pady=6, font=("Segoe UI", 9))
        list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=5)

        # Alarm listbox with scrollbar
        listbox_frame = tk.Frame(list_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        alarm_scrollbar = tk.Scrollbar(listbox_frame)
        alarm_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.main_window.alarm_listbox = tk.Listbox(
            listbox_frame,
            yscrollcommand=alarm_scrollbar.set,
            font=("Segoe UI", 9),
            height=6,
            selectmode=tk.SINGLE
        )
        self.main_window.alarm_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        alarm_scrollbar.config(command=self.main_window.alarm_listbox.yview)

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

    def show_add_alarm_dialog(self) -> None:
        """Show dialog to add a new alarm."""
        self.main_window.show_alarm_dialog(mode="add")

    def edit_selected_alarm(self) -> None:
        """Edit the selected alarm."""
        selection = self.main_window.alarm_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an alarm to edit")
            return

        index = selection[0]
        self.main_window.show_alarm_dialog(mode="edit", alarm_index=index)

    def delete_selected_alarm(self) -> None:
        """Delete the selected alarm."""
        selection = self.main_window.alarm_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an alarm to delete")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this alarm?"):
            index = selection[0]
            del self.main_window.alarms[index]
            self.main_window.refresh_alarm_list()
            self.log("Alarm deleted")
            self.main_window.save_alarms()

    def toggle_selected_alarm(self) -> None:
        """Toggle the selected alarm on/off."""
        selection = self.main_window.alarm_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an alarm to toggle")
            return

        index = selection[0]
        self.main_window.alarms[index]['enabled'] = not self.main_window.alarms[index]['enabled']
        self.main_window.refresh_alarm_list()
        status = "enabled" if self.main_window.alarms[index]['enabled'] else "disabled"
        self.log(f"Alarm {status}")
        self.main_window.save_alarms()
