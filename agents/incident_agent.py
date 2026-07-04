"""
agents/incident_agent.py — Agentic workflow demo.
Drafts the incident report from live state. In production this is an ADK agent that
also files the report and notifies engineers via Cloud Functions (email/WhatsApp).
"""
import datetime

def draft_incident_report(state):
    today = datetime.date.today().strftime("%d-%m-%Y")
    f4 = state["feeders"][3]
    return f"""INCIDENT REPORT — AUTO-DRAFTED BY GRID SENTINEL
Date: {today}   Grid: Udaipur Smart Utility

1. EVENT: Feeder F7 (Ambamata) earth-fault trip at 12:14; third trip in 4 days.
2. ROOT CAUSE (AI-correlated): Progressive cable insulation failure, span P-114 to P-117,
   accelerated by peak thermal stress. Prior O/C trips on 29 Jun and 01 Jul were precursors.
3. IMPACT: ~9 MW / est. 14,000 consumers; backfeed via F5 restored 78% within 31 min.
4. CONCURRENT RISK: XFMR T-4 Sukher oil temperature {f4['temp']:.0f} C, rising; mitigation in progress.
5. ACTIONS: PTW issued; megger test scheduled; cable replacement within 48h;
   mobile transformer pre-positioned; demand response active 17:00-20:00.
6. RECOMMENDATION: Add 1980s PILC cable spans of this class to the predictive
   replacement program; 11 similar spans identified city-wide.

Drafted by: Control Room Copilot        Reviewed by: ____________
"""
