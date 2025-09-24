# Lead Intent Scoring API (FastAPI)

A small FastAPI backend that ingests an offer definition and a CSV of leads, then scores buying intent using rules (0–50) + AI (0–50) via Groq model `openai/gpt-oss-20b`.

## Features
- POST `/offer` to set the product/offer context
- POST `/leads/upload` to upload a CSV of leads
- POST `/score` to run scoring pipeline (rules + AI)
- GET `/results` to fetch results as JSON
- GET `/results.csv` to export results as CSV

## Setup
1. Create and activate a Python 3.10+ env.
2. Install deps:
```
pip install -r requirements.txt
```
3. Copy `.env.example` to `.env` and set your Groq key:
```
GROQ_API_KEY=your_key_here
```

Run the server:
```
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Run the Streamlit tester:
```
streamlit run streamlit_app.py
```
Optionally set `API_BASE_URL` to point to a deployed backend before launching.

## CSV Format
Columns required: `name,role,company,industry,location,linkedin_bio`.

Use `sample_leads.csv` to test quickly.

## API Examples (curl)
- Set offer
```
curl -X POST http://localhost:8000/offer -H "Content-Type: application/json" -d '{
  "name": "AI Outreach Automation",
  "value_props": ["24/7 outreach", "6x more meetings"],
  "ideal_use_cases": ["B2B SaaS mid-market"]
}'
```

- Upload leads
```
curl -X POST http://localhost:8000/leads/upload -F "file=@sample_leads.csv"
```

- Score
```
curl -X POST http://localhost:8000/score
```

- Results (JSON)
```
curl http://localhost:8000/results
```

- Results (CSV)
```
curl -L http://localhost:8000/results.csv -o results.csv
```

## Scoring Logic
- Rule layer (max 50):
  - Role relevance: decision maker +20 (titles like CEO, Founder, Head of Growth, VP Marketing/Sales), influencer +10 (Marketing/Growth/Product/RevOps etc.), else 0.
  - Industry match: exact ICP token in `ideal_use_cases` found in industry/bio +20; adjacent broad tech/SaaS terms +10; else 0.
  - Data completeness: all required fields present +10.
- AI layer (max 50):
  - Groq chat completion (`openai/gpt-oss-20b`), prompt with offer + lead context.
  - Parse intent from reply: High=50, Medium=30, Low=10. Final score = rules + ai points.

If Groq isn’t configured or errors, AI layer defaults to Low (10) with an explanation.

## Deployment
You can deploy to Render/Railway/Fly/Heroku. Typical Procfile:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

Expose env `GROQ_API_KEY` in your platform dashboard.

### Streamlit Cloud (for the UI)
You can deploy `streamlit_app.py` to Streamlit Cloud and point it at your deployed API.

1) Push this repo to GitHub.
2) In Streamlit Cloud, create a new app from the repo (set the main file to `streamlit_app.py`).
3) Configure Secrets (Settings → Secrets):
```
API_BASE_URL = "https://your-api.onrender.com"
```
4) Save and deploy. The Streamlit app will call your backend.

Note: Streamlit Cloud is ideal for the UI only. The FastAPI backend should run on a server (Render/Railway/etc.) because Streamlit Cloud doesn’t expose a background ASGI server.

## Notes
- Everything is in-memory by design for speed. Restarting the process clears state.
- Keep commit history clean; this repo demonstrates endpoints and logic per the assignment.