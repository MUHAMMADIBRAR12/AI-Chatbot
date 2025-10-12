import os
from typing import List, Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import json
import datetime as dt

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY environment variable not set. Chat functionality will be disabled.")
else:
    genai.configure(api_key=GEMINI_API_KEY)


class Message(BaseModel):
    role: str  # "user" | "bot" | "system"
    text: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = None


class ChatResponse(BaseModel):
    reply: str
    history: List[Message]


app = FastAPI(title="OrderBot API", version="1.0.0")

# CORS (adjust allowed origins as needed)
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
vercel_url = os.getenv("FRONTEND_ORIGIN")
if vercel_url:
    allowed_origins.append(vercel_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


INITIAL_INSTRUCTION = (
    "You are OrderBot, an automated service to collect orders for a pizza restaurant. "
    "You first greet the customer, then collect the order and ask if it's pickup or delivery. "
    "You wait to collect the entire order, summarize it, and check for final additions. "
    "If delivery, you ask for an address. Finally, you collect the payment. "
    "Menu: Pepperoni Pizza (L 12.95, M 10.00, S 7.00), Cheese Pizza (L 10.95, M 9.25, S 6.50), "
    "Eggplant Pizza (L 11.95, M 9.75, S 6.75), Fries (L 4.50, S 3.50), Greek Salad 7.25, "
    "Toppings: Extra Cheese 2.00, Mushrooms 1.50, Sausage 3.00, Canadian Bacon 3.50, AI Sauce 1.50, Peppers 1.00, "
    "Drinks: Coke (L 3.00, M 2.00, S 1.00), Sprite (L 3.00, M 2.00, S 1.00), Bottled Water 5.00. "
    "Respond in a friendly, conversational style."
)


# --- Persistence helpers ---
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.jsonl")

def _ensure_history_file_exists():
    try:
        base_dir = os.path.dirname(HISTORY_FILE)
        if base_dir and not os.path.exists(base_dir):
            os.makedirs(base_dir, exist_ok=True)
        if not os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "w", encoding="utf-8") as _:
                pass
    except Exception:
        pass

def log_message(role: str, text: str):
    _ensure_history_file_exists()
    try:
        record = {
            "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
            "role": role,
            "text": text,
        }
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        # Avoid breaking UX on logging issues
        pass

def load_history_for_date(target_date: dt.date):
    entries = []
    if not os.path.exists(HISTORY_FILE):
        return entries
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    ts = rec.get("timestamp")
                    if not ts:
                        continue
                    d = dt.datetime.fromisoformat(ts).date()
                    if d == target_date:
                        entries.append(rec)
                except Exception:
                    continue
    except Exception:
        return []
    return entries


def to_gemini_history(messages: List[Message]):
    # Gemini expects a list of {role, parts:[{text}]}
    gem_history = []
    for m in messages:
        role = "user" if m.role == "user" else "model"
        gem_history.append({"role": role, "parts": [{"text": m.text}]})
    return gem_history


@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    if not GEMINI_API_KEY:
        return ChatResponse(
            reply="❌ Server Error: GEMINI_API_KEY is not configured. Please set the GEMINI_API_KEY environment variable.",
            history=req.history or [],
        )

    # Provide the system instruction via the model configuration so it reliably
    # conditions the chat regardless of how the turn history is filtered.
    # Pass system instruction using the Content format Gemini expects
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=[{"text": INITIAL_INSTRUCTION}],
    )

    # Build history
    history: List[Message] = []
    if req.history:
        # Keep client-provided history as-is (may or may not include a system role)
        history.extend(req.history)

    # Add the new user message
    history.append(Message(role="user", text=req.message))
    log_message("user", req.message)

    try:
        # Start chat with user/model turns only; system instruction is configured on the model
        chat = model.start_chat(history=to_gemini_history([m for m in history if m.role != "system"]))
        # Apply a short timeout so requests don't hang indefinitely
        response = chat.send_message(
            req.message,
            request_options={"timeout": 15},
        )
        reply_text = getattr(response, "text", None) or "Sorry, I couldn't generate a response."
    except Exception as e:
        print(f"Gemini API Error: {e}")
        reply_text = f"❌ AI Error: {str(e)}. Please check your GEMINI_API_KEY and try again."

    # Append assistant reply to history
    history.append(Message(role="bot", text=reply_text))
    log_message("bot", reply_text)

    # Return reply and updated history
    return ChatResponse(reply=reply_text, history=history)


@app.get("/api/history", response_model=List[Message])
def get_history(
    year: int = Query(..., description="Year of the history to retrieve"),
    month: int = Query(..., description="Month of the history to retrieve"),
    day: int = Query(..., description="Day of the history to retrieve"),
):
    try:
        target_date = dt.date(year, month, day)
        logged_messages = load_history_for_date(target_date)
        return [Message(**m) for m in logged_messages]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date provided: {e}")


@app.post("/api/clear_history")
def clear_history_endpoint():
    try:
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        return {"detail": "Chat history cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear chat history: {e}")


@app.get("/healthz")
def healthz():
    return {"ok": True}


