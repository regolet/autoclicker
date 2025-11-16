"""
Screenshot capture and image template matching
Uses OpenCV for template matching to find and click on screen elements
"""
import pyautogui
import cv2
import numpy as np
from PIL import Image
from mss import mss


class ScreenshotAnalyzer:
    def __init__(self, api_key=None):
        """
        Initialize the screenshot analyzer
        """
        pass

    def get_monitors(self):
        """
        Get list of all monitors

        Returns:
            List of monitor dictionaries with 'left', 'top', 'width', 'height'
        """
        with mss() as sct:
            monitors = sct.monitors[1:]  # Skip the first one (combined screen)
            return monitors

    def capture_screenshot(self, region=None, monitor=None):
        """
        Capture a screenshot

        Args:
            region: Tuple (x, y, width, height) for specific region, or None for full screen
            monitor: Monitor number (1, 2, etc.) or None for all monitors

        Returns:
            PIL Image object
        """
        if monitor is not None:
            # Capture specific monitor
            with mss() as sct:
                monitors = sct.monitors
                if monitor < len(monitors):
                    mon = monitors[monitor]
                    screenshot = sct.grab(mon)
                    return Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                else:
                    print(f"Warning: Monitor {monitor} not found, using default")

        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()
        return screenshot

    def save_screenshot(self, screenshot, filename):
        """Save screenshot to file"""
        screenshot.save(filename)
        print(f"Screenshot saved to {filename}")

    def find_image_on_screen(self, template_image_path, confidence=0.8, monitor=None):
        """
        Find a template image on the current screen using OpenCV

        Args:
            template_image_path: Path to the template image to search for
            confidence: Confidence threshold (0-1)
            monitor: Monitor number (1, 2, etc.) or None for all monitors

        Returns:
            Tuple (x, y, confidence) of the center of the found image, or None
        """
        # Load template
        template = cv2.imread(template_image_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            raise ValueError(f"Could not load template image: {template_image_path}")

        if monitor is None:
            # Search all monitors individually and return the best match
            best_match = None
            best_confidence = 0

            with mss() as sct:
                monitors = sct.monitors[1:]  # Skip combined screen

                for idx, mon in enumerate(monitors, 1):
                    # Capture this monitor
                    screenshot = sct.grab(mon)
                    screenshot_img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                    screenshot_np = np.array(screenshot_img)
                    screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)

                    # Perform template matching
                    result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                    if max_val >= confidence and max_val > best_confidence:
                        # Get center of the found template
                        template_h, template_w = template.shape
                        # Add monitor offset to get absolute coordinates
                        center_x = mon['left'] + max_loc[0] + template_w // 2
                        center_y = mon['top'] + max_loc[1] + template_h // 2
                        best_match = (center_x, center_y, max_val)
                        best_confidence = max_val

            return best_match
        else:
            # Search specific monitor using pyautogui approach (works with relative coordinates)
            screenshot = self.capture_screenshot(monitor=monitor)
            screenshot_np = np.array(screenshot)
            screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)

            # Perform template matching
            result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= confidence:
                # Get center of the found template
                template_h, template_w = template.shape
                center_x = max_loc[0] + template_w // 2
                center_y = max_loc[1] + template_h // 2
                return (center_x, center_y, max_val)
            else:
                return None

    def get_monitor_thumbnails(self, max_width=200):
        """
        Capture thumbnails of all monitors

        Args:
            max_width: Maximum width for thumbnail (height scaled proportionally)

        Returns:
            List of PIL Image thumbnails
        """
        thumbnails = []
        monitors = self.get_monitors()

        for i, mon in enumerate(monitors):
            # Capture the monitor
            screenshot = self.capture_screenshot(monitor=i+1)

            # Calculate thumbnail size maintaining aspect ratio
            width, height = screenshot.size
            scale = max_width / width
            new_height = int(height * scale)

            # Resize to thumbnail
            thumbnail = screenshot.resize((max_width, new_height), Image.Resampling.LANCZOS)
            thumbnails.append(thumbnail)

        return thumbnails
