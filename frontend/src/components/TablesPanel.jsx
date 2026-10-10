const TITLES = {
  joint: "Joint probability P(soil ∩ rain)",
  marginal_soil: "Marginal P(soil)",
  marginal_rain: "Marginal P(rain)",
  conditional: "P(dry tomorrow | soil, rain)",
};
const fmt = (v) => (typeof v === "number" ? v.toFixed(3) : v ?? "–");

function Grid({ data }) {
  if (!data || typeof data !== "object") return <p className="text-muted">No data.</p>;
  const rows = Object.entries(data);
  const nested = rows.length && typeof rows[0][1] === "object" && rows[0][1] !== null;
  if (!nested) return (
    <table className="w-full text-left"><thead><tr>{rows.map(([k]) => <th key={k} className="border-b border-line px-3 py-2 font-semibold">{k}</th>)}</tr></thead>
      <tbody><tr>{rows.map(([k, v]) => <td key={k} className="px-3 py-2 tabular-nums">{fmt(v)}</td>)}</tr></tbody></table>
  );
  const cols = Object.keys(rows[0][1]);
  return (
    <table className="w-full text-left">
      <thead><tr><th className="border-b border-line px-3 py-2 font-semibold">Soil ↓ / Rain →</th>
        {cols.map((c) => <th key={c} className="border-b border-line px-3 py-2 font-semibold">{c}</th>)}</tr></thead>
      <tbody>{rows.map(([r, vals]) => (
        <tr key={r}><th scope="row" className="px-3 py-2 font-semibold">{r}</th>
          {cols.map((c) => <td key={c} className="px-3 py-2 tabular-nums">{fmt(vals[c])}</td>)}</tr>))}</tbody>
    </table>
  );
}

export default function TablesPanel({ tables, error, onReload }) {
  return (
    <section aria-labelledby="t-h" className="rounded-lg border border-line bg-card p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 id="t-h" className="font-display text-2xl font-semibold">Probability tables</h3>
        <button type="button" onClick={onReload} className="rounded border border-ink px-4 py-2 font-semibold hover:bg-ink hover:text-white focus-visible:ring-2 focus-visible:ring-water">Reload</button>
      </div>
      {error && <p role="alert" className="mt-3 text-red-800">{error}</p>}
      {tables?.mock && <p className="mt-3 text-sm font-semibold text-wait">Mock tables: placeholder values.</p>}
      {tables && (
        <div className="mt-4 grid gap-6 lg:grid-cols-2">
          {Object.keys(TITLES).map((k) => (
            <div key={k} className="overflow-x-auto"><h4 className="mb-2 font-semibold">{TITLES[k]}</h4><Grid data={tables[k]} /></div>
          ))}
        </div>
      )}
      <div id="charts-slot" className="mt-6" /> {/* Member 6: add report charts here */}
    </section>
  );
}
