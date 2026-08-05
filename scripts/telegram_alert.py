"""Publica alertas al canal de Telegram del eclipse (via bot admin).

Uso:
  python3 telegram_alert.py                -> alerta automatica (proximo evento + enlace)
  python3 telegram_alert.py --test         -> mensaje de prueba
  python3 telegram_alert.py --message "..." -> mensaje personalizado
  python3 telegram_alert.py --forecast     -> alerta con previsión de nubosidad del próximo evento

El token se lee de /home/deploy/.secrets/telegram_eclipse_token (fuera del repo).
Canal destino: @eclipse2026osint  (el bot debe ser admin del canal).
"""
import argparse
import json
import sys
import urllib.request
import urllib.parse
from datetime import datetime, date
from pathlib import Path

TOKEN_FILE = Path("/home/deploy/.secrets/telegram_eclipse_token")
CHANNEL = "@eclipse2026osint"
SITE = "https://eclipse.viajeinteligencia.com"
BASE_DIR = Path(__file__).resolve().parent.parent
EVENTS_FILE = BASE_DIR / "data" / "events.json"


def send_message(text: str) -> dict:
    token = TOKEN_FILE.read_text().strip()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHANNEL, "text": text, "disable_web_page_preview": "false"}).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def next_event() -> dict | None:
    try:
        ev = json.loads(EVENTS_FILE.read_text(encoding="utf-8")).get("events", [])
    except Exception:
        return None
    today = date.today()
    future = [e for e in ev if datetime.strptime(e["date"], "%Y-%m-%d").date() >= today]
    if not future:
        return None
    future.sort(key=lambda e: e["date"])
    return future[0]


def auto_message() -> str:
    ev = next_event()
    lines = ["🌑 <b>Eclipse 2026 OSINT</b>"]
    if ev:
        d = datetime.strptime(ev["date"], "%Y-%m-%d").date()
        days = (d - date.today()).days
        emoji = "🌑" if "eclipse" in ev["type"] else "☄️"
        when = "hoy" if days == 0 else ("mañana" if days == 1 else f"en {days} días")
        lines.append(f"{emoji} {ev['name']} · {ev['date']} ({when})")
        lines.append(f"📍 {ev['visible']}")
        if ev.get("note"):
            lines.append(f"📝 {ev['note']}")
    else:
        lines.append("☀️ Sin próximos eventos anotados.")
    lines.append(f"🗺️ Mapa, horarios y nubosidad: {SITE}")
    return "\n".join(lines)


def forecast_message() -> str:
    """Alerta con la previsión de nubosidad de las ciudades totales."""
    try:
        data = json.loads((BASE_DIR / "data" / "2026" / "cities.json").read_text(encoding="utf-8"))
        fc = json.loads((BASE_DIR / "data" / "forecast_cache_2026.json").read_text(encoding="utf-8"))
    except Exception:
        return auto_message()
    totales = [c for c in data["cities"] if c["tipo"] == "total"]
    cats = {c["id"]: c.get("category", "desconocido") for c in fc.get("cities", [])}
    label = {"despejado": "🟢", "parcialmente_nublado": "🟡", "nublado": "🟠", "muy_nublado": "🔴"}
    best = sorted(totales, key=lambda c: {"despejado": 4, "parcialmente_nublado": 3, "nublado": 2, "muy_nublado": 1}.get(cats.get(c["id"], ""), 0), reverse=True)[:3]
    lines = ["🌑 <b>Previsión de nubosidad · Eclipse 12-Ago</b>", "Mejores sitios ahora:"]
    for c in best:
        lines.append(f"{label.get(cats.get(c['id']), '⚪')} {c['name']} — {cats.get(c['id'], 'desconocido').replace('_', ' ')}")
    lines.append(f"🗺️ {SITE}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--message")
    ap.add_argument("--forecast", action="store_true")
    args = ap.parse_args()
    if args.test:
        text = "✅ Test del bot Eclipse 2026 OSINT — todo operativo."
    elif args.message:
        text = args.message
    elif args.forecast:
        text = forecast_message()
    else:
        text = auto_message()
    out = send_message(text)
    print("enviado:", out.get("ok"), "| msg_id:", out.get("result", {}).get("message_id"))
    if not out.get("ok"):
        sys.exit(1)


if __name__ == "__main__":
    main()
