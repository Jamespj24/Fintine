import requests
import sys

try:
    print("Health check...")
    r = requests.get("http://localhost:8000/agent/health", timeout=2)
    print(f"Status: {r.status_code}")
    print(r.json())
except Exception as e:
    print(f"Failed: {e}")
