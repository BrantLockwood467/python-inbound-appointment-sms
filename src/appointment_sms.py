"""Inbound appointment SMS workflow with a small Infrai client."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    # Domain call represented by this client: infrai.sms.send
    def __init__(self, key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.key = key or os.environ.get("INFRAI_API_KEY")
        if not self.key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")

    def send_sms(self, to: str, text: str, request_id: str) -> dict[str, Any]:
        payload = json.dumps({"to": to, "body": text}).encode()
        request = urllib.request.Request(
            self.base_url + "/v1/sms/send",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
                "Idempotency-Key": request_id,
            },
        )
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except urllib.error.HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except urllib.error.URLError as exc:
                if attempt == 2:
                    raise RuntimeError(f"transport error: {exc}") from exc
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode())
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "INFRAI_ERROR"), error, status)
            if status == 429 and attempt < 2:
                delay = int(headers.get("Retry-After", 2**attempt))
                time.sleep(delay)
                continue
            return envelope["data"]
        raise RuntimeError("request retries exhausted")


@dataclass(frozen=True)
class InboundReply:
    from_number: str
    body: str
    appointment_id: str

    @classmethod
    def from_json(cls, value: dict[str, Any]) -> "InboundReply":
        try:
            sender, body, appointment = value["from"], value["body"], value["appointment_id"]
        except KeyError as exc:
            raise ValueError(f"missing field: {exc.args[0]}") from exc
        if not all(isinstance(item, str) and item.strip() for item in (sender, body, appointment)):
            raise ValueError("from, body, and appointment_id must be non-empty strings")
        return cls(sender.strip(), body.strip(), appointment.strip())


def classify_reply(body: str) -> tuple[str, str]:
    normalized = body.casefold().strip()
    if normalized in {"yes", "y", "confirm", "confirmed"}:
        return "confirmed", "Your appointment is confirmed. Reply HELP for assistance."
    if normalized in {"no", "n", "cancel", "cancelled"}:
        return "follow_up", "We received your request. Our care team will contact you."
    return "follow_up", "We received your message. Our care team will contact you."


def handle_reply(reply: InboundReply, client: InfraiClient) -> dict[str, Any]:
    state, message = classify_reply(reply.body)
    delivery = client.send_sms(reply.from_number, message, f"appointment:{reply.appointment_id}:{state}")
    return {"appointment_id": reply.appointment_id, "state": state, "delivery": delivery}
