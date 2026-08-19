import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

BASE = Path("/home/deploy/eclipse-2026-osint")
FRONT = BASE / "frontend"
SITE = "https://eclipse.viajeinteligencia.com"

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
         "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_es(iso):
    try:
        d = datetime.fromisoformat(iso)
        return f"{d.day} de {MESES[d.month - 1]} de {d.year}"
    except Exception:
        return iso


def slugify(name, date):
    s = name.lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return f"{s}-{date}"


def page_html(ev):
    slug = slugify(ev["name"], ev["date"])
    nombre = ev["name"]
    fecha = fecha_es(ev["date"])
    nota = ev.get("note", "")
    visible = ev.get("visible", "España")
    desc = f"{nombre} el {fecha}: {nota} Visible desde {visible}. Datos y mapa interactivo."
    schema = {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": f"{nombre} · {fecha}",
        "startDate": ev["date"],
        "endDate": ev["date"],
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "image": "https://eclipse.viajeinteligencia.com/og-image.png",
        "location": {"@type": "Place", "name": visible, "address": {"@type": "PostalAddress", "addressCountry": "ES"}},
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR", "availability": "https://schema.org/InStock", "url": f"{SITE}/{slug}.html"},
        "description": nota,
        "organizer": {"@type": "Organization", "name": "Viaje Inteligencia", "url": "https://www.viajeinteligencia.com/"},
    }
    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{nombre} · {fecha} | Viaje Inteligencia</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{SITE}/{slug}.html">
<meta property="og:type" content="article">
<meta property="og:title" content="{nombre} · {fecha}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{SITE}/{slug}.html">
<meta property="og:locale" content="es_ES">
<script type="application/ld+json">
{json.dumps(schema, ensure_ascii=False, indent=2)}
</script>
<style>
body {{ font-family: -apple-system, sans-serif; max-width: 720px; margin: 0 auto; padding: 24px; line-height: 1.6; background: #0b0f17; color: #e7ebf3; }}
h1 {{ font-size: 1.5em; }} a {{ color: #67e8f9; }}
.meta {{ color: #8993a8; font-size: 0.9em; }}
</style>
</head>
<body>
<h1>{nombre} · {fecha}</h1>
<p>{nota}</p>
<p class="meta">📅 {fecha} · 📍 Visible desde {visible}</p>
<p><a href="/">🌑 Mapa interactivo (Eclipse 2026 OSINT)</a></p>
<p><a href="/eventos-astronomicos.html">🗓️ Próximos eventos astronómicos</a></p>
</body>
</html>
"""
    return slug, html


def main():
    data = json.load(open(BASE / "data" / "events.json"))
    events = data if isinstance(data, list) else data.get("events", [])
    events.sort(key=lambda e: e["date"])

    pages = []
    for ev in events:
        slug, html = page_html(ev)
        (FRONT / f"{slug}.html").write_text(html, encoding="utf-8")
        pages.append((ev["date"], ev["name"], slug))

    años = {}
    for date, name, slug in pages:
        años.setdefault(date[:4], []).append((date, name, slug))

    rows = []
    itemlist = []
    for i, (date, name, slug) in enumerate(pages, start=1):
        itemlist.append({
            "@type": "ListItem", "position": i,
            "name": f"{name} · {fecha_es(date)}",
            "url": f"{SITE}/{slug}.html",
        })
    for year in sorted(años):
        rows.append(f"<h2>{year}</h2><ul>")
        for date, name, slug in sorted(años[year]):
            fecha = fecha_es(date)
            rows.append(f'  <li><a href="/{slug}.html"><strong>{name}</strong></a> · {fecha}</li>')
        rows.append("</ul>")
    itemlist_ld = json.dumps(
        {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": itemlist},
        ensure_ascii=False, indent=2,
    )

    hub = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Próximos eventos astronómicos 2026-2028 · Calendario | Viaje Inteligencia</title>
<meta name="description" content="Calendario de eventos astronómicos visibles desde España: eclipses, lluvias de estrellas, oposiciones. Fechas, horas y mapa interactivo.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{SITE}/eventos-astronomicos.html">
<meta property="og:locale" content="es_ES">
<script type="application/ld+json">
{itemlist_ld}
</script>
<style>
body {{ font-family: -apple-system, sans-serif; max-width: 720px; margin: 0 auto; padding: 24px; line-height: 1.6; background: #0b0f17; color: #e7ebf3; }}
h1 {{ font-size: 1.5em; }} a {{ color: #67e8f9; }} ul {{ line-height: 1.8; }}
</style>
</head>
<body>
<h1>🗓️ Próximos eventos astronómicos</h1>
<p>Eclipses, lluvias de estrellas y oposiciones visibles desde España, con datos oficiales y mapa interactivo.</p>
{"".join(rows)}
<p><a href="/">🌑 Mapa interactivo del eclipse solar (2026 · 2027 · Perseidas)</a></p>
</body>
</html>
"""
    (FRONT / "eventos-astronomicos.html").write_text(hub, encoding="utf-8")
    print(f"OK: {len(pages)} paginas de evento + hub generadas")


if __name__ == "__main__":
    main()
