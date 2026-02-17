import sys
import os

# Add backend directory to Python path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from fastapi import FastAPI
from main import app as backend_app

# Vercel sends the FULL path (e.g. /api/ledger) to this handler.
# But our FastAPI routes are defined WITHOUT the /api prefix (e.g. /ledger).
# Solution: mount the backend app under /api so paths match.
app = FastAPI()
app.mount("/api", backend_app)
