const SOILS = ["Dry", "Moderate", "Wet"];
const RAINS = ["None", "Light", "Heavy"];
const PRESETS = [
  { name: "Dry + None", soil: "Dry", rain: "None" },
  { name: "Moderate + Light", soil: "Moderate", rain: "Light" },
  { name: "Wet + Heavy", soil: "Wet", rain: "Heavy" },
];
const field = "w-full rounded border border-line bg-white px-3 py-2.5 text-lg focus:border-ink focus:outline-none focus-visible:ring-2 focus-visible:ring-water";

export default function InputPanel({ form, setForm, t, costsValid, onCheck, loading, mock, setMock }) {
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  return (
    <section aria-labelledby="in-h" className="rounded-lg border border-line bg-card p-6">
      <h3 id="in-h" className="font-display text-2xl font-semibold">Today’s conditions</h3>
      <div className="mt-4 flex flex-wrap gap-2" role="group" aria-label="Quick scenarios">
        {PRESETS.map((p) => {
          const active = form.soil === p.soil && form.rain === p.rain;
          return (
            <button key={p.name} type="button" aria-pressed={active}
              onClick={() => setForm({ ...form, soil: p.soil, rain: p.rain })}
              className={`rounded border px-3 py-1.5 text-sm font-medium ${active ? "border-ink bg-ink text-white" : "border-line bg-white hover:border-ink"}`}>
              {p.name}
            </button>
          );
        })}
      </div>
      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <label className="block"><span className="mb-1 block text-sm font-semibold">Soil moisture</span>
          <select className={field} value={form.soil} onChange={set("soil")}>{SOILS.map((s) => <option key={s}>{s}</option>)}</select></label>
        <label className="block"><span className="mb-1 block text-sm font-semibold">Rainfall today</span>
          <select className={field} value={form.rain} onChange={set("rain")}>{RAINS.map((r) => <option key={r}>{r}</option>)}</select></label>
        <label className="block"><span className="mb-1 block text-sm font-semibold">Cost to irrigate (c_irr)</span>
          <input className={field} type="number" min="0.01" step="0.1" value={form.c_irr} onChange={set("c_irr")} /></label>
        <label className="block"><span className="mb-1 block text-sm font-semibold">Cost of crop stress (c_stress)</span>
          <input className={field} type="number" min="0.01" step="0.1" value={form.c_stress} onChange={set("c_stress")} /></label>
      </div>
      <p className="mt-4 text-lg">Threshold t = c_irr ÷ c_stress = <strong>{costsValid ? t.toFixed(2) : "enter positive costs"}</strong></p>
      <div className="mt-5 flex flex-wrap items-center gap-4">
        <button type="button" onClick={onCheck} disabled={loading || !costsValid}
          className="rounded bg-ink px-8 py-3 text-lg font-semibold text-white hover:bg-ink/90 focus-visible:ring-2 focus-visible:ring-water focus-visible:ring-offset-2 disabled:opacity-50">
          {loading ? "Checking…" : "Check"}
        </button>
        <label className="flex cursor-pointer items-center gap-2 text-sm text-muted">
          <input type="checkbox" checked={mock} onChange={(e) => setMock(e.target.checked)} className="h-4 w-4" />
          Mock mode (backend not running)
        </label>
      </div>
    </section>
  );
}
