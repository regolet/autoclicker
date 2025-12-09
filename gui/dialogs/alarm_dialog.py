"""
Alarm dialog for adding and editing alarms.
This is a placeholder that delegates to the main window's show_alarm_dialog method.
The full dialog logic remains in main_window.py for now to avoid breaking changes.
"""
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from gui.main_window import AutoClickerGUI


class AlarmDialog:
    """
    Wrapper class for alarm dialog functionality.
    
    The actual dialog implementation remains in AutoClickerGUI.show_alarm_dialog()
    to maintain the complex state management with the main window.
    """
    
    def __init__(
        self,
        main_window: 'AutoClickerGUI',
        mode: str = "add",
        alarm_index: Optional[int] = None
    ) -> None:
        """
        Initialize and show the alarm dialog.
        
        Args:
            main_window: Reference to the main AutoClickerGUI instance
            mode: 'add' for new alarm, 'edit' for existing
            alarm_index: Index of alarm to edit (required if mode='edit')
        """
        # Delegate to the main window's method which has full access to state
        main_window.show_alarm_dialog(mode=mode, alarm_index=alarm_index)
