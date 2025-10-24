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

    def save_recording(self, filename):
        """Save recorded events to a JSON file"""
        data = {
            'recorded_at': datetime.now().isoformat(),
            'events': self.events
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
