from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from controllers.webhook import router


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("API_KEY", "testing")
    monkeypatch.setenv("NEXTCLOUD_URL", "https://nextcloud.example.com")
    monkeypatch.setenv("NEXTCLOUD_TALK_TOKEN", "databasus-token")
    monkeypatch.setenv("NEXTCLOUD_TALK_SECRET", "databasus-secret")
    monkeypatch.setenv("BESZEL_NEXTCLOUD_TALK_TOKEN", "beszel-token")
    monkeypatch.setenv("BESZEL_NEXTCLOUD_TALK_SECRET", "beszel-secret")
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as test_client:
        yield test_client


PAYLOAD = {
    "title": "Server CPU above threshold",
    "message": "CPU averaged 63.53% for the previous 10 minutes.",
}
HEADERS = {"X-API-KEY": "testing"}


def test_beszel_sends_using_its_own_bot(client):
    with patch("controllers.webhook.TalkMessenger") as messenger:
        messenger.return_value.send.return_value = True
        response = client.post("/webhook/beszel", headers=HEADERS, json=PAYLOAD)

    assert response.status_code == 200
    assert response.json() == {"status": "sent"}
    messenger.assert_called_once_with(
        endpoint_url="https://nextcloud.example.com",
        token="beszel-token",
        secret="beszel-secret",
    )
    messenger.return_value.send.assert_called_once_with(
        f"**{PAYLOAD['title']}**\n{PAYLOAD['message']}"
    )


@pytest.mark.parametrize("headers, status", [({}, 422), ({"X-API-KEY": "wrong"}, 401)])
def test_beszel_requires_api_key(client, headers, status):
    with patch("controllers.webhook.TalkMessenger") as messenger:
        response = client.post("/webhook/beszel", headers=headers, json=PAYLOAD)
    assert response.status_code == status
    messenger.assert_not_called()


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": "title"},
        {"message": "message"},
        {**PAYLOAD, "title": ""},
        {**PAYLOAD, "title": " \t\n"},
        {**PAYLOAD, "message": ""},
        {**PAYLOAD, "message": " \t\n"},
        {**PAYLOAD, "title": "x" * 201},
        {**PAYLOAD, "message": "x" * 32001},
    ],
)
def test_beszel_rejects_invalid_payload(client, payload):
    with patch("controllers.webhook.TalkMessenger") as messenger:
        response = client.post("/webhook/beszel", headers=HEADERS, json=payload)
    assert response.status_code == 422
    messenger.assert_not_called()


@pytest.mark.parametrize(
    "variable",
    ["NEXTCLOUD_URL", "BESZEL_NEXTCLOUD_TALK_TOKEN", "BESZEL_NEXTCLOUD_TALK_SECRET"],
)
@pytest.mark.parametrize("value", [None, "", "   "])
def test_beszel_requires_configuration(client, monkeypatch, variable, value):
    if value is None:
        monkeypatch.delenv(variable)
    else:
        monkeypatch.setenv(variable, value)
    with patch("controllers.webhook.TalkMessenger") as messenger:
        response = client.post("/webhook/beszel", headers=HEADERS, json=PAYLOAD)
    assert response.status_code == 500
    assert response.json()["detail"] == "Nextcloud Talk is not configured"
    messenger.assert_not_called()


def test_beszel_requires_https(client, monkeypatch):
    monkeypatch.setenv("NEXTCLOUD_URL", "http://nextcloud.example.com")
    with patch("controllers.webhook.TalkMessenger") as messenger:
        response = client.post("/webhook/beszel", headers=HEADERS, json=PAYLOAD)
    assert response.status_code == 500
    messenger.assert_not_called()


def test_beszel_reports_delivery_failure(client):
    with patch("controllers.webhook.TalkMessenger") as messenger:
        messenger.return_value.send.return_value = False
        response = client.post("/webhook/beszel", headers=HEADERS, json=PAYLOAD)
    assert response.status_code == 502
    assert response.json()["detail"] == "Failed to send message to Nextcloud Talk"


def test_databasus_keeps_its_existing_bot(client):
    with patch("controllers.webhook.TalkMessenger") as messenger:
        messenger.return_value.send.return_value = True
        response = client.post(
            "/webhook/databasus",
            headers=HEADERS,
            json={"header": "Backup complete", "message": "Success"},
        )
    assert response.status_code == 200
    messenger.assert_called_once_with(
        endpoint_url="https://nextcloud.example.com",
        token="databasus-token",
        secret="databasus-secret",
    )
