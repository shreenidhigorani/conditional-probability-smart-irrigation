const SOILS = ["Dry", "Moderate", "Wet"];
const RAINS = ["None", "Light", "Heavy"];
const MIN_SUPPORT = 10;

// Click a cell to choose soil + rain. Colour = P(dry tomorrow | soil, rain).
// Dashed border = fewer than MIN_SUPPORT days (unreliable estimate).
export default function Heatmap({ conditional, counts, soil, rain, onPick }) {
  if (!conditional) return <p className="text-muted">Probability map appears when /tables is available.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="border-separate border-spacing-2">
        <caption className="mb-2 text-left text-sm text-muted">
          P(dry tomorrow | soil, rain). Click a cell to select that condition.
        </caption>
        <thead>
          <tr>
            <th className="text-left text-sm font-semibold">Soil ↓ / Rain →</th>
            {RAINS.map((r) => <th key={r} className="px-2 text-sm font-semibold">{r}</th>)}
          </tr>
        </thead>
        <tbody>
          {SOILS.map((s) => (
            <tr key={s}>
              <th scope="row" className="pr-2 text-left text-sm font-semibold">{s}</th>
              {RAINS.map((r) => {
                const p = conditional?.[s]?.[r];
                const n = counts?.[s]?.[r];
                const has = typeof p === "number";
                const selected = soil === s && rain === r;
                const low = typeof n === "number" && n < MIN_SUPPORT;
                return (
                  <td key={r}>
                    <button type="button" onClick={() => onPick(s, r)} aria-pressed={selected}
                      aria-label={`${s} soil, ${r} rain: ${has ? p.toFixed(2) : "no data"}${n != null ? `, ${n} days` : ""}`}
                      style={{ backgroundColor: has ? `rgba(138,79,38,${0.1 + 0.85 * p})` : "#fff", color: has && p > 0.5 ? "#fff" : "#14221c" }}
                      className={`h-20 w-28 rounded-md border-2 text-center ${low ? "border-dashed" : "border-solid"} ${
                        selected ? "border-ink ring-2 ring-ink ring-offset-2" : "border-line hover:border-ink"
                      }`}>
                      <span className="block text-xl font-bold">{has ? p.toFixed(2) : "–"}</span>
                      {n != null && <span className="block text-xs">n = {n}{low ? " (few)" : ""}</span>}
                    </button>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
