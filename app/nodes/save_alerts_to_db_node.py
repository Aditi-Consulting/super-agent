from store.db import ensure_tables, upsert_alert

def save_alerts_to_db_node(state):
    ensure_tables()
    for alert in state["alerts"]:
        upsert_alert(alert)
    return state
