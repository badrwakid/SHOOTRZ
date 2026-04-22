# Gemini Setup Guide

## Prerequisites

- Python 3.10+
- A Google AI Studio API key (free tier available)

## 1. Get a Gemini API Key

1. Visit [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key

## 2. Configure Environment Variables

Edit `backend/.env`:

```env
# Required
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Optional (defaults shown)
GEMINI_TIMEOUT=60
GEMINI_MAX_RETRIES=3
```

### Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | — | Google AI Studio API key |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Model identifier |
| `GEMINI_TIMEOUT` | No | `60` | Request timeout in seconds |
| `GEMINI_MAX_RETRIES` | No | `3` | Max retry attempts for 429/5xx |

## 3. Install Dependencies

```bash
cd SHOOTRZ/backend
pip install -r requirements.txt
```

The `google-genai` package is the official Google GenAI SDK. It replaces the
deprecated `google-generativeai` package and the previous raw REST approach.

## 4. Verify Setup

Start the server and check the health endpoint:

```bash
uvicorn backend.main:app --reload
curl http://localhost:8000/health
```

The response should include:
```json
{
  "gemini_configured": true,
  "gemini_model": "gemini-2.5-flash"
}
```

## 5. Security Notes

- **Never commit API keys.** The `.env` file is gitignored.
- The API key is passed via the `google-genai` SDK client, not in URL parameters.
- Rate limit handling (429) is built into `GeminiService` with exponential backoff.
- All Gemini calls have deterministic fallbacks — the app works without a valid key
  (it just returns rule-based text instead of LLM-generated content).

## 6. Rate Limits (Free Tier)

As of 2026, the Gemini free tier allows:
- 15 requests per minute (RPM)
- 1 million tokens per minute (TPM)
- 1,500 requests per day (RPD)

For production use, enable billing in Google AI Studio for higher quotas.

## Removed Configuration

The following environment variables are no longer used:
- `OPENAI_API_KEY` — OpenAI path removed
- `OPENAI_MODEL` — OpenAI path removed
- `LLM_PROVIDER` — Single-provider architecture (Gemini only)
