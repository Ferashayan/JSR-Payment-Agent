# JSR-Payment-Agent 🤖
.\venv\Scripts\uvicorn app.main:app --reload --port 8000


**Jisr AI Assistant** — A FastAPI + LangChain backend agent specialized in Saudi payroll management, GOSI, and Mudad systems.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Runtime | Python 3.10+ |
| Framework | FastAPI |
| AI Agent | LangChain 0.3 + Gemini 2.5 Flash |
| Schemas | Pydantic v2 |
| Streaming | SSE via `sse-starlette` |
| Config | python-dotenv |

## Project Structure

```
JSR-Payment-Agent/
├── app/
│   ├── main.py                 # FastAPI entry point
│   ├── api/
│   │   └── v1/
│   │       └── chat.py         # Chat endpoints (streaming + non-streaming)
│   ├── agent/
│   │   ├── assistant.py        # LangChain agent definition & executor
│   │   ├── tools.py            # Function-calling tools (payroll data)
│   │   └── prompts.py          # System prompt for Jisr AI
│   └── data/
│       └── mock_data.json      # Mock employee & payroll records
├── .env.example                # Environment variables template
├── .gitignore
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Create virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### 4. Run the server
```bash
uvicorn app.main:app --reload --port 8000
```

Or directly:
```bash
python -m app.main
```

### 5. Open the docs
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/` | Health check |
| `GET`  | `/health` | Health status |
| `POST` | `/api/v1/chat/` | Non-streaming chat |
| `POST` | `/api/v1/chat/stream` | SSE streaming chat |

### Chat Request Body
```json
{
  "message": "ما هو إجمالي الرواتب لهذا الشهر؟",
  "session_id": "optional-session-id"
}
```

### SSE Stream Events
- `token` — Individual text chunk: `{"content": "..."}`
- `done` — Stream complete: `{"status": "complete"}`
- `error` — Error occurred: `{"error": "..."}`

## Agent Tools

The AI agent has access to these function-calling tools:

| Tool | Description |
|------|-------------|
| `get_all_employees` | List all employees |
| `get_employee_by_id` | Get employee details by ID |
| `search_employee_by_name` | Search by name (AR/EN) |
| `get_employee_salary` | Salary breakdown |
| `get_payroll_summary` | Monthly payroll totals |
| `get_company_info` | Company/establishment details |
| `get_employees_by_department` | Filter by department |

## License

Private — JSR Technology Solutions
