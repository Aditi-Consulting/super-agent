from flask import Flask, jsonify, request
from graph.graph_builder import build_graph
import json
import os
import sys
import threading
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("super-agent")

app_flask = Flask(__name__)

POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL_SECONDS", "15"))


@app_flask.route('/invoke', methods=['POST'])
def invoke():
    data = request.get_json() or {}
    alert_id = data.get("alertId") or data.get("alert_id")
    graph = build_graph()
    app = graph.compile()
    result = app.invoke({"alert_id": alert_id})
    return jsonify(result)


def poll_and_classify():
    """Background poller that picks up unclassified alerts from DB."""
    from store.db import fetch_unprocessed

    while True:
        try:
            rows = fetch_unprocessed(limit=10)
            if rows:
                logger.info("Poller found %d unclassified alert(s)", len(rows))
                for row in rows:
                    try:
                        graph = build_graph()
                        app = graph.compile()
                        app.invoke({"alert_id": row["id"]})
                        logger.info("Classified alert id=%s", row["id"])
                    except Exception as e:
                        logger.error("Failed to classify alert id=%s: %s", row["id"], e)
        except Exception as e:
            logger.error("Poller error: %s", e)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'serve':
        poller = threading.Thread(target=poll_and_classify, daemon=True)
        poller.start()
        logger.info("Poller started — checking every %ds for unclassified alerts", POLL_INTERVAL)
        app_flask.run(host='0.0.0.0', port=5000)
    else:
        graph = build_graph()
        app = graph.compile()
        result = app.invoke({})
        print("Processing Done.")
        print(json.dumps(result.get("classified", []), indent=2))