"""Notificaciones push PWA (web push vía pywebpush + VAPID)."""
import json

from src.config import BASE_DIR, VAPID_FILE, PUSH_SUBS_FILE, PUSH_SENT_FILE, VAPID_SUBJECT


def _read_subs():
    try:
        return json.loads(PUSH_SUBS_FILE.read_text())
    except Exception:
        return []


def _write_subs(subs):
    PUSH_SUBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PUSH_SUBS_FILE.write_text(json.dumps(subs, ensure_ascii=False, indent=1))


def vapid_public_key():
    try:
        return json.loads(VAPID_FILE.read_text())["public_key"]
    except Exception:
        return ""


def _vapid_private_key():
    return json.loads(VAPID_FILE.read_text())["private_key"]


def subscribe(payload: dict):
    subs = _read_subs()
    subs = [s for s in subs if s.get("endpoint") != payload.get("endpoint")]
    subs.append(payload)
    _write_subs(subs)
    return {"ok": True, "count": len(subs)}


def unsubscribe(endpoint: str):
    subs = _read_subs()
    subs = [s for s in subs if s.get("endpoint") != endpoint]
    _write_subs(subs)
    return {"ok": True, "count": len(subs)}


def send_push(title: str, body: str, url: str = ""):
    subs = _read_subs()
    if not subs:
        return {"ok": True, "sent": 0, "total": 0}
    from pywebpush import webpush
    payload = json.dumps({"title": title, "body": body, "url": url})
    sent = 0
    for s in subs:
        try:
            webpush(
                subscription_info=s,
                data=payload,
                vapid_private_key=_vapid_private_key(),
                vapid_claims={"sub": VAPID_SUBJECT},
            )
            sent += 1
        except Exception:
            continue
    return {"ok": True, "sent": sent, "total": len(subs)}
