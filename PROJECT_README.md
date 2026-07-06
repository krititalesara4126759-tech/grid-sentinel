# GRID SENTINEL — Control Room Copilot (Full Project)
AI-powered Decision Intelligence Platform for city utility control rooms.
Built by Team Pyrotech (Udaipur) for the Gen AI Academy APAC hackathon (Google Cloud / Hack2skill).

## What it does
Operators ask the grid questions in plain language ("Why did Feeder 7 trip?") and get
root-cause analysis, 24h risk forecasts, retrieved SOPs (RAG), citizen-impact assessment
and auto-drafted incident reports — grounded in live telemetry, with sources.

## Project structure
```
grid-sentinel-pro/
├── app.py                     # Flask server + REST API
├── simulator.py               # Live grid telemetry (stands in for Pub/Sub→BigQuery)
├── copilot.py                 # AI layer: RAG retrieval + reasoning + Gemini integration
├── agents/
│   └── incident_agent.py      # ADK-style agent: auto-drafts incident reports
├── sop_docs/                  # SOP corpus for RAG (production: Vertex AI Search)
│   ├── SOP-EL-07_overcurrent.md
│   ├── SOP-EL-09_earthfault.md
│   ├── SOP-TR-03_transformer_temp.md
│   └── SOP-WS-02_reservoir_low.md
├── static/index.html          # Operator console (mimic diagram, alarms, forecast, chat)
├── standalone_demo.html       # Zero-install single-file demo (for offline/video use)
├── requirements.txt
└── Dockerfile                 # Cloud Run ready
```

## Run locally (2 commands)
```bash
pip install -r requirements.txt
python app.py            # open http://localhost:8080
```

## Enable live Gemini answers (optional)
Get a free key at https://aistudio.google.com/apikey then:
```bash
# Windows (PowerShell):   $env:GEMINI_API_KEY="YOUR_KEY"; python app.py
# Linux/Mac:              GEMINI_API_KEY=YOUR_KEY python app.py
```
Without a key, a deterministic demo engine answers using the same live grid state
(safer for recorded demos — identical UX).

## Deploy to Google Cloud Run
```bash
gcloud run deploy grid-sentinel --source . --region asia-south1 \
  --allow-unauthenticated --set-env-vars GEMINI_API_KEY=YOUR_KEY
```

## API
| Endpoint | Method | Purpose |
|---|---|---|
| `/api/state` | GET | Live grid snapshot (feeders, alarms, history, forecast) |
| `/api/ask` | POST `{"q":"..."}` | Copilot answer (Gemini if key set, else demo engine) |
| `/api/report` | GET | Auto-drafted incident report (agent) |

## Production architecture (Google Cloud)
Pub/Sub + Dataflow → BigQuery → Gemini 2.x on Vertex AI (+ Vertex AI Search RAG over SOPs,
BigQuery ML forecasting) → ADK agents (reports/escalation/demand response) → Cloud Run app.
`simulator.py` and the keyword retriever in `copilot.py` are the swap-out points —
the API contract and frontend stay identical.
