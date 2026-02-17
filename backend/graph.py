from langgraph.graph import StateGraph, END
from typing import TypedDict, List
import random

# Define State
class AgentState(TypedDict):
    ledger_data: List[dict]
    unpaid_invoices: List[dict]
    risks: List[str]
    emails_to_send: List[dict]
    logs: List[str]

# 1. Scan Ledger Node
def scan_ledger(state: AgentState):
    print("🔍 [Agent] Scanning Ledger...")
    # Mock reading from our Sheet tool
    # In real app: data = get_sheet_db().get_all_records()
    
    # We'll use passed state or fetch fresh if needed
    # For Hackathon speed, let's assume we fetch fresh every run
    from tools.google_sheets import get_sheet_db
    db = get_sheet_db()
    data = db.get_all_records()
    
    unpaid = [row for row in data if str(row.get("Status", "")).lower() == "pending"]
    total_unpaid = sum([float(u.get("Amount", 0)) for u in unpaid if str(u.get("Amount", "")).replace(".","").isdigit()])
    
    log = f"Scanned {len(data)} rows. Found {len(unpaid)} unpaid invoices totaling ${total_unpaid}."
    
    return {
        "ledger_data": data,
        "unpaid_invoices": unpaid,
        "logs": [log]
    }

# 2. Analyze Risk Node (The "CFO Persona")
def analyze_risk(state: AgentState):
    print("🤔 [Agent] Analyzing Risk...")
    unpaid_count = len(state["unpaid_invoices"])
    risks = []
    logs = []
    
    # Simple logic + LLM flavor
    if unpaid_count > 2:
        risks.append("High Receivables Risk")
        logs.append("Identified High Receivables Risk: Too many pending invoices.")
    
    # Mocking "Burn Rate" check
    # In real app, we check dates of expenses
    if random.random() > 0.7:
        risks.append("Accelerated Burn Rate")
        logs.append("Flagged: Expenses are 15% higher than last week.")

    return {
        "risks": risks,
        "logs": logs
    }

# 3. Draft Email Node
def draft_email(state: AgentState):
    # Only if we have unpaid invoices
    if not state["unpaid_invoices"]:
        return {"emails_to_send": [], "logs": ["No unpaid invoices to chase."]}
    
    print("✍️ [Agent] Drafting Emails...")
    emails = []
    for inv in state["unpaid_invoices"]:
        # Mock Email Content
        vendor = inv.get("Vendor", "Client")
        amount = inv.get("Amount", "0")
        
        email = {
            "to": "client@example.com", # In real app, from vendor list
            "subject": f"Overdue Invoice: {vendor} - ${amount}",
            "body": f"Hi there, just a friendly reminder about the invoice for {vendor}..."
        }
        emails.append(email)
    
    return {
        "emails_to_send": emails,
        "logs": [f"Drafted {len(emails)} follow-up emails."]
    }

# Edge Logic
def should_draft_email(state: AgentState):
    if len(state["unpaid_invoices"]) > 0:
        return "draft_email"
    return END

# Build Graph
flow = StateGraph(AgentState)

flow.add_node("scan_ledger", scan_ledger)
flow.add_node("analyze_risk", analyze_risk)
flow.add_node("draft_email", draft_email)

flow.set_entry_point("scan_ledger")

flow.add_edge("scan_ledger", "analyze_risk")
flow.add_conditional_edges(
    "analyze_risk",
    should_draft_email,
    {
        "draft_email": "draft_email",
        END: END
    }
)
flow.add_edge("draft_email", END)

app_graph = flow.compile()
