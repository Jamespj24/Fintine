import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from datetime import datetime

class MockSheetAppender:
    def __init__(self):
        self.data = []
        print("⚠️  USING MOCK SHEETS DB - DATA WILL NOT PERSIST")

    def append_row(self, values):
        print(f"📝 [MOCK] Appending to sheet: {values}")
        self.data.append(values)
        return {"status": "success", "row": len(self.data)}

    def get_all_records(self):
        return self.data

class RealSheetAppender:
    def __init__(self, check_connection=True):
        self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        # Load from env or file
        creds_file = "credentials.json"
        
        if os.path.exists(creds_file):
             self.creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, self.scope)
        else:
             raise Exception("No credentials.json found")
             
        self.client = gspread.authorize(self.creds)
        
        # Open the sheet (assumes one exists or uses the first one)
        # You might want to make the sheet name configurable
        try:
            self.sheet = self.client.open("BalanceAI_Ledger").sheet1
        except Exception:
             # Fallback: Create if not exists logic is complex for gspread without drive perm, 
             # so we assume it exists or fail to mock
             print("❌ Could not open 'BalanceAI_Ledger'. Falling back to Mock.")
             raise Exception("Sheet not found")

    def append_row(self, values):
        self.sheet.append_row(values)
        return {"status": "success", "type": "real"}

    def get_all_records(self):
        return self.sheet.get_all_records()

def get_sheet_db():
    if os.getenv("USE_MOCK_SHEETS", "false").lower() == "true":
        return MockSheetAppender()
    
    try:
        return RealSheetAppender()
    except Exception as e:
        print(f"⚠️  Google Sheets Auth Failed: {e}. Switching to Mock Mode.")
        return MockSheetAppender()
