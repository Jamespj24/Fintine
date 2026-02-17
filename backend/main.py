from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import uvicorn
from contextlib import asynccontextmanager

# Tools
from tools.google_sheets import get_sheet_db
from tools.gemini import get_vision_model
from graph import app_graph

# App State
processed_images_log = []
simulation_events = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("🚀 Balance AI Backend Starting...")
    yield
    # Shutdown logic
    print("🛑 Shutting down...")

app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Tools (Lazy load or immediate)
# We instantiate them per request or here if stateless enough
# but get_vision_model handles env checks

@app.get("/")
def health_check():
    return {"status": "ok", "agent": "Balance AI v1.0"}

@app.post("/upload")
async def upload_receipt(file: UploadFile = File(...)):
    print(f"📥 Received upload: {file.filename}")
    
    try:
        content = await file.read()
        
        # 1. Analyze with Gemini
        vision = get_vision_model()
        # Mock Gemini expects list, Real expects bytes/dict
        # We wrapped it to handle clean dict interfaces?
        # Actually RealGeminiVision.analyze_image takes bytes
        
        # Wait, MockGeminiVision.analyze_image logic was:
        # returns dict.
        
        # RealGeminiVision uses:
        # genai to generate content.
        
        analysis = vision.analyze_image(content)
        print(f"🧠 Analysis: {analysis}")
        
        # 2. Append to Sheets
        # Flatten dict to list of values in specific order?
        # Or just dump JSON string?
        # Let's flatten for a nice sheet: Date, Vendor, Amount, Category, Description
        
        row_data = [
            analysis.get("date", ""),
            analysis.get("vendor", "Unknown"),
            analysis.get("amount", 0),
            analysis.get("category", "Uncategorized"),
            analysis.get("description", ""),
            "Pending" # Status
        ]
        
        db = get_sheet_db()
        result = db.append_row(row_data)
        
        # Log for "Agent Feed"
        log_entry = {
            "id": len(processed_images_log) + 1,
            "action": "processed_receipt",
            "details": f"Processed {analysis.get('vendor')} receipt for ${analysis.get('amount')}",
            "timestamp": "Just now"
        }
        processed_images_log.append(log_entry)
        
        return {
            "status": "success",
            "data": analysis,
            "sheet_result": result
        }

    except Exception as e:
        print(f"❌ Error processing upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/run")
async def run_agent():
    print("🤖 Triggering Autonomous Auditor Agent...")
    try:
        # Run LangGraph
        initial_state = {
            "ledger_data": [],
            "unpaid_invoices": [],
            "risks": [],
            "emails_to_send": [],
            "logs": []
        }
        
        # Invoke the graph
        # Note: app_graph.invoke is synchronous unless using aRunner?
        # For demo, sync is fine if fast (mocked).
        result = app_graph.invoke(initial_state)
        
        # Log the output
        for log in result.get("logs", []):
            processed_images_log.append({
                "id": len(processed_images_log) + 1,
                "action": "agent_log",
                "details": log,
                "timestamp": "Just now"
            })
            
        return {"status": "success", "result": result}
    except Exception as e:
        print(f"❌ Agent Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulation/event")
async def trigger_simulation(event_data: dict):
    # event_data: {"type": "payment_received", "details": "Client X paid $500"}
    print(f"🎭 Simulation Event: {event_data}")
    processed_images_log.append({
        "id": len(processed_images_log) + 1,
        "action": "simulation",
        "details": event_data.get("details", "Simulated Event"),
        "timestamp": "Just now"
    })
    return {"status": "simulated"}

@app.get("/agent/status")
def get_status():
    return {"logs": processed_images_log[-10:]} # Return last 10 logs

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
