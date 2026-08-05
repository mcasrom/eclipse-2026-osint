"""Estado de auroras: Kp en tiempo real (NOAA SWPC) con caché de 10 min.

Fuente: https://services.swpc.noaa.gov/json/planetary_k_index_1m.json
Tabla Kp -> latitud minima de visibilidad (aprox., aurora oval).
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from src.config import BASE_DIR

NOAA_URL = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
NOAA_FORECAST_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json"
CACHE_FILE = Path(BASE_DIR) / "data" / "aurora_cache.json"
TTL_SECONDS = 10 * 60

# Kp -> latitud minima (grados N) donde la aurora suele ser visible
KP_LATITUDE = {0: 66, 1: 66, 2: 65, 3: 60, 4: 55, 5: 50, 6: 45, 7: 40, 8: 35, 9: 30}


def _gscale(kp: float):
    if kp >= 7:
        return "G3+", "#f87171", "tormenta geomagnética fuerte"
    if kp >= 5:
        return "G2", "#fb923c", "tormenta geomagnética moderada"
    if kp >= 4:
        return "G1", "#fbbf24", "tormenta geomagnética menor"
    return "G0", "#34d399", "actividad tranquila"


def _read_cache() -> dict | None:
    if not CACHE_FILE.exists():
        return None
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None
    if time.time() - data.get("ts", 0) < TTL_SECONDS:
        return data
    return None


def _write_cache(payload: dict) -> None:
    payload["ts"] = int(time.time())
    try:
        CACHE_FILE.write_text(json.dumps(payload), encoding="utf-8")
    except Exception:
        pass


def _parse_forecast(rows: list) -> list:
    """Prevision Kp por dia (max del dia), proximos 3 dias. Filas: dicts con time_tag/kp/observed."""
    from collections import defaultdict
    today = datetime.now(timezone.utc).date().isoformat()
    days: dict[str, float] = defaultdict(lambda: 0.0)
    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("observed") != "predicted":
            continue
        tt = row.get("time_tag") or ""
        day = str(tt)[:10]
        if day < today:
            continue
        try:
            kp = float(row.get("kp") or 0)
        except (TypeError, ValueError):
            continue
        if kp > days[day]:
            days[day] = kp
    out = []
    for day in sorted(days)[:3]:
        kp = days[day]
        g, color, label = _gscale(kp)
        out.append({"date": day, "max_kp": round(kp, 1), "gscale": g, "color": color, "label": label})
    return out


def _apply_forecast(payload: dict, forecast: list) -> dict:
    payload["forecast"] = forecast
    return payload


async def get_aurora() -> dict:
    cached = _read_cache()
    if cached:
        return {"cached": True, "kp": cached["kp"], "aurora_lat": cached["aurora_lat"],
                "gscale": cached["gscale"], "color": cached["color"], "updated": cached["updated"],
                "forecast": cached.get("forecast", [])}
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(NOAA_URL)
            r.raise_for_status()
            rows = r.json()
            rf = await client.get(NOAA_FORECAST_URL)
            rf.raise_for_status()
            frows = rf.json()
        last = rows[-1] if rows else {}
        kp = float(last.get("estimated_kp") if last.get("estimated_kp") is not None
                  else last.get("kp_index") or 0)
        forecast = _parse_forecast(frows)
    except Exception as e:
        if cached:
            return {"cached": True, "stale": True, "kp": cached["kp"],
                    "aurora_lat": cached["aurora_lat"], "gscale": cached["gscale"],
                    "color": cached["color"], "updated": cached["updated"],
                    "forecast": cached.get("forecast", []), "error": str(e)}
        return {"cached": False, "error": str(e)}
    lat = KP_LATITUDE.get(int(round(kp)), 60)
    g, color, label = _gscale(kp)
    payload = {"kp": kp, "aurora_lat": lat, "gscale": g, "color": color, "label": label,
               "updated": datetime.now(timezone.utc).isoformat(),
               "forecast": forecast}
    _write_cache(payload)
    return {"cached": False, **payload}
