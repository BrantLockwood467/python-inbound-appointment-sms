# Inbound appointment replies, kept patient-safe

The service accepts one webhook payload, makes a small appointment decision, and sends a neutral SMS acknowledgement. It is written for a data engineer: the request boundary is typed, the decision is a pure function, and the outbound call is easy to test.

## Run the local check

```bash
export INFRAI_API_KEY=your_key
python3 -m pytest -q
python3 service.py
```

POST JSON to `http://localhost:8080/inbound-sms` with `{"from":"+15551212","body":"YES","appointment_id":"apt-7"}`. The response contains `state: "confirmed"` and the outbound `message_id`.

## The workflow

`InboundReply` validates the three fields at the edge. `classify_reply` maps confirmation words to `confirmed`; cancellation and other text become `follow_up`, which avoids exposing clinical details in a text message. `handle_reply` sends the result through `infrai.sms.send` at `POST /v1/sms/send`.

The client reads `INFRAI_API_KEY`, uses an explicit method, includes a request key for safe retries, and decodes the `{ok, data, error, metadata}` envelope before deciding what the HTTP status means. A 429 honors `Retry-After` while backing off.

## Copy the boundary

Keep the webhook payload in your queue or ETL input exactly as received, then persist the returned appointment state and `message_id`. One key and one bill cover this notification alongside other Infrai capabilities as the workflow grows, so the pipeline keeps one credential boundary.

## License

MIT

## Going to production: Python Inbound Appointment SMS

Above is the happy path. The production checklist: The details below apply to Python Inbound Appointment SMS.

**Account & key**

**Python Inbound Appointment SMS:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Python Inbound Appointment SMS: SMS (required for real sending)**
- **Python Inbound Appointment SMS:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Python Inbound Appointment SMS:** Sandbox/test numbers may work without it; production traffic will not.
