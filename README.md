<p align="center">
  <img src="https://img.shields.io/badge/live-eclipse.viajeinteligencia.com-ffd54f?style=flat-square" alt="Live">
  <img src="https://img.shields.io/badge/stack-FastAPI%20%2B%20Leaflet-00d4ff?style=flat-square" alt="Stack">
  <img src="https://img.shields.io/badge/license-MIT-34d399?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/open%20source-%E2%9C%93-8aa0c0?style=flat-square" alt="Open source">
</p>

<h1 align="center">🌑 Eclipse 2026 OSINT</h1>

<p align="center">
  <b>Qué pasa hoy en el cielo.</b> El primer eclipse solar total visible desde la península en más de un siglo,<br>
  y un portal <b>perpetuo de fenómenos celestes</b>: el próximo evento siempre en la portada, astronomía diaria,<br>
  franjas de totalidad 2026 y 2027, horarios por ciudad, nubosidad, auroras (Kp), Perseidas, guías — con PWA y SEO.
</p>

<p align="center">
  <a href="https://eclipse.viajeinteligencia.com"><b>→ Ver el mapa en vivo</b></a>
</p>

---

## ✨ Qué ofrece

| | |
|---|---|
| 🌑 | **Eclipse 2026** (12-Ago): franja de totalidad A Coruña → Valencia → Baleares, horarios IGN por ciudad, previsión de nubosidad a la hora de la totalidad |
| 🌒 | **Eclipse 2027** (2-Ago): franja sobre el sur peninsular + N.África (Cádiz, Málaga, Ceuta, Melilla) con horarios estimados de la línea central NASA |
| 🌌 | **Auroras**: mapa con el **Kp real de NOAA** (caché 10 min) y ciudades del norte coloreadas por visibilidad |
| ☄️ | **Perseidas**: mapa con el radiant y pico la noche del eclipse |
| 🌠 | **Próximo en el cielo**: hero auto-rotativo que siempre muestra el siguiente evento con countdown |
| ☀️ | **Hoy en el cielo**: amanecer/atardecer, fase lunar y UV, auto-alimentado a diario |
| 📖 | **Guías evergreen**: cómo observar eclipses, meteoros y auroras con seguridad |
| 📅 | **Calendario de fenómenos** 2026-2027: eclipses, lluvias de meteoros, oposiciones |
| ⏳ | **Contador regresivo** + totalidad restante por ciudad · **mejores spots** (duración × nubosidad) |
| 📲 | **PWA**: instalable, offline, iOS, banner de conexión · botón Ko-fi |
| 🕶️ | Seguridad **ISO 12312-2** con enlaces oficiales (obligatorio) |
| 🔗 | Enlaces de viaje y al planificador IA de [viajeinteligencia.com](https://viajeinteligencia.com) |

## 🏗️ Arquitectura (pensada para el pico de tráfico)

```
  Usuario ──► Cloudflare (edge cache, proxy) ──► Nginx
      │  estáticos servidos directo (0 backend): index.html · data/2026 · data/2027 · events.json · og-image
      └─► /api/forecast?year=2026|2027 ──► FastAPI (127.0.0.1:8700) ──► caché fichero (TTL 3h) ──► Open-Meteo
      └─► /api/aurora ──► FastAPI ──► caché fichero (TTL 10 min) ──► NOAA SWPC (Kp)
      └─► /api/sky ──► FastAPI ──► caché fichero (TTL 24 h) ──► Open-Meteo (amanecer/UV) + fase lunar
```

- **Sin PostgreSQL** — los datos de cada fenómeno viven en JSON estáticos servidos por nginx.
- **Sin pipeline ni cron** — todo pre-calculado; tres endpoints dinámicos cacheados (forecast, Kp y sky).
- Coste real: **~55 MB de RAM**, CPU ≈ 0.

## 📊 Fuentes de datos

| Dato | Fuente | Tipo |
|---|---|---|
| Horarios 2026 por ciudad | [IGN](https://astronomia.ign.es) | Estático |
| Franjas de totalidad 2026/2027 | [NASA GSFC](https://eclipse.gsfc.nasa.gov) | Estático (GeoJSON) |
| Nubosidad | [Open-Meteo](https://open-meteo.com) | Dinámico, cacheado 3 h |
| Kp (auroras) | [NOAA SWPC](https://www.swpc.noaa.gov) | Dinámico, cacheado 10 min |
| Amanecer/fase lunar | [Open-Meteo](https://open-meteo.com) | Dinámico, cacheado 24 h |

## 🌌 Más allá del eclipse

Portal de **fenómenos celestes** pensado como base para futuros eventos:
- Datos **por fenómeno** (`data/2026`, `data/2027`, `events.json`) — añadir uno = añadir sus datos estáticos.
- `/api/forecast` sirve nubosidad para **cualquier lat/lon/fecha**; `/api/aurora` da el Kp en tiempo real.
- Tabs: Eclipse 2026 · Perseidas · Eclipse 2027 · Auroras · Calendario.

## 🌍 Fase 2 — Expansión global (post-12-Ago)

El eclipse de 2026 es global: franja por **Islandia** (total) y **parcial** en toda Europa y N.África. Tras el lanzamiento:
- Path global completo + **contornos de parcialidad** (%) sobre Europa/N.África.
- Más ciudades (Islandia, capitales europeas) y **i18n ES/EN**.
- Calibración de horarios 2027 con datos oficiales del IGN cuando los publique.

## 🚀 Despliegue

```bash
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
# Cloudflare: A eclipse → 178.105.80.193 (luego proxy naranja)
sudo certbot --nginx -d eclipse.viajeinteligencia.com
pm2 start ./venv/bin/python --name eclipse-api -- -m uvicorn server:app --host 127.0.0.1 --port 8700
pm2 save
curl -s https://eclipse.viajeinteligencia.com/health
curl -s https://eclipse.viajeinteligencia.com/api/forecast?year=2027
```

Nginx (`/etc/nginx/sites-enabled/eclipse`): estáticos directos (cache 1 día para `/data/`, `/vendor/`, imágenes), `/api/` → `127.0.0.1:8700`, `/sw.js` sin cache, `index.html` siempre fresco.

## 🛠️ Proyectos del mismo autor

- [NearMe OSINT](https://github.com/mcasrom/nearme-osint) — radar de incidencias en tiempo real
- [MigrationFlow OSINT](https://github.com/mcasrom/migrationflow-osint) — flujos migratorios globales

## 📬 Contacto

[eclipse@viajeinteligencia.com](mailto:eclipse@viajeinteligencia.com)

## ⚖️ Licencia

MIT — código abierto. Sin tracking, sin cookies, sin dependencias externas a la observación del cielo. ☀️
