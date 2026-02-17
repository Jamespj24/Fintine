# 🔄 Project Handover & Developer Context

> **For Future AI Sessions & Developers**
> This project (`Fintine`) is a Financial AI Agent.
> **Current Focus**: The current session is strictly **BACKEND ONLY**.
> **UI & Testing**: Delegated to other agents/teams.

## 🏗 System State (As of Feb 2026)
- **Backend**: FastAPI (Port 8000). Fully functional.
  - **Auth**: Service Account (`credentials.json`) for Google Sheets.
  - **AI**: Gemini 1.5 Flash (Vision + Text) via `tools/gemini.py`.
  - **Agent**: LangGraph state machine in `graph.py`.
  - **Database**: Google Sheets (Real Mode active).
- **Frontend**: React + Vite (Port 5173). Basic implementation done.
- **Infrastructure**: Dockerized (`docker-compose.yml`).

## 🔑 Key Configuration
- **.env**: Required. Must contain `GEMINI_API_KEY`, `USE_MOCK_SHEETS=false`.
- **credentials.json**: Required for Sheets API.

## 📋 Work Queues (Delegated)

### 🎨 Frontend Team (UI/UX)
**Goal**: Make it look like a "Winning Hackathon Demo".
1.  **Mobile Responsiveness**: Fix `Dashboard.jsx` layout on small screens.
2.  **Streaming Responses**: Connect to backend to show "Agent Thinking..." events in real-time.
3.  **Error Toasts**: Replace `console.error` with UI Toasts (shadcn/ui `useToast`).
4.  **Charts**: Enhancement `Recharts` to use real data from the `/ledger` endpoint instead of mock data.

### 🧪 QA Team (Testing)
**Goal**: 90% Code Coverage.
1.  **E2E Testing**: Use Cypress/Playwright to test the full "Upload -> Audit -> Sheet" flow.
2.  **Edge Cases**: Test uploading non-image files (PDF, CSV) and 100MB+ files.
3.  **Security Audit**: Ensure `verify_sheets.py` doesn't leak info.

## 🧠 Backend / AI Context (Current Session Focus)
We are currently working on **Advanced Logic**.
- **Next Steps**:
  - Implement **Real Email Sending** (currently simulated).
  - Improve **LangGraph Decision Making** (Multi-turn reasoning).
  - Add **Database Caching** (Redis or local JSON) for speed.
