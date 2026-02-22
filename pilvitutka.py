#!/usr/bin/env python3
"""
Pilvitutka v1.0
---------------
Seuraa pilvisyyttä Etelä-Suomessa (meri vs. mantere) Open-Meteo API:lla.
Lähettää Telegram-viestin kun merellä on selkeämpää kuin mantereella.

Käyttö:
  python3 pilvitutka.py          # normaali ajo
  python3 pilvitutka.py --force  # pakota viesti (ohita hälytyslogiikka)
  python3 pilvitutka.py --loop   # jatkuva seuranta (tunnin välein)

Riippuvuudet:
  pip install requests python-dotenv

Ympäristö (.env):
  TELEGRAM_BOT_TOKEN=...
  TELEGRAM_CHAT_ID=...
"""

import os
import sys
import time
import signal
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Tuple

import requests
from dotenv import load_dotenv

# -------------------------
# Versio & logging
# -------------------------
VERSION = "1.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("pilvitutka")

# -------------------------
# Graceful shutdown
# -------------------------
_running = True

def _shutdown_handler(signum, frame):
    global _running
    log.info("Sammutussignaali (%s), lopetetaan...", signal.Signals(signum).name)
    _running = False

signal.signal(signal.SIGTERM, _shutdown_handler)
signal.signal(signal.SIGINT, _shutdown_handler)

# -------------------------
# .env
# -------------------------
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# -------------------------
# Seurantapisteet
# -------------------------
POINTS = [
    {"name": "Avomeri (etelä)",  "lat": 59.90, "lon": 24.50, "zone": "meri"},
    {"name": "Avomeri (länsi)",  "lat": 59.95, "lon": 23.80, "zone": "meri"},
    {"name": "Harmaja",          "lat": 60.10, "lon": 24.97, "zone": "rannikko"},
    {"name": "Helsinki",         "lat": 60.17, "lon": 24.94, "zone": "rannikko"},
    {"name": "Vantaa",           "lat": 60.30, "lon": 25.05, "zone": "mantere"},
    {"name": "Hyvinkää",         "lat": 60.63, "lon": 24.86, "zone": "mantere"},
]

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Hälytyskynnykset
DIFF_THRESHOLD = 30   # meri-mantere ero prosenttiyksiköissä
CLEAR_MAX = 40        # meren max pilvisyys jotta "selkeää merellä"

# Loop-tilan asetukset
LOOP_INTERVAL = 3600  # 1 tunti

