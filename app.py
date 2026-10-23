import copy
import json
import os
import time

from flask import Flask, jsonify, render_template, request
from jinja2 import TemplateNotFound
from werkzeug.exceptions import HTTPException

import data as default_data
from errors import ApiError
from solver import solve
from validation import area_name, parse_problem, station_name

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024


def default_payload():
    return {
        "supply": copy.deepcopy(default_data.SUPPLY),
        "demand": copy.deepcopy(default_data.DEMAND),
        "cost_matrix": copy.deepcopy(default_data.COST_MATRIX),
        "current_allocation": copy.deepcopy(default_data.CURRENT_ALLOCATION),
    }


def wants_html():
    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    return best == "text/html"


@app.get("/")
def home():
    if wants_html():
        try:
            return render_template("index.html")
        except TemplateNotFound:
            pass
    return get_data()


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/data")
def get_data():
    if not default_data.validate_data():
        return (
            jsonify({"error": "Invalid transportation data", "code": "INVALID_DEFAULT_DATA"}),
            500,
        )
    return jsonify(
        {
            "supply": default_data.SUPPLY,
            "demand": default_data.DEMAND,
            "cost_matrix": default_data.COST_MATRIX,
            "current_allocation": default_data.CURRENT_ALLOCATION,
            "current_cost": default_data.calculate_current_cost(),
            "stations": [station_name(i) for i in range(len(default_data.SUPPLY))],
            "areas": [area_name(j) for j in range(len(default_data.DEMAND))],
            "data_is_synthetic": default_data.DATA_IS_SYNTHETIC,
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
    result["data_is_synthetic"] = default_data.DATA_IS_SYNTHETIC
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
