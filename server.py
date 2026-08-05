"""Eclipse 2026 OSINT — API mínima.

Solo dinámica la previsión de nubosidad (cacheada con TTL de horas).
Todo lo demás (HTML, JSON de ciudades, franja) lo sirve Nginx directamente.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src import aurora
from src import forecast

app = FastAPI(title="Eclipse 2026 OSINT",
              version="1.0.0",
              docs_url="/docs",
              openapi_url="/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "Eclipse 2026 OSINT"}


@app.get("/api/aurora")
async def api_aurora():
    return await aurora.get_aurora()


@app.get("/api/forecast")
async def api_forecast(year: str = "2026"):
    return await forecast.get_forecast(year=year)
