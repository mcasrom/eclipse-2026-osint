"""Envía recordatorios push de eventos próximos (dedupe diario por evento).

Cron sugerido:
  0 8 * * * cd /home/deploy/eclipse-2026-osint && venv/bin/python scripts/send_push_alerts.py >> logs/push.log 2>&1
"""
import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import BASE_DIR, PUSH_SENT_FILE, PUSH_REMINDER_DAYS
from src import push


def upcoming(days=PUSH_REMINDER_DAYS, limit=3):
    evs = json.loads((BASE_DIR / "data" / "events.json").read_text(encoding="utf-8")).get("events", [])
    today = date.today()
    fut = [e for e in evs if datetime.strptime(e["date"], "%Y-%m-%d").date() >= today]
    fut.sort(key=lambda e: e["date"])
    return [e for e in fut if (datetime.strptime(e["date"], "%Y-%m-%d").date() - today).days <= days][:limit]


def main():
    today = date.today().isoformat()
    sent = {}
    if PUSH_SENT_FILE.exists():
        try:
            sent = json.loads(PUSH_SENT_FILE.read_text())
        except Exception:
            sent = {}
    evs = upcoming()
    sent_any = 0
    for e in evs:
        key = f"{e['date']}_{e.get('type', 'evento')}"
        if sent.get(key) == today:
            continue
        days = (datetime.strptime(e["date"], "%Y-%m-%d").date() - date.today()).days
        when = "hoy" if days == 0 else ("mañana" if days == 1 else f"en {days} días")
        emoji = "🌑" if "eclipse" in e.get("type", "") else "☄️"
        body = f"{emoji} {e['name']} {when} · {e.get('visible', '')}"
        res = push.send_push("Eclipse 2026 OSINT", body, "https://eclipse.viajeinteligencia.com/?tab=calendario")
        sent[key] = today
        sent_any += 1
        print(f"  {key}: {res}")
    PUSH_SENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    PUSH_SENT_FILE.write_text(json.dumps(sent, ensure_ascii=False, indent=1))
    print(f"recordatorios nuevos: {sent_any}")


if __name__ == "__main__":
    main()
