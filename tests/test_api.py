from fastapi.testclient import TestClient

from taja_bot.api import app


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["knowledge_base_entries"] == 7


def test_chat_endpoint() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat",
            json={
                "session_id": "api-test",
                "language": "en",
                "message": "Can I convert crypto to cash?",
            },
        )
        assert response.status_code == 200
        assert response.json()["matched_faq_id"] == "crypto-to-cash"


def test_home_demo() -> None:
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "Taja multilingual FAQ assistant" in response.text


def test_gupshup_webhook_dry_run_uses_pseudonymous_session() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/webhooks/gupshup",
            json={
                "type": "message",
                "payload": {
                    "sender": {"phone": "2348000000000"},
                    "payload": {"text": "How fast are Taja transfers?"},
                },
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["accepted"] is True
        assert body["delivery"]["mode"] == "dry-run"
        assert "2348000000000" not in body["chatbot"]["session_id"]
        assert body["chatbot"]["matched_faq_id"] == "transfer-speed"


def test_gupshup_webhook_rejects_wrong_secret() -> None:
    with TestClient(app) as client:
        app.state.settings.webhook_secret = "correct-secret"
        response = client.post(
            "/webhooks/gupshup",
            headers={"X-Webhook-Secret": "wrong-secret"},
            json={
                "type": "message",
                "payload": {
                    "sender": {"phone": "2348000000000"},
                    "payload": {"text": "What is Taja?"},
                },
            },
        )
        assert response.status_code == 401
