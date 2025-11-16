"""
Auto clicker playback functionality
Plays back recorded mouse movements and clicks, with AI-based target detection
"""
import time
import pyautogui
from pynput.mouse import Button, Controller
from screenshot_analyzer import ScreenshotAnalyzer


class AutoClicker:
    def __init__(self):
        """
        Initialize the auto clicker
        """
        self.mouse = Controller()
        self.analyzer = ScreenshotAnalyzer()
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        pyautogui.PAUSE = 0.1  # Short pause between actions

    def play_recording(self, events, speed=1.0, skip_moves=False, skip_delay=False, instant=False):
        """
        Play back recorded mouse events

        Args:
            events: List of recorded events
            speed: Playback speed multiplier (1.0 = normal, 2.0 = double speed, etc.)
            skip_moves: If True, skip move events and only execute clicks/scrolls (default: False)
            skip_delay: If True, skip the 2-second preparation delay (default: False)
            instant: If True, execute all events instantly without timing delays (default: False)
        """
        print(f"Starting playback of {len(events)} events (skip_moves={skip_moves}, instant={instant})...")
        if not skip_delay:
            print("Move mouse to top-left corner to abort (FAILSAFE)")
            time.sleep(2)  # Give user time to prepare

        # Disable pyautogui pause to avoid extra delays
        original_pause = pyautogui.PAUSE
        pyautogui.PAUSE = 0

        last_timestamp = 0
        events_executed = 0

        for i, event in enumerate(events):
            # Skip move events if requested
            if skip_moves and event['type'] == 'move':
                continue

            # Calculate delay (only if not in instant mode)
            if not instant and event['timestamp'] > last_timestamp:
                delay = (event['timestamp'] - last_timestamp) / speed
                time.sleep(delay)

            # Execute event
            if event['type'] == 'move':
                # Use duration=0 for instant movement (no animation)
                pyautogui.moveTo(event['x'], event['y'], duration=0)
                events_executed += 1

            elif event['type'] == 'click':
                button = Button.left if event['button'] == 'left' else Button.right
                self.mouse.position = (event['x'], event['y'])
                self.mouse.click(button, 1)
                print(f"Clicked at ({event['x']}, {event['y']})")
                events_executed += 1

            elif event['type'] == 'scroll':
                self.mouse.position = (event['x'], event['y'])
                self.mouse.scroll(event['dx'], event['dy'])
                events_executed += 1

            last_timestamp = event['timestamp']

            # Progress update
            if events_executed > 0 and events_executed % 100 == 0:
                print(f"Progress: {events_executed} events executed")

        # Restore original pause setting
        pyautogui.PAUSE = original_pause
        print(f"Playback completed! Executed {events_executed} events")

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

    def click_on_image(self, template_image_path, confidence=0.8, monitor=None, repeat_count=1, interval=0, playback_events=None, playback_speed=1.0, unlimited=False, retry_on_not_found=False, stop_flag=None, log_callback=None):
        """
        Find and click on a template image using OpenCV matching

        Args:
            template_image_path: Path to the image to find
            confidence: Confidence threshold (0-1)
            monitor: Monitor number (1, 2, etc.) or None for all monitors
            repeat_count: Number of times to repeat the action (default: 1, ignored if unlimited=True)
            interval: Seconds to wait before searching for image again (default: 0)
            playback_events: If provided, plays back these recorded events instead of simple click
            playback_speed: Speed multiplier for playback (default: 1.0)
            unlimited: If True, repeats indefinitely until manually stopped (default: False)
            retry_on_not_found: If True, keeps retrying when image not found instead of stopping (default: False)
            stop_flag: A callable that returns True when the process should stop (default: None)
            log_callback: Optional callback function to log messages to GUI (default: None)

        Returns:
            True if found and action performed, False otherwise
        """
        iteration = 0
        successful_iterations = 0
        max_iterations = float('inf') if unlimited else repeat_count

        while successful_iterations < max_iterations:
            # Check if we should stop
            if stop_flag and stop_flag():
                print("Stopping image click - stop flag set")
                return False
            iteration += 1

            print(f"Searching for image: {template_image_path} (iteration {iteration}{'...' if unlimited else f'/{repeat_count}'})")

            # Add small delay before screenshot to prevent rapid capture errors
            if iteration > 1:
                time.sleep(0.1)

            # Try to find image with retry on error
            result = None
            for retry in range(3):
                try:
                    result = self.analyzer.find_image_on_screen(template_image_path, confidence, monitor=monitor)
                    break  # Success, exit retry loop
                except Exception as e:
                    if retry < 2:
                        print(f"Error searching for image (attempt {retry + 1}/3): {e}. Retrying...")
                        time.sleep(0.5)
                    else:
                        print(f"Failed to search for image after 3 attempts: {e}")
                        raise

            if result:
                x, y, match_confidence = result
                msg = f"Image found at ({x}, {y}) with confidence {match_confidence:.2f}"
                print(msg)
                if log_callback:
                    log_callback(msg)

                # Adjust coordinates if monitor was specified
                if monitor is not None:
                    monitors = self.analyzer.get_monitors()
                    if monitor > 0 and monitor <= len(monitors):
                        mon = monitors[monitor - 1]
                        x += mon['left']
                        y += mon['top']

                time.sleep(0.5)

                # Perform action based on mode
                if playback_events:
                    # Playback recorded mouse movements
                    msg = "Playing back recorded actions..."
                    print(msg)
                    if log_callback:
                        log_callback(msg)
                    # Use normal playback with timing to match original recording duration
                    self.play_recording(playback_events, speed=playback_speed, skip_moves=False, skip_delay=True, instant=False)
                else:
                    # Simple click
                    self.click_at_position(x, y)
                    if log_callback and successful_iterations == 0:
                        log_callback("Clicked on image")

                # Increment successful iterations counter
                successful_iterations += 1

                # If more iterations to go, wait the interval before searching again
                if successful_iterations < max_iterations:
                    if interval > 0:
                        print(f"Waiting {interval} seconds before next search...")
                        time.sleep(interval)
                    else:
                        # Add minimum delay to prevent errors from rapid successive searches
                        time.sleep(0.1)
                elif successful_iterations >= max_iterations:
                    print(f"Completed {successful_iterations} successful iterations")
                    break
            else:
                print(f"Image not found with confidence >= {confidence}")

                # Check if retry mode is enabled
                if retry_on_not_found:
                    # Keep retrying - don't increment iteration, just wait and try again
                    retry_delay = interval if interval > 0 else 2.0
                    if successful_iterations == 0:
                        msg = f"Retry mode: Image not found, waiting {retry_delay}s before retrying..."
                        print(msg)
                        if log_callback:
                            log_callback(msg)
                    else:
                        msg = f"Image disappeared after {successful_iterations} successful clicks. Waiting {retry_delay}s to search again..."
                        print(msg)
                        if log_callback:
                            log_callback(msg)

                    # Sleep in small chunks to allow stopping
                    for _ in range(int(retry_delay * 10)):
                        if stop_flag and stop_flag():
                            print("Stopping retry - stop flag set")
                            return False
                        time.sleep(0.1)

                    # Don't increment iteration counter, keep trying
                    iteration = 0
                    continue
                else:
                    # Retry not enabled
                    if iteration == 1:
                        # First attempt failed and no retry mode
                        return False
                    else:
                        # Image disappeared during repeats, stop gracefully
                        print(f"Image no longer found after {successful_iterations} successful iterations")
                        break

        return successful_iterations > 0

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
