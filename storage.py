from typing import List, Optional
from models import Offer, Lead, ScoreResult

_offer: Optional[Offer] = None
_leads: List[Lead] = []
_results: List[ScoreResult] = []


def set_offer(offer: Offer) -> None:
    global _offer
    _offer = offer


def get_offer() -> Optional[Offer]:
    return _offer


def set_leads(leads: List[Lead]) -> None:
    global _leads
    _leads = list(leads)


def get_leads() -> List[Lead]:
    return list(_leads)


def set_results(results: List[ScoreResult]) -> None:
    global _results
    _results = list(results)


def get_results() -> List[ScoreResult]:
    return list(_results)


def clear_results():
    global _results
    _results = []
