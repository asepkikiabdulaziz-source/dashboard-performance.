"""
Competition Configuration Registry
Maps competition IDs to their specific BigQuery tables and UI metadata.

To disable a competition or table:
- Set "enabled": false in competition config
- Or remove the competition entry entirely
- Or set table name to None to disable specific level
"""

COMPETITIONS = {
    "amo_jan_2026": {
        "title": "MONITORING KOMPETISI AMO",
        "period": "JANUARI 2026",
        "description": "Periode Januari - Juni 2026",
        "enabled": True,  # Set to False to disable this competition
        "tables": {
            "ass": "rank_ass",  # Set to None to disable this level
            "bm": "rank_bm", 
            "rbm": "rank_rbm"
        }
    }
}

def get_competition_config(competition_id: str):
    """Get competition config, returns None if not found or disabled"""
    config = COMPETITIONS.get(competition_id)
    if config and not config.get("enabled", True):
        return None  # Competition is disabled
    return config

def get_available_competitions():
    """Get list of enabled competitions only"""
    return {
        k: v for k, v in COMPETITIONS.items() 
        if v.get("enabled", True)
    }
