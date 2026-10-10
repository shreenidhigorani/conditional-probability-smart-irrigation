"""Optional Flask API for the IrrigAI Probability Engine.

POST /predict JSON: {"soil":"Dry","rain":"None","c_irr":2,"c_stress":10}
GET /tables returns frequency/probability tables as JSON.
"""
from flask import Flask, jsonify, request

from probability import (
    SOIL_ORDER,
    RAIN_ORDER,
    build_probability_tables,
    conditional_prob,
    dry_tomorrow_table,
    irrigation_decision,
    load_data,
)

app = Flask(__name__)
DATA = load_data()
DRY_TABLE = dry_tomorrow_table(DATA)


def _json_records(df):
    return df.reset_index().where(df.reset_index().notna(), None).to_dict(orient="records")


@app.get("/health")
def health():
    return jsonify({"status": "ok", "rows": len(DATA)})


@app.get("/tables")
def tables():
    tables = build_probability_tables(DATA)
    return jsonify({
        "counts": _json_records(tables["counts"]),
        "joint": _json_records(tables["joint"].round(6)),
        "marginal_soil": _json_records(tables["marginal_soil"].round(6)),
        "marginal_rain": _json_records(tables["marginal_rain"].round(6)),
        "conditional": _json_records(DRY_TABLE.round(6)),
        "conditional_soil_given_rain": _json_records(tables["soil_given_rain"].round(6)),
        "conditional_rain_given_soil": _json_records(tables["rain_given_soil"].round(6)),
        "dry_tomorrow_by_soil_and_rain": _json_records(DRY_TABLE.round(6)),
    })


@app.post("/predict")
def predict():
    payload = request.get_json(silent=True) or {}
    soil = payload.get("soil")
    rain = payload.get("rain")
    c_irr = payload.get("c_irr")
    c_stress = payload.get("c_stress")

    if soil not in SOIL_ORDER or rain not in RAIN_ORDER:
        return jsonify({"error": "soil must be Dry/Moderate/Wet and rain must be None/Light/Heavy"}), 400
    try:
        c_irr = float(c_irr)
        c_stress = float(c_stress)
        if c_irr < 0 or c_stress <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "c_irr must be >= 0 and c_stress must be > 0"}), 400

    row = DRY_TABLE[(DRY_TABLE["soil_cat"] == soil) & (DRY_TABLE["rain_cat"] == rain)].iloc[0]
    p = row["p_dry_tomorrow"]
    if p is not None and p != p:  # NaN check
        p = None
    decision = irrigation_decision(p, c_irr, c_stress)
    return jsonify({
        "soil": soil,
        "rain": rain,
        "p_dry_tomorrow": p,
        "support_count": int(row["support_count"]),
        "threshold": decision["threshold"],
        "upper_threshold": decision["upper_threshold"],
        "decision": decision["decision"],
        "reason": decision["reason"],
        "warning": "Experimental result based on the supplied dataset; not verified agricultural advice.",
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
