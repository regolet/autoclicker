"""
Mouse movement and click recorder
Records mouse positions, clicks, and delays for playback
"""
import json
import time
from datetime import datetime
from pynput import mouse
from pynput.mouse import Button


class MouseRecorder:
    def __init__(self):
        self.events = []
        self.recording = False
        self.start_time = None
        self.listener = None

    def on_move(self, x, y):
        """Record mouse movement"""
        if self.recording:
            timestamp = time.time() - self.start_time
            self.events.append({
                'type': 'move',
                'x': x,
                'y': y,
                'timestamp': timestamp
            })

    def on_click(self, x, y, button, pressed):
        """Record mouse clicks"""
        if self.recording and pressed:
            timestamp = time.time() - self.start_time
            self.events.append({
                'type': 'click',
                'x': x,
                'y': y,
                'button': button.name,
                'timestamp': timestamp
            })

    def on_scroll(self, x, y, dx, dy):
        """Record mouse scroll"""
        if self.recording:
            timestamp = time.time() - self.start_time
            self.events.append({
                'type': 'scroll',
                'x': x,
                'y': y,
                'dx': dx,
                'dy': dy,
                'timestamp': timestamp
            })

    def start_recording(self):
        """Start recording mouse events"""
        self.events = []
        self.recording = True
        self.start_time = time.time()

        self.listener = mouse.Listener(
            on_move=self.on_move,
            on_click=self.on_click,
            on_scroll=self.on_scroll
        )
        self.listener.start()
        print("Recording started. Press Ctrl+C to stop.")

    def stop_recording(self):
        """Stop recording mouse events"""
        self.recording = False
        if self.listener:
            self.listener.stop()
        print(f"Recording stopped. Captured {len(self.events)} events.")
        return self.events

    def save_recording(self, filename, optimize=True):
        """Save recorded events to a JSON file

        Args:
            filename: Path to save the recording
            optimize: If True, simplify move events to reduce file size and improve playback speed
        """
        events = self.events

        # Optimize by keeping only significant moves (before clicks/scrolls)
        if optimize:
            original_count = len(events)
            optimized_events = []

            for i, event in enumerate(events):
                if event['type'] in ('click', 'scroll'):
                    # Always keep clicks and scrolls
                    optimized_events.append(event)
                elif event['type'] == 'move':
                    # Keep move event only if it's followed by a click/scroll within next few events
                    # This preserves the movement path before actions
                    is_significant = False
                    for j in range(i + 1, min(i + 10, len(events))):
                        if events[j]['type'] in ('click', 'scroll'):
                            is_significant = True
                            break

                    # Also keep if it's a significant movement (more than 50 pixels from last kept move)
                    if not is_significant and optimized_events:
                        last_move = None
                        for prev_event in reversed(optimized_events):
                            if prev_event['type'] == 'move':
                                last_move = prev_event
                                break

                        if last_move:
                            distance = ((event['x'] - last_move['x'])**2 + (event['y'] - last_move['y'])**2)**0.5
                            if distance > 50:
                                is_significant = True

                    if is_significant or i == 0:  # Always keep first move
                        optimized_events.append(event)

            events = optimized_events
            print(f"Optimized recording: {original_count} -> {len(events)} events (removed {original_count - len(events)} move events)")

        data = {
            'recorded_at': datetime.now().isoformat(),
            'events': events,
            'optimized': optimize
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Recording saved to {filename}")

    def load_recording(self, filename):
        """Load recorded events from a JSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)

        self.events = data['events']
        print(f"Loaded {len(self.events)} events from {filename}")
        return self.events
