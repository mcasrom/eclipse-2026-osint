"""Configuración Eclipse 2026 OSINT."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

PORT = 8700
HOST = "127.0.0.1"

CITY_DATA = BASE_DIR / "data" / "cities.json"
FORECAST_CACHE = BASE_DIR / "data" / "forecast_cache.json"

# Previsión: caché agresiva (3-6h). Un solo evento, no pipeline continuo.
FORECAST_TTL_SECONDS = 3 * 3600

# Open-Meteo (sin API key). Da cobertura de nubes horaria por lat/lon y aguanta
# el pico del 12-Ago con un solo request cacheado. Alternativa: AEMET
# (api.opendata.aemet.es) pero requiere key + códigos municipio INE.
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

EVENT_DATE = "2026-08-12"
TIMEZONE = "Europe/Madrid"
# horas locales relevantes para la cobertura de nubes (18:00-22:00)
HOURS_FROM = 17
HOURS_TO = 22
