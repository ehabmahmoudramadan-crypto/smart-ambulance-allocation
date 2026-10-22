
from flask import Flask, jsonify
from data import (
    SUPPLY,
    DEMAND,
    COST_MATRIX,
    CURRENT_ALLOCATION,
    DATA_IS_SYNTHETIC,
    validate_data,
    calculate_current_cost
)

app = Flask(__name__)


@app.route("/")
def home():
    if not validate_data():
        return jsonify({
            "error": "Invalid transportation data"
        }), 400

    return jsonify({
        "supply": SUPPLY,
        "demand": DEMAND,
        "cost_matrix": COST_MATRIX,
        "current_allocation": CURRENT_ALLOCATION,
        "current_cost": calculate_current_cost(),
        "data_is_synthetic": DATA_IS_SYNTHETIC
    })


@app.route("/api/data")
def get_data():
    if not validate_data():
        return jsonify({
            "error": "Invalid transportation data"
        }), 400

    return jsonify({
        "supply": SUPPLY,
        "demand": DEMAND,
        "cost_matrix": COST_MATRIX,
        "current_allocation": CURRENT_ALLOCATION,
        "current_cost": calculate_current_cost(),
        "data_is_synthetic": DATA_IS_SYNTHETIC
    })


if __name__ == "__main__":
    app.run(debug=True)
