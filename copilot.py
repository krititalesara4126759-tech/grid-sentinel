"""
copilot.py — The AI decision layer.
- retrieve():   lightweight RAG over sop_docs/ (production: Vertex AI Search)
- local_answer(): deterministic reasoning engine grounded on live sim state (demo mode)
- gemini_answer(): live Gemini call grounded on the same state (set GEMINI_API_KEY)
"""
import os, glob, requests

SOP_DIR = os.path.join(os.path.dirname(__file__), "sop_docs")

def _load_sops():
    docs = {}
    for p in glob.glob(os.path.join(SOP_DIR, "*.md")):
        docs[os.path.basename(p)] = open(p, encoding="utf-8").read()
    return docs

SOPS = _load_sops()

def retrieve(query):
    """Keyword-scored retrieval over the SOP corpus. Returns [(filename, text, score)]."""
    q = set(query.lower().replace("-", " ").split())
    scored = []
    for name, text in SOPS.items():
        words = set(text.lower().replace("-", " ").split())
        score = len(q & words)
        if score:
            scored.append((name, text, score))
    scored.sort(key=lambda x: -x[2])
    return scored[:2]

def _fmt(n, d=1):
    return f"{n:.{d}f}"

def state_summary(s):
    fl = "; ".join(f"{f['id']} {f['name']} {f['status']} load {_fmt(f['load'])}/{f['cap']}MW temp {f['temp']:.0f}C"
                   for f in s["feeders"])
    trips = " | ".join(t["when"] + " " + t["cause"] for t in s["f7_trips"])
    return (f"City load {_fmt(s['total_load'])} MW, ambient {s['ambient']}C heatwave, N-1 limit {s['n1_limit']} MW. "
            f"Feeders: {fl}. Reservoir {s['water']:.0f}%. F7 trip history: {trips}")

def local_answer(q, s):
    ql = q.lower()
    f4 = s["feeders"][3]; f5 = s["feeders"][4]

    if any(k in ql for k in ("feeder 7", "f7", "trip")):
        trips = "".join(f"<br>• <b>{t['when']}</b> — {t['cause']} ({t['dur']})" for t in s["f7_trips"])
        return {"a": f"<b>Feeder 7 (Ambamata) — trip analysis.</b> 3 trips in 4 days:{trips}<br><br>"
                     f"Pattern: two over-current trips at evening peak, then an earth fault on the same span. "
                     f"AI assessment: <b>progressive cable insulation failure</b> (span P-114→P-117), accelerated by peak thermal stress."
                     f"<div class='reco'>Isolate span P-114→P-117, megger test before re-energisation (SOP-EL-09). "
                     f"Backfeed ~9 MW via F5 Hiranmagri ({_fmt(f5['cap']-f5['load'])} MW headroom). Replace cable within 48h.</div>",
                "src": "SCADA event log · relay DR records · SOP-EL-09 (RAG) · load-flow calc"}

    if any(k in ql for k in ("overload", "risk", "heatwave", "tomorrow", "transformer")):
        return {"a": f"<b>Overload risk (next 24h, heatwave-adjusted):</b><br><br>"
                     f"1. <b>XFMR T-4 Sukher</b> — <em>CRITICAL</em>: oil {f4['temp']:.0f}°C, "
                     f"{f4['load']/f4['cap']*100:.0f}% loaded, cooling degradation suspected.<br>"
                     f"2. <b>F5 Hiranmagri</b> — elevated if backfeeding F7 at peak.<br>"
                     f"3. <b>F2 Fatehpura</b> — evening AC peak.<br><br>"
                     f"Forecast peak ~{s['total_load']+9:.0f} MW vs N-1 limit {s['n1_limit']} MW — thin margin if T-4 is lost."
                     f"<div class='reco'>Verify T-4 cooling (SOP-TR-03), shed 20% Sukher industrial load 17:00–20:00, "
                     f"pre-position mobile transformer tonight → converts a 6h blackout into a zero-outage event.</div>",
                "src": "Transformer health model · weather-coupled forecast · SOP-TR-03 (RAG)"}

    if "water" in ql or "reservoir" in ql:
        return {"a": f"<b>Water system.</b> Reservoir at <em>{s['water']:.0f}%</em> under summer draw. "
                     f"Pumping is the 2nd-largest grid load (~11% of city MW)."
                     f"<div class='reco'>Shift 60% of pumping to 23:00–06:00 (saves ~4 MW at peak), "
                     f"prepare Fateh Sagar secondary intake (SOP-WS-02), push conservation advisory proactively.</div>",
                "src": "Reservoir telemetry · pump load profile · SOP-WS-02 (RAG)"}

    if any(k in ql for k in ("procedure", "sop", "earth fault", "fault")):
        hits = retrieve(q if len(q.split()) > 1 else "earth fault megger")
        body = "<br><br>".join(f"<em>{n}</em><br>" + t.replace("\n", "<br>") for n, t, _ in hits) or "No matching SOP."
        return {"a": f"<b>Relevant SOP retrieved (RAG):</b><br><br>{body}",
                "src": "sop_docs/ corpus — keyword retrieval (production: Vertex AI Search)"}

    if "report" in ql or "incident" in ql:
        return {"a": "<b>Incident report drafted</b> from live SCADA data — "
                     "<a class='dl' href='/api/report' target='_blank'>⬇ download incident_report_F7.txt</a>"
                     "<div class='reco'>In production an ADK agent files this automatically and notifies the AE/SE.</div>",
                "src": "Generated from: SCADA event log · restoration timeline · asset register"}

    if any(k in ql for k in ("compare", "headroom", "loading")):
        rows = "".join(
            f"<br>• <b>{f['id']}</b> — " + ("<em>TRIPPED</em>" if f["status"] == "TRIP"
            else f"{_fmt(f['load'])}/{f['cap']} MW ({f['load']/f['cap']*100:.0f}%) · headroom {_fmt(f['cap']-f['load'])} MW · {f['temp']:.0f}°C")
            for f in s["feeders"])
        return {"a": f"<b>Feeder comparison:</b>{rows}<div class='reco'>Reserve F5 headroom for the F7 backfeed; "
                     f"shift ~2 MW Sukher industrial load to F8 via the 11kV tie.</div>",
                "src": "Live SCADA loading · network topology"}

    return {"a": "I'm watching the whole grid in real time. Ask about <b>Feeder 7</b>, <b>overload risk</b>, "
                 "<b>water</b>, <b>SOPs</b>, <b>feeder comparison</b>, or <b>draft the incident report</b>.",
            "src": "Demo engine · production: Gemini 2.x on Vertex AI"}

def gemini_answer(q, s, key):
    body = {"contents": [{"parts": [{"text":
        "You are GRID SENTINEL, an AI copilot for a city utility control room in Udaipur. "
        "Answer the operator concisely with specific numbers and one recommended action. "
        "Live grid state: " + state_summary(s) +
        "\nRelevant SOPs: " + " | ".join(n + ": " + t[:300] for n, t, _ in retrieve(q)) +
        "\n\nOperator question: " + q}]}]}
    models = ["gemini-flash-latest", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    last_err = ""
    for m in models:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key=" + key,
            json=body, timeout=30)
        if r.ok:
            text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            return {"a": text.replace("\n", "<br>"),
                    "src": f"Live Gemini ({m}) · grounded on real-time grid state + RAG"}
        try:
            last_err = f"{r.status_code}: " + r.json().get("error", {}).get("message", r.text[:150])
        except Exception:
            last_err = f"{r.status_code}: {r.text[:150]}"
    raise RuntimeError(last_err)
