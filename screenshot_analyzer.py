"""
Screenshot capture and AI-based analysis
Uses OpenAI Vision API to analyze screenshots and identify click targets
"""
import pyautogui
import cv2
import numpy as np
from PIL import Image
import base64
import io
from openai import OpenAI
import os


class ScreenshotAnalyzer:
    def __init__(self, api_key=None):
        """
        Initialize the screenshot analyzer

        Args:
            api_key: OpenAI API key (if not provided, will try to load from environment)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            print("Warning: No OpenAI API key provided. AI analysis will not be available.")
            self.client = None

    def capture_screenshot(self, region=None):
        """
        Capture a screenshot

        Args:
            region: Tuple (x, y, width, height) for specific region, or None for full screen

        Returns:
            PIL Image object
        """
        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()
        return screenshot

    def save_screenshot(self, screenshot, filename):
        """Save screenshot to file"""
        screenshot.save(filename)
        print(f"Screenshot saved to {filename}")

    def image_to_base64(self, image):
        """Convert PIL Image to base64 string"""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    def analyze_screenshot_with_ai(self, screenshot, target_description):
        """
        Analyze screenshot using OpenAI Vision API to find target element

        Args:
            screenshot: PIL Image object
            target_description: Description of what to look for (e.g., "the blue submit button")

        Returns:
            Dictionary with x, y coordinates and confidence
        """
        if not self.client:
            raise ValueError("OpenAI client not initialized. Please provide API key.")

        # Convert image to base64
        base64_image = self.image_to_base64(screenshot)

        # Create the prompt
        prompt = f"""Analyze this screenshot and locate: {target_description}

Please provide the approximate position as a percentage of the image dimensions (0-100% for both x and y).

Respond in JSON format:
{{
    "found": true/false,
    "x_percent": <number 0-100>,
    "y_percent": <number 0-100>,
    "confidence": <number 0-1>,
    "description": "<brief description of what was found>"
}}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response.choices[0].message.content)

            # Convert percentages to actual pixel coordinates
            width, height = screenshot.size
            if result.get('found'):
                result['x'] = int((result['x_percent'] / 100) * width)
                result['y'] = int((result['y_percent'] / 100) * height)

            return result

        except Exception as e:
            print(f"Error analyzing screenshot: {e}")
            return {
                "found": False,
                "error": str(e)
            }

    def find_image_on_screen(self, template_image_path, confidence=0.8):
        """
        Find a template image on the current screen using OpenCV

        Args:
            template_image_path: Path to the template image to search for
            confidence: Confidence threshold (0-1)

        Returns:
            Tuple (x, y) of the center of the found image, or None
        """
        # Capture current screen
        screenshot = self.capture_screenshot()
        screenshot_np = np.array(screenshot)
        screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)

        # Load template
        template = cv2.imread(template_image_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            raise ValueError(f"Could not load template image: {template_image_path}")

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

    def highlight_target(self, screenshot, x, y, output_path='highlighted.png'):
        """
        Draw a circle on the screenshot at the target location

        Args:
            screenshot: PIL Image object
            x, y: Coordinates to highlight
            output_path: Where to save the highlighted image
        """
        img_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        cv2.circle(img_cv, (x, y), 20, (0, 255, 0), 3)
        cv2.imwrite(output_path, img_cv)
        print(f"Highlighted target saved to {output_path}")
