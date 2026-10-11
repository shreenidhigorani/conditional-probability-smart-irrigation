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
        : body.detail || body.error || "";
    } catch {
      /* ignore non-JSON error bodies */
    }
    throw new Error(`API error ${res.status}. ${detail}`.trim());
  }
  return res.json();
}

const MIN_SUPPORT = 10; // same cut-off the backend uses for "LOW SUPPORT"
const SOILS = ["Dry", "Moderate", "Wet"];
const RAINS = ["None", "Light", "Heavy"];

// Flask sends tables as lists of rows; the UI wants {soil: {rain: value}}.
function nest(rows, valueOf) {
  const out = {};
  SOILS.forEach((s) => (out[s] = {}));
  (rows || []).forEach((r) => RAINS.forEach((c) => {
    const v = valueOf(r, c);
    if (r.soil_cat && out[r.soil_cat]) out[r.soil_cat][c] = v;
  }));
  return out;
}
const flat = (rows, key) =>
  Object.fromEntries((rows || []).map((r) => [r[key], r.probability]));

function explainIndependence(i) {
  const p = Number(i.p_value);
  const base = p < i.alpha
    ? `p = ${p.toExponential(2)} is below ${i.alpha}, so independence is rejected: rain and soil category are associated in this record (not proof of cause).`
    : `p = ${p.toFixed(4)} is not below ${i.alpha}, so independence cannot be rejected in this record.`;
  return `${base} Cramér’s V = ${i.cramers_v} shows the strength. Daily data are correlated, so the p-value is optimistic.`;
}

export async function predict(payload) {
  const r = await request("/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const n = r.support_count ?? null;
  return { ...r, n, low_support: n !== null && n < MIN_SUPPORT };
}

export async function getTables() {
  const t = await request("/tables");
  const conditional = {};
  const counts = {};
  SOILS.forEach((s) => { conditional[s] = {}; counts[s] = {}; });
  (t.conditional || []).forEach((r) => {
    if (!conditional[r.soil_cat]) return;
    conditional[r.soil_cat][r.rain_cat] = r.p_dry_tomorrow; // null when no days
    counts[r.soil_cat][r.rain_cat] = r.support_count;
  });
  const ind = t.independence
    ? { ...t.independence, df: t.independence.dof, conclusion: explainIndependence(t.independence) }
    : null;
  return {
    joint: nest(t.joint, (r, c) => r[c]),
    marginal_soil: flat(t.marginal_soil, "soil_cat"),
    marginal_rain: flat(t.marginal_rain, "rain_cat"),
    conditional,
    counts,
    independence: ind,
  };
}

export function getTimeseries() {
  return request("/timeseries");
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

export async function mockTimeseries() {
  const n = 1460;
  const dates = [], soil_wetness = [], rain_mm = [], rain_cat = [];
  const start = new Date(Date.UTC(2022, 0, 1));
  for (let i = 0; i < n; i++) {
    const d = new Date(start.getTime() + i * 86400000);
    dates.push(d.toISOString().slice(0, 10));
    const s = 0.75 + 0.24 * Math.sin((2 * Math.PI * i) / 365 - 1.9);
    soil_wetness.push(Math.round(Math.min(0.99, Math.max(0.5, s)) * 100) / 100);
    const wetSeason = s > 0.8;
    const r = wetSeason ? (i * 7919) % 11 : 0;
    rain_cat.push(r > 8 ? "Heavy" : r > 4 ? "Light" : "None");
    rain_mm.push(r > 8 ? 20 : r > 4 ? 6 : 0);
  }
  return { dates, soil_wetness, rain_mm, rain_cat, dry_max: 0.53, moderate_max: 0.81, mock: true };
}
