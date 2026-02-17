import google.generativeai as genai
import os
import json
import time

class MockGeminiVision:
    def analyze_image(self, image_bytes, mime_type="image/jpeg"):
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

    def analyze_image(self, image_data, mime_type="image/jpeg"):
        prompt = """
        You are an autonomous CFO Agent for a company. Your job is to extract financial data from receipts and invoices.
        
        GUARDRAILS:
        - If the image is NOT a receipt, invoice, or financial document, return JSON with {"error": "Irrelevant image detected"}.
        - Do not hallucinate values. If a field is missing, use null or 0.
        
        Extract the following details in JSON format:
        - vendor (string)
        - amount (number)
        - currency (string, always use "INR" or "₹" if unsure, but try to detect)
        - date (YYYY-MM-DD string)
        - category (string, e.g. Office Supplies, Travel, Food)
        - description (short summary string, e.g. "Lunch meeting", "Printer paper")
        
        Return ONLY valid JSON. No markdown backticks.
        """
        
        try:
            # image_data is bytes
            response = self.model.generate_content([
                prompt,
                {
                    "mime_type": mime_type,
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
            print("⚠️  Falling back to Mock Gemini due to API error.")
            return MockGeminiVision().analyze_image(image_data, mime_type)

def get_vision_model():
    if os.getenv("USE_MOCK_GEMINI", "false").lower() == "true":
        return MockGeminiVision()
    
    try:
        return RealGeminiVision()
    except Exception as e:
        print(f"⚠️  Gemini Init Failed: {e}. Switching to Mock Mode.")
        return MockGeminiVision()
