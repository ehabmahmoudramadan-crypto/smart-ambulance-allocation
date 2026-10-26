"""Flask backend: serves the frontend and exposes the optimiser as a JSON API.

Run from the project root:   python -m backend.app
"""
from pathlib import Path

from flask import Flask, jsonify, request

from algorithms.model import load_dataset, plan_cost, solve
from simulation.engine import replay, run_comparison

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
app = Flask(__name__, static_folder=str(FRONTEND), static_url_path="")


class BadRequest(ValueError):
    pass


def _int_matrix(value, name):
    ok = (isinstance(value, list) and value and
          all(isinstance(r, list) and r for r in value) and
          all(type(v) is int and v >= 0 for r in value for v in r))
    if not ok:
        raise BadRequest(f"'{name}' must be a non-empty matrix of non-negative integers.")


def _validate(p):
    """Check a problem payload; raise BadRequest with a readable message."""
    s, d, c = p["supply"], p["demand"], p["cost_matrix"]
    for name, v in (("supply", s), ("demand", d)):
        if not (isinstance(v, list) and v and all(type(x) is int and x >= 0 for x in v)):
            raise BadRequest(f"'{name}' must be a non-empty list of non-negative integers.")
    _int_matrix(c, "cost_matrix")
    m, n = len(s), len(d)
    if len(c) != m or any(len(r) != n for r in c):
        raise BadRequest(f"cost_matrix must be {m} x {n} (stations x areas).")
    if sum(s) != sum(d):
        raise BadRequest(f"Supply ({sum(s)}) must equal demand ({sum(d)}).")
    for i, j in p["closed"]:
        if not (0 <= i < m and 0 <= j < n):
            raise BadRequest("A closed road points outside the matrix.")
    seen = set()
    for i, j, k in p["caps"]:
        if not (0 <= i < m and 0 <= j < n) or type(k) is not int or k < 0:
            raise BadRequest("A route capacity is invalid.")
        if i in seen:
            raise BadRequest("Only one capacity constraint per station is supported.")
        seen.add(i)


def default_problem():
    ds, closed, caps = load_dataset()
    return {
        "stations": ds["stations"], "areas": ds["areas"],
        "supply": ds["supply"], "demand": ds["demand"],
        "cost_matrix": ds["cost_matrix"],
        "station_coords": ds["station_coords_km"], "area_coords": ds["area_coords_km"],
        "current_allocation": ds["current_allocation"],
        "closed": [list(c) for c in closed],
        "caps": [list(c) for c in caps],
    }


def run(p):
    _validate(p)
    r = solve(p["supply"], p["demand"], p["cost_matrix"],
              [tuple(c) for c in p["closed"]], [tuple(c) for c in p["caps"]])
    out = dict(p)
    out["initial"], out["optimal"] = r["initial"], r["optimal"]
    cur = p.get("current_allocation")
    if cur:
        cost = plan_cost(cur, p["cost_matrix"])
        out["current"] = {"allocation": cur, "cost": cost}
        out["saving"] = cost - r["optimal"]["cost"]
        out["saving_percent"] = round(100 * out["saving"] / cost, 1) if cost else 0.0
    return out


@app.after_request
def allow_local_frontend(resp):
    if request.path.startswith("/api/"):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp


@app.errorhandler(BadRequest)
def bad_request(e):
    return jsonify({"error": str(e)}), 400


@app.errorhandler(Exception)
def server_error(e):
    code = getattr(e, "code", 500)
    if code == 500 or not isinstance(code, int):
        return jsonify({"error": "Internal error while solving."}), 500
    return jsonify({"error": getattr(e, "description", "Error")}), code


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/data")
def data():
    return jsonify(default_problem())


@app.post("/api/solve")
def api_solve():
    body = request.get_json(silent=True)
    problem = default_problem()
    if body:                                   # allow overriding any part of the problem
        for key in ("supply", "demand", "cost_matrix", "closed", "caps", "current_allocation"):
            if key in body:
                problem[key] = body[key]
    return jsonify(run(problem))


def _int_param(body, key, default, lo, hi):
    v = body.get(key, default)
    if type(v) is not int or not lo <= v <= hi:
        raise BadRequest(f"'{key}' must be an integer between {lo} and {hi}.")
    return v


@app.post("/api/simulate")
def api_simulate():
    body = request.get_json(silent=True) or {}
    rate = _int_param(body, "incidents_per_hour", 48, 1, 100)
    hours = _int_param(body, "hours", 24, 1, 48)
    reps = _int_param(body, "reps", 10, 1, 30)
    seed = _int_param(body, "seed", 2026, 0, 10**9)
    if rate * hours * reps > 80000:
        raise BadRequest("Simulation too large: reduce incidents per hour, hours or replications.")

    problem = default_problem()
    _validate(problem)
    closed = [tuple(c) for c in problem["closed"]]
    caps = [tuple(c) for c in problem["caps"]]
    plan = solve(problem["supply"], problem["demand"], problem["cost_matrix"],
                 closed, caps)["optimal"]["allocation"]
    return jsonify(run_comparison(problem, closed, caps, plan,
                                  incidents_per_hour=rate, hours=hours, reps=reps, seed=seed))


@app.post("/api/simulate/run")
def api_simulate_run():
    body = request.get_json(silent=True) or {}
    strategy = body.get("strategy", "plan")
    if strategy not in ("plan", "greedy"):
        raise BadRequest("'strategy' must be 'plan' or 'greedy'.")
    rate = _int_param(body, "incidents_per_hour", 48, 1, 100)
    hours = _int_param(body, "hours", 6, 1, 12)
    seed = _int_param(body, "seed", 2026, 0, 10**9)
    problem = default_problem()
    closed = [tuple(c) for c in problem["closed"]]
    caps = [tuple(c) for c in problem["caps"]]
    plan = solve(problem["supply"], problem["demand"], problem["cost_matrix"],
                 closed, caps)["optimal"]["allocation"]
    return jsonify({"hours": hours, "missions": replay(strategy, problem, closed, caps, plan,
                                                       rate, hours, seed)})


if __name__ == "__main__":
    app.run(debug=False, port=5000)
