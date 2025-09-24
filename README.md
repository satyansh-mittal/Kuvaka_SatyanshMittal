# Lead Intent Scoring API

Backend service that accepts Offer info + a CSV of leads and scores each lead’s buying intent using rule-based logic (0–50) + AI reasoning (0–50).

Tech: Python, FastAPI, Streamlit (tester UI), Groq API (`model=openai/gpt-oss-20b`).

Note: Assignment mentions Ollama `phi-4-mini`. I used Groq’s hosted model as requested; swapping to Ollama is straightforward (same prompt and mapping).

---

## Live URLs (replace with yours)
- API base URL: `https://<your-api>.onrender.com`
- Streamlit UI: `https://<your-streamlit-app>.streamlit.app`

---

## Setup (local)
1) Python 3.10+
2) Install deps:
```powershell
pip install -r requirements.txt
```
3) Env vars: copy `.env.example` to `.env` and set a key (prefers `GROQ_API_KEY`, fallback `GROK_API_KEY`):
```
GROQ_API_KEY=your_key_here
```
4) Run API:
```powershell
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
5) Optional UI:
```powershell
streamlit run streamlit_app.py
```
`streamlit_app.py` uses `API_BASE_URL` secret/env or defaults to `http://localhost:8000`.

---

## CSV Format
Required columns: `name,role,company,industry,location,linkedin_bio`

Sample: `sample_leads.csv`

---

## API Reference

### POST `/offer`
Set product/offer context

Request body
```json
{
  "name": "AI Outreach Automation",
  "value_props": ["24/7 outreach", "6x more meetings"],
  "ideal_use_cases": ["B2B SaaS mid-market"]
}
```

Response: 200 OK (echoes offer)

curl
```bash
curl -X POST $API/offer -H "Content-Type: application/json" -d '{
  "name": "AI Outreach Automation",
  "value_props": ["24/7 outreach", "6x more meetings"],
  "ideal_use_cases": ["B2B SaaS mid-market"]
}'
```

Postman
- Method: POST
- URL: `$API/offer`
- Body: raw JSON (same as above)

---

### POST `/leads/upload`
Upload CSV of leads.

Form-data
- Key: `file` (type File) → select CSV

curl
```bash
curl -X POST $API/leads/upload -F "file=@sample_leads.csv"
```

Postman
- Method: POST
- URL: `$API/leads/upload`
- Body: form-data → key `file`, type File, choose CSV

---

### POST `/score`
Run scoring on uploaded leads.

Response: `ScoreResult[]`
```json
[
  {
    "name": "Ava Patel",
    "role": "Head of Growth",
    "company": "FlowMetrics",
    "industry": "B2B SaaS mid-market",
    "location": "San Francisco",
    "intent": "High",
    "score": 85,
    "reasoning": "Fits ICP SaaS mid-market and role is decision maker."
  }
]
```

curl
```bash
curl -X POST $API/score
```

Postman
- Method: POST
- URL: `$API/score`

---

### GET `/results`
Fetch last scoring results (JSON array).

curl
```bash
curl $API/results
```

### GET `/results.csv` (Bonus)
Export results as CSV.

curl
```bash
curl -L $API/results.csv -o results.csv
```

---

## Scoring Logic & Prompt

Rule layer (max 50)
- Role relevance: decision maker +20 (CEO, Founder, Head/VP Growth/Marketing/Sales, etc.), influencer +10 (Marketing/Growth/Product/RevOps/BD/SalOps), else 0.
- Industry match: if any `ideal_use_cases` token appears in lead industry or bio → +20; else if adjacent (broad tech/SaaS terms like `saas`, `software`, `technology`, `b2b`, `startup`, `mid-market`, `enterprise`) → +10; else 0.
- Data completeness: all required fields present → +10.

AI layer (max 50)
- Provider: Groq Chat Completions API
- Model: `openai/gpt-oss-20b`
- Prompt summary: System asks assistant to classify buying intent (High/Medium/Low) for the offer + lead context with concise reasoning (1–2 sentences).
- Mapping: High = 50, Medium = 30, Low = 10.
- Final Score = `rule_score + ai_points` (clamped 0–100).

If AI is not configured or errors, defaults to `Low` with a short explanation.

---

## Deployment

Backend (Render)
1) New Web Service → connect repo
2) Build command: `pip install -r requirements.txt`
3) Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4) Environment variables: `GROQ_API_KEY` (or `GROK_API_KEY`)
5) Deploy and copy base URL → use it in Streamlit

Frontend (Streamlit Cloud)
1) New app → repo → main file: `streamlit_app.py`
2) Secrets:
```
API_BASE_URL = "https://<your-api>.onrender.com"
```
3) Deploy

Procfile (for platforms like Render/Heroku)
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

## Dev Notes
- Everything is in-memory (offer, leads, results). Restart clears state.
- Minimal code footprint; easy to extend to a DB if needed.
- Streamlit tester is optional but handy for demos.

## Demo (optional)
Add a Loom link here showing offer upload → CSV upload → score → results.


## Notes
- Everything is in-memory by design for speed. Restarting the process clears state.
- Keep commit history clean; this repo demonstrates endpoints and logic per the assignment.