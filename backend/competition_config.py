
"""
Competition Configuration Registry
Maps competition IDs to their specific BigQuery tables and UI metadata.
"""

COMPETITIONS = {
    "amo_jan_2026": {
        "title": "MONITORING KOMPETISI AMO",
        "period": "JANUARI 2026",
        "description": "Periode Januari - Juni 2026",
        "tables": {
            "ass": "rank_ass",
            "bm": "rank_bm", 
            "rbm": "rank_rbm"
        }
    }
}

def get_competition_config(competition_id: str):
    return COMPETITIONS.get(competition_id)
