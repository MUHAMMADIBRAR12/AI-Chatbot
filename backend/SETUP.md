# Backend Setup Instructions

## Environment Variables

Create a `.env` file in the backend directory with your Gemini API key:

```
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

## Getting a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click "Get API Key" 
4. Create a new API key
5. Copy the key and add it to your `.env` file

## Running the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Troubleshooting

- If you see "GEMINI_API_KEY is not configured" error, make sure your `.env` file is in the backend directory
- If you see "Illegal header value" errors, your API key might be invalid or expired
- Make sure your API key has the necessary permissions for the Gemini API
