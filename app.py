
from flask import Flask, jsonify

from data import (
    AREAS,
    CLOSED_ROUTES,
    COST_MATRIX,
    CURRENT_DISTRIBUTION,
    DATA_IS_SYNTHETIC,
    DEMAND,
    OPTIMAL_DISTRIBUTION,
    REFERENCE_CURRENT_COST,
    REFERENCE_OPTIMAL_COST,
    ROUTE_CAPACITIES,
    STATIONS,
    SUPPLY,
    calculate_distribution_cost,
    validate_data,
    validate_distribution,
)

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify({
        "message": "Smart Ambulance Allocation API",
        "stations": STATIONS,
        "areas": AREAS,
        "ambulance_supply": SUPPLY,
        "area_demand": DEMAND,
        "cost_matrix": COST_MATRIX,
        "current_distribution": CURRENT_DISTRIBUTION,
        "optimal_distribution": OPTIMAL_DISTRIBUTION,
        "current_cost": calculate_distribution_cost(
            CURRENT_DISTRIBUTION
        ),
        "current_reference_cost": REFERENCE_CURRENT_COST,
        "optimal_cost": calculate_distribution_cost(
            OPTIMAL_DISTRIBUTION
        ),
        "optimal_reference_cost": REFERENCE_OPTIMAL_COST,
        "closed_routes": [
            {"from": station, "to": area}
            for station, area in CLOSED_ROUTES
        ],
        "route_capacities": [
            {
                "from": station,
                "to": area,
                "max": maximum
            }
            for (station, area), maximum
            in ROUTE_CAPACITIES.items()
        ],
        "synthetic_data": DATA_IS_SYNTHETIC,
    })


@app.route("/api/data")
def get_data():
    return jsonify({
        "stations": STATIONS,
        "areas": AREAS,
        "supply": SUPPLY,
        "demand": DEMAND,
        "cost_matrix": COST_MATRIX,
        "closed_routes": [
            {"from": station, "to": area}
            for station, area in CLOSED_ROUTES
        ],
        "route_capacities": [
            {
                "from": station,
                "to": area,
                "max": maximum
            }
            for (station, area), maximum
            in ROUTE_CAPACITIES.items()
        ],
        "synthetic_data": DATA_IS_SYNTHETIC,
    })


@app.route("/api/validate")
def validate():
    errors = validate_data()

    return jsonify({
        "valid": not errors,
        "errors": errors,
    }), (200 if not errors else 400)


@app.route("/api/distribution/current")
def current_distribution():
    errors = validate_distribution(CURRENT_DISTRIBUTION)

    return jsonify({
        "distribution": CURRENT_DISTRIBUTION,
        "valid": not errors,
        "errors": errors,
    }), (200 if not errors else 400)


@app.route("/api/distribution/optimal-reference")
def optimal_distribution():
    errors = validate_distribution(OPTIMAL_DISTRIBUTION)

    return jsonify({
        "distribution": OPTIMAL_DISTRIBUTION,
        "valid": not errors,
        "errors": errors,
    }), (200 if not errors else 400)


@app.route("/api/cost/current")
def current_cost():
    return jsonify({
        "cost": calculate_distribution_cost(
            CURRENT_DISTRIBUTION
        ),
        "reference_cost": REFERENCE_CURRENT_COST,
    })


@app.route("/api/cost/optimal-reference")
def optimal_cost():
    return jsonify({
        "cost": calculate_distribution_cost(
            OPTIMAL_DISTRIBUTION
        ),
        "reference_cost": REFERENCE_OPTIMAL_COST,
    })


if __name__ == "__main__":
    app.run(debug=True)
