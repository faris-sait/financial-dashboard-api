from __future__ import annotations

from tests.conftest import get_auth_header


def test_authentication_flow(client):
    register_response = client.post(
        "/auth/register",
        json={"email": "viewer@example.com", "password": "ViewerPass123"},
    )
    assert register_response.status_code == 201
    register_payload = register_response.json()
    assert register_payload["success"] is True
    assert register_payload["data"]["email"] == "viewer@example.com"
    assert register_payload["data"]["role"] == "viewer"
    assert register_payload["data"]["is_active"] is True

    duplicate_response = client.post(
        "/auth/register",
        json={"email": "viewer@example.com", "password": "ViewerPass123"},
    )
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["error"] == "A user with this email already exists."

    login_response = client.post(
        "/auth/login",
        json={"email": "viewer@example.com", "password": "ViewerPass123"},
    )
    assert login_response.status_code == 200
    login_payload = login_response.json()["data"]
    assert login_payload["token_type"] == "bearer"
    assert login_payload["expires_in"] == 3600
    assert login_payload["user"]["role"] == "viewer"

    wrong_password_response = client.post(
        "/auth/login",
        json={"email": "viewer@example.com", "password": "WrongPass123"},
    )
    assert wrong_password_response.status_code == 401
    assert wrong_password_response.json()["error"] == "Invalid email or password."

    unauthorized_response = client.get("/users")
    assert unauthorized_response.status_code == 401
    assert unauthorized_response.json()["error"] == "Authentication credentials were not provided."

    viewer_headers = get_auth_header(login_payload["access_token"])
    forbidden_response = client.get("/transactions", headers=viewer_headers)
    assert forbidden_response.status_code == 403
    assert forbidden_response.json()["error"] == "You do not have permission to perform this action."

    viewer_create_response = client.post(
        "/transactions",
        headers=viewer_headers,
        json={
            "amount": 100.0,
            "type": "expense",
            "category": "Food",
            "date": "2026-04-02T10:00:00Z",
            "description": "Viewer cannot create",
        },
    )
    assert viewer_create_response.status_code == 403
    assert viewer_create_response.json()["error"] == "You do not have permission to perform this action."

    dashboard_response = client.get("/dashboard/summary", headers=viewer_headers)
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["data"]["net_balance"] == 0.0
