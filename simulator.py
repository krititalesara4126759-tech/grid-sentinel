"""
simulator.py — Simulated city grid telemetry.
In production this module is replaced by Pub/Sub subscribers writing to BigQuery;
the rest of the app is unchanged (same state schema).
"""
import random, time, threading

FEEDERS = [
    {"id": "F1", "name": "Feeder 1 · Old City",      "load": 12.0, "cap": 20, "temp": 52, "status": "OK"},
    {"id": "F2", "name": "Feeder 2 · Fatehpura",     "load": 14.0, "cap": 20, "temp": 55, "status": "OK"},
    {"id": "F3", "name": "Feeder 3 · Sector 14",     "load": 11.0, "cap": 18, "temp": 49, "status": "OK"},
    {"id": "F4", "name": "Feeder 4 · Sukher Ind.",   "load": 16.5, "cap": 18, "temp": 74, "status": "WARN"},
    {"id": "F5", "name": "Feeder 5 · Hiranmagri",    "load": 13.0, "cap": 20, "temp": 53, "status": "OK"},
    {"id": "F6", "name": "Feeder 6 · Pratap Nagar",  "load": 12.5, "cap": 20, "temp": 51, "status": "OK"},
    {"id": "F7", "name": "Feeder 7 · Ambamata",      "load": 0.0,  "cap": 16, "temp": 41, "status": "TRIP"},
    {"id": "F8", "name": "Feeder 8 · Bhuwana",       "load": 10.0, "cap": 18, "temp": 48, "status": "OK"},
]

F7_TRIPS = [
    {"when": "Mon 29 Jun 17:42", "cause": "Over-current (O/C) relay pickup · 118% of rated", "dur": "22 min"},
    {"when": "Wed 01 Jul 18:05", "cause": "Over-current (O/C) relay pickup · 124% of rated", "dur": "31 min"},
    {"when": "Today 12:14",      "cause": "Earth-fault (E/F) — suspected cable insulation degradation, span P-114 to P-117", "dur": "ongoing"},
]

class GridSim:
    def __init__(self):
        self.feeders = [dict(f) for f in FEEDERS]
        self.water = 68.0
        self.ambient = 43
        self.history = []
        self.alarms = []
        self._lock = threading.Lock()
        self._seed_alarms()
        for _ in range(50):
            self._step(quiet=True)
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def _seed_alarms(self):
        self.push("crit", "Feeder 7 · Ambamata", "Earth-fault trip at 12:14. Breaker open. 3rd trip in 4 days — AI flags pattern.")
        self.push("warn", "XFMR T-4 · Sukher", "Oil temperature 74°C, rising trend — faster than load growth (cooling issue?).")
        self.push("info", "Weather Service", "Heatwave alert: 45°C forecast tomorrow. Load forecast auto-adjusted +8.5%.")
        self.push("info", "Water SCADA", "Reservoir 68% — pump station P-2 duty cycle elevated.")

    def push(self, sev, src, text):
        self.alarms.insert(0, {"t": time.strftime("%H:%M:%S"), "sev": sev, "src": src, "text": text})
        del self.alarms[40:]

    def _step(self, quiet=False):
        for f in self.feeders:
            if f["status"] == "TRIP":
                f["load"] = 0.0
                continue
            f["load"] = max(4.0, f["load"] + (random.random() - 0.48) * 0.5)
            if f["id"] == "F4":
                f["temp"] = min(86.0, f["temp"] + random.random() * 0.15)
                if f["temp"] > 78 and f["status"] != "CRIT":
                    f["status"] = "CRIT"
                    if not quiet:
                        self.push("crit", "XFMR T-4 Sukher",
                                  f"Oil temperature {f['temp']:.1f}°C — exceeds 78°C threshold. AI: failure risk HIGH within 6h.")
            else:
                f["temp"] = max(45.0, f["temp"] + (random.random() - 0.5) * 0.6)
            if f["load"] / f["cap"] > 0.92 and random.random() < 0.10 and not quiet:
                self.push("warn", f["name"], f"Loading at {f['load']/f['cap']*100:.0f}% of capacity.")
        self.water = max(55.0, self.water - 0.002 + (random.random() - 0.5) * 0.05)
        self.history.append(self.total_load())
        del self.history[:-60]

    def _run(self):
        while True:
            with self._lock:
                self._step()
            time.sleep(2)

    def total_load(self):
        return sum(f["load"] for f in self.feeders)

    def snapshot(self):
        with self._lock:
            fc, last = [], self.history[-1]
            import math
            for i in range(1, 16):
                fc.append(last + i * 0.28 + math.sin(i / 3) * 0.4)
            return {
                "feeders": [dict(f) for f in self.feeders],
                "water": self.water,
                "ambient": self.ambient,
                "total_load": self.total_load(),
                "history": list(self.history),
                "forecast": fc,
                "alarms": list(self.alarms),
                "f7_trips": F7_TRIPS,
                "n1_limit": 112,
            }

SIM = GridSim()
