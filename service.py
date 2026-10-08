import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from src.appointment_sms import InboundReply, InfraiClient, handle_reply


class AppointmentHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != "/inbound-sms":
            self.send_error(404)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            reply = InboundReply.from_json(json.loads(self.rfile.read(size)))
            result = handle_reply(reply, InfraiClient())
            body, status = json.dumps(result).encode(), 200
        except ValueError as exc:
            body, status = json.dumps({"error": str(exc)}).encode(), 400
        except Exception as exc:
            body, status = json.dumps({"error": str(exc)}).encode(), 502
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    HTTPServer(("", 8080), AppointmentHandler).serve_forever()
