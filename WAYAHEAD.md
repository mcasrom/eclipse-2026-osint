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

### Infra (06-Ago)
- **Disco 67% → 53%**: el salto 56%→67% era basura de **Docker** (imágenes viejas + build cache ~10GB reclamables tras los rebuilds de MyIP). `docker system prune -f` + `docker image prune -a -f` recuperaron ~4.2GB (incluida la imagen de deploy-anonimation 702MB). Verificado: contenedores healthy, sitios 200. **Lección**: tras cada rebuild de imagen, `docker system prune -f`.
- **Seguridad**: el repo `viajeinteligencia-landing` tenía un **token GitHub en la URL del remote** (caducado). Eliminado (`remote set-url`); el push ahora usa el credential store. **Revocar el token caducado** en GitHub por si estuvo válido.

### Mejoras de durabilidad (06-Ago, v0.39)
- **[Hito 1] Simulación del eclipse hora a hora** ✅ (v0.40): 65 footprints de la umbra (1-min, motor besseliano NASA) en `data/2026/simulacion.geojson` (45KB); panel con slider/play, **el mapa sigue la sombra** (panTo), sombra oscura + punto central, empieza en Islandia 17:30, y **estado por ciudad** (ventanas de totalidad IGN reales). Commits `cd977ba` + `986480f`.
- **[Hito 1b] Simulación Eclipse 2027** ✅ (v0.41): footprints de la umbra 2027 (60 pasos, besseliano NASA t0=10h) + simulación multi-año (2026/2027 según pestaña) + estado por ciudad con max_estimado. Commit 8062c11.
- **[Hito 2] Página por fenómeno**: deep-links `?tab=` (eclipse, 2027, perseidas, auroras, calendario, guias) con **título y descripción SEO por tab** + og. Commit `cb90e1f`.
- **[Hito 3] Calendario perpetuo + almanaque**: events.json ampliado a **27 fenómenos (2026-2028)** + **"Qué ver esta noche"** (fase lunar + próximo evento). Commit `bb7fd37`.
- Reutilizable para el eclipse 2027 (mismo motor). SW v32, v0.39, purgado.

### Pendientes de infraestructura (servidor)
- **[PENDIENTE DECOMISIÓN] `deploy-anonimation`** (Docker, puerto 5000): anonimizador de documentos con IA (Flask + Gemini/Groq). **Parado manualmente** desde el 2-Ago-2026; `anonimizacion.viajeinteligencia.com` devuelve **502**. Para decomisar: `docker compose -f /home/deploy/anomination/deploy/docker-compose.yml down -v` + `docker image rm deploy-anonimation` (libera ~750 MB: imagen 702MB + volumen `deploy_uploads` 41MB) + **rotar la GEMINI_API_KEY** (visible en la config del contenedor) + decidir sobre `anomination_backup_20260724_1703` y sobre el DNS/nginx de anonimizacion.viajeinteligencia.com.
- **emergency.viajeinteligencia.com** (resuelto 6-Ago): el app está en `/var/www/emergency-dashboard` (Node, `PORT=3000`, `NODE_ENV=production`), PM2 `emergency-dashboard`. Se arregló liberando el puerto 3000 (myip PM2 redundante eliminado; el Docker myip sirve `myip.viajeinteligencia.com` en 3004). Verificado: web 200, `/api/health` 200, `/api/emergencies` 200.

