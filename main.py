"""
Main application - Auto Clicker with Mouse Recording and AI Analysis
"""
import argparse
import sys
import os
from mouse_recorder import MouseRecorder
from auto_clicker import AutoClicker
from screenshot_analyzer import ScreenshotAnalyzer
from dotenv import load_dotenv


def print_banner():
    """Print application banner"""
    banner = """
╔═══════════════════════════════════════════════════════╗
║         AI-Powered Auto Clicker & Recorder            ║
║  Record mouse movements, AI analysis, and automation  ║
╚═══════════════════════════════════════════════════════╝
    """
    print(banner)


def record_mode(args):
    """Record mouse movements and clicks"""
    recorder = MouseRecorder()

    try:
        recorder.start_recording()
        input("Press Enter to stop recording...\n")
    except KeyboardInterrupt:
        print("\nRecording interrupted")
    finally:
        recorder.stop_recording()

        if args.output:
            recorder.save_recording(args.output)
        else:
            recorder.save_recording('recording.json')


def playback_mode(args):
    """Play back recorded mouse movements"""
    if not args.input:
        print("Error: Please specify input file with --input")
        return

    if not os.path.exists(args.input):
        print(f"Error: File not found: {args.input}")
        return

    load_dotenv()
    clicker = AutoClicker(api_key=os.getenv('OPENAI_API_KEY'))
    recorder = MouseRecorder()

    # Load recording
    events = recorder.load_recording(args.input)

    # Play back with specified speed
    speed = args.speed if args.speed else 1.0
    clicker.play_recording(events, speed=speed)


def ai_click_mode(args):
    """Use AI to find and click on screen elements"""
    if not args.target:
        print("Error: Please specify target with --target")
        return

    load_dotenv()
    clicker = AutoClicker(api_key=os.getenv('OPENAI_API_KEY'))

    # Parse region if specified
    region = None
    if args.region:
        try:
            region = tuple(map(int, args.region.split(',')))
            if len(region) != 4:
                raise ValueError
        except ValueError:
            print("Error: Region must be in format: x,y,width,height")
            return

    # Find and click
    success = clicker.click_on_ai_target(args.target, region=region)

    if success:
        print("Successfully found and clicked target!")
    else:
        print("Failed to find target")


def image_click_mode(args):
    """Find and click on a template image"""
    if not args.image:
        print("Error: Please specify image with --image")
        return

    if not os.path.exists(args.image):
        print(f"Error: Image file not found: {args.image}")
        return

    load_dotenv()
    clicker = AutoClicker()

    confidence = args.confidence if args.confidence else 0.8

    success = clicker.click_on_image(args.image, confidence=confidence)

    if success:
        print("Successfully found and clicked image!")
    else:
        print("Failed to find image")


def screenshot_mode(args):
    """Capture a screenshot"""
    load_dotenv()
    analyzer = ScreenshotAnalyzer()

    # Parse region if specified
    region = None
    if args.region:
        try:
            region = tuple(map(int, args.region.split(',')))
            if len(region) != 4:
                raise ValueError
        except ValueError:
            print("Error: Region must be in format: x,y,width,height")
            return

    screenshot = analyzer.capture_screenshot(region)

    output_file = args.output if args.output else 'screenshot.png'
    analyzer.save_screenshot(screenshot, output_file)


def repeat_click_mode(args):
    """Repeat clicks at a specific position"""
    if not all([args.x, args.y, args.count]):
        print("Error: Please specify --x, --y, and --count")
        return

    load_dotenv()
    clicker = AutoClicker()

    interval = args.interval if args.interval else 1.0
    button = args.button if args.button else 'left'

    clicker.repeat_clicks(args.x, args.y, args.count, interval, button)




def main():
    """Main entry point"""
    print_banner()

    parser = argparse.ArgumentParser(
        description='AI-Powered Auto Clicker with Mouse Recording',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Record mouse movements
  python main.py record --output my_recording.json

  # Play back recording
  python main.py playback --input my_recording.json --speed 1.5

  # Click on element using AI
  python main.py ai-click --target "the blue submit button"

  # Click on image template
  python main.py image-click --image button.png --confidence 0.9

  # Take a screenshot
  python main.py screenshot --output screen.png

  # Repeat clicks
  python main.py repeat --x 100 --y 200 --count 10 --interval 0.5
        """
    )

    subparsers = parser.add_subparsers(dest='mode', help='Operation mode')

    # Record mode
    record_parser = subparsers.add_parser('record', help='Record mouse movements')
    record_parser.add_argument('--output', '-o', help='Output file (default: recording.json)')

    # Playback mode
    playback_parser = subparsers.add_parser('playback', help='Play back recorded movements')
    playback_parser.add_argument('--input', '-i', required=True, help='Input recording file')
    playback_parser.add_argument('--speed', '-s', type=float, help='Playback speed (default: 1.0)')

    # AI click mode
    ai_click_parser = subparsers.add_parser('ai-click', help='Use AI to find and click element')
    ai_click_parser.add_argument('--target', '-t', required=True, help='Description of target to click')
    ai_click_parser.add_argument('--region', '-r', help='Screen region to search (x,y,width,height)')

    # Image click mode
    image_click_parser = subparsers.add_parser('image-click', help='Find and click template image')
    image_click_parser.add_argument('--image', '-i', required=True, help='Template image path')
    image_click_parser.add_argument('--confidence', '-c', type=float, help='Confidence threshold (default: 0.8)')

    # Screenshot mode
    screenshot_parser = subparsers.add_parser('screenshot', help='Capture screenshot')
    screenshot_parser.add_argument('--output', '-o', help='Output file (default: screenshot.png)')
    screenshot_parser.add_argument('--region', '-r', help='Screen region (x,y,width,height)')

    # Repeat click mode
    repeat_parser = subparsers.add_parser('repeat', help='Repeat clicks at position')
    repeat_parser.add_argument('--x', type=int, required=True, help='X coordinate')
    repeat_parser.add_argument('--y', type=int, required=True, help='Y coordinate')
    repeat_parser.add_argument('--count', type=int, required=True, help='Number of clicks')
    repeat_parser.add_argument('--interval', type=float, help='Interval between clicks (default: 1.0)')
    repeat_parser.add_argument('--button', choices=['left', 'right'], help='Mouse button (default: left)')


    args = parser.parse_args()

    if not args.mode:
        parser.print_help()
        return

    # Route to appropriate mode
    modes = {
        'record': record_mode,
        'playback': playback_mode,
        'ai-click': ai_click_mode,
        'image-click': image_click_mode,
        'screenshot': screenshot_mode,
        'repeat': repeat_click_mode

    }

    if args.mode in modes:
        modes[args.mode](args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
