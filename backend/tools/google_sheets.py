import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from datetime import datetime

# --- Singleton Sheet Connection ---
# This prevents re-authenticating on every API call, which causes rate-limiting.
_sheet_instance = None

class RealSheetAppender:
    def __init__(self):
        self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_file = "credentials.json"
        
        if not os.path.exists(creds_file):
            raise Exception("No credentials.json found. Cannot connect to Google Sheets.")
              
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, self.scope)
        self.client = gspread.authorize(self.creds)
        
        try:
            self.sheet = self.client.open("BalanceAI_Ledger").sheet1
            print("✅ Connected to Google Sheet: BalanceAI_Ledger")
        except Exception as e:
            raise Exception(f"Sheet 'BalanceAI_Ledger' not found: {e}")

        # Check headers once on init
        try:
            rows = self.sheet.get_all_values()
            if not rows:
                print("📝 Initializing Sheet Headers...")
                self.sheet.append_row(["date", "vendor", "amount", "category", "description", "billed_to", "status"])
        except Exception as e:
            print(f"⚠️ Error checking headers: {e}")

    def _reconnect_if_needed(self):
        """Re-authorize if the token has expired."""
        try:
            if self.creds.access_token_expired:
                self.client = gspread.authorize(self.creds)
                self.sheet = self.client.open("BalanceAI_Ledger").sheet1
                print("🔄 Re-authorized Google Sheets connection.")
        except Exception as e:
            print(f"⚠️ Reconnect failed: {e}")
            raise

    def append_row(self, values):
        try:
            self._reconnect_if_needed()
            self.sheet.append_row(values)
            return {"status": "success", "type": "real"}
        except Exception as e:
            print(f"❌ Sheets Append Error: {e}")
            return {"status": "error", "message": str(e), "type": "real_failed"}

    def get_all_records(self):
        try:
            self._reconnect_if_needed()
            rows = self.sheet.get_all_values()
            if not rows:
                return []
             
            # Check if first row is header
            first_row = [str(c).lower().strip() for c in rows[0]]
            if "date" in first_row and "vendor" in first_row:
                rows = rows[1:]  # Skip header
                 
            records = []
            for row in rows:
                # Pad row to 7 columns
                while len(row) < 7:
                    row.append("")
                     
                record = {
                    "date": row[0],
                    "vendor": row[1],
                    "amount": row[2],
                    "category": row[3],
                    "description": row[4],
                    "billed_to": row[5],
                    "status": row[6]
                }
                records.append(record)
                 
            return records
        except Exception as e:
            print(f"❌ Error fetching records: {e}")
            raise  # Don't silently return empty — let the caller handle it

def get_sheet_db():
    """Returns a singleton RealSheetAppender. Raises if connection fails."""
    global _sheet_instance
    
    if _sheet_instance is not None:
        return _sheet_instance
    
    # Always try real sheets — no mock fallback
    _sheet_instance = RealSheetAppender()
    return _sheet_instance
