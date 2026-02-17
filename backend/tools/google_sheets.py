import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from datetime import datetime

class MockSheetAppender:
    def __init__(self):
        # Initial Seed Data for Mock Mode (So it's not empty)
        self.data = [
             {"date": "2023-10-24", "vendor": "AWS Web Services", "amount": "$1,200.00", "category": "Infrastructure", "description": "Cloud Hosting", "status": "Paid"},
             {"date": "2023-10-25", "vendor": "WeWork", "amount": "$850.00", "category": "Office", "description": "Co-working entry", "status": "Paid"}
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

        # Check for headers and init if empty
        try:
            if not self.sheet.get_all_values():
                print("📝 Initializing Sheet Headers...")
                self.sheet.append_row(["date", "vendor", "amount", "category", "description", "status"])
        except Exception as e:
            print(f"⚠️ Error checking headers: {e}")

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
             rows = self.sheet.get_all_values()
             if not rows:
                 return []
             
             # Check if first row is header
             first_row = [str(c).lower().strip() for c in rows[0]]
             if "date" in first_row and "vendor" in first_row:
                 rows = rows[1:] # Skip header
                 
             records = []
             for row in rows:
                 # Ensure row has enough columns (pad with empty strings)
                 while len(row) < 6:
                     row.append("")
                     
                 record = {
                     "date": row[0],
                     "vendor": row[1],
                     "amount": row[2],
                     "category": row[3],
                     "description": row[4],
                     "status": row[5]
                 }
                 records.append(record)
                 
             return records
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
