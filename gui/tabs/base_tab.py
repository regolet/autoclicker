"""
Base tab class with shared functionality for all GUI tabs.
"""
import tkinter as tk
from tkinter import ttk
from typing import Tuple, Callable, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from gui.main_window import AutoClickerGUI


class BaseTab:
    """Base class for all tab components with shared utilities."""
    
    def __init__(self, notebook: ttk.Notebook, main_window: 'AutoClickerGUI') -> None:
        """
        Initialize the base tab.
        
        Args:
            notebook: The ttk.Notebook widget to add the tab to
            main_window: Reference to the main AutoClickerGUI instance
        """
        self.notebook = notebook
        self.main_window = main_window
        self.root = main_window.root
        
    def log(self, message: str) -> None:
        """Log a message through the main window."""
        self.main_window.log(message)
        
    def update_status(self, message: str) -> None:
        """Update status bar through the main window."""
        self.main_window.update_status(message)

    def create_scrollable_tab(self, tab_name: str) -> Tuple[ttk.Frame, ttk.Frame]:
        """
        Create a scrollable tab frame.

        Args:
            tab_name: Name to display on the tab
            
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
        def _on_mousewheel(event: Any) -> None:
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        # Bind to enter/leave events to enable scrolling when mouse is over the tab
        def _bind_to_mousewheel(event: Any) -> None:
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_from_mousewheel(event: Any) -> None:
            canvas.unbind_all("<MouseWheel>")

        # Bind when mouse enters the canvas area
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)
        scrollable_frame.bind('<Enter>', _bind_to_mousewheel)
        scrollable_frame.bind('<Leave>', _unbind_from_mousewheel)

        # Make scrollable frame expand to fill canvas width
        def _configure_canvas(event: Any) -> None:
            # Get the canvas width (subtract scrollbar if visible)
            canvas_width = event.width
            # Set the embedded window to fill the canvas width
            canvas.itemconfig(window_id, width=canvas_width)
            # Also update the scroll region
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", _configure_canvas)

        return tab, scrollable_frame

    def create(self) -> None:
        """Create the tab. Must be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement create()")
