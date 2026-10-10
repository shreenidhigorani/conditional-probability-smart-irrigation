import { decide } from "./lib/decision";

// Change in frontend/.env (VITE_API_URL) if your backend runs elsewhere.
const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options) {
  let res;
  try {
    res = await fetch(`${BASE}${path}`, options);
  } catch {
    throw new Error(
      `Cannot reach the API at ${BASE}. Start the backend (uvicorn app.main:app --reload) or switch on Mock mode.`
    );
  }
  if (!res.ok) {
    let detail = "";
    try {
      const body = await res.json();
      detail = Array.isArray(body.detail)
        ? body.detail.map((d) => `${d.loc?.slice(-1)[0]}: ${d.msg}`).join("; ")
        : body.detail || "";
    } catch {
      /* ignore non-JSON error bodies */
    }
    throw new Error(`API error ${res.status}. ${detail}`.trim());
  }
  return res.json();
}

export function predict(payload) {
  return request("/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getTables() {
  return request("/tables");
}

/* ---------- Mock mode: placeholder numbers, NOT real results ---------- */
const MOCK_P = {
  Dry: { None: 0.8, Light: 0.6, Heavy: 0.35 },
  Moderate: { None: 0.45, Light: 0.3, Heavy: 0.15 },
  Wet: { None: 0.12, Light: 0.06, Heavy: 0.02 },
};

export async function mockPredict({ soil, rain, c_irr, c_stress }) {
  await new Promise((r) => setTimeout(r, 300));
  const p = MOCK_P[soil][rain];
  return { ...decide(p, c_irr, c_stress), n: 120, mock: true };
}

export async function mockTables() {
  const soils = ["Dry", "Moderate", "Wet"];
  const rains = ["None", "Light", "Heavy"];
  const conditional = {};
  const counts = {};
  soils.forEach((s) => {
    conditional[s] = {};
    counts[s] = {};
    rains.forEach((r) => {
      conditional[s][r] = MOCK_P[s][r];
      counts[s][r] = r === "Heavy" ? 6 : 120; // placeholder
    });
  });
  return {
    joint: conditional,
    marginal_soil: { Dry: 0.33, Moderate: 0.33, Wet: 0.34 },
    marginal_rain: { None: 0.7, Light: 0.2, Heavy: 0.1 },
    conditional,
    counts,
    independence: { chi2: 0, df: 4, p_value: 1, alpha: 0.05, conclusion: "MOCK placeholder, not a real test result." },
    mock: true,
  };
}
