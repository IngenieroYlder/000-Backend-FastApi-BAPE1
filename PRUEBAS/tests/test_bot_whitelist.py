from app import models
from app.routers.webhooks import is_bot_allowed_for_contact


def _register_payload(seed: str) -> dict:
    return {
        "email": f"wl_{seed}@example.com",
        "password": "Pass1234!",
        "first_name": "QA",
        "last_name": "Whitelist",
        "phone": "3000000000",
        "company_name": f"Compania WL {seed}",
    }


def _register_and_login(client, seed: str) -> str:
    payload = _register_payload(seed)
    register_response = client.post("/auth/register", json=payload)
    assert register_response.status_code == 200

    login_response = client.post(
        "/auth/login",
        data={"username": payload["email"], "password": payload["password"]},
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def test_whitelist_helper_allows_only_test_contacts():
    wa_session = models.WhatsAppSession(
        session_name="company_1_pruebas",
        alias="Pruebas",
        company_id=1,
        bot_whitelist_enabled=True,
        bot_whitelist_numbers=["+57 300 123 4567"],
    )

    assert is_bot_allowed_for_contact(wa_session, "573001234567@s.whatsapp.net")
    assert is_bot_allowed_for_contact(wa_session, "3001234567")
    assert not is_bot_allowed_for_contact(wa_session, "573009999999@s.whatsapp.net")

    wa_session.bot_whitelist_enabled = False
    assert is_bot_allowed_for_contact(wa_session, "573009999999@s.whatsapp.net")


def test_session_config_saves_whitelist_from_channels(client, unique_seed):
    token = _register_and_login(client, unique_seed)
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/whatsapp/sessions?alias=Pruebas&ai_provider=openai",
        headers=headers,
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["bot_whitelist_enabled"] is True
    assert created["bot_whitelist_numbers"] == []

    update_response = client.put(
        f"/whatsapp/sessions/{created['id']}/config",
        headers=headers,
        json={
            "bot_whitelist_enabled": True,
            "bot_whitelist_numbers": ["573001234567", "+57 301 000 0000"],
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["bot_whitelist_enabled"] is True
    assert updated["bot_whitelist_numbers"] == ["573001234567", "+57 301 000 0000"]
