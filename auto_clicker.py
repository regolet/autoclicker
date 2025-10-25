"""
Auto clicker playback functionality
Plays back recorded mouse movements and clicks, with AI-based target detection
"""
import time
import pyautogui
from pynput.mouse import Button, Controller
from screenshot_analyzer import ScreenshotAnalyzer


class AutoClicker:
    def __init__(self, api_key=None):
        """
        Initialize the auto clicker

        Args:
            api_key: OpenAI API key for AI-based analysis
        """
        self.mouse = Controller()
        self.analyzer = ScreenshotAnalyzer(api_key)
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        pyautogui.PAUSE = 0.1  # Short pause between actions

    def play_recording(self, events, speed=1.0):
        """
        Play back recorded mouse events

        Args:
            events: List of recorded events
            speed: Playback speed multiplier (1.0 = normal, 2.0 = double speed, etc.)
        """
        print(f"Starting playback of {len(events)} events...")
        print("Move mouse to top-left corner to abort (FAILSAFE)")

        time.sleep(2)  # Give user time to prepare

        last_timestamp = 0

        for i, event in enumerate(events):
            # Calculate delay
            if event['timestamp'] > last_timestamp:
                delay = (event['timestamp'] - last_timestamp) / speed
                time.sleep(delay)

            # Execute event
            if event['type'] == 'move':
                pyautogui.moveTo(event['x'], event['y'])

            elif event['type'] == 'click':
                button = Button.left if event['button'] == 'left' else Button.right
                self.mouse.position = (event['x'], event['y'])
                self.mouse.click(button, 1)
                print(f"Clicked at ({event['x']}, {event['y']})")

            elif event['type'] == 'scroll':
                self.mouse.position = (event['x'], event['y'])
                self.mouse.scroll(event['dx'], event['dy'])

            last_timestamp = event['timestamp']

            # Progress update
            if (i + 1) % 100 == 0:
                print(f"Progress: {i + 1}/{len(events)} events")

        print("Playback completed!")

    def click_at_position(self, x, y, button='left', clicks=1):
        """
        Click at specific coordinates

        Args:
            x, y: Coordinates to click
            button: 'left' or 'right'
            clicks: Number of clicks
        """
        pyautogui.click(x, y, clicks=clicks, button=button)
        print(f"Clicked at ({x}, {y})")

    def click_on_ai_target(self, target_description, region=None, monitor=None, repeat_count=1, interval=0):
        """
        Use AI to find and click on a target

        Args:
            target_description: What to look for (e.g., "the submit button")
            region: Optional screen region to search in (x, y, width, height)
            monitor: Monitor number (1, 2, etc.) or None for all monitors
            repeat_count: Number of times to repeat the click (default: 1)
            interval: Seconds between repeated clicks (default: 0)

        Returns:
            True if found and clicked, False otherwise
        """
        print(f"Analyzing screen for: {target_description}")

        # Capture screenshot with monitor support
        screenshot = self.analyzer.capture_screenshot(region=region, monitor=monitor)

        # Analyze with AI
        result = self.analyzer.analyze_screenshot_with_ai(screenshot, target_description)

        if result.get('found'):
            x, y = result['x'], result['y']
            confidence = result.get('confidence', 0)

            print(f"Target found at ({x}, {y}) with confidence {confidence:.2f}")
            print(f"Description: {result.get('description', 'N/A')}")

            # Highlight the target (optional, for debugging)
            self.analyzer.highlight_target(screenshot, x, y, 'target_found.png')

            # Adjust coordinates if region was specified
            if region:
                x += region[0]
                y += region[1]

            # Adjust coordinates if monitor was specified
            if monitor is not None:
                monitors = self.analyzer.get_monitors()
                if monitor > 0 and monitor <= len(monitors):
                    mon = monitors[monitor - 1]
                    x += mon['left']
                    y += mon['top']

            # Click on the target (with repeat if specified)
            time.sleep(0.5)
            for i in range(repeat_count):
                self.click_at_position(x, y)
                if i < repeat_count - 1 and interval > 0:
                    print(f"Waiting {interval} seconds before next click...")
                    time.sleep(interval)

            if repeat_count > 1:
                print(f"Completed {repeat_count} clicks")

            return True
        else:
            print(f"Target not found: {result.get('error', 'Unknown error')}")
            return False

    def click_on_image(self, template_image_path, confidence=0.8, monitor=None):
        """
        Find and click on a template image using OpenCV matching

        Args:
            template_image_path: Path to the image to find
            confidence: Confidence threshold (0-1)
            monitor: Monitor number (1, 2, etc.) or None for all monitors

        Returns:
            True if found and clicked, False otherwise
        """
        print(f"Searching for image: {template_image_path}")

        result = self.analyzer.find_image_on_screen(template_image_path, confidence, monitor=monitor)

        if result:
            x, y, match_confidence = result
            print(f"Image found at ({x}, {y}) with confidence {match_confidence:.2f}")

            # Adjust coordinates if monitor was specified
            if monitor is not None:
                monitors = self.analyzer.get_monitors()
                if monitor > 0 and monitor <= len(monitors):
                    mon = monitors[monitor - 1]
                    x += mon['left']
                    y += mon['top']

            # Click on the found image
            time.sleep(0.5)
            self.click_at_position(x, y)
            return True
        else:
            print(f"Image not found with confidence >= {confidence}")
            return False

    def repeat_clicks(self, x, y, count, interval=1.0, button='left'):
        """
        Repeat clicks at a specific position

        Args:
            x, y: Coordinates to click
            count: Number of times to click
            interval: Seconds between clicks
            button: 'left' or 'right'
        """
        print(f"Repeating {count} clicks at ({x}, {y}) with {interval}s interval")

        for i in range(count):
            self.click_at_position(x, y, button)
            if i < count - 1:  # Don't wait after last click
                time.sleep(interval)

        print("Repeat clicking completed!")
