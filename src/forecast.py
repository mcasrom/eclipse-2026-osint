"""Previsión de nubosidad para el eclipse (única parte dinámica).

Usa Open-Meteo (sin API key) con caché en fichero TTL ~3h. Un solo request
cubierto de nubes horario para todas las ciudades el 12-Ago-2026.
"""
import json
import time
from datetime import datetime, timezone

import httpx

from src.config import (BASE_DIR, FORECAST_TTL_SECONDS,
                        OPEN_METEO_URL, EVENT_DATE, TIMEZONE, HOURS_FROM, HOURS_TO)

CACHE_LOCK = False


def _cloud_category(cc: float) -> str:
    if cc is None:
        return "desconocido"
    if cc < 20:
        return "despejado"
    if cc < 50:
        return "parcialmente_nublado"
    if cc < 80:
        return "nublado"
    return "muy_nublado"


def _load_cities(year: str) -> list[dict]:
    path = BASE_DIR / "data" / year / "cities.json"
    return json.loads(path.read_text(encoding="utf-8"))["cities"]


def _cache_path(year: str):
    return BASE_DIR / "data" / f"forecast_cache_{year}.json"


def _read_cache(year: str) -> dict | None:
    FORECAST_CACHE = _cache_path(year)
    if not FORECAST_CACHE.exists():
        return None
    try:
        data = json.loads(FORECAST_CACHE.read_text(encoding="utf-8"))
    except Exception:
        return None
    age = time.time() - data.get("ts", 0)
    if age < FORECAST_TTL_SECONDS:
        return data
    return None


def _write_cache(year: str, payload: dict) -> None:
    payload["ts"] = int(time.time())
    try:
        _cache_path(year).write_text(json.dumps(payload, ensure_ascii=False),
                                  encoding="utf-8")
    except Exception:
        pass


async def _fetch_open_meteo(cities: list[dict]) -> dict:
    lats = ",".join(str(c["lat"]) for c in cities)
    lons = ",".join(str(c["lon"]) for c in cities)
    params = {
        "latitude": lats,
        "longitude": lons,
        "hourly": "cloud_cover",
        "timezone": TIMEZONE,
        "start_date": EVENT_DATE,
        "end_date": EVENT_DATE,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(OPEN_METEO_URL, params=params)
        r.raise_for_status()
        return r.json()


def _city_key_time(city: dict) -> int:
    """Hora local (int) del instante clave de cada ciudad (totalidad o máximo)."""
    t = city.get("tot_inicio") or city.get("max_estimado") or "20:30"
    return int(t.split(":")[0])


async def get_forecast(year: str = "2026") -> dict:
    cached = _read_cache(year)
    if cached:
        return {"cached": True, "updated": cached.get("updated"),
                "cities": cached.get("cities")}

    cities = _load_cities(year)
    try:
        data = await _fetch_open_meteo(cities)
    except Exception as e:
        # si AEMET/Open-Meteo falla: devolver lo último cacheado o estado desconocido
        if cached:
            return {"cached": True, "stale": True, "updated": cached.get("updated"),
                    "cities": cached.get("cities")}
        return {"cached": False, "error": str(e), "cities": []}

    # Open-Meteo multi-ubicación devuelve una lista (un dict por localización).
    items = data if isinstance(data, list) else [data]
    result = []
    for i, city in enumerate(cities):
        loc = items[i] if i < len(items) else {}
        times = (loc.get("hourly") or {}).get("time", [])
        row = (loc.get("hourly") or {}).get("cloud_cover", [])
        key_hour = _city_key_time(city)
        # cobertura en la hora clave
        cc = None
        for j, t in enumerate(times):
            hh = int(t[11:13]) if len(t) >= 13 else None
            if hh == key_hour and j < len(row):
                cc = row[j]
                break
        result.append({
            "id": city["id"],
            "cloud_cover": cc,
            "category": _cloud_category(cc),
            "at_hour": key_hour,
        })
    payload = {"updated": datetime.now(timezone.utc).isoformat(), "cities": result}
    _write_cache(year, payload)
    return {"cached": False, "updated": payload["updated"], "cities": result}
