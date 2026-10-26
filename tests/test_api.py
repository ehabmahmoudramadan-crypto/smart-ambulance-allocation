"""Phase 3/4 - backend API."""
from Backend.app import app

client = app.test_client()


def test_health_and_data():
    assert client.get("/api/health").json == {"status": "ok"}
    d = client.get("/api/data").json
    assert len(d["stations"]) == 8 and len(d["areas"]) == 12


def test_solve_default():
    r = client.post("/api/solve", json={})
    assert r.status_code == 200
    j = r.json
    assert j["optimal"]["cost"] == 1111 and j["initial"]["cost"] == 1261
    assert j["optimal"]["allocation"][1][6] == 0 and j["optimal"]["allocation"][4][8] <= 5


def test_solve_rejects_bad_input():
    assert client.post("/api/solve", json={"supply": [1, 2]}).status_code == 400
    assert client.post("/api/solve", json={"closed": [[99, 0]]}).status_code == 400


def test_simulate_default_small():
    r = client.post("/api/simulate", json={"reps": 2, "hours": 6})
    assert r.status_code == 200
    j = r.json
    assert j["audit"]["greedy"]["closed_uses"] == 0 and j["audit"]["plan"]["closed_uses"] == 0
    assert j["audit"]["plan"]["capped_routes"][0]["max_load"] <= 5


def test_simulate_rejects_bad_input():
    for bad in ({"reps": 0}, {"incidents_per_hour": "x"}, {"hours": 999},
                {"incidents_per_hour": 100, "hours": 48, "reps": 30}):
        assert client.post("/api/simulate", json=bad).status_code == 400


def test_cors_header_for_local_frontend():
    assert client.get("/api/health").headers["Access-Control-Allow-Origin"] == "*"
