import os
from typing import List, Tuple

import requests

from models import Offer, Lead, ScoreResult


def _normalize(s: str) -> str:
    return (s or "").strip().lower()


DECISION_MAKER_TITLES = {
    "founder",
    "co-founder",
    "ceo",
    "chief executive",
    "cto",
    "cpo",
    "head of growth",
    "vp growth",
    "vp marketing",
    "head of marketing",
    "director of marketing",
    "growth lead",
    "product lead",
    "head of sales",
    "vp sales",
}

INFLUENCER_TITLES = {
    "growth",
    "marketing",
    "demand generation",
    "product",
    "revenue operations",
    "sales operations",
    "business development",
}


def score_role(role: str) -> int:
    r = _normalize(role)
    for t in DECISION_MAKER_TITLES:
        if t in r:
            return 20
    for t in INFLUENCER_TITLES:
        if t in r:
            return 10
    return 0


def score_industry(offer: Offer, lead: Lead) -> int:
    
    industry = _normalize(lead.industry)
    bio = _normalize(lead.linkedin_bio)
    exact = False
    adjacent = False

    for icp in offer.ideal_use_cases:
        tok = _normalize(icp)
        if tok and (tok in industry or tok in bio):
            exact = True
            break

    if not exact:
        
        broad = ["saas", "software", "technology", "b2b", "startup", "mid-market", "enterprise"]
        for b in broad:
            if b in industry or b in bio:
                adjacent = True
                break

    if exact:
        return 20
    if adjacent:
        return 10
    return 0


def score_completeness(lead: Lead) -> int:
    fields = [lead.name, lead.role, lead.company, lead.industry, lead.location, lead.linkedin_bio]
    return 10 if all(bool((f or "").strip()) for f in fields) else 0


def rule_score(offer: Offer, lead: Lead) -> int:
    return min(50, score_role(lead.role) + score_industry(offer, lead) + score_completeness(lead))


class _GroqClient:
    def __init__(self):
        # Prefer GROQ_API_KEY; allow GROK_API_KEY as fallback
        self.api_key = os.getenv("GROQ_API_KEY") or os.getenv("GROK_API_KEY")
        self.base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

    def classify(self, offer: Offer, lead: Lead) -> Tuple[str, str]:
        if not self.api_key:
            return ("Low", "AI not configured; defaulting to Low.")

        system = (
            "You are a helpful B2B sales assistant. Classify lead buying intent"
            " as High, Medium, or Low for the given offer. Keep reasoning concise."
        )
        user = (
            f"Offer: {offer.name}\n"
            f"Value Props: {', '.join(offer.value_props)}\n"
            f"Ideal Use Cases: {', '.join(offer.ideal_use_cases)}\n\n"
            f"Lead name: {lead.name}\n"
            f"Role: {lead.role}\n"
            f"Company: {lead.company}\n"
            f"Industry: {lead.industry}\n"
            f"Location: {lead.location}\n"
            f"LinkedIn bio: {lead.linkedin_bio}\n\n"
            "Task: Classify intent as High, Medium, or Low and explain in 1–2 sentences."
        )
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "openai/gpt-oss-20b",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.2,
                "max_tokens": 200,
            }
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=30,
            )
            if not resp.ok:
                return ("Low", "AI unavailable; defaulted to Low.")
            data = resp.json()
            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
        except Exception:
            # Avoid leaking environment/errors to client
            return ("Low", "AI error; defaulted to Low.")

        text = content.strip().lower()
        intent = "Low"
        if "high" in text:
            intent = "High"
        elif "medium" in text:
            intent = "Medium"
        reasoning = content.strip()
        return intent, reasoning


def ai_points(intent: str) -> int:
    return {"High": 50, "Medium": 30, "Low": 10}.get(intent, 10)


def run_scoring_pipeline(offer: Offer, leads: List[Lead]) -> List[ScoreResult]:
    groq = _GroqClient()
    results: List[ScoreResult] = []
    for lead in leads:
        rules = rule_score(offer, lead)
        intent, reasoning = groq.classify(offer, lead)
        total = max(0, min(100, rules + ai_points(intent)))
        results.append(ScoreResult(
            name=lead.name,
            role=lead.role,
            company=lead.company,
            industry=lead.industry,
            location=lead.location,
            intent=intent,
            score=total,
            reasoning=reasoning,
        ))
    return results
