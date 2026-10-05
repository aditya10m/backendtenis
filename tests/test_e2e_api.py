import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_full_e2e_flow():
    # 1. Health check
    health_res = client.get("/api/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "ok"

    # 2. Login with demo user
    login_res = client.post("/api/auth/login", json={
        "email": "demo@tennisai.com",
        "password": "demo123456",
    })
    assert login_res.status_code == 200, login_res.text
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Get Player Profile
    profile_res = client.get("/api/players/me", headers=headers)
    assert profile_res.status_code == 200, profile_res.text
    profile_data = profile_res.json()
    assert profile_data["playing_hand"] == "right"
    assert profile_data["skill_level"] == "advanced"

    # 4. Get Progress history
    progress_res = client.get("/api/players/me/progress?period=all", headers=headers)
    assert progress_res.status_code == 200, progress_res.text
    snapshots = progress_res.json()["snapshots"]
    assert len(snapshots) >= 5
    assert snapshots[-1]["overall_score"] is not None

    # 5. Coach login and coach players check
    coach_login = client.post("/api/auth/login", json={
        "email": "coach@tennisai.com",
        "password": "coach123456",
    })
    assert coach_login.status_code == 200
    coach_token = coach_login.json()["access_token"]
    coach_headers = {"Authorization": f"Bearer {coach_token}"}

    coach_players = client.get("/api/coach/players", headers=coach_headers)
    assert coach_players.status_code == 200
    players_list = coach_players.json()
    assert len(players_list) >= 1
    assert any(p["email"] == "demo@tennisai.com" for p in players_list)
