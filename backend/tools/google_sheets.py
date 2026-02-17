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
        # Resolve path relative to the backend directory, not the CWD
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        creds_file = os.path.join(backend_dir, "credentials.json")
        
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
                self.sheet.append_row(["date", "vendor", "amount", "category", "description", "billed_to", "status", "invoice_no"])
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
            
            # Check for duplicates based on Invoice No (Index 7 / Column H)
            # values is expected to be [date, vendor, amount, category, description, billed_to, status, invoice_no]
            if len(values) >= 8:
                new_invoice_no = str(values[7]).strip().lower()
                if new_invoice_no:
                    # Get all existing invoice numbers (Column 8)
                    existing_invoices = self.sheet.col_values(8)
                    # col_values includes header, so skip it if needed, but simple "in" check is fine
                    if any(inv.strip().lower() == new_invoice_no for inv in existing_invoices):
                         print(f"❌ Duplicate Invoice Detected: {new_invoice_no}")
                         return {"status": "error", "message": "Duplicate Invoice"}

            self.sheet.append_row(values)
            return {"status": "success", "type": "real"}
        except Exception as e:
            print(f"❌ Sheets Append Error: {e}")
            return {"status": "error", "message": str(e), "type": "real_failed"}

    def update_cell_value(self, row, col, value):
        """Update a single cell. row and col are 1-indexed sheet coordinates."""
        try:
            self._reconnect_if_needed()
            print(f"📝 Updating cell R{row}C{col} to '{value}'")
            self.sheet.update_cell(row, col, value)
            return {"status": "success"}
        except Exception as e:
            print(f"❌ Sheets Update Error: {e}")
            return {"status": "error", "message": str(e)}

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
                    "status": row[6],
                    "invoice_no": row[7] if len(row) > 7 else ""
                }
                records.append(record)
                 
            return records
        except Exception as e:
            print(f"❌ Error fetching records: {e}")
            raise  # Don't silently return empty — let the caller handle it

    def update_status_by_match(self, match_criteria, new_status):
        """
        Finds a row matching 'date', 'vendor', and 'amount' and updates its status.
        match_criteria: dict containing 'date', 'vendor', 'amount'
        new_status: str
        """
        try:
            self._reconnect_if_needed()
            print(f"🔍 Searching for transaction: {match_criteria}")
            
            rows = self.sheet.get_all_values()
            if not rows:
                return {"status": "error", "message": "Sheet is empty"}
                
            # Normalize match criteria
            target_date = str(match_criteria.get("date", "")).strip().lower()
            target_vendor = str(match_criteria.get("vendor", "")).strip().lower()
            # Handle amount: remove currency symbols, commas, etc.
            target_amount = str(match_criteria.get("amount", "0")).replace("₹", "").replace(",", "").strip()
            
            # Find matching row
            target_row_idx = -1
            
            # Skip header (row 1)
            for i in range(1, len(rows)):
                row = rows[i]
                # Pad row if needed
                while len(row) < 7: row.append("")
                
                # Check match (Columns: Date=0, Vendor=1, Amount=2, Status=6, InvoiceNo=7)
                r_date = str(row[0]).strip().lower()
                r_vendor = str(row[1]).strip().lower()
                r_amount = str(row[2]).replace("₹", "").replace(",", "").strip()
                r_invoice = str(row[7]).strip().lower() if len(row) > 7 else ""
                
                # Priority 1: Match by Invoice No if provided
                raw_invoice = match_criteria.get("invoice_no")
                target_invoice = str(raw_invoice).strip().lower() if raw_invoice else ""
                
                if target_invoice and r_invoice == target_invoice:
                     target_row_idx = i
                     break
                
                # Priority 2: Fallback to Date+Vendor+Amount
                # Only use fallback if we didn't search by invoice OR invoice search failed (optional: strictly, if invoice IS passed, we expect it to match)
                # But here, if target_invoice is present, we skipped the loop break above.
                # Actually, if target_invoice IS present but didn't match r_invoice, we continue to next row.
                # The fallback checks should only run if target_invoice is empty. 
                # If target_invoice is "INV-123", we shouldn't match a row by date/amount if the invoice ID doesn't match.
                if not target_invoice:
                     if r_date == target_date and r_vendor == target_vendor and float(r_amount or 0) == float(target_amount or 0):
                        target_row_idx = i
                        break
            
            if target_row_idx != -1:
                # Update status (Column 7 / Index 6 in 0-based list, but 1-based for API)
                # Row is i + 1 (1-based)
                sheet_row = target_row_idx + 1
                print(f"✅ Found match at Row {sheet_row}. Updating status to {new_status}...")
                self.sheet.update_cell(sheet_row, 7, new_status)
                return {"status": "success", "row": sheet_row, "new_status": new_status}
            else:
                print("❌ No matching transaction found.")
                return {"status": "error", "message": "Transaction not found"}
                
        except Exception as e:
            print(f"❌ Update Error: {e}")
            return {"status": "error", "message": str(e)}

def get_sheet_db():
    """Returns a singleton RealSheetAppender. Raises if connection fails."""
    global _sheet_instance
    
    if _sheet_instance is not None:
        return _sheet_instance
    
    # Always try real sheets — no mock fallback
    _sheet_instance = RealSheetAppender()
    return _sheet_instance
