import google.generativeai as genai
import os
import json

# --- Singleton Gemini Instance ---
_gemini_instance = None

class RealGeminiVision:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise Exception("No GEMINI_API_KEY found in environment. Set it in .env")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        print("✅ Gemini Vision initialized (gemini-2.5-flash)")

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
        - billed_to (string, the person or company being billed/paying)
        
        Return ONLY valid JSON. No markdown backticks.
        """
        
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

    def chat_with_data(self, query, data_context):
        prompt = f"""
        You are Balance AI, the company's autonomous CFO. 
        You have access to the following financial ledger data (JSON format):
        
        {json.dumps(data_context, indent=2)}
        
        User Query: "{query}"
        
        Instructions:
        1. Answer the user's question accurately based ONLY on the data provided.
        2. Be concise and professional, but friendly.
        3. If you calculate totals, show your math briefly (e.g. "Found 3 items...").
        4. If the data doesn't contain the answer, say so clearly.
        5. Use currency symbols correctly (₹ for INR, $ for USD).
        6. IMPORTANT: Respond in PLAIN TEXT only. Do NOT use any markdown formatting like **, ##, or bullet points with *. Use simple dashes (-) for lists.
        """
        
        response = self.model.generate_content(prompt)
        return response.text.strip()

def get_vision_model():
    """Returns a singleton RealGeminiVision. Raises if API key missing."""
    global _gemini_instance
    
    if _gemini_instance is not None:
        return _gemini_instance
    
    _gemini_instance = RealGeminiVision()
    return _gemini_instance
