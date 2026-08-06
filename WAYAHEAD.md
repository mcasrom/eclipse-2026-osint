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

## Sprint 4 — Eclipse 2027 con mapa + PWA visible + ayuda generica (5 Ago 2026)

- **Eclipse 2027 (2-Ago-2027) con MAPA**: `data/2027/cities.json` (Cádiz, Málaga, Ceuta, Melilla = total; Granada, Almería = parcial en el borde norte) + `data/2027/franja.geojson` (path completo de NASA SE2027Aug02T). El frontend ahora es **multi-fenómeno**: `loadPhenomenon(year)` intercambia capas de mapa por tab (Eclipse 2026 <-> 2027). El tab 2027 deja de ser tarjeta.
- **Horarios 2027**: maximo estimado de la **linea central NASA** (interpolado), hora local CEST (~10:47 mañana), etiquetado como estimado y refinable con IGN. Backend `/api/forecast?year=2026|2027` con cache por anio (usa `max_estimado` si no hay `tot_inicio`).
- **PWA visible**: boton **📲 Instalar app** siempre en el panel (no solo cuando el navegador dispara beforeinstallprompt), con instrucciones manuales de fallback. El boton del header (⬇️ Instalar) sigue mostrandose cuando el navegador lo ofrece.
- **Ayuda generica**: los horarios de la ayuda ya no son solo del 2026 (mencionan 2026 ~20:28 y 2027 ~10:47, estimados NASA).

## Fix — Mapa en movil (5 Ago 2026)

- **Problema**: en smartphone se veia toda la narrativa pero el mapa geografico no renderizaba (colapso a 0 de altura).
- **Causa**: `100vh`/flex se comporta distinto en movil y Leaflet mide el contenedor al iniciar; el overlay de bienvenida podia cubrirlo y el mapa quedaba a 0x0.
- **Fix**: `height:100dvh` (viewport dinamico) + `min-height:50vh` en #map (55vh en el media query movil) + `map.invalidateSize()` al cerrar el funnel y en el evento resize (barra del navegador movil). Verificado en viewport 390x844 (mapa 390x464, tiles cargados, 0 errores). SW v6.

## Sprint 5 — Opcion 4: Auroras (Kp) y Perseidas con mapa (5 Ago 2026)

- **Auroras (amplio, hemisferio norte)**: nuevo endpoint `GET /api/aurora` (`src/aurora.py`) con el **Kp en tiempo real de NOAA SWPC** cacheado (TTL 10 min) + tabla Kp->latitud minima de visibilidad. Frontend: en el tab Auroras, mapa del norte de Europa con puntos de ciudades coloreados segun su latitud vs el Kp actual + linea de latitud auroral + lectura Kp/G-scale. ~+5MB RAM.
- **Perseidas (amplio)**: el tab Perseidas ahora incluye un mapa con el **radiant** (Perseo, direccion noreste) + nota de mejor observacion.
- Cobertura amplia (no solo España): son fenomenos del hemisferio norte; los contornos de PARCIALIDAD del eclipse (Europa/N.Africa) quedan para la opcion 5 (global), donde se traen datos de magnitud parcial de fuente fiable.

## Sprint 6 — SEO completo + RRSS (5 Ago 2026)

- **Head SEO**: title orientado a busqueda ("donde ver el eclipse total 2026 + mapa + nubosidad"), meta description, keywords, robots index/follow, canonical, og:locale es_ES + og:site_name.
- **JSON-LD @graph**: WebSite (con publisher Viaje con Inteligencia) + Event detallado (fechas, ubicacion, imagen, organizer, offers gratis). Valido.
- **robots.txt + sitemap.xml** servidos estaticamente (200 via CF).
- Todo verificado via Cloudflare: keywords/canonical/og:locale/@graph presentes, JSON-LD JSON valido, robots/sitemap 200.

## 🔜 Próximos sprints

