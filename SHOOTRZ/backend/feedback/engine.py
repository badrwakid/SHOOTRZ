from typing import List, Dict
from .rules import rules_from_metrics


def generate_feedback(metrics: List[Dict], enrich: bool = False) -> List[Dict]:
    return rules_from_metrics(metrics, enrich=enrich)