### NUEVO MICROSERVICIO (06-Ago): Country Intelligence OSINT
- **Qué**: dashboards de inteligencia geopolitica por pais (datos abiertos + IA futura). **Opción A ligera**: FastAPI + SQLite + cron + JSON estatico + PWA.
- **Live**: https://country.viajeinteligencia.com · **Repo**: https://github.com/mcasrom/country-intel (publico).
- **PM2**: `country-intel-api` (puerto 8710) — **solo ~8.5 MB RAM** (impacto minimo: PM2 total 568MB, disco 54%, swap ok).
- **Pipeline**: cron 03:00 (seed de referencia 13 paises x 11 indicadores: poblacion, PIB, inflacion, desempleo, IDH, moneda, region, renta pc, alfabetizacion, seguridad social, titulados + defensa GFP/SIPRI 2025: gasto, %PIB, personal, aviones, barcos, tanques) — 13 JSON. **Incluye MA (Marruecos), DZ (Argelia), EG (Egipto)**.
- **Email**: country@viajeinteligencia.com (Cloudflare Email Routing -> mybloggingnotes@gmail.com, regla ya existente).
- **vi-core embrio**: `src/core/` (CachedClient + BaseCollector) reutilizable.
- **Dashboard por pais (v5, commits `aeac75b`→`a02612d`)**: panel con **Resumen IA** (7 lineas), **Indicadores** (11), **Estructura etaria**, **Defensa** (gasto/%PIB/personal/aviones/barcos/tanques), **Riesgo**, **🧳 Riesgo visita pais** (nivel + consejos), **🛂 Ficha de viaje UK FCDO** (endpoint `/api/travel/{cc}` con caché 24h; alertas activas + partes clave Entry/Safety/Health), **Noticias** (proxy server `/api/news/{cc}`: GDELT con caché 1h + fallback Google News RSS — evita 429/CORS), **Alertas EMSC** (flynn_region + ventana 30 dias M3+, sin terremotos antiguos). **15 paises** (PT, AU). **🔍 Heatmap** (17 x 15), **⚖️ Comparador 1v1** (19 indicadores, 2 selectores), **🏆 Rankings** por indicador (top-15, menor-primero para inflacion/desempleo). **Acerca de**: funnel como **popup de bienvenida** al llegar (cierre ✕); Metodologia/Fuentes/About/Aviso legal como **tabs desplegables en fila horizontal** bajo el mapa (acordeon al clicar), Ko-fi. Server v0.2. Validado headless (sin errores JS).
- **Alto valor (commit `a9e3491`)**: **📈 Tendencias** (conteo agregado anonimo de fichas abiertas, sin cookies, ranking con barras) · **SEO** paginas `/pais/{code}` estaticas (title/description/OG/JSON-LD Country/canonical/hreflang) + `sitemap.xml` + `robots.txt` + OG/JSON-LD en home · **📤 Compartir** (Web Share/clipboard, texto+ficha) · **🗂️ Icon view** (toggle mapa <-> rejilla de banderas) · **deep-link** `?c=cc` (abre la ficha al llegar). Server v0.4.
- **🔍 Busquedas reales por pais (commit `ea74b82`)**: seccion "Qué se busca sobre este país" en cada ficha — Google Autocomplete via `/api/trending/{cc}` (8 temas: hoteles, precios, trabajo, vacaciones, vuelos, comida, seguridad, alquiler; sugerencias reales, caché 6h). Server v0.5.
- **Solución global de búsquedas (commit `d3511b5`)**: panel **🔍 Tendencias web** (`/api/trending/all`) — para cada tema (hoteles, precios, trabajo...) ranking de países por búsquedas reales de Google (precargado en el pipeline diario, caché 6h, respuesta ~25ms con caché). **🛂 Migración** por país: saldo migratorio (‰) + inmigrantes (% pobl.) con etiqueta receptor/emisor, incluido en resumen IA, heatmap y comparador. Server v0.6.
- **OG image de marca (commit `fc212df`)**: og.png 1200x630 generado con PIL + og:image/width/height/alt en home y paginas /pais/{cc} — preview RRSS con imagen.
- **Config unica (commit `ddea406`)**: valores fijos externalizados a `data/config.json` (TTLs, temas de busqueda, nombres, slugs FCDO, queries de noticias, limites, y frontend: META de paises, etiquetas, umbrales de riesgo/IDH/visita, parametros de alertas, zoom, listas heat/cmp/rank). Servido en `/api/config`; server v0.7 lee `CFG` con fallbacks; frontend lo consume en el arranque (applyConfig). Cambiar un umbral o anadir pais ya no requiere tocar codigo.
- **Evolución autónoma (1+2+3+4, commits `5573122`+`e6acd96`)**: (1) **Cobertura autónoma** — colector WorldBank VIVO `all-countries` (9 indicadores, retry/backoff, throttle, geo lat/lon de los 217 países desde el API, fallback al seed, conserva valores previos si el API falla) → **15→217 países**; el mapa lee geo de los datos (flag derivado, sin tocar META). (2) **Datos vivos** con cadencia (economía diaria, noticias 1h, búsquedas 6h, viaje 24h). (3) **`/api/health`** (last_run, edad de datos, stale, errores) + **badge de frescura** por ficha + heatmap limitado configurable (20/50/100/200/Todos). (4) **Auto-commit de datos**: el cron commitea+pushea `data/json`, `geo.json`, `seed`, `last_run.json` cuando cambian. Config: `sleep_worldbank`, `max_countries`, `stale_days`. **Pendiente manual**: monitor de uptime-kuma sobre `https://country.viajeinteligencia.com/api/health` (frescura, no solo uptime).
- **Respuesta a la crítica de rigor (commit `b85868f`)**: +12 indicadores WB (PIB PPA pc, esperanza de vida y saludable, homicidios, Gini, deuda pública, gasto sanitario/educativo, CO₂ pc, Internet, urbanización, fertilidad) + índices institucionales (Transparency CPI, RSF prensa, EIU democracia) para los 15 países. **Año por indicador** (periodo único 2023-2024, último año disponible persistido) y **fuente por bloque** (Banco Mundial/FMI, ONU, PNUD, UNESCO, SIPRI, TI, RSF, EIU). Nueva sección "📈 Desarrollo e instituciones" + heatmap (31 indicadores)/comparador/rankings ampliados. **Cache de WB por indicador (7d)** y **backfill sin red** para los 15 países (39 indicadores en ES). Nota metodológica en la pestaña Metodología. **Pendiente**: WB throttled hoy → los 217 países rellenarán los indicadores con lag vía cron nocturno cuando el API se recupere (periodo 2023-2024).
- **Notas metodológicas al pie (commit `ae680e7`)**: 33 definiciones con fuente y alcance en `config.json` (notas); tooltip fuente+año en cada celda + año visible; aviso dinámico de fuentes en cada ficha (Banco Mundial vs valores de referencia); notas en Indicadores, Desarrollo, Defensa, heatmap, comparador y rankings. Rigor estilo OCDE/BM.
- **Calidad de datos sistémica en todas las series (commit `06373d1`)**: fiabilidad por indicador (37 ratings alta/media/baja) con badge en las notas; resumen de fiabilidad por ficha; desglose de defensa por rol (cazas/transporte/entrenadores/helicópteros/submarinos) con % de combate sobre el total («45 de 228 aeronaves son de combate»); caveats de representatividad en notas (internet UIT, homicidios cobertura, titulados ISCED, Gini, deuda, desempleo, urbanización, gasto educativo); bloque **Homogeneidad y tiempos de captura** en Metodología; cazas/submarinos en heatmap/comparador/rankings.
- **[HECHO 07-Ago] Country Intel: cobertura de datos + fixes (commits `4ca3eef`, `d17b0d2`)**. (1) **net_mig corregido**: `SM.POP.NETM` es valor absoluto → convertido a tasa por 1000 hab usando población (KZ antes -7368‰ → ahora -0.36‰). (2) **Población de indicadores WB**: relanzado el pipeline con `sleep_worldbank=8s` (evita throttling) → **esperanza_vida 217, internet_pct 184, pib_ppa_pc 197, net_mig 217** (antes ~15). Los escasos (Gini 15, CO₂ 15, fertilidad/urbanización 17, deuda/gasto ~1-2) se rellenan con el cron nocturno; Gini/HALE son genuinamente antiguos en WB. (3) **Frontend**: renta_pc/PIB PPA redondeados a enteros; estructura etaria muestra «—» sin datos; **toggle tema claro/oscuro** (body.light + localStorage + botón 🌙/☀️ en el header). Nota: IDH/defensa/edad/índices institucionales siguen solo para los 15 países del seed (no están en WB).
- **[HECHO 07-Ago] Country Intel v0.8: enriquecimiento global + version (commit `304100a`)**. **region** desde geo WB (217/217), **moneda + IDH** estáticos (188/217, `data/enrich.json` PNUD/ISO) — el pipeline los emite para todos los países. Mejora de cobertura con la corrida cacheada: **urbanizacion y fertilidad 217**, gasto_educacion 134, gini 70 (antes ~15). Kazajistán pasó de 10 a 18 indicadores. **v0.8.0 en el pie** del site. Pendiente: co₂ pc y esperanza vida saludable siguen 0 (escasos/throttle, el cron nocturno los reintenta).
- **[HECHO 07-Ago] Country Intel: viabilidad de tendencias de búsqueda (commit `9ce8caf`)**. **SÍ es viable** — era un bug: para países fuera de los 15 curados, el query usaba el **código ISO** (p. ej. `my`) en vez del nombre real → Google devolvía basura («hoteles my mcdonalds», «mi trabajo aquí ha terminado»). Fix: usar el **nombre real del país desde `geo.json`** (Malaysia, Chile...) como fallback. Verificado: `my`→Malaysia («hoteles malaysia», «trabajo malaysia»), `cl`→Chile («chile vuelos baratos», «chile comida típica»...) en los 8 temas. La cobertura de nombres reales ahora alcanza los 217 países.
- **[HECHO 07-Ago] Country Intel: botones de búsqueda por país (commit `f0a2f3d`)**. Cada patrón real de «Qué se busca sobre este país» es ahora un **chip 🔍 clickeable** que abre la consulta en Google (`google.com/search?q=...`). Verificado headless (40 chips, p. ej. `q=chile hoteles limitada`).
- **[HECHO 07-Ago] Country Intel: busquedas accionables (commit `6395b71`)**. Selector de buscador Google/Bing/Startpage (re-renderiza enlaces); botón 🔍 por tema (pais+tema); botón 📋 copiar prompt por sugerencia (data-q + encodeURIComponent, sin problemas de comillas). Validado headless (48 enlaces, 40 copiar, cambio de motor OK).
- **[HECHO 07-Ago] Country Intel: fix contraste comparador (commit `1c6b61c`)**. En tema claro, `.ov table` tenía fondo fijo oscuro `#111827` y el texto oscuro se fundía con él (datos indistinguibles). Añadido override `body.light .ov table` (fondo blanco, texto oscuro, bordes claros). Verificado headless: diff 685 (legible) en tema claro.
- **[HECHO 08-Ago] Country Intel: SEO 217 países + protección de recursos (commit `6dae21c`)**. (1) **217 páginas `/pais/{code}`** (antes solo 15 curados): nombre real vía geo.json, indicadores reales del JSON estático (población, PIB, IDH, inflación, desempleo, internet, esperanza de vida, urbanización, moneda), title único por país, JSON-LD Country con población/continente, canonical + hreflang es. (2) **Sitemap 218 URLs** (antes 16). (3) **Rate-limit anti-bots** 60 req/min/IP en `/api/country`, `/api/news`, `/api/trending` (en memoria, respeta X-Forwarded-For) — frena los ~4.240 bots/scrapers que martilleaban /api/country; Googlebot indexa `/pais` sin limitar. Verificado: ráfaga 70 → 55 OK + 15×429. **Coste ~0 recursos** (datos ya en disco); RAM 52.6→45.9MB. Todo en prod (200 con UA Googlebot, sitemap XML válido).
- **Backlog**: resumen IA LLM (1/dia, si hay API key) · alertas FIRMS/ReliefWeb · timeline/Chart.js (historicos) · enviar sitemap a Google Search Console · export PDF/API (PRO).

