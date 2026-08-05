# Eclipse 2026 OSINT

Micrositio/mapa interactivo del **eclipse solar total del 12 de agosto de 2026** en España — el primero visible desde la península en más de un siglo.

**Live:** https://eclipse.viajeinteligencia.com
**Stack:** Python async (httpx) → FastAPI (solo previsión de nubosidad) → Nginx (todo lo estático) → Leaflet PWA.

## Filosofía de recursos
Diseñado para aguantar el pico de tráfico del 12-Ago sin sobrecargar el servidor (compartido con ~15 servicios en PM2):
- **Todo lo estático lo sirve Nginx directo** (HTML, `data/cities.json`, `data/franja.geojson`, Leaflet) — cero carga de backend/BD.
- **Los datos del eclipse son pre-calculados y estáticos** (un solo evento, no hay pipeline de ingesta).
- **Sin PostgreSQL**: los datos de ciudades viven en un JSON estático.
- **Única parte dinámica**: la previsión de nubosidad, cacheada en un fichero con TTL de **3 horas** (un solo request por ventana a Open-Meteo).
- Sin Redis, sin cronjobs, sin daemons pesados. ~50 MB de RAM total.

## Fenómenos celestes y meteorológicos (más allá del eclipse)

Este portal está diseñado para alojar **otros fenómenos** además del eclipse del 12-Ago-2026:
próximos eclipses (2027), lluvias de meteoros, auroras, olas de calor, tormentas, etc.

La arquitectura es extensible por diseño:
- **Datos por fenómeno**: cada evento tiene su carpeta de datos estáticos (ej. el eclipse usa
  `data/cities.json` + `data/franja.geojson`). Añadir un fenómeno = añadir sus datos estáticos
  y referenciarlos en el frontend — sin tocar el backend.
- **Previsión genérica**: el endpoint `/api/forecast` ya sirve nubosidad para cualquier
  lat/lon/fecha (Open-Meteo, sin key) → sirve igual para una lluvia de meteoros que para una aurora.
- **Cero carga extra**: todo sigue siendo estático servido por nginx + un solo request cacheado.

Para añadir un fenómeno nuevo: crea `data/<fenomeno>/` con su JSON/GeoJSON, añade una pestaña/
sección en `frontend/index.html`, y reutiliza `/api/forecast` para su previsión.

## Estructura
```
eclipse-2026-osint/
├── server.py            # FastAPI mínimo: /api/forecast + /health (puerto 8700)
├── src/
│   ├── config.py        # constantes (puerto, TTL caché, fechas)
│   └── forecast.py      # previsión de nubosidad (Open-Meteo) + caché en fichero
├── data/
│   ├── cities.json      # 13 ciudades con horarios pre-calculados
│   ├── franja.geojson   # polígono de la franja de totalidad
│   └── forecast_cache.json  # caché (generado)
├── frontend/
│   ├── index.html       # Leaflet PWA (mapa, marcadores, nubosidad, seguridad)
│   ├── sw.js / manifest.json / icon.svg
│   └── vendor/          # Leaflet self-hosted
├── deploy.sh            # despliegue desde el server
└── README.md
```

## Datos (fuentes)
- **Horarios por ciudad** (inicio, totalidad, magnitud, altura, azimut): **Instituto Geográfico Nacional (IGN)** vía eclipsetotal.info (horas locales CEST).
- **Franja de totalidad**: tabla de trayectoria de **NASA GSFC** (límites N/S WGS84, intervalos 120s) convertida a polígono GeoJSON.
- **Nubosidad**: **Open-Meteo** (sin API key, cobertura horaria por lat/lon). Alternativa: AEMET (requiere key + códigos municipio INE) — Open-Meteo es más robusto para el pico.

## Despliegue (Ubuntu + PM2 + Nginx)

### 1. Código
```bash
cd /home/deploy/eclipse-2026-osint
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
```

### 2. DNS + Cloudflare (IMPORTANTE, lo más crítico)
- Añade en Cloudflare: **A `eclipse` → 178.105.80.193** (gris/DNS-only primero).
- Emite el certificado: `sudo certbot --nginx -d eclipse.viajeinteligencia.com`
- Cuando funcione, activa el **proxy naranja (Cloudflare)** en ese registro A → Cloudflare cachea los estáticos en el edge y absorbe el grueso del pico del 12-Ago.

### 3. Nginx
Config ya instalada en `/etc/nginx/sites-enabled/eclipse`: estáticos servidos directo, `/api/` → `127.0.0.1:8700`, `/sw.js` sin cache. Tras el cert, `sudo nginx -s reload`.

### 4. PM2
```bash
pm2 start ./venv/bin/python --name eclipse-api -- -m uvicorn server:app --host 127.0.0.1 --port 8700
pm2 save
```

### 5. Verificar
```bash
curl -s https://eclipse.viajeinteligencia.com/health
curl -s https://eclipse.viajeinteligencia.com/api/forecast | python3 -m json.tool
```

## Notas de seguridad
El sitio incluye aviso obligatorio (ISO 12312-2) y enlaces a información oficial de observación segura. Es contenido de seguridad real, no decorativo.

MIT License. Código abierto, sin tracking, sin cookies.
