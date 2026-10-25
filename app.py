import copy
import json
import os
import time

from flask import Flask, jsonify, render_template, request
from jinja2 import TemplateNotFound
from werkzeug.exceptions import HTTPException

import data as store
from errors import ApiError
from solver import solve
from validation import parse_problem

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024


def closed_routes_view():
    return [{"from": station, "to": area} for station, area in store.CLOSED_ROUTES]


def route_capacities_view():
    return [
        {"from": station, "to": area, "max": maximum}
        for (station, area), maximum in store.ROUTE_CAPACITIES.items()
    ]


def default_payload():
    return {
        "stations": list(store.STATIONS),
        "areas": list(store.AREAS),
        "supply": list(store.SUPPLY),
        "demand": list(store.DEMAND),
        "cost_matrix": copy.deepcopy(store.COST_MATRIX),
        "current_distribution": copy.deepcopy(store.CURRENT_DISTRIBUTION),
        "closed_routes": closed_routes_view(),
        "route_capacities": route_capacities_view(),
    }


def wants_html():
    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    return best == "text/html"


@app.route("/")
def home():
    if wants_html():
        try:
            return render_template("index.html")
        except TemplateNotFound:
            pass
    return jsonify(
        {
            "message": "Smart Ambulance Allocation API",
            "stations": store.STATIONS,
            "areas": store.AREAS,
            "ambulance_supply": store.SUPPLY,
            "area_demand": store.DEMAND,
            "cost_matrix": store.COST_MATRIX,
            "current_distribution": store.CURRENT_DISTRIBUTION,
            "optimal_distribution": store.OPTIMAL_DISTRIBUTION,
            "current_cost": store.calculate_distribution_cost(store.CURRENT_DISTRIBUTION),
            "current_reference_cost": store.REFERENCE_CURRENT_COST,
            "optimal_cost": store.calculate_distribution_cost(store.OPTIMAL_DISTRIBUTION),
            "optimal_reference_cost": store.REFERENCE_OPTIMAL_COST,
            "closed_routes": closed_routes_view(),
            "route_capacities": route_capacities_view(),
            "synthetic_data": store.DATA_IS_SYNTHETIC,
        }
    )


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/data")
def get_data():
    return jsonify(
        {
            "stations": store.STATIONS,
            "areas": store.AREAS,
            "supply": store.SUPPLY,
            "demand": store.DEMAND,
            "cost_matrix": store.COST_MATRIX,
            "closed_routes": closed_routes_view(),
            "route_capacities": route_capacities_view(),
            "synthetic_data": store.DATA_IS_SYNTHETIC,
        }
    )


@app.route("/api/validate")
def validate():
    errors = store.validate_data()
    return jsonify({"valid": not errors, "errors": errors}), (200 if not errors else 400)


@app.route("/api/distribution/current")
def current_distribution():
    errors = store.validate_distribution(store.CURRENT_DISTRIBUTION)
    return (
        jsonify(
            {
                "distribution": store.CURRENT_DISTRIBUTION,
                "valid": not errors,
                "errors": errors,
            }
        ),
        200 if not errors else 400,
    )


@app.route("/api/distribution/optimal-reference")
def optimal_distribution():
    errors = store.validate_distribution(store.OPTIMAL_DISTRIBUTION)
    return (
        jsonify(
            {
                "distribution": store.OPTIMAL_DISTRIBUTION,
                "valid": not errors,
                "errors": errors,
            }
        ),
        200 if not errors else 400,
    )


@app.route("/api/cost/current")
def current_cost():
    return jsonify(
        {
            "cost": store.calculate_distribution_cost(store.CURRENT_DISTRIBUTION),
            "reference_cost": store.REFERENCE_CURRENT_COST,
        }
    )


@app.route("/api/cost/optimal-reference")
def optimal_cost():
    return jsonify(
        {
            "cost": store.calculate_distribution_cost(store.OPTIMAL_DISTRIBUTION),
            "reference_cost": store.REFERENCE_OPTIMAL_COST,
        }
    )


@app.post("/api/solve")
def solve_route():
    raw = request.get_data()
    source = "user"

    if not raw.strip():
        payload = default_payload()
        source = "default"
    else:
        try:
            payload = json.loads(raw)
        except ValueError:
            raise ApiError("The request body is not valid JSON.", "INVALID_JSON") from None
        if isinstance(payload, dict) and payload.get("use_default_data") is True:
            payload = default_payload()
            source = "default"

    problem = parse_problem(payload)

    started = time.perf_counter()
    result = solve(problem)

    result["data_source"] = source
    result["data_is_synthetic"] = store.DATA_IS_SYNTHETIC
    result["meta"] = {"elapsed_ms": round((time.perf_counter() - started) * 1000, 2)}
    return jsonify(result)


@app.errorhandler(ApiError)
def handle_api_error(error):
    return jsonify(error.to_dict()), error.status


@app.errorhandler(HTTPException)
def handle_http_error(error):
    if request.path.startswith("/api/"):
        code = error.name.upper().replace(" ", "_")
        return jsonify({"error": error.description, "code": code}), error.code
    return error


@app.errorhandler(500)
def handle_server_error(error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "An unexpected server error occurred.", "code": "INTERNAL_ERROR"}), 500
    return error


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "1") == "1")