# -------------------------
# API-haku
# -------------------------
def fetch_cloud_data() -> List[Dict]:
    """Hakee pilvisyysdatan kaikille pisteille Open-Meteo API:sta."""
    lats = ",".join(str(p["lat"]) for p in POINTS)
    lons = ",".join(str(p["lon"]) for p in POINTS)

    params = {
        "latitude": lats,
        "longitude": lons,
        "hourly": "cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high",
        "models": "metno_nordic",
        "timezone": "Europe/Helsinki",
        "forecast_hours": 6,
    }

    r = requests.get(OPEN_METEO_URL, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    # Open-Meteo palauttaa listan jos useita pisteitä
    if isinstance(data, dict) and "hourly" in data:
        data = [data]

    results = []
    now = datetime.now()
    current_hour = now.strftime("%Y-%m-%dT%H:00")

    for i, point in enumerate(POINTS):
        hourly = data[i]["hourly"]
        times = hourly["time"]

        # Etsi nykyinen tai lähin tunti
        idx = 0
        for j, t in enumerate(times):
            if t >= current_hour:
                idx = j
                break

        results.append({
            "name": point["name"],
            "zone": point["zone"],
            "lat": point["lat"],
            "lon": point["lon"],
            "time": times[idx],
            "cloud_cover": hourly["cloud_cover"][idx],
            "cloud_cover_low": hourly["cloud_cover_low"][idx],
            "cloud_cover_mid": hourly["cloud_cover_mid"][idx],
            "cloud_cover_high": hourly["cloud_cover_high"][idx],
            # 6h ennuste
            "forecast": [
                {"time": times[k], "cloud_cover": hourly["cloud_cover"][k]}
                for k in range(len(times))
            ],
        })

    return results


# -------------------------
# Analyysi
# -------------------------
def cloud_text(pct: int) -> str:
    if pct <= 10:
        return "Selkeää"
    if pct <= 30:
        return "Melko selkeää"
    if pct <= 60:
        return "Puolipilvistä"
    if pct <= 80:
        return "Melko pilvistä"
    return "Pilvistä"


def bar(pct: int, width: int = 10) -> str:
    filled = round(pct / 100 * width)
    return "\u2588" * filled + "\u2591" * (width - filled)


def analyze(results: List[Dict]) -> Tuple[str, bool]:
    """Analysoi tulokset ja palauttaa (viesti, hälytys)."""
    zones: Dict[str, List[int]] = {"meri": [], "rannikko": [], "mantere": []}
    for r in results:
        zones[r["zone"]].append(r["cloud_cover"])

    avg = {}
    for zone, values in zones.items():
        avg[zone] = round(sum(values) / len(values)) if values else 0

    now_str = datetime.now().strftime("%d.%m. klo %H:%M")

    lines = [f"PILVITUTKA {now_str}", ""]

    # Pisteiden tiedot
    for r in results:
        lines.append(f"  {r['name']:20s} {bar(r['cloud_cover'])} {r['cloud_cover']:3d}% – {cloud_text(r['cloud_cover'])}")

    lines.append("")
    lines.append(f"Keskiarvot:")
    lines.append(f"  Meri:      {avg['meri']:3d}% – {cloud_text(avg['meri'])}")
    lines.append(f"  Rannikko:  {avg['rannikko']:3d}% – {cloud_text(avg['rannikko'])}")
    lines.append(f"  Mantere:   {avg['mantere']:3d}% – {cloud_text(avg['mantere'])}")

    # 6h ennuste tiivistelmä
    lines.append("")
    lines.append("6h ennuste (meri keskiarvo):")
    meri_points = [r for r in results if r["zone"] == "meri"]
    if meri_points:
        n_hours = len(meri_points[0]["forecast"])
        for h in range(n_hours):
            t = meri_points[0]["forecast"][h]["time"]
            avg_h = round(sum(p["forecast"][h]["cloud_cover"] for p in meri_points) / len(meri_points))
            lines.append(f"  {t[11:16]}  {bar(avg_h)} {avg_h:3d}%")

    # Hälytyslogiikka
    diff = avg["mantere"] - avg["meri"]
    alert = diff >= DIFF_THRESHOLD and avg["meri"] <= CLEAR_MAX

    if alert:
        lines.append("")
        lines.append(f"Merellä {diff} prosenttiyksikköä selkeämpää kuin mantereella!")

    msg = "\n".join(lines)
    return msg, alert


# -------------------------
# Telegram
# -------------------------
def send_telegram(text: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.warning("TELEGRAM_* puuttuu – ei lähetetä.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        r = requests.post(url, data=data, timeout=15)
        if r.status_code == 200:
            log.info("Telegram-viesti lähetetty.")
        else:
            log.error("Telegram %d: %s", r.status_code, r.text)
    except requests.RequestException as e:
        log.error("Telegram: %s", e)


# -------------------------
# Main
# -------------------------
def run_once(force: bool = False):
    results = fetch_cloud_data()
    msg, alert = analyze(results)
    log.info("\n%s", msg)

    if alert or force:
        send_telegram(msg)
    else:
        log.info("Ei merkittävää eroa meren ja mantereen välillä – ei lähetetä viestiä.")


def main():
    parser = argparse.ArgumentParser(description=f"Pilvitutka v{VERSION}")
    parser.add_argument("--force", action="store_true", help="Pakota Telegram-viesti")
    parser.add_argument("--loop", action="store_true", help="Jatkuva seuranta")
    args = parser.parse_args()

    log.info("Pilvitutka v%s käynnistyy...", VERSION)

    if args.loop:
        consecutive_errors = 0
        while _running:
            try:
                run_once(force=args.force)
                consecutive_errors = 0
            except Exception as e:
                consecutive_errors += 1
                backoff = min(2 ** consecutive_errors, 300)
                log.error("Virhe (%d peräkkäin): %s", consecutive_errors, e)
                log.info("Odotetaan %d s ennen uutta yritystä.", backoff)
                _interruptible_sleep(backoff)
                continue
            _interruptible_sleep(LOOP_INTERVAL)
        log.info("Pilvitutka sammutettu.")
    else:
        run_once(force=args.force)


def _interruptible_sleep(seconds: int):
    for _ in range(seconds):
        if not _running:
            break
        time.sleep(1)


if __name__ == "__main__":
    main()
