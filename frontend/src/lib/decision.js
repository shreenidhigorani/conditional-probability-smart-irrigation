// Same rule as the Python engine. Used for (a) drawing the gauge zones
// from the API's threshold and (b) mock mode only.
export const HIGH_P = 0.75;

export function zones(threshold) {
  const lower = threshold;
  const upper = Math.max(HIGH_P, threshold);
  return { lower: Math.min(lower, 1), upper: Math.min(upper, 1) };
}

export function decide(p, c_irr, c_stress) {
  const t = c_irr / c_stress;
  const upper = Math.max(HIGH_P, t);
  let decision;
  if (p >= upper) decision = "IRRIGATE NOW";
  else if (p >= t) decision = "DELAY & RE-CHECK";
  else decision = "DON’T IRRIGATE";
  return {
    p_dry_tomorrow: p,
    threshold: t,
    decision,
    reason: `MOCK: P(dry tomorrow) = ${p.toFixed(2)} compared with threshold ${t.toFixed(2)}.`,
  };
}

export const DECISION_STYLE = {
  "IRRIGATE NOW": { bg: "bg-water", label: "Irrigate" },
  "DELAY & RE-CHECK": { bg: "bg-wait", label: "Wait" },
  "DON’T IRRIGATE": { bg: "bg-field", label: "Hold off" },
};

export function styleFor(decision) {
  // Tolerate straight or curly apostrophe from the backend
  const key = decision?.replace("'", "’");
  return DECISION_STYLE[key] || { bg: "bg-ink", label: decision };
}
