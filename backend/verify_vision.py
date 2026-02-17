import os
import io
from dotenv import load_dotenv
from tools.gemini import RealGeminiVision

# Load Env
load_dotenv()

import base64

def create_dummy_png():
    # 1x1 Red Dot PNG
    base64_str = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    return base64.b64decode(base64_str)

def test_gemini():
    print("🔮 Testing Gemini Vision API Connection...")
    
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("❌ Error: GEMINI_API_KEY not found in .env")
        return

    print(f"🔑 API Key found: {key[:5]}...{key[-3:]}")
    
    try:
        vision = RealGeminiVision()
        image_data = create_dummy_png()
        
        print("📤 Sending test image (1x1 PNG)...")
        result = vision.analyze_image(image_data, mime_type="image/png")
        
        print("\n✅ Gemini Vision Success!")
        print("Parsed Result:", result)
        
    except Exception as e:
        print(f"\n❌ Gemini Vision Failed: {e}")

if __name__ == "__main__":
    test_gemini()
