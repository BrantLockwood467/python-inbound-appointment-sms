from src.appointment_sms import InboundReply, classify_reply, handle_reply


class FakeClient:
    def __init__(self):
        self.calls = []

    def send_sms(self, to, text, request_id):
        self.calls.append((to, text, request_id))
        return {"message_id": "msg-test"}


def test_confirmation_reply_sends_safe_confirmation():
    reply = InboundReply.from_json({"from": "+15551212", "body": "YES", "appointment_id": "apt-7"})
    client = FakeClient()
    result = handle_reply(reply, client)
    assert result["state"] == "confirmed"
    assert client.calls[0][0] == "+15551212"
    assert "confirmed" in client.calls[0][1]


def test_unknown_reply_requires_follow_up():
    assert classify_reply("Can I ask a question?")[0] == "follow_up"
