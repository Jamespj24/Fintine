import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import sys

def test_sheets():
    print("📋 Testing Google Sheets Connection...")
    
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_file = "credentials.json"
    
    if not os.path.exists(creds_file):
        print("❌ Error: credentials.json not found!")
        return

    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
        client = gspread.authorize(creds)
        print("✅ Auth Successful!")
        print(f"📧 Service Account Email: {creds.service_account_email}")
        print("---------------------------------------------------")
        
        sheet_name = "BalanceAI_Ledger"
        print(f"🔍 Looking for sheet: '{sheet_name}'...")
        
        try:
            sheet = client.open(sheet_name).sheet1
            print("✅ Sheet Found!")
            
            # Read existing
            records = sheet.get_all_records()
            print(f"📊 Found {len(records)} existing records.")
            
            print("---------------------------------------------------")
            print("🎉 Google Sheets Integration is READY!")
            
        except gspread.SpreadsheetNotFound:
            print(f"❌ ERROR: Sheet '{sheet_name}' not found.")
            print("👉 ACTION REQUIRED:")
            print(1, f"Go to Google Sheets and create a blank sheet named '{sheet_name}'")
            print(2, f"Click 'Share' and add this email: {creds.service_account_email}")
            print(3, "Select 'Editor' role and click Send.")
            
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    test_sheets()
