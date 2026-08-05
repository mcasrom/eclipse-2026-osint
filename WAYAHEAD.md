# WAYAHEAD — Eclipse 2026 OSINT

**Objetivo**: micrositio/mapa interactivo del eclipse solar total del **12 de agosto de 2026** en España (primer total en la península en más de un siglo). Primera pieza del módulo durable **"Fenómenos celestes & meteorológicos"** de Viaje con Inteligencia.
**Live**: https://eclipse.viajeinteligencia.com
**GitHub**: https://github.com/mcasrom/eclipse-2026-osint
**Server**: `deploy@178.105.80.193` — PM2 `eclipse-api` (puerto 8700) — Nginx — Cloudflare (proxy naranja).

---

## Sprint 1 — Lanzamiento del eclipse (5 Ago 2026)

- **Datos (estáticos, pre-calculados)**:
  - `data/cities.json`: 13 ciudades (10 de totalidad + 3 parciales) con horarios reales del **IGN** (inicio, totalidad, duración, magnitud, altura, azimut; hora local CEST).
  - `data/franja.geojson`: polígono de la franja de totalidad construido desde la tabla de trayectoria de **NASA GSFC** (límites N/S WGS84, intervalos 120s).
- **Backend mínimo** (única parte dinámica): FastAPI en `127.0.0.1:8700`:
  - `GET /api/forecast` → nubosidad por ciudad (Open-Meteo, sin key) con **caché en fichero TTL 3h**. Un solo request por ventana.
  - `GET /health`.
  - Sin PostgreSQL, sin cron, sin Redis → ~50 MB RAM.
- **Nginx**: todo lo estático servido directo; `/api/` → 8700; `/sw.js` no-cache; cache larga (1 día) para `/data/`, `/vendor/`, iconos y `og-image`; `index.html` siempre fresco.
- **Frontend Leaflet PWA** (self-host Leaflet):
  - Mapa + franja + marcadores de ciudad con horarios/nubosidad + geolocalización + enlaces de viaje por provincia + aviso de seguridad ISO 12312-2.
  - **Tabs de fenómenos**: Eclipse 2026 (mapa) · Perseidas · Eclipse 2027 · Auroras (tarjetas informativas).
  - **PWA**: botón instalar (`beforeinstallprompt`), metas iOS, banner offline, iconos PNG reales, SW network-first.
  - **Funnel de entrada**: overlay de bienvenida (localStorage) con datos clave + CTA.
  - **Ayuda**: modal con cómo leer el mapa, horarios, nubosidad, seguridad y fuentes.
  - **Preview RRSS**: `og-image.png` (1200×630) + meta OG/Twitter + JSON-LD Event + apple-touch-icon.
- **Deploy**: cert Let's Encrypt, PM2 `eclipse-api`, **Cloudflare proxy naranja activo** (el `vendor/` lo bloqueaba una regla de firewall CF "PHP Exploits" → excepción para este host + purge).
- **Correo**: `eclipse@viajeinteligencia.com` (referencias mailto; falta crear la regla de reenvío en Cloudflare Email Routing).

## Sprint 2 — T1: valor añadido (5 Ago 2026)

- **Ko-fi** (`ko-fi.com/m_castillo`, el mismo de NearMe/MigrationFlow) en el footer — 0 carga (enlace externo).
- **Contador regresivo** + "totalidad restante" por ciudad (JS cliente puro, hora CEST correcta vía UTC+2).
- **Mejores spots**: ranking duración × nubosidad (del forecast cacheado) — 5 mejores con clic para volar.
- **Enlace al planificador IA** de viajeinteligencia.com ("Planifica tu viaje 2-3 días con IA").
- **Offline PWA**: verificado que SW precachea cities.json + franja.geojson + Leaflet.
- **JSON-LD `Event`** (SEO estructurado).

## Sprint 3 — Refactor por fenomeno + Calendario Cielos y Eventos (5 Ago 2026)

- **Refactor por fenomeno**: datos del 2026 movidos a `data/2026/` (cities.json + franja.geojson); nginx alias `/data/` sirve la arbol completa. El frontend carga `/data/2026/...`.
- **Calendario durable**: `data/events.json` con 15 fenomenos 2026-2027 (eclipses solares, lunares, lluvias de meteoros Perseidas/Geminidas/Cuadrantidas/Liridas/etc., oposiciones Saturno/Jupiter/Marte). Nuevo tab **📅 Calendario** con listado ordenado, destacando los eclipses y marcando los pasados.
- Esto deja el sitio listo para el resto de fenomenos (2027, auroras, perseidas globales) sin tocar el backend.

## 🔜 Próximos sprints

### Fase 2 — Cielos & Eventos (durable, post-12-Ago)
- [ ] **Expansión global**: path completo NASA (Islandia, resto de la franja) + zonas de parcialidad (%) sobre Europa/N.África + más ciudades + **i18n ES/EN**.
- [ ] **Eclipse 2027** (2-Ago, sur peninsular + N.África, ~6 min): mismo patrón de datos estáticos.
- [ ] **Calendario "Cielos & Eventos"**: eclipses solares/lunares, lluvias de meteoros, auroras (Kp), conjunciones — hub durable que resuelve lo efímero.
- [ ] **Perseidas / auroras globales**: datos estáticos + `/api/forecast` (ya genérico por lat/lon/fecha).

### No aquí (pertenece a viajeinteligencia.com)
- Chat IA / planificador (solo enlace). Email capture / alertas push con BD (choca con sin-tracking; si se hace, en la plataforma). API pública con backend (los datos ya son JSON estáticos).

## 📁 Estructura
```
eclipse-2026-osint/
├── server.py            # FastAPI: /api/forecast + /health (puerto 8700)
├── src/
│   ├── config.py        # constantes (puerto, TTL caché, fechas)
│   └── forecast.py      # Open-Meteo + caché fichero (TTL 3h)
├── data/
│   ├── cities.json      # 13 ciudades con horarios (IGN)
│   ├── franja.geojson   # franja de totalidad (NASA GSFC)
│   └── forecast_cache.json  # caché (generado)
├── frontend/
│   ├── index.html       # Leaflet PWA (tabs, contador, spots, ayuda, funnel, og)
│   ├── sw.js / manifest.json / iconos / og-image
│   └── vendor/          # Leaflet self-hosted
├── deploy.sh
└── README.md
```

## ⚠️ Pendientes
- [ ] Regla de reenvío `eclipse@viajeinteligencia.com` en Cloudflare Email Routing (acción del usuario).
- [ ] Verificación final en móvil de la experiencia completa (funnel → mapa → tabs).
- [ ] Decidir sobre el beacon de Web Analytics de Cloudflare (errores de consola cosméticos vs. analytics).
