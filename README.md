<p align="center">
  <img src="https://img.shields.io/badge/live-eclipse.viajeinteligencia.com-ffd54f?style=flat-square" alt="Live">
  <img src="https://img.shields.io/badge/stack-FastAPI%20%2B%20Leaflet-00d4ff?style=flat-square" alt="Stack">
  <img src="https://img.shields.io/badge/license-MIT-34d399?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/open%20source-%E2%9C%93-8aa0c0?style=flat-square" alt="Open source">
</p>

<h1 align="center">🌑 Eclipse 2026 OSINT</h1>

<p align="center">
  <b>El primer eclipse solar total visible desde la península ibérica en más de un siglo.</b><br>
  Mapa interactivo de la franja de totalidad sobre España y Baleares — con horarios por ciudad,<br>
  duración, previsión de nubosidad y seguridad. Diseñado para aguantar el pico del <b>12 de agosto de 2026</b>.
</p>

<p align="center">
  <a href="https://eclipse.viajeinteligencia.com"><b>→ Ver el mapa en vivo</b></a>
</p>

---

## ✨ Qué ofrece

| | |
|---|---|
| 🗺️ | **Franja de totalidad** sobre España y Baleares, construida desde la tabla de trayectoria de **NASA GSFC** |
| 🕐 | **Horarios por ciudad** pre-calculados (inicio, totalidad, duración, altura, magnitud) del **IGN** |
| ☁️ | **Previsión de nubosidad** por ciudad (la única parte dinámica), cacheada cada 3 h |
| 📍 | **Geolocalización** para localizar tu ciudad más cercana a la franja |
| 🛣️ | Enlaces de viaje por provincia hacia tu plataforma principal |
| 🕶️ | Aviso de seguridad **ISO 12312-2** con enlaces oficiales (obligatorio, no decorativo) |

## 🏗️ Arquitectura (pensada para el pico de tráfico)

```
                    ┌──────────────────────────────────────────────┐
  Usuario ──► Cloudflare (opcional: edge cache) ──► Nginx ──────► │  Frontend estático (Leaflet PWA) │
                    │  todo lo estático directo (0 backend)       │  data/cities.json · franja.geojson │
                    └──────────────────────────────────────────────┘
                        └─► /api/forecast ──► FastAPI (127.0.0.1:8700)
                            └─► caché en fichero (TTL 3 h) ──► Open-Meteo
```

- **Sin PostgreSQL** — los datos del evento viven en JSON estáticos servidos por nginx.
- **Sin pipeline ni cron** — un solo evento, todo pre-calculado.
- **Un solo request dinámico por ventana** de 3 h para la previsión.
- Coste real: **~50 MB de RAM**, CPU ≈ 0.

## 📊 Fuentes de datos

| Dato | Fuente | Tipo |
|---|---|---|
| Horarios por ciudad | [IGN](https://astronomia.ign.es) | Estático |
| Franja de totalidad | [NASA GSFC](https://eclipse.gsfc.nasa.gov) | Estático (GeoJSON) |
| Nubosidad | [Open-Meteo](https://open-meteo.com) | Dinámico, cacheado 3 h |

> Alternativa de nubosidad: AEMET (requiere API key + códigos municipio INE). Open-Meteo se eligió por robustez: sin key, cobertura horaria directa por lat/lon.

## 🌌 Más allá del eclipse

Este portal está pensado como base para **otros fenómenos celestes y meteorológicos**:
próximos eclipses (2027), lluvias de meteoros, auroras, olas de calor…

- Los datos son **por fenómeno** (carpetas estáticas independientes).
- `/api/forecast` sirve nubosidad para **cualquier lat/lon/fecha** → reutilizable sin cambios.
- Añadir un fenómeno = añadir sus datos estáticos + una sección en el frontend.

## 🌍 Fase 2 — Expansión global (post-lanzamiento 12-Ago)

El eclipse de 2026 es un fenómeno global: la franja cruza **Islandia** (total) → Atlántico → **España**, y es **parcial** en toda Europa y el norte de África. Tras el lanzamiento del 12-Ago, la expansión natural es:

- **Path global completo** de NASA (ya disponible en la tabla de trayectoria) + **zonas de parcialidad** (%) sobre Europa/N.África.
- **Más ciudades**: Islandia y capitales europeas con sus horarios.
- **i18n ES/EN** para audiencia global.
- **Otros fenómenos**: Eclipse 2027 (sur peninsular + N.África, ~6 min), 2028 (Australia), eclipses lunares, Perseidas, auroras — encajan en los tabs + datos estáticos + `/api/forecast` genérico.

La arquitectura ya lo soporta: datos por fenómeno (JSON/GeoJSON estáticos) + forecast por lat/lon/fecha sin cambios de backend.

## 🚀 Despliegue

```bash
# 1. Código
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt

# 2. DNS + certificado
#    Cloudflare: A eclipse → 178.105.80.193 (DNS only primero)
sudo certbot --nginx -d eclipse.viajeinteligencia.com

# 3. PM2
pm2 start ./venv/bin/python --name eclipse-api -- -m uvicorn server:app --host 127.0.0.1 --port 8700
pm2 save

# 4. Verificar
curl -s https://eclipse.viajeinteligencia.com/health
curl -s https://eclipse.viajeinteligencia.com/api/forecast
```

La configuración de nginx está en `/etc/nginx/sites-enabled/eclipse`: estáticos directos,
`/api/` → `127.0.0.1:8700`, `/sw.js` sin cache.

## 🛠️ Proyectos del mismo autor

- [NearMe OSINT](https://github.com/mcasrom/nearme-osint) — radar de incidencias en tiempo real
- [MigrationFlow OSINT](https://github.com/mcasrom/migrationflow-osint) — flujos migratorios globales

## 📬 Contacto

[eclipse@viajeinteligencia.com](mailto:eclipse@viajeinteligencia.com)

## ⚖️ Licencia

MIT — código abierto. Sin tracking, sin cookies, sin dependencias externas a la observación del cielo. ☀️
