import os
import io
import csv
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from models import Offer, Lead, ScoreResult
from storage import set_offer, get_offer, set_leads, get_leads, set_results, get_results, clear_results
from scoring import run_scoring_pipeline


# Load environment variables early
load_dotenv()

app = FastAPI(title="Lead Intent Scoring API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"]
    ,allow_headers=["*"]
)


class OfferIn(BaseModel):
    name: str
    value_props: List[str] = Field(default_factory=list)
    ideal_use_cases: List[str] = Field(default_factory=list)


@app.post("/offer", response_model=Offer)
def post_offer(body: OfferIn):
    offer = Offer(**body.dict())
    set_offer(offer)
    # reset previous results if offer changes to avoid stale context
    clear_results()
    return offer


@app.post("/leads/upload")
async def upload_leads(file: UploadFile = File(...)):
    if not (file.filename and file.filename.lower().endswith(".csv")):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")

    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")  # tolerate BOM
    except UnicodeDecodeError:
        # try latin-1 as a lenient fallback
        text = raw.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    required = ["name", "role", "company", "industry", "location", "linkedin_bio"]
    for r in required:
        if r not in (reader.fieldnames or []):
            raise HTTPException(status_code=400, detail=f"Missing column: {r}")

    leads: List[Lead] = []
    for row in reader:
        # normalize missing keys to empty strings
        data = {k: (row.get(k) or "").strip() for k in required}
        leads.append(Lead(**data))

    if not leads:
        raise HTTPException(status_code=400, detail="No leads found in CSV.")

    set_leads(leads)
    # uploading new leads invalidates prior results
    clear_results()
    return {"count": len(leads)}


@app.post("/score", response_model=List[ScoreResult])
def score_now():
    offer = get_offer()
    if not offer:
        raise HTTPException(status_code=400, detail="Offer not set. POST /offer first.")
    leads = get_leads()
    if not leads:
        raise HTTPException(status_code=400, detail="No leads uploaded. POST /leads/upload first.")

    results = run_scoring_pipeline(offer, leads)
    set_results(results)
    return results


@app.get("/results", response_model=List[ScoreResult])
def get_results_json():
    return get_results()


@app.get("/results.csv")
def get_results_csv():
    results = get_results()
    if not results:
        raise HTTPException(status_code=404, detail="No results yet. Run POST /score first.")

    def _iter():
        out = io.StringIO()
        cols = [
            "name",
            "role",
            "company",
            "industry",
            "location",
            "intent",
            "score",
            "reasoning",
        ]
        writer = csv.DictWriter(out, fieldnames=cols)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "name": r.name,
                "role": r.role,
                "company": r.company,
                "industry": r.industry,
                "location": r.location,
                "intent": r.intent,
                "score": r.score,
                "reasoning": r.reasoning,
            })
            yield out.getvalue()
            out.seek(0)
            out.truncate(0)

    return StreamingResponse(_iter(), media_type="text/csv", headers={
        "Content-Disposition": "attachment; filename=results.csv"
    })


@app.get("/")
def root():
    return {"ok": True, "endpoints": [
        "POST /offer",
        "POST /leads/upload",
        "POST /score",
        "GET /results",
        "GET /results.csv"
    ]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)