### Sprint 7 — Global + i18n ES/EN (5 Ago 2026)
- [x] **Eclipse 2026 global**: franja completa NASA GSFC (Islandia → España → Mediterráneo) con 19 ciudades; **Reykjavik (Islandia) total** + Akureyri parcial + europeas de referencia (Londres, París, Lisboa, Roma) con nota de parcialidad. Forecast de nubosidad ampliado a 19 ciudades.
- [x] **i18n ES/EN** con toggle (botón EN/ES en header, param lang + localStorage): título, tabs, botones, títulos de sección, countdown, next-event, cielo, leyendas y popups — diccionario I18N + t() + data-i18n (el contenido profundo de Guías/Ayuda/Calendario sigue en ES de momento).
- [x] **Compartir RRSS** (v0.25): Web Share + X/WhatsApp/Telegram/Facebook + copiar.
- [x] **Contornos de parcialidad (%)** (v0.27): isomagnéticas 90/70/50/30/10% del diámetro solar, calculadas con **elementos besselianos NASA + algoritmo Espenak/Meeus**, limitadas por atardecer, validadas contra 24 ciudades de Wikipedia (±1.5%). Toggle + leyenda + cobertura en popups.
- [ ] Tras el 12-Ago: el eclipse 2026 pasa a "pasado" en el calendario (la app ya lo marca).
- [x] **i18n contenido profundo** (v0.28): Guías, Ayuda, Perseidas/2027/Auroras/Calendario, safety, popups, eventos (name/visible/note_en) y ciudades internacionales (name_en) — verificado ES↔EN en móvil headless.

### Fase 2 — Cielos & Eventos (avance)
- [x] **Eclipse 2027 con mapa** (Sprint 4): Cádiz/Málaga/Ceuta/Melilla total · Granada/Almería parcial (borde norte). Horarios estimados de la línea central NASA.
- [x] **Calendario "Cielos & Eventos"** (Sprint 3): 15 fenómenos 2026-2027 (eclipses, meteoros, oposiciones).
- [x] **Auroras (Kp real NOAA)** y **Perseidas (radiant)** con mapa (Sprint 5), cobertura amplia (hemisferio norte).
- [x] **Refactor por fenómeno** (`data/2026`, `data/2027`) — base para todo lo anterior.

### Mejores opciones (roadmap evaluado)
- **Hecho (T1 + sprites)**: Ko-fi · contador + totalidad restante · mejores spots (duración×nubosidad) · enlace planificador IA · JSON-LD · PWA (instalar visible, iOS, offline, mapa móvil) · funnel · ayuda genérica · SEO/RRSS completo (og:image, @graph, robots/sitemap).
- **Hecho (Sprint 7)**: global 2026 (Islandia + europeas) · i18n ES/EN core · compartir RRSS.
- **Hecho (6 Ago, v0.29)**: i18n residual (welcome, offline, toast, instalación, spots, forecast) · **previsión Kp 3 días** (NOAA SWPC, pestaña Auroras, cache 10 min) · **Alertas Telegram** (canal `@eclipse2026osint` + bot `@eclipse_2026_osint_bot` admin; script `scripts/telegram_alert.py` con alerta diaria 09:00 y modo forecast; token en `.secrets/` fuera del repo).
- **Hecho (6 Ago, v0.30-v0.35)**: **icono Telegram** del canal generado y subido (`setChatPhoto`) · **bandas de visibilidad sombreadas por %** (isobandas 10/30/50/70/90/100 del diámetro solar; elementos besselianos NASA + Espenak/Meeus limitado por atardecer; **fusionadas con shapely → 9 KB**; 100% = franja NASA) · **etiquetas de % sobre el mapa** (en el punto de cada banda más cercano a la totalidad española) · **parcialidad activa por defecto** · **localStorage seguro para incógnito** · **optimización de pantalla** (mapa ~2× más alto: banner PRÓXIMO redundante eliminado, SEGURIDAD/countdown compactos, etiqueta "Fenómenos" fuera, banner de instalación solo móvil) · PWA instalable desde header/panel.
- **Próximo**: ajustar alertas tras el 12-Ago (cadencia) · calibración horarios 2027 con datos oficiales IGN · contornos de parcialidad con resolución más fina si se quiere (a costa de tamaño).
- **Ideas futuras**: calibración horarios 2027 con datos oficiales IGN · capa de tráfico/afluencia esperada (si hay datos públicos) · packs "qué llevar" · notificaciones locales del contador.

