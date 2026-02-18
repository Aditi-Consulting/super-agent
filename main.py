from flask import Flask, jsonify, request
from graph.graph_builder import build_graph
# from flask_cors import CORS
import json
import sys

app_flask = Flask(__name__)
# CORS(app_flask, origins=["http://localhost:3000","http://localhost:8083"])

@app_flask.route('/invoke', methods=['POST'])
def invoke():
    data = request.get_json() or {}
    # Accept both "alertId" and "alert_id" for compatibility
    alert_id = data.get("alertId") or data.get("alert_id")
    graph = build_graph()
    app = graph.compile()
    result = app.invoke({"alert_id": alert_id})
    return jsonify(result)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'serve':
        app_flask.run(host='0.0.0.0', port=5000)
    else:
        graph = build_graph()
        app = graph.compile()
        result = app.invoke({})
        print("Processing Done.")
        print(json.dumps(result.get("classified", []), indent=2))