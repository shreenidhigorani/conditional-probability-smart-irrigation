"""Flask API for the IrrigAI Probability Engine."""
import math
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
from scipy.stats import chi2_contingency

from probability import (
    SOIL_ORDER,
    RAIN_ORDER,
    build_probability_tables,
    dry_tomorrow_table,
    irrigation_decision,
    load_data,
)

app = Flask(__name__)
CORS(app)

DATA = load_data()
DRY_TABLE = dry_tomorrow_table(DATA)


def _clean_value(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def _json_records(df):
    records = df.reset_index().to_dict(orient="records")
    return [{k: _clean_value(v) for k, v in r.items()} for r in records]


@app.get("/health")
def health():
    return jsonify({"status": "ok", "rows": len(DATA)})


@app.get("/tables")
def tables():
    tbls = build_probability_tables(DATA)

    # Compute Chi-Square Independence Statistics
    observed = tbls["counts"]
    chi2, p_val, dof, expected = chi2_contingency(observed)
    k = min(observed.shape) - 1
    cramers_v = float(np.sqrt(chi2 / (len(DATA) * k)))

    independence = {
        "chi2": round(float(chi2), 4),
        "p_value": float(p_val),
        "dof": int(dof),
        "cramers_v": round(cramers_v, 4),
        "independent": bool(p_val >= 0.05),
        "alpha": 0.05,
    }

    return jsonify({
        "counts": _json_records(tbls["counts"]),
        "joint": _json_records(tbls["joint"].round(6)),
        "marginal_soil": _json_records(tbls["marginal_soil"].round(6)),
        "marginal_rain": _json_records(tbls["marginal_rain"].round(6)),
        "conditional": _json_records(DRY_TABLE.round(6)),
        "conditional_soil_given_rain": _json_records(tbls["soil_given_rain"].round(6)),
        "conditional_rain_given_soil": _json_records(tbls["rain_given_soil"].round(6)),
        "dry_tomorrow_by_soil_and_rain": _json_records(DRY_TABLE.round(6)),
        "independence": independence,
    })


@app.get("/timeseries")
def timeseries():
    """Daily soil wetness and rain for the timeline chart."""
    d = DATA
    dry_max = float(d.loc[d["soil_cat"] == "Dry", "soil_wetness"].max())
    moderate_max = float(
        d.loc[d["soil_cat"] == "Moderate", "soil_wetness"].max())
    return jsonify({
        "dates": d["date"].tolist(),
        "soil_wetness": d["soil_wetness"].round(4).tolist(),
        "rain_mm": d["rain_mm"].round(2).tolist(),
        "rain_cat": d["rain_cat"].tolist(),
        "dry_max": dry_max,
        "moderate_max": moderate_max,
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

    row = DRY_TABLE[(DRY_TABLE["soil_cat"] == soil) &
                    (DRY_TABLE["rain_cat"] == rain)].iloc[0]
    p = _clean_value(row["p_dry_tomorrow"])
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
    app.run(host="127.0.0.1", port=8000, debug=False)
