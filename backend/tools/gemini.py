import google.generativeai as genai
import os
import json
import time

class MockGeminiVision:
    def analyze_image(self, image_bytes):
        print("⚠️  USING MOCK GEMINI - RETURNING CANNED RESPONSE")
        time.sleep(1.5) # Simulate processing delay
        return {
            "vendor": "Starbucks Coffee",
            "amount": 5.40,
            "currency": "USD",
            "date": "2023-10-25",
            "category": "Food & Drink",
            "description": "Latte & Croissant"
        }

class RealGeminiVision:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise Exception("No GEMINI_API_KEY found")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def analyze_image(self, image_data):
        prompt = """
        Analyze this receipt image. Extract the following details in JSON format:
        - vendor (string)
        - amount (number)
        - currency (string, e.g. USD)
        - date (YYYY-MM-DD string)
        - category (string, e.g. Office Supplies, Travel, Food)
        - description (short summary string)
        
        Return ONLY valid JSON. No markdown backticks.
        """
        
        try:
            # image_data is bytes
            response = self.model.generate_content([
                prompt,
                {
                    "mime_type": "image/jpeg",
                    "data": image_data
                }
            ])
            # Clean response text
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
            return json.loads(text)
        except Exception as e:
            print(f"❌ Gemini Error: {e}")
            raise e

def get_vision_model():
    if os.getenv("USE_MOCK_GEMINI", "false").lower() == "true":
        return MockGeminiVision()
    
    try:
        return RealGeminiVision()
    except Exception as e:
        print(f"⚠️  Gemini Init Failed: {e}. Switching to Mock Mode.")
        return MockGeminiVision()
