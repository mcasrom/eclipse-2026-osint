"""Astronomía diaria (Hoy en el cielo).

Open-Meteo forecast (salida/puesta de sol, UV máx) + fase lunar calculada
(fórmula estándar sinódica). Caché 24h.
"""
import json
import math
import time
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

import httpx

from src.config import BASE_DIR

OM_FORECAST = "https://api.open-meteo.com/v1/forecast"
CACHE_FILE = Path(BASE_DIR) / "data" / "sky_cache.json"
TTL_SECONDS = 24 * 3600

SYNODIC = 29.53058867  # meses sinódico (días)
NEW_MOON_REF = date(2000, 1, 6)  # luna nueva conocida


def _phase_name(frac):
    if frac < 0.0625 or frac >= 0.9375:
        return "Luna nueva"
    if frac < 0.1875:
        return "Luna creciente"
    if frac < 0.4375:
        return "Cuarto creciente"
    if frac < 0.5625:
        return "Luna llena"
    if frac < 0.8125:
        return "Cuarto menguante"
    return "Luna menguante"


def _moon_phase_frac(d: date) -> float:
    """Fracción de fase lunar 0-1 (0=luna nueva, 0.5=llena). Aprox. sinódica."""
    days = (d - NEW_MOON_REF).days
    return (days % SYNODIC) / SYNODIC


def _read_cache(key):
    if not CACHE_FILE.exists():
        return None
    try:
        d = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None
    if d.get("key") != key:
        return None
    if time.time() - d.get("ts", 0) < TTL_SECONDS:
        return d
    return None


def _write_cache(key, payload):
    payload["ts"] = int(time.time())
    payload["key"] = key
    try:
        CACHE_FILE.write_text(json.dumps(payload), encoding="utf-8")
    except Exception:
        pass


async def get_sky(lat: float = 40.4168, lon: float = -3.7038) -> dict:
    key = f"{round(lat, 2)},{round(lon, 2)}"
    cached = _read_cache(key)
    if cached:
        return {"cached": True, "date": cached["date"], "sunrise": cached["sunrise"],
                "sunset": cached["sunset"], "uv_max": cached["uv_max"],
                "moon_phase": cached["moon_phase"], "moon_phase_name": cached["moon_phase_name"],
                "updated": cached["updated"]}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(OM_FORECAST, params={
                "latitude": lat, "longitude": lon,
                "daily": "sunrise,sunset,uv_index_max",
                "timezone": "Europe/Madrid", "forecast_days": 1,
            })
            r.raise_for_status()
            d = r.json()["daily"]
        today = date.today()
        payload = {
            "date": d["time"][0],
            "sunrise": d["sunrise"][0],
            "sunset": d["sunset"][0],
            "uv_max": d["uv_index_max"][0],
            "moon_phase": round(_moon_phase_frac(today), 3),
            "moon_phase_name": _phase_name(_moon_phase_frac(today)),
            "updated": datetime.now(timezone.utc).isoformat(),
        }
        _write_cache(key, payload)
        return {"cached": False, **payload}
    except Exception as e:
        if cached:
            return {"cached": True, "stale": True, **{k: cached[k] for k in
                    ("date", "sunrise", "sunset", "uv_max", "moon_phase",
                     "moon_phase_name", "updated")}}
        return {"cached": False, "error": str(e)}