### Sesiones pendientes (multiproyecto, para retomar ASAP)
- **[HECHO 06-Ago] MyIP: revisión de funcionalidades rotas**. Se reconstruyó el contenedor y se arregló: (1) **botón Ko-fi enorme** → la **CSP de nginx bloqueaba estilos/scripts inline** (`style-src` sin `'unsafe-inline'`); fix: CSP corregida en `/etc/nginx/sites-available/myip.viajeinteligencia.com` + botón compacto 46px circular; (2) **tarjeta "Usuarios Premium" (NaN) eliminada** + refs premium de la UI (xAI Grok, HowToGuides, AdvancedTools, AuthSection); (3) **historial por usuario verificado INTACTO** (backend devuelve 20 scans de mcasrom; los scans se guardan; requiere login por diseño). Commit `e9a3629` pusheado.
- **[RESUELTO 06-Ago] 503 en nearme con WireGuard VPN**: mismo bug que eclipse - artefactos 127.0.0.1 en /etc/hosts (myip, nearme, migrationflow) hacían que AdGuardHome devolviera 127.0.0.1 al móvil via VPN -> conectaba a su localhost -> 503 en filtros. Fix: eliminar entradas + restart AdGuardHome. **LEGAJO**: no usar /etc/hosts para pruebas headless; usar --resolve y limpiar siempre.: el artefacto `127.0.0.1 eclipse.viajeinteligencia.com` en `/etc/hosts` del server (añadido para pruebas headless) hacía que AdGuardHome devolviera 127.0.0.1 → el navegador conectaba a localhost → `ERR_ECH_FALLBACK_CERTIFICATE_INVALID`. Fix: eliminar la entrada + `systemctl restart AdGuardHome`. Verificado 200. **Lección**: no dejar entradas de prueba en `/etc/hosts` (usar `--resolve` en curl; re-añadir solo temporalmente para CDP).
- **[HECHO 06-Ago] MyIP Sprint 6 — Exportar Reporte PDF**: endpoint `POST /api/export/pdf` (pdfkit, score/datos/puertos/blacklist/resumen) + botón "📄 Exportar PDF" en la dashboard. Commit `320bfab`.
- **[HECHO 06-Ago] MyIP Sprint C — Blog técnico SEO**: 3 nuevas guías (7 puertos más atacados · DNSBL/blacklist · escaneo de puertos) → 13 guías. Commit `37eabfc`. **README del repo actualizado** — commit `9f85647`.
- **[HECHO 06-Ago] MyIP pendientes menores**: 7 `portDefinitions` nuevos (21/25/53/3389/5432/6379/27017) · `sendEmail` unificado (exportado de alerts.ts) · **landing limpia** de Emergency Dashboard (row, ticker, panel pulse, enlace muerto; commit `b91c172`; token GitHub caducado fuera del remote URL). Commit MyIP `475e73c`. Queda: endurecer CSP (opcional).
- **[Servidor] Decomisar `deploy-anonimation`** (Docker, ~750MB): `docker compose -f /home/deploy/anomination/deploy/docker-compose.yml down -v` + `docker image rm deploy-anonimation` + rotar GEMINI_API_KEY + decidir sobre backup y DNS/nginx de anonimizacion.viajeinteligencia.com.
- **[HECHO 06-Ago] NearMe Sprint 41 - Timeline/playback + track patterns UI**: backend (tabla event_history con snapshots al cambiar, GET /api/timeline activos por ventana, GET /api/event/{id}/history track patterns, cleanup_history_retention(365) + cron diario 03:00) + frontend (panel playback 7 dias con slider temporal, y patron por evento con tira de estados y cambios de nivel) - commits c4cfef3 + b41291c + 1028596. Estimacion disco 1 ano de historial: ~0,8-1,8 GB (Postgres), estable con rotacion de 365 dias.
- **[HECHO 06-Ago] NearMe: narrativa de uso** - paso 5 del onboarding (Timeline + Patron) en ES/EN + hint del panel timeline. Commit f5d9244.
- **[DECISIÓN] mapasdeincendios.es/incendios-hoy**: sitio **fiable/transparente** (disclaimers honestos, cita NASA FIRMS/AEMET/EFFIS/MITECO, páginas legales). **NO se scrapea**: NearMe ya usa la misma fuente autoritativa (NASA FIRMS directo: MODIS + 2 VIIRS). Opcional futuro: añadir EFFIS perímetros quemados desde la fuente oficial Copernicus.
- **[HECHO 06-Ago] MigrationFlow pre-PH revisado y LISTO para el 18-Ago**: sitio 200 (mapa, choropleth, Frontex, PWA, SEO fallback, JSON-LD), `PH_LAUNCH_PACK.md` completo (tagline, descripción, FAQ, maker comment, checklist día-1, borradores X/Telegram/Reddit/Show HN), galería 8 capturas + demo_30s.mp4/gif. **Pendiente = ejecución del día-1** (D-2 16-Ago: subir borrador PH; 18-Ago: publicar + maker comment + oleada RRSS).
- **[HECHO 06-Ago] NearMe: fix UI solape (commit `2aac9a5`)**. El selector de idioma (ES) se solapaba con el botón compartir (ambos `right:58px`); idioma movido a la izquierda del share (`right:102px`). Verificado headless sin solapes.
- **[HECHO 06-Ago] NearMe: panel 📊 Tendencias / Estadísticas (commit `95642ec`)**. Tabla `daily_stats` pre-agregada por **cron 23:00** (script `compute_daily_stats.py` con backfill 30 días): embalses nivel medio, RENFE retraso medio y nº de retrasos, FIRMS incendios/FRP/hectáreas estimadas (proxy 0.3 ha/MW), MITECO ICA medio y días Regular/Malo. Endpoint `/api/stats/trends`. Pestaña "📊 Tendencias" en el frontend con 7 gráficos SVG caseros (sin dependencias, offline-friendly). Consumo mínimo: un job diario de segundos + JSON pequeño. Validado headless (7 charts, sin errores).
- **[HECHO 07-Ago] NearMe: UX panel Tendencias (commit `a962376`)**. Cada gráfico ahora muestra **título, unidad, descripción** de qué mide y cómo se calcula, último valor y **rango**; aclaraciones de interpretación (registros RENFE = tren·parada; detecciones de incendio = puntos de calor satelital; lecturas de calidad = mediciones por estación, no días) + bloque de notas al pie. Validado headless (7 charts, sin errores).
- **[HECHO 07-Ago] NearMe: UX usuario final (commit `974a4ea`)**. Tarjeta **📍 Resumen de tu zona** (texto natural con conteos por tipo + enlaces a Tendencias/Playback); filtro **⏱ Solo activos** (oculta expirados); botón **📤 Compartir zona** con deep-link `?lat&lon&r` (se aplica al cargar); lista de eventos **ordenada por severidad + recencia** (`getFilteredEvents` estable para lista/detalle/share). Validado headless.
- **[FIX 07-Ago] NearMe: botones desbordados en móvil (commit `ddb5520`)**. La fila de controles (7 botones) se salía de pantalla; "Solo activos" y "Compartir zona" movidos a su **propia fila** + `flex-wrap` en las filas de controles. Verificado headless a 360px: fila propia y dentro del viewport.
- **Mejora potencial futura NearMe: cobertura de inundaciones (validada)**: hoy las inundaciones se cubren indirectamente con los avisos de lluvia de ProtecciónCivil (precursores). Si el producto crece a global o se quieren mapas validados por expertos, opciones: (1) **GloFAS** (Global Flood Awareness System, Copernicus, API pública) — la más limpia; (2) re-escanear **Copernicus EMS** cuando publiquen un feed JSON (el portal actual es HTML). NO necesario ahora.
- **[HECHO 06-Ago] NearMe: auditoría de colectores + 2 arreglados (commit `df8c95c`)**. De los 16, 2 producían 0 eventos: **MITECO-CalidadAire** (fallaba por SSL del certificado roto del emisor → `verify=False`) y **ProtecciónCivil/AEMET avisos** (endpoint con código de área **`esp`** no `es` + el archivo de datos es un **GTAR** con 453 XML CAP que el zip/XML directo no parseaba → extracción `<?xml`…`</alert>` + geolocalización por **centroide del polígono CAP**, antes caían en Madrid). Resultado: **miteco 240 eventos/24h** (6 alert) y **aemet_avisos 439/24h** (14 alert, 192 warning). Copernicus EMS/GWIS retirados (0, esperado). **Nota**: `/api/status` `events_24h` cuenta el output bruto de los colectores antes de dedupe/expiración (p. ej. OpenAQ 97k bruto → 148 activos en BD); no es ruido real pero el pipeline procesa ~100k/ciclo.
- **[HECHO 06-Ago] NearMe: limpieza y arreglos tras analisis**. (1) **/etc/hosts**: eliminado artefacto residual `127.0.0.1 eclipse.viajeinteligencia.com` (riesgo de bug VPN/cert) + restart AdGuardHome → resuelve a IP real. (2) **AEMET**: decode robusto con fallback latin-1 (antes 'utf-8 codec can't decode byte 0xd3'). (3) **Copernicus GWIS+EMS retirados**: el feed de activaciones se movio a portal web sin JSON (mapping.emergency.copernicus.eu); producian 0 eventos y ~1060x HTTP 301 + 825x 404/dia; incendios cubiertos por NASA FIRMS y terremotos por USGS (colector DGT). URLs muertas eliminadas de config. (4) **Fix CRITICO PM2**: `--update-env` reseteo el interpreter a `python3`/`node` del sistema → nearme-api crash-loop (ModuleNotFoundError dotenv); recreado con `--interpreter /home/deploy/nearme-osint/venv/bin/python` + `pm2 save`. **Leccion**: no usar `pm2 restart --update-env` en procesos con venv (re-crear con interpreter explicito). Commit `68d0c29`.
- **[HECHO 06-Ago] Eclipse: notificaciones push + Telegram próximos eventos (commit `33839bf`)**. **Push PWA**: claves VAPID ECDSA generadas en `/home/deploy/.secrets/eclipse_vapid.json` (fuera del repo), endpoints `/api/push/{vapid-key,subscribe,unsubscribe}`, `src/push.py` (pywebpush), botón **🔔 Recordatorios** en el header (solicita permiso, suscribe con la clave pública, muestra estado), SW **v35** con handlers `push`/`notificationclick`, script `scripts/send_push_alerts.py` (eventos próximos en 14 días con **dedupe diario** en `data/push_sent.json`) + **cron 08:00**. **Telegram**: el mensaje diario (09:00) ahora lista los **próximos 3 eventos en 14 días** con notas. Validado: endpoints subscribe/unsubscribe OK, SW y botón servidos públicamente (Cloudflare bloquea headless, verificado por curl). `data/push_subs.json`/`push_sent.json` en .gitignore.
- **[FIX CRITICO 06-Ago, commit `7698a77`]** la insercion del boton push dejo una llave `}` huerfana en el JS inline de index.html -> el script entero fallaba a parsear y la pagina no renderizaba (ni mapa ni zonas de aurora). Eliminada la llave extra + SW v36. Verificado con node --check sobre el HTML publico. (Cloudflare bloquea el headless, no es fallo de la app.)
- **Backlog Eclipse**: paridad de datos **2027** (bandas de visibilidad/parcialidad como en 2026) — requiere reconstruir el pipeline besseliano NASA+shapely que generó los geojson de 2026 (script puntual no versionado); versionar el generador para reutilizarlo. Opcional: ranking "dónde verlo" por nubosidad, vida en vivo del 12-Ago-2026.

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

## Sprint 9b — NearMe fix: embalses invisibles (8 Ago 2026)

- **Síntoma**: el embalse de Alarcón (1112 hm³, Cuenca) no aparecía en el mapa, aunque embalses menores sí.
- **Causa raíz**: la fuente `estadoembalses.es` no renueva `ultima_lectura` de todos los embalses; el colector ponía `expires_at = ultima_lectura + 6h` → con lecturas viejas (Alarcón, Contreras, La Toba +80 más) `expires_at` quedaba en el pasado → `/api/nearby` (filtra `expires_at > NOW()`) los excluía. **83 embalses invisibles** pese a estar en la BD.
- **Fix**: `EMBALSE_TTL_DAYS = 7` (expiración desde el momento de recolección, no desde `ultima_lectura`). El colector corre cada 30 min y refresca `expires_at`, así que el dato es estable. Verificado: 0 expirados (antes 83), 452/452 visibles, Alarcón en `/api/nearby` y en prod. Commit `54ba2a2`, WAYAHEAD NearMe `38a97b9`.
- **Sin impacto en recursos**: solo cambia la fecha de expiración al insertar.
- **Siguiente (Opción 1, `e47eca5`)**: frescura visible — la descripción del embalse incluye "Medición: DD/MM/AAAA HH:MM" (la `ultima_lectura` real) y el popup del mapa + modal de detalle muestran `freshnessBadge(updated_at)` (verde <30min / naranja <2h / rojo ≥2h). El dato nunca desaparece del mapa y el usuario ve cuándo se midió. WAYAHEAD NearMe `e73d713`.

## Sprint 9c — Monitorización del ecosistema con uptime-kuma (8 Ago 2026)

- **Objetivo**: centralizar la salud de todos los servicios en un solo panel con histórico y alertas. Coste de recursos ~0 (uptime-kuma ya corría; solo se añadieron monitores).
- **Estado previo**: uptime-kuma tenía 6 monitores desactualizados (2 muertos de georisk decomisionado, faltaban casi todos los servicios vivos).
- **Hallazgo de despliegue**: el contenedor Docker monta SOLO el volumen `/var/lib/docker/volumes/uptime-kuma/_data` → `/app/data`. La BD `/opt/uptime-kuma/data/kuma.db` (donde estaban los monitores originales) estaba **huérfana**. Se copió la BD buena al volumen para que kuma la cargue.
- **Monitores añadidos (11)**: nearme `/health`, country `/api/health`, eclipse `/health`, myip (dominio público, el `127.0.0.1` interno no funciona desde el contenedor), centro-juego, migrationflow `/health`, intelligence-hub `/api/count`, landing-pulse `/api/stats/pulse` (vía IP directa `178.105.80.193` + Host header + `ignore_tls`, porque Cloudflare da 403 a kuma en `/api/*`), corrupcion `/health`, wiki, sieg-security (acepta 401).
- **Monitores desactivados**: checks de puerto obsoletos `viajeinteligencia`(3000) y `gc-motors`(3008) — Cloudflare no expone puertos no-80/443, ya cubiertos por monitores HTTP.
- **Estado final**: **12/12 monitores UP**. kuma ~141MB RAM, carga servidor 0.82 (estable). Backup BD en `/opt/uptime-kuma/data/kuma.db.bak-20260808`.
- **Nota**: para futuros cambios, editar SIEMPRE la BD del volumen (`/var/lib/docker/volumes/uptime-kuma/_data/kuma.db`) con kuma detenido, no `/opt`.

## Sprint 9d — Country fix: rate-limit rompía comparador/popups (8 Ago 2026)

- **Síntoma**: tras el rate-limit anti-bots, comparador y heatmap de Country sin datos, y popups del mapa (ej. Italia) con "Población: — PIB: — Renta pc: —".
- **Causa raíz**: el frontend carga los 217 países en ráfaga (fetch en paralelo). Rate-limit de 60/min (luego 500) cortaba la ráfaga → 429 → `ALL` incompleto. Cloudflare agrupa usuarios tras pocas IPs → comparten cuota y agotan el límite.
- **Fix**: **3000 req/min por IP** en `/api/country`, `/api/news`, `/api/trending` — frena bots masivos pero SIEMPRE deja pasar la carga legítima (217 × usuarios).
- **Verificado**: 2 cargas completas seguidas (434 req) → 0 errores. Italia: 59.0M · 2.38T · $40.430. Commits `cf6bbf9` + `4e02e45` (WAYAHEAD country).
- **Lección**: al añadir rate-limit a un servicio cuyo frontend hace carga masiva, probar SIEMPRE la ráfaga del propio frontend; el límite debe ser > picos legítimos × usuarios tras la misma IP de proxy.

## Sprint 9 — Landing v3 viajeinteligencia.com: hub en vivo del ecosistema (8 Ago 2026)

- **Landing rediseñada en 3 bloques**: OSINT en vivo · Para la Fundación (Centro de Juego RyM) · B2B/lanzamientos. Proyectos en construcción marcados con candado 🔒 (Tools, MigrationFlow, Fundación).
- **Pulse API v2** (`landing-stats-api`): agrega en vivo NearMe, MyIP, Country, Eclipse, Intelligence Hub (news.db) y SIEG + ticker con los últimos runs de colectores NearMe. Cada bloque independiente; si una fuente falla se reporta, nunca se inventa.
- **10 gráficos en vivo** con sparklines SVG y CTA (incendios, embalses, ICA, RENFE, escaneos, países, cielos, bans, noticias).
- **Sección Fuentes** con narrativa "Cada dato, verificable en su origen" + agrupación por dominio (Geofísica, Incendios, Meteorología, Medio ambiente, Movilidad, Energía, Socioeconómico, Marítimo).
- **PWA**: manifest + service worker (shell cache-first, APIs en red) + botón de instalación + sección "Lleva el pulso contigo". Fix content-type nginx (`application/manifest+json` en mime.types global).
- **SEO/RRSS**: og-v6.png 1200×630 generado con Chromium+fuentes web, favicon v2, apple-touch-icon, meta og:locale/twitter:site. Sitemap regenerado (quitados georisk/verifica/gc.motors muertos).
- **UX**: toggle claro/oscuro persistido (localStorage + prefers-color-scheme), FAQ, nota de privacidad, enlaces externos en pestaña nueva, animaciones de entrada con `prefers-reduced-motion`.
- **Ko-fi** (ko-fi.com/m_castillo) con icono de taza SVG en hero, sección Empezar y footer.
- **Analítica propia**: `POST /api/visit` (sendBeacon, IP hasheada sha256, sin cookies, rate-limit 30/5min) + widget de estadísticas en footer + dashboard `/analytics.html` (auth básica, reutiliza htpasswd de SIEG). Endpoint `/api/visit/summary` con byDay/byHour/topPaths/topReferrers.
- **Seguro de vida**: repos GitHub privados `viajeinteligencia-landing` y `landing-stats-api`. Secreto Resend movido de `ecosystem.config.cjs` a `.env` gitignored (se carga con `--env-file=.env`, Node 22).
- **Monitorización**: formato de log nginx con `host=` añadido para atribuir tráfico por dominio destino (ranking de atractivo por servicio).

## 🚀 Sprint activo: MigrationFlow · Product Hunt 18-Ago (ejecución, no código)
- Sitio **listo para producción** (verificado 07-Ago): HTTP 200, PM2 online, PWA+SEO+JSON-LD, `/health` 200, `PH_LAUNCH_PACK.md` completo.
- **Checklist a ejecutar por el usuario**: D-2 (16-Ago) subir borrador PH · D-1 (17-Ago) preparar RRSS sin publicar · 18-Ago 00:00 PT publicar + maker comment · 0-2h primer círculo · mañana r/... + X · tarde Show HN · responder comentarios <1h · D+1 thank-you + `/analytics`.
- **Siguiente sprint (recomendado)**: Country Intel **resumen IA LLM** (1/día) + **monitor uptime-kuma sobre `/api/health`** (frescura de datos).

## Sprint 9e — Alertas proactivas: healthcheck del ecosistema por Telegram (8 Ago 2026)

- **Objetivo**: aviso temprano cuando un servicio cae. Complementa a uptime-kuma (panel visual + histórico) con alertas proactivas.
- **Intento 1 — notificación nativa de kuma por SQL**: creada notificación `telegram-alertas` (provider telegram) + asociación a los 12 monitores vía SQL directo en la BD del volumen. **No funciona**: kuma no activa el envío en memoria al insertar `monitor_notification` a mano (ORM RedBeanPHP gestiona la relación M:N; el `type` del provider no se carga, y el login admin no está disponible para configurarlo por la UI). Lección: **las notificaciones de kuma se configuran por la UI, no por SQL**.
- **Solución — `ecosystem-healthcheck.sh`** (`/home/deploy/scripts/`): verifica los 12 servicios (mismos endpoints de kuma), avisa por Telegram (mismo bot `nearme_status_bot` + chat_id de NearMe) **solo en cambios de estado** (down/recovery), con estado persistido en `state/ecosystem.state`. Cron `*/5`.
- **Verificado**: down→"🚨 ECOSISTEMA DOWN: myip(502)" → recovery→"✅ ECOSISTEMA OK de nuevo". sendMessage confirmado ("enviado: True"). myip restaurado (200).
- **Recursos**: ~0 (curl cada 5 min, 12 peticiones ligeras). Carga 0.30, swap bajó a 876MB.
- **Pendiente (opcional)**: configurar notificación nativa de kuma por la UI (login admin) para tener alertas + panel en uno solo.

## Sprint 9f — Landing: Fundación RyM activa + acceso al panel de estado (8 Ago 2026)

- **Fundación RyM**: la fila pasó de "en construcción/próximamente" a **activa** — `boinasverdes.es` verificado (200, "Fundación de los Boinas Verdes Españoles"). Descripción real + enlace "Visitar →" (target blank).
- **Panel de estado (uptime-kuma)**: se mantiene **privado** (decisión de producto: no exponer infraestructura/nombres de servicios/latencias).
- **Aclaración de URLs (confusión resuelta)**: el dominio `status.viajeinteligencia.com` NO era kuma — sirve el **mapa fail2ban de SIEG Security** (`/var/www/html`, raíz). kuma estaba oculto en `status.../dashboard`.
- **Subdominio dedicado para kuma**: creado **`uptime.viajeinteligencia.com`** → registro A grey-cloud en Cloudflare + vhost nginx + cert Let's Encrypt (plugin nginx) + auth básica (htpasswd). kuma ahora tiene URL propia y clara, separada del mapa fail2ban.
- **Enlaces de la landing actualizados**: "monitoreo" en la barra superior + "📡 Monitoreo del ecosistema" en el footer → `uptime.viajeinteligencia.com`.
- **Commit**: `3402236` (Fundación activa) + `3813659` (enlaces uptime).

## Sprint 10 — SEO técnico por subdominio (NearMe + MyIP) (8 Ago 2026)

- **Motivación** (análisis SME): el dominio raíz fragmenta autoridad SEO; NearMe compite con landing mono-propósito (incendiohoy.es) usando las mismas fuentes FIRMS. Subdominios deben rankear por su keyword.
- **NearMe** (commits `a714af9`, `82e5dcb`):
  - `<title>`/meta/og/twitter en **español** enfocado a keyword: "Incendios en vivo España · Mapa de eventos en tiempo real".
  - `<link rel="canonical">`, `robots.txt` (disallow /admin y /api), `sitemap.xml`.
  - **Página evergreen `/firms`** ("¿Qué es FIRMS y cómo detecta incendios por satélite?") — contenido informativo indexable con CTA al mapa. Ruta servida por el server (FileResponse), coste ~0.
  - **IndexNow**: key `133a9cae...` en `/indexnow.key` + ping 202 a Bing/Yandex.
- **MyIP** (commits `64d1e34`, `8d9241f`):
  - `robots.txt` + `sitemap.xml` en `public/` (incluidos en build Vite) y copiados al `dist/` del contenedor (producción inmediata sin rebuild).
  - **IndexNow** key + ping 202.
  - Nota: `/robots.txt` antes devolvía el fallback SPA (HTML); ahora sirve el archivo real (text/plain).
- **Coste recursos**: ~0 (solo HTML/meta/estáticos, un endpoint). Carga 0.48, RAM 2.1G libres.
- **Pendiente siguiente**: título/meta por keyword en Eclipse, landing indexada; replicar IndexNow si hace falta.

## Fix 10a — NearMe: selector de radio 50/200/500 km bloqueado (8 Ago 2026)

- **Síntoma**: los botones 50/200/500 km no respondían; solo 50 km parecía activo. El usuario hacía clic en 200/500 y nada cambiaba.
- **Causa raíz (2 niveles)**:
  1. `localStorage.setItem('nearme_radius', km)` en `setRadius()` lanzaba **`DOMException: The quota has been exceeded`** (el storage del navegador estaba lleno, probablemente por `nearme_guest_alerts`/`nearme_alerts_seen` acumuladas).
  2. Como no había try/catch, la excepción **cortaba `setRadius()` a mitad**: nunca llamaba a `updateRadiusBtns()`, `updateMap()` ni `loadEvents()` → el botón no se activaba ni el mapa cambiaba.
- **Fix**: try/catch en las escrituras a localStorage de las funciones críticas: `setRadius`, toggle de filtros, `setGuestLocations`, `setGuestAlerts`. El radio ahora funciona aunque el storage esté lleno (el guardado falla en silencio, la UI no se bloquea).
- **Diagnóstico**: el headless no reproducía el bug porque su localStorage estaba vacío; se detectó con el test que llena localStorage antes de cargar + captura de `pageerror`. Confirma la regla: **nunca dejar que localStorage.setItem pueda romper la UI**.
- **Verificado**: con localStorage lleno, click en 200/500 activa el botón y sin errores JS. Commit `302fd9d`.

## Sprint 10b — Cierre SEO: Eclipse + Landing (8 Ago 2026)

- **Eclipse** (commit `e0825bf`): ya tenía title/meta ES por keyword, canonical, robots y sitemap (del trabajo anterior). Solo faltaba **IndexNow**: añadida key `133a9cae...` en `frontend/indexnow.key` (nginx `try_files` la sirve directo). Ping **202**.
- **Landing** (commit `c920d63`): añadido **`<link rel="canonical">`** (faltaba) + **IndexNow key** (`indexnow.key`, servida 200). Robots y sitemap (9 subdominios) ya existían. Ping **202**.
- **Estado SEO del ecosistema tras el Sprint 10 completo**: NearMe (title ES, canonical, robots, sitemap, /firms, IndexNow), MyIP (robots, sitemap, IndexNow), Eclipse (todo + IndexNow), Landing (title, robots, sitemap, canonical + IndexNow). **Todos los subdominios rankean por su keyword con IndexNow activo.**
- **Coste recursos**: ~0 (archivos estáticos + 1 key por dominio). Carga <0.3, RAM estable.

## Sprint 10c — Landing: acceso rápido a herramientas primero (8 Ago 2026)

- **Motivación** (análisis SME): para el 90% del tráfico de búsqueda el log técnico en vivo es "ruido antes de la respuesta". Un visitante que busca "incendios ahora" quiere la herramienta, no el log.
- **Cambios** (commit `71f0193`):
  - Nueva sección **`#acceso`** justo tras el hero: 6 tarjetas de acceso directo (NearMe, MyIP, Eclipse, Country, Centro de Juego, Intelligence Hub) con icono, descripción, CTA y fuentes. Tarjetas clicables completas.
  - **CTA del hero** "Usar una herramienta →" apunta a `#acceso` (antes a `#datos`/log). "Ver datos en vivo" queda como ghost button.
  - **Nav superior** añade "acceso" como primer elemento.
  - El log en vivo (`#datos`) y el resto se mantienen, ahora después del acceso rápido.
- **Verificado**: orden DOM `acceso` → `datos` → `osint`; render headless 200; las 6 tarjetas presentes.
- **Coste recursos**: ~0 (solo HTML/CSS).

## ⚠️ Pendientes
- [ ] **Opción 5** (global + i18n + parcialidad) — post-12-Ago.
- [ ] Calibración horarios 2027 con datos oficiales IGN cuando los publique.
- [ ] Decidir sobre el beacon de Web Analytics de Cloudflare (consola limpia vs analytics) — opcional.
- [ ] Monitorizar el día 12-Ago (pico de tráfico, caché CF, forecast).
- [ ] **Próximo sprint: notificaciones nativas de uptime-kuma por la UI** (email/Telegram) — el SQL directo no activa el envío en memoria (kuma no respeta la tabla monitor_notification insertada a mano). Canal ya probado con healthcheck propio (ver Sprint 9e); la notificación `telegram-alertas` existe en la BD de kuma pero requiere configurarla desde la UI (login admin) para que kuma la envíe.