### Pendientes de infraestructura (servidor)
- **[PENDIENTE DECOMISIÓN] `deploy-anonimation`** (Docker, puerto 5000): anonimizador de documentos con IA (Flask + Gemini/Groq). **Parado manualmente** desde el 2-Ago-2026; `anonimizacion.viajeinteligencia.com` devuelve **502**. Para decomisar: `docker compose -f /home/deploy/anomination/deploy/docker-compose.yml down -v` + `docker image rm deploy-anonimation` (libera ~750 MB: imagen 702MB + volumen `deploy_uploads` 41MB) + **rotar la GEMINI_API_KEY** (visible en la config del contenedor) + decidir sobre `anomination_backup_20260724_1703` y sobre el DNS/nginx de anonimizacion.viajeinteligencia.com.
- **emergency.viajeinteligencia.com** (resuelto 6-Ago): el app está en `/var/www/emergency-dashboard` (Node, `PORT=3000`, `NODE_ENV=production`), PM2 `emergency-dashboard`. Se arregló liberando el puerto 3000 (myip PM2 redundante eliminado; el Docker myip sirve `myip.viajeinteligencia.com` en 3004). Verificado: web 200, `/api/health` 200, `/api/emergencies` 200.

### Sesiones pendientes (multiproyecto, para retomar ASAP)
- **[HECHO 06-Ago] MyIP: revisión de funcionalidades rotas**. Se reconstruyó el contenedor y se arregló: (1) **botón Ko-fi enorme** → la **CSP de nginx bloqueaba estilos/scripts inline** (`style-src` sin `'unsafe-inline'`); fix: CSP corregida en `/etc/nginx/sites-available/myip.viajeinteligencia.com` + botón compacto 46px circular; (2) **tarjeta "Usuarios Premium" (NaN) eliminada** + refs premium de la UI (xAI Grok, HowToGuides, AdvancedTools, AuthSection); (3) **historial por usuario verificado INTACTO** (backend devuelve 20 scans de mcasrom; los scans se guardan; requiere login por diseño). Commit `e9a3629` pusheado.
- **[RESUELTO 06-Ago] Eclipse caía para el usuario**: el artefacto `127.0.0.1 eclipse.viajeinteligencia.com` en `/etc/hosts` del server (añadido para pruebas headless) hacía que AdGuardHome devolviera 127.0.0.1 → el navegador conectaba a localhost → `ERR_ECH_FALLBACK_CERTIFICATE_INVALID`. Fix: eliminar la entrada + `systemctl restart AdGuardHome`. Verificado 200. **Lección**: no dejar entradas de prueba en `/etc/hosts` (usar `--resolve` en curl; re-añadir solo temporalmente para CDP).
- **[MyIP] Sprint 6 — Exportar Reporte PDF** (prioridad alta): endpoint `POST /api/export/pdf` + botón "📄 Exportar PDF" en dashboard/historial + i18n ES + pruebas. `PDFDocument` ya importado. 3-5 días. Detalle en `/home/deploy/myip/WAYAHEAD.md`.
- **[MyIP] Sprint C — Blog técnico SEO** (continuo): guías CVE / "cómo interpretar vulnerabilidades".
- **[MyIP] Pendientes menores**: 7 `portDefinitions` faltantes · unificar `sendEmail` (alerts.ts + server.ts) · opcional: endurecer CSP (mover script inline a archivo) · **revisar landing** (viajeinteligencia-landing: mapa embebido de emergency usa `emergencies_history.json` → obsoleto).
- **[Servidor] Decomisar `deploy-anonimation`** (Docker, ~750MB): `docker compose -f /home/deploy/anomination/deploy/docker-compose.yml down -v` + `docker image rm deploy-anonimation` + rotar GEMINI_API_KEY + decidir sobre backup y DNS/nginx de anonimizacion.viajeinteligencia.com.
- **[MigrationFlow] Lanzamiento PH 18-Ago-2026** (próximo hito): revisar estado antes de la fecha.
- **[Eclipse] Sin pendiente urgente** (consolidado v0.35).

### No aquí (pertenece a viajeinteligencia.com)
- Chat IA / planificador (solo enlace). Email capture / alertas push con BD (choca con sin-tracking; si se hace, en la plataforma). API pública con backend (los datos ya son JSON estáticos servidos por nginx).

