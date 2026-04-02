from __future__ import annotations

from tests.conftest import get_auth_header


def _login_user(client, email: str, password: str):
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    return data["user"], get_auth_header(data["access_token"])


def _login_admin(client):
    return _login_user(client, "admin@example.com", "AdminPass123")


def test_transaction_flow_and_dashboard_aggregations(client):
    admin_user, admin_headers = _login_admin(client)

    income_response = client.post(
        "/transactions",
        headers=admin_headers,
        json={
            "amount": 5000.0,
            "type": "income",
            "category": "Salary",
            "date": "2026-01-15T10:00:00Z",
            "description": "January salary",
        },
    )
    assert income_response.status_code == 201
    income_transaction = income_response.json()["data"]

    expense_response = client.post(
        "/transactions",
        headers=admin_headers,
        json={
            "amount": 1200.0,
            "type": "expense",
            "category": "Rent",
            "date": "2026-01-20T10:00:00Z",
            "description": "January rent",
        },
    )
    assert expense_response.status_code == 201
    expense_transaction = expense_response.json()["data"]

    groceries_response = client.post(
        "/transactions",
        headers=admin_headers,
        json={
            "amount": 350.0,
            "type": "expense",
            "category": "Groceries",
            "date": "2026-02-02T10:00:00Z",
            "description": "Weekly groceries",
        },
    )
    assert groceries_response.status_code == 201

    list_response = client.get(
        "/transactions?page=1&limit=2&type=income&category=Salary&search=salary",
        headers=admin_headers,
    )
    assert list_response.status_code == 200
    list_payload = list_response.json()["data"]
    assert list_payload["total"] == 1
    assert list_payload["page"] == 1
    assert list_payload["limit"] == 2
    assert list_payload["total_pages"] == 1
    assert list_payload["items"][0]["id"] == income_transaction["id"]

    get_response = client.get(f"/transactions/{income_transaction['id']}", headers=admin_headers)
    assert get_response.status_code == 200
    assert get_response.json()["data"]["category"] == "Salary"

    update_response = client.put(
        f"/transactions/{income_transaction['id']}",
        headers=admin_headers,
        json={"description": "Updated salary payment", "amount": 5100.0},
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["amount"] == 5100.0
    assert update_response.json()["data"]["description"] == "Updated salary payment"

    summary_response = client.get("/dashboard/summary", headers=admin_headers)
    assert summary_response.status_code == 200
    summary_payload = summary_response.json()["data"]
    assert summary_payload["total_income"] == 5100.0
    assert summary_payload["total_expense"] == 1550.0
    assert summary_payload["net_balance"] == 3550.0

    categories_response = client.get("/dashboard/categories", headers=admin_headers)
    assert categories_response.status_code == 200
    categories_payload = categories_response.json()["data"]
    assert categories_payload[0]["category"] == "Salary"

    trends_response = client.get("/dashboard/trends?group_by=month", headers=admin_headers)
    assert trends_response.status_code == 200
    trends_payload = trends_response.json()["data"]
    assert len(trends_payload) == 2
    assert trends_payload[0]["total_income"] == 5100.0
    assert trends_payload[1]["total_expense"] == 350.0

    recent_response = client.get("/dashboard/recent", headers=admin_headers)
    assert recent_response.status_code == 200
    recent_payload = recent_response.json()["data"]
    assert len(recent_payload) == 3
    assert recent_payload[0]["category"] == "Groceries"

    delete_response = client.delete(
        f"/transactions/{expense_transaction['id']}",
        headers=admin_headers,
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["is_deleted"] is True

    deleted_get_response = client.get(
        f"/transactions/{expense_transaction['id']}",
        headers=admin_headers,
    )
    assert deleted_get_response.status_code == 404
    assert deleted_get_response.json()["error"] == "Transaction not found."

    deleted_get_including_deleted = client.get(
        f"/transactions/{expense_transaction['id']}?include_deleted=true",
        headers=admin_headers,
    )
    assert deleted_get_including_deleted.status_code == 200
    assert deleted_get_including_deleted.json()["data"]["is_deleted"] is True

    deleted_list_response = client.get(
        "/transactions?page=1&limit=10&include_deleted=true",
        headers=admin_headers,
    )
    assert deleted_list_response.status_code == 200
    assert deleted_list_response.json()["data"]["total"] == 3

    restore_response = client.patch(
        f"/transactions/{expense_transaction['id']}/restore",
        headers=admin_headers,
    )
    assert restore_response.status_code == 200
    assert restore_response.json()["data"]["is_deleted"] is False

    post_delete_list = client.get("/transactions?page=1&limit=10", headers=admin_headers)
    assert post_delete_list.status_code == 200
    assert post_delete_list.json()["data"]["total"] == 3

    post_delete_summary = client.get("/dashboard/summary", headers=admin_headers)
    assert post_delete_summary.status_code == 200
    assert post_delete_summary.json()["data"]["total_expense"] == 1550.0


def test_analyst_cannot_include_deleted_transactions(client):
    _, admin_headers = _login_admin(client)

    register_response = client.post(
        "/auth/register",
        json={"email": "analyst@example.com", "password": "AnalystPass123"},
    )
    assert register_response.status_code == 201
    analyst_user_id = register_response.json()["data"]["id"]

    promote_response = client.patch(
        f"/users/{analyst_user_id}/role",
        headers=admin_headers,
        json={"role": "analyst"},
    )
    assert promote_response.status_code == 200

    login_response = client.post(
        "/auth/login",
        json={"email": "analyst@example.com", "password": "AnalystPass123"},
    )
    assert login_response.status_code == 200
    analyst_headers = get_auth_header(login_response.json()["data"]["access_token"])

    transaction_response = client.post(
        "/transactions",
        headers=admin_headers,
        json={
            "amount": 1200.0,
            "type": "expense",
            "category": "Travel",
            "date": "2026-03-10T10:00:00Z",
            "description": "Taxi",
        },
    )
    assert transaction_response.status_code == 201
    transaction_id = transaction_response.json()["data"]["id"]

    delete_response = client.delete(
        f"/transactions/{transaction_id}",
        headers=admin_headers,
    )
    assert delete_response.status_code == 200

    analyst_list_response = client.get(
        "/transactions?page=1&limit=10&include_deleted=true",
        headers=analyst_headers,
    )
    assert analyst_list_response.status_code == 403
    assert analyst_list_response.json()["error"] == "Only admins can view deleted transactions."

    analyst_detail_response = client.get(
        f"/transactions/{transaction_id}?include_deleted=true",
        headers=analyst_headers,
    )
    assert analyst_detail_response.status_code == 403
    assert analyst_detail_response.json()["error"] == "Only admins can view deleted transactions."


def test_analyst_can_only_read_own_transactions(client):
    admin_user, admin_headers = _login_admin(client)

    register_response = client.post(
        "/auth/register",
        json={"email": "analyst2@example.com", "password": "AnalystPass123"},
    )
    assert register_response.status_code == 201
    analyst_user_id = register_response.json()["data"]["id"]

    promote_response = client.patch(
        f"/users/{analyst_user_id}/role",
        headers=admin_headers,
        json={"role": "analyst"},
    )
    assert promote_response.status_code == 200

    analyst_transaction_response = client.post(
        f"/transactions?user_id={analyst_user_id}",
        headers=admin_headers,
        json={
            "amount": 450.0,
            "type": "expense",
            "category": "Utilities",
            "date": "2026-03-01T10:00:00Z",
            "description": "Electricity bill",
        },
    )
    assert analyst_transaction_response.status_code == 201
    analyst_transaction_id = analyst_transaction_response.json()["data"]["id"]

    admin_transaction_response = client.post(
        "/transactions",
        headers=admin_headers,
        json={
            "amount": 2000.0,
            "type": "income",
            "category": "Bonus",
            "date": "2026-03-05T10:00:00Z",
            "description": "Admin bonus",
        },
    )
    assert admin_transaction_response.status_code == 201
    admin_transaction_id = admin_transaction_response.json()["data"]["id"]

    _, analyst_headers = _login_user(client, "analyst2@example.com", "AnalystPass123")

    analyst_list_response = client.get(
        "/transactions?page=1&limit=10",
        headers=analyst_headers,
    )
    assert analyst_list_response.status_code == 200
    analyst_list_payload = analyst_list_response.json()["data"]
    assert analyst_list_payload["total"] == 1
    assert len(analyst_list_payload["items"]) == 1
    assert analyst_list_payload["items"][0]["id"] == analyst_transaction_id
    assert analyst_list_payload["items"][0]["user_id"] == analyst_user_id

    analyst_get_own_response = client.get(
        f"/transactions/{analyst_transaction_id}",
        headers=analyst_headers,
    )
    assert analyst_get_own_response.status_code == 200
    assert analyst_get_own_response.json()["data"]["user_id"] == analyst_user_id

    analyst_get_admin_response = client.get(
        f"/transactions/{admin_transaction_id}",
        headers=analyst_headers,
    )
    assert analyst_get_admin_response.status_code == 404
    assert analyst_get_admin_response.json()["error"] == "Transaction not found."


def test_analyst_cannot_create_transactions(client):
    admin_user, admin_headers = _login_admin(client)

    register_response = client.post(
        "/auth/register",
        json={"email": "analyst-create@example.com", "password": "AnalystPass123"},
    )
    assert register_response.status_code == 201
    analyst_user_id = register_response.json()["data"]["id"]

    promote_response = client.patch(
        f"/users/{analyst_user_id}/role",
        headers=admin_headers,
        json={"role": "analyst"},
    )
    assert promote_response.status_code == 200

    analyst_user, analyst_headers = _login_user(client, "analyst-create@example.com", "AnalystPass123")
    assert analyst_user["id"] == analyst_user_id

    create_response = client.post(
        f"/transactions?user_id={admin_user['id']}",
        headers=analyst_headers,
        json={
            "amount": 220.0,
            "type": "expense",
            "category": "Food",
            "date": "2026-03-07T10:00:00Z",
            "description": "Lunch",
            "user_id": admin_user["id"],
        },
    )
    assert create_response.status_code == 403
    assert create_response.json()["error"] == "You do not have permission to perform this action."


def test_dashboard_is_scoped_to_authenticated_user(client):
    admin_user, admin_headers = _login_admin(client)

    register_response = client.post(
        "/auth/register",
        json={"email": "viewer2@example.com", "password": "ViewerPass123"},
    )
    assert register_response.status_code == 201
    viewer_user_id = register_response.json()["data"]["id"]

    admin_income_response = client.post(
        "/transactions",
        headers=admin_headers,
        json={
            "amount": 3000.0,
            "type": "income",
            "category": "Salary",
            "date": "2026-04-01T10:00:00Z",
            "description": "Admin salary",
        },
    )
    assert admin_income_response.status_code == 201

    viewer_expense_response = client.post(
        f"/transactions?user_id={viewer_user_id}",
        headers=admin_headers,
        json={
            "amount": 900.0,
            "type": "expense",
            "category": "Rent",
            "date": "2026-04-01T12:00:00Z",
            "description": "Viewer rent",
        },
    )
    assert viewer_expense_response.status_code == 201

    admin_summary_response = client.get("/dashboard/summary", headers=admin_headers)
    assert admin_summary_response.status_code == 200
    admin_summary = admin_summary_response.json()["data"]
    assert admin_summary["total_income"] == 3000.0
    assert admin_summary["total_expense"] == 0.0
    assert admin_summary["net_balance"] == 3000.0

    _, viewer_headers = _login_user(client, "viewer2@example.com", "ViewerPass123")

    viewer_summary_response = client.get("/dashboard/summary", headers=viewer_headers)
    assert viewer_summary_response.status_code == 200
    viewer_summary = viewer_summary_response.json()["data"]
    assert viewer_summary["total_income"] == 0.0
    assert viewer_summary["total_expense"] == 900.0
    assert viewer_summary["net_balance"] == -900.0

    viewer_categories_response = client.get("/dashboard/categories", headers=viewer_headers)
    assert viewer_categories_response.status_code == 200
    viewer_categories = viewer_categories_response.json()["data"]
    assert len(viewer_categories) == 1
    assert viewer_categories[0]["category"] == "Rent"
    assert viewer_categories[0]["total"] == 900.0

    viewer_recent_response = client.get("/dashboard/recent", headers=viewer_headers)
    assert viewer_recent_response.status_code == 200
    viewer_recent = viewer_recent_response.json()["data"]
    assert len(viewer_recent) == 1
    assert viewer_recent[0]["user_id"] == viewer_user_id
