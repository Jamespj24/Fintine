import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from datetime import datetime

class MockSheetAppender:
    def __init__(self):
        # Initial Seed Data for Mock Mode (So it's not empty)
        self.data = [
             {"date": "2023-10-24", "vendor": "AWS Web Services", "amount": "$1,200.00", "category": "Infrastructure", "status": "Paid"},
             {"date": "2023-10-25", "vendor": "WeWork", "amount": "$850.00", "category": "Office", "status": "Paid"}
        ]
        print("⚠️  USING MOCK SHEETS DB - DATA WILL NOT PERSIST")

    def append_row(self, values):
        # Value is list: [Date, Vendor, Amount, Category, Description, Status]
        # Convert to dict for get_all_records consistency in mock
        record = {
            "date": values[0],
            "vendor": values[1],
            "amount": f"${values[2]}",
            "category": values[3],
            "description": values[4],
            "status": values[5]
        }
        print(f"📝 [MOCK] Appending to sheet: {record}")
        self.data.insert(0, record) # Prepend
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
        try:
            self.sheet = self.client.open("BalanceAI_Ledger").sheet1
        except Exception:
             print("❌ Could not open 'BalanceAI_Ledger'. Falling back to Mock.")
             raise Exception("Sheet not found")

    def append_row(self, values):
        try:
            self.sheet.append_row(values)
            return {"status": "success", "type": "real"}
        except Exception as e:
            print(f"❌ Sheets Append Error: {e}")
            return {"status": "error", "message": str(e), "type": "real_failed"}

    def get_all_records(self):
        # Returns list of dicts
        try:
             return self.sheet.get_all_records()
        except Exception as e:
             print(f"❌ Error fetching records: {e}")
             return []

def get_sheet_db():
    if os.getenv("USE_MOCK_SHEETS", "false").lower() == "true":
        return MockSheetAppender()
    
    try:
        return RealSheetAppender()
    except Exception as e:
        print(f"⚠️  Google Sheets Auth Failed: {e}. Switching to Mock Mode.")
        return MockSheetAppender()