## 📁 Estructura
```
eclipse-2026-osint/
├── server.py            # FastAPI: /api/forecast (por año), /api/aurora, /health (8700)
├── src/
│   ├── config.py        # constantes (puerto, TTL caché, fechas)
│   ├── forecast.py      # Open-Meteo + caché fichero por año (TTL 3h)
│   └── aurora.py        # Kp NOAA SWPC + caché (TTL 10 min)
├── data/
│   ├── 2026/cities.json + franja.geojson + visibilidad.geojson  # eclipse 2026 (IGN + NASA + bandas %)
│   ├── 2027/cities.json + franja.geojson   # eclipse 2027 (NASA línea central)
│   ├── events.json      # calendario 15 fenómenos 2026-2027
│   └── forecast_cache_{year}.json + aurora_cache.json  # cachés (generados)
├── frontend/
│   ├── index.html       # Leaflet PWA (tabs multi-fenómeno, contador, spots, ayuda, funnel, og, SEO)
│   ├── sw.js / manifest.json / iconos / og-image / robots.txt / sitemap.xml
│   └── vendor/          # Leaflet self-hosted
├── scripts/telegram_alert.py  # publica alertas al canal @eclipse2026osint (token en .secrets/)
├── deploy.sh
├── README.md
└── WAYAHEAD.md
```

## Sprint 7b — Instalacion PWA visible en moviles y tablets (5 Ago 2026)

- **Banner siempre visible** "📲 Instalar la app (gratis)" bajo el aviso de seguridad (antes el boton solo aparecia cuando el navegador disparaba beforeinstallprompt, que en iOS nunca ocurre y en Android exige interaccion).
- **Deteccion de plataforma**: Android/escritorio -> dialogo nativo de instalacion (prompt), con fallback robusto (catch de la promesa) a un modal con pasos; iOS -> pasos exactos "Compartir -> Anadir a pantalla de inicio".
- **Metas iOS** anadidas (apple-mobile-web-app-capable/status-bar/title) para modo standalone.
- Verificado headless: banner visible, modal con pasos Android y pasos iOS, 0 errores. SW v9.

## Sprint 7c — Selector de fenomeno en el panel + robustez de actualizacion (5 Ago 2026)

- **Selector de fenomeno** (dropdown) al inicio del panel, ademas de las pestañas: garantiza cambiar entre Eclipse 2026/2027, Perseidas, Auroras y Calendario incluso si el navegador no muestra las pestañas. Refactor a `switchTab(t)` compartido por pestañas y selector.
- **Toast "Nueva version disponible — recarga"**: el SW notifica al activarse para que el usuario sepa cuando hay actualizacion (evita quedarse con la version antigua cacheada).
- El problema reportado (solo se veia el mapa eclipse en movil) es CACHE del dispositivo (SW/HTTP viejo); el servidor esta verificado (headless movil: 5 tabs + selector + 2027 Cádiz + perseidas mapa). Para el usuario: borrar datos del sitio / reinstalar la PWA.

## Sprint 8 — No efimero: auto-rotacion, astronomia diaria y guias (5 Ago 2026)

- **"Proximo en el cielo" auto-rotativo**: hero que muestra SIEMPRE el siguiente fenomeno (desde events.json + fecha) con boton Ver y countdown al proximo evento (ya no fijo al 2026). Tras el 12-Ago rota a Perseidas -> Saturno -> Eclipse lunar -> Jupiter -> Geminidas -> Eclipse 2027.
- **"Hoy en el cielo"**: endpoint /api/sky (Open-Meteo forecast: amanecer/atardecer/UV max + fase lunar calculada por formula sinodica) con cache 24h. Panel que se auto-alimenta a diario.
- **Pestana Guias**: 4 guias evergreen (eclipse, meteoros, auroras, fotografia) — contenido permanente.
- Con esto el sitio es un portal perpetuo "que pasa hoy en el cielo", no un landing del eclipse. v0.24.

## ⚠️ Pendientes
- [ ] **Opción 5** (global + i18n + parcialidad) — post-12-Ago.
- [ ] Calibración horarios 2027 con datos oficiales IGN cuando los publique.
- [ ] Decidir sobre el beacon de Web Analytics de Cloudflare (consola limpia vs analytics) — opcional.
- [ ] Monitorizar el día 12-Ago (pico de tráfico, caché CF, forecast).
