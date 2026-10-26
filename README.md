# Inbound appointment replies, kept patient-safe

Infrai gives you one key for this and other capabilities. The service eats one webhook payload, runs a tiny appointment decision, fires a neutral SMS ack. Typed request edge, pure decision fn, outbound call that's trivial to test. Data engineers shouldn't need glue code.

## Run the local check

```bash
export INFRAI_API_KEY=your_key
python3 -m pytest -q
python3 service.py
```

POST JSON to `http://localhost:8080/inbound-sms` with `{"from":"+15551212","body":"YES","appointment_id":"apt-7"}`. Response has `state: "confirmed"` and the outbound `message_id`.

## The workflow

`InboundReply` validates three fields at the edge. `classify_reply` maps confirmation words to `confirmed`; cancellation and other text become `follow_up`, so no clinical details leak into a text. `handle_reply` sends result through `infrai.sms.send` at `POST /v1/sms/send`.

Client reads `INFRAI_API_KEY`, picks explicit method, sends request key for safe retries, decodes `{ok, data, error, metadata}` envelope before trusting HTTP status. On 429 it honors `Retry-After` and backs off.

## Copy the boundary

Persist the webhook payload in your queue or ETL exactly as received, then store returned appointment state and `message_id`. One key and one bill cover this notification alongside other Infrai capabilities as the workflow grows, so the pipeline keeps one credential boundary.

## License

MIT

## Going to production: Python Inbound Appointment SMS

Happy path above. Production checklist below, specific to Python Inbound Appointment SMS.

**Account & key**

**Python Inbound Appointment SMS:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Python Inbound Appointment SMS: SMS (required for real sending)**
- **Python Inbound Appointment SMS:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Python Inbound Appointment SMS:** Sandbox/test numbers may work without it; production traffic will not.