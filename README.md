# AI-Powered Auto Clicker

A Python-based auto clicker with mouse recording capabilities and AI-powered image analysis for intelligent clicking.

## Features

- **Mouse Recording**: Record mouse movements, clicks, and scrolls with timestamps
- **Playback**: Play back recorded mouse actions at any speed
- **AI-Powered Clicking**: Use OpenAI Vision API to analyze screenshots and click on specific elements by description
- **Image Template Matching**: Find and click on screen elements using template images (OpenCV)
- **Screenshot Capture**: Take screenshots of full screen or specific regions
- **Repeat Clicking**: Automatically repeat clicks at specific positions

## Installation

1. Install Python 3.8 or higher

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Set up OpenAI API key for AI features:
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key to `.env`
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

## Usage

### GUI Application (Recommended)

Launch the graphical user interface:

```bash
python gui.py
```

The GUI provides an easy-to-use interface with tabs for:
- **Record**: Record mouse movements and clicks
- **Playback**: Load and replay recordings with speed control
- **AI Click**: Use AI to find and click elements by description
- **Image Click**: Find and click using template images
- **Screenshot**: Capture screenshots

### CLI Application

Alternatively, use the command-line interface for automation:

#### Record Mouse Movements

Record your mouse movements and clicks:

```bash
python main.py record --output my_recording.json
```

Press Enter to stop recording.

### Play Back Recording

Play back a recorded session:

```bash
python main.py playback --input my_recording.json
```

Play back at different speed (2x faster):

```bash
python main.py playback --input my_recording.json --speed 2.0
```

### AI-Powered Click

Use AI to find and click on screen elements by description:

```bash
python main.py ai-click --target "the blue submit button"
```

Search within a specific screen region:

```bash
python main.py ai-click --target "the login button" --region "100,100,800,600"
```

**Note**: Requires OpenAI API key in `.env` file.

### Image Template Click

Find and click on elements using a template image:

```bash
python main.py image-click --image button_template.png
```

Adjust confidence threshold:

```bash
python main.py image-click --image button.png --confidence 0.9
```

### Capture Screenshot

Take a screenshot:

```bash
python main.py screenshot --output my_screen.png
```

Capture specific region:

```bash
python main.py screenshot --output region.png --region "0,0,1920,1080"
```

### Repeat Clicks

Click multiple times at a specific position:

```bash
python main.py repeat --x 500 --y 300 --count 10 --interval 0.5
```

## Safety Features

- **FAILSAFE**: Move mouse to the top-left corner of the screen to abort any operation
- All operations include small delays to prevent system overload
- Recording can be stopped at any time with Enter key

## Project Structure

```
autoclicker/
├── gui.py                    # GUI application (recommended)
├── main.py                   # CLI interface
├── mouse_recorder.py         # Mouse recording functionality
├── auto_clicker.py          # Auto clicker and playback
├── screenshot_analyzer.py   # Screenshot capture and AI analysis
├── requirements.txt         # Python dependencies
├── .env                     # Your API key (create from .env.example)
├── .env.example            # Example environment variables
└── README.md               # This file
```

## Requirements

- Python 3.8+
- Windows/macOS/Linux
- OpenAI API key (optional, for AI features only)

## Dependencies

- `pyautogui`: Mouse control and screenshots
- `pynput`: Mouse event listening
- `Pillow`: Image processing
- `opencv-python`: Template matching
- `numpy`: Numerical operations
- `openai`: AI-powered analysis
- `python-dotenv`: Environment variable management

## Examples

**Example 1: Record and replay a workflow**
```bash
# Record your actions
python main.py record --output workflow.json

# Replay them later
python main.py playback --input workflow.json
```

**Example 2: Click on a button using AI**
```bash
# The AI will analyze the screen and click the described element
python main.py ai-click --target "the red close button in the top right"
```

**Example 3: Automated clicking loop**
```bash
# Click 100 times at position (500, 300) with 0.1s between clicks
python main.py repeat --x 500 --y 300 --count 100 --interval 0.1
```

## Troubleshooting

**Issue**: `FailSafeException` raised
- **Solution**: This is a safety feature. Move your mouse away from the top-left corner and try again.

**Issue**: AI click not working
- **Solution**: Ensure you have set your OpenAI API key in the `.env` file.

**Issue**: Image template not found
- **Solution**: Try lowering the confidence threshold with `--confidence 0.7` or use a better template image.

## License

This project is for educational and automation purposes. Use responsibly and in accordance with applicable terms of service.

## Warning

Be careful when using automation tools. Make sure you have permission to automate interactions with the applications you're targeting. Some applications and games have terms of service that prohibit automation.
