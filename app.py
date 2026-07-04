"""
app.py — Grid Sentinel server.
Endpoints:
  GET  /               operator console (static/index.html)
  GET  /api/state      live grid snapshot (telemetry, alarms, forecast)
  POST /api/ask        {"q": "..."} -> copilot answer (Gemini if GEMINI_API_KEY set, else demo engine)
  GET  /api/report     auto-drafted incident report (agent)
Run:   python app.py          (http://localhost:8080)
Cloud: gcloud run deploy --source .
"""
import os
from flask import Flask, jsonify, request, send_from_directory, Response

from simulator import SIM
import copilot
from agents.incident_agent import draft_incident_report

app = Flask(__name__, static_folder="static")

@app.get("/")
def index():
    return send_from_directory("static", "index.html")

@app.get("/api/state")
def state():
    return jsonify(SIM.snapshot())

def _get_key():
    """Gemini key from env var, or from a gemini_key.txt file next to app.py."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gemini_key.txt")
    if os.path.exists(p):
        return open(p, encoding="utf-8").read().strip()
    return ""

@app.post("/api/ask")
def ask():
    q = (request.get_json(silent=True) or {}).get("q", "").strip()
    if not q:
        return jsonify({"a": "Please ask a question.", "src": ""}), 400
    snap = SIM.snapshot()
    key = _get_key()
    if key:
        try:
            return jsonify(copilot.gemini_answer(q, snap, key))
        except Exception as e:
            ans = copilot.local_answer(q, snap)
            ans["src"] += f" · (Gemini failed — {e} — demo engine used)"
            return jsonify(ans)
    return jsonify(copilot.local_answer(q, snap))

@app.get("/api/report")
def report():
    txt = draft_incident_report(SIM.snapshot())
    return Response(txt, mimetype="text/plain",
                    headers={"Content-Disposition": "attachment; filename=incident_report_F7.txt"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
