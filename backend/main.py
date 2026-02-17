from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import uvicorn
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

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
    print("🚀 Fintine Backend Starting...")
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
    return {"status": "ok", "agent": "Fintine v1.0"}

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
        
        analysis = vision.analyze_image(content, mime_type=file.content_type)
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
            analysis.get("billed_to", "Unknown"),
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



@app.get("/ledger")
async def get_ledger():
    try:
        db = get_sheet_db()
        records = db.get_all_records()
        
        # Normalize keys to lowercase to handle mismatched Sheet headers (e.g. "Date" vs "date")
        normalized_records = []
        for r in records:
            normalized_records.append({k.lower(): v for k, v in r.items()})
            
        return {"status": "success", "data": normalized_records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class StatusUpdate(BaseModel):
    status: str

@app.put("/ledger/{row_index}/status")
async def update_ledger_status(row_index: int, body: StatusUpdate):
    """Update the status of a ledger row. row_index is 0-based (first data row = 0)."""
    try:
        db = get_sheet_db()
        # Sheet row = row_index + 2 (1 for 0-index, 1 for header row)
        sheet_row = row_index + 2
        # Status is column 7
        result = db.update_cell(sheet_row, 7, body.status)
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        return {"status": "success", "row": row_index, "new_status": body.status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    query: str

@app.post("/agent/chat")
async def chat_with_agent(request: ChatRequest):
    print(f"💬 Chat Query: {request.query}")
    try:
        # 1. Get Data Context
        db = get_sheet_db()
        records = db.get_all_records()
        
        # 2. Call Gemini
        vision = get_vision_model()
        response_text = vision.chat_with_data(request.query, records)
        
        # 3. Log it
        processed_images_log.append({
            "id": len(processed_images_log) + 1,
            "action": "chat",
            "details": f"Q: {request.query} | A: {response_text[:50]}...",
            "timestamp": "Just now"
        })
        
        return {"status": "success", "response": response_text}
    except Exception as e:
         print(f"❌ Chat Error: {e}")
         raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/health")
async def get_agent_health():
    # Check Gemini
    gemini_status = "inactive"
    try:
        if os.getenv("GEMINI_API_KEY"):
             gemini_status = "active"
    except:
        pass

    # Check Sheets
    sheets_status = "mock"
    if os.getenv("USE_MOCK_SHEETS", "false").lower() == "false":
        sheets_status = "active"
        
    return {
        "status": "online",
        "components": {
            "vision": gemini_status,
            "database": sheets_status
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
