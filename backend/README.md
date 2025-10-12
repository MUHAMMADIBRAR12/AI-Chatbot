# OrderBot FastAPI Backend

## Local run

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:GEMINI_API_KEY="YOUR_KEY"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- POST `/api/chat` → `{ message, history? }` returns `{ reply, history }`
- GET `/healthz` → `{ ok: true }`

## Deploy
- Render/Railway: set start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Set env: `GEMINI_API_KEY`


