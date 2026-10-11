import { useCallback, useEffect, useMemo, useState } from "react";
import { predict, mockPredict, getTables, mockTables, getTimeseries, mockTimeseries } from "./api";
import useStages from "./hooks/useStages";
import StageNav from "./components/StageNav";
import Stage from "./components/Stage";
import SoilCrossSection from "./components/SoilCrossSection";
import InputPanel from "./components/InputPanel";
import ResultPanel from "./components/ResultPanel";
import Heatmap from "./components/Heatmap";
import TablesPanel from "./components/TablesPanel";
import IndependencePanel from "./components/IndependencePanel";
import Footer from "./components/Footer";
import SoilTimeline from "./components/SoilTimeline";
import FigureGallery from "./components/FigureGallery";

const card = "rounded-lg border border-line bg-card p-6";

export default function App() {
  const [form, setForm] = useState({ soil: "Dry", rain: "None", c_irr: 1, c_stress: 3 });
  const [mock, setMock] = useState(false);
  const [state, setState] = useState({ status: "idle", data: null, error: null, asked: null });
  const [tables, setTables] = useState(null);
  const [tablesError, setTablesError] = useState(null);
  const [series, setSeries] = useState(null);
  const [seriesError, setSeriesError] = useState(null);
  const active = useStages();

  const cIrr = Number(form.c_irr);
  const cStress = Number(form.c_stress);
  const costsValid = cIrr > 0 && cStress > 0;
  const t = useMemo(() => (costsValid ? cIrr / cStress : NaN), [cIrr, cStress, costsValid]);

  const loadTables = useCallback(async () => {
    setTablesError(null);
    try { setTables(mock ? await mockTables() : await getTables()); }
    catch (e) { setTables(null); setTablesError(e.message); }
  }, [mock]);
  useEffect(() => { loadTables(); }, [loadTables]);

  useEffect(() => {
    let cancelled = false;
    setSeriesError(null);
    (mock ? mockTimeseries() : getTimeseries())
      .then((d) => !cancelled && setSeries(d))
      .catch((e) => { if (!cancelled) { setSeries(null); setSeriesError(e.message); } });
    return () => { cancelled = true; };
  }, [mock]);

  async function check() {
    const payload = { soil: form.soil, rain: form.rain, c_irr: cIrr, c_stress: cStress };
    setState({ status: "loading", data: null, error: null, asked: payload });
    try {
      const data = mock ? await mockPredict(payload) : await predict(payload);
      setState({ status: "done", data, error: null, asked: payload });
    } catch (e) {
      setState({ status: "error", data: null, error: e.message, asked: payload });
    }
  }
  const go = (id) => document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });

  return (
    <>
      <StageNav active={active} mock={mock} />
      <main>
        {/* PROBLEM */}
        <Stage id="problem" title="Should we irrigate today?"
          intro="Water costs money and dry soil stresses the crop. Instead of guessing, IrrigAI asks: given today’s soil and rain, how likely is it that tomorrow is dry?">
          <div className="grid items-center gap-10 lg:grid-cols-2">
            <div>
              <ul className="space-y-3 text-xl">
                <li>Over-irrigation wastes water and pumping cost.</li>
                <li>Under-irrigation stresses sugarcane and cuts yield.</li>
                <li>Conditional probability turns past data into a decision rule.</li>
              </ul>
              <div className="mt-8 flex flex-wrap gap-3">
                <button type="button" onClick={() => go("decision")} className="rounded bg-ink px-6 py-3 text-lg font-semibold text-white focus-visible:ring-2 focus-visible:ring-water focus-visible:ring-offset-2">Try the live demo</button>
                <button type="button" onClick={() => go("data")} className="rounded border border-ink px-6 py-3 text-lg font-semibold focus-visible:ring-2 focus-visible:ring-water">See the data</button>
                <label className="flex cursor-pointer items-center gap-2 rounded border border-line bg-white px-4 py-3 text-base">
                  <input type="checkbox" checked={mock} onChange={(e) => setMock(e.target.checked)} className="h-5 w-5" />
                  Mock mode (backend not running)
                </label>
              </div>
            </div>
            <div className="overflow-hidden rounded-lg border border-line bg-card">
              <SoilCrossSection soil={form.soil} rain={form.rain} />
              <p className="px-4 py-2 text-sm text-muted">Illustration of the selected conditions: {form.soil} soil, {form.rain} rain.</p>
            </div>
          </div>
        </Stage>

        {/* DATA */}
        <Stage id="data" index={1} title="Real data, then categories"
          intro="NASA POWER daily record for Kolhapur, Maharashtra, 2022–2025, sorted into categories.">
          <div className="grid gap-5 md:grid-cols-3">
            <div className={card}><h3 className="font-display text-2xl font-semibold">Source</h3>
              <p className="mt-2 text-lg">NASA POWER (Prediction Of Worldwide Energy Resources), daily values for a point near Kolhapur. Satellite- and model-derived, publicly verifiable.</p></div>
            <div className={card}><h3 className="font-display text-2xl font-semibold">Variables</h3>
              <p className="mt-2 text-lg">Rainfall in mm/day and root-zone soil wetness (0 to 1, modelled). Next-day soil is built by shifting the series one day.</p></div>
            <div className={card}><h3 className="font-display text-2xl font-semibold">Categories</h3>
              <p className="mt-2 text-lg">Rain: None below 2.5 mm, Light 2.5–15.5 mm, Heavy above 15.5 mm. Soil: Dry, Moderate, Wet by tertiles of this dataset.</p></div>
          </div>
          <p className="mt-6 max-w-3xl text-muted">Soil wetness is a modelled estimate, not a field sensor reading. Treat results as patterns in this record.</p>
        </Stage>

        {/* METHOD */}
        <Stage id="method" index={2} title="Probability from counting"
          intro="Every probability here is a relative frequency: a count divided by a count.">
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
            {[["Joint", "P(A ∩ B) = n(A ∩ B) ÷ N", "Both happen on the same day."],
              ["Marginal", "P(A) = n(A) ÷ N", "One variable, ignoring the other."],
              ["Conditional", "P(A | B) = P(A ∩ B) ÷ P(B)", "Restrict to days where B holds."],
              ["Independence", "P(A ∩ B) = P(A) P(B)", "If true, rain tells us nothing about soil."]].map(([h, f, d]) => (
              <div key={h} className={card}><h3 className="font-display text-xl font-semibold">{h}</h3>
                <p className="mt-2 text-lg font-semibold">{f}</p><p className="mt-1 text-muted">{d}</p></div>))}
          </div>
          <div className={`${card} mt-6`}>
            <h3 className="font-display text-2xl font-semibold">Pick a condition on the probability map</h3>
            <p className="mt-1 text-lg">
              P(dry tomorrow | soil = {form.soil}, rain = {form.rain}) = days like this followed by a dry day ÷ all days like this
            </p>
            <div className="mt-4"><Heatmap conditional={tables?.conditional} counts={tables?.counts} soil={form.soil} rain={form.rain}
              onPick={(soil, rain) => setForm({ ...form, soil, rain })} /></div>
            {tablesError && <p role="alert" className="mt-3 text-red-800">{tablesError}</p>}
          </div>
        </Stage>

        {/* LIVE DECISION */}
        <Stage id="decision" index={3} title="Live decision"
          intro="Change the conditions or the costs and press Check. The probability comes from the dataset; the decision weighs it against cost.">
          <div className="grid items-start gap-6 lg:grid-cols-5">
            <div className="lg:col-span-2"><InputPanel form={form} setForm={setForm} t={t} costsValid={costsValid} onCheck={check}
              loading={state.status === "loading"} mock={mock} setMock={setMock} /></div>
            <div className="lg:col-span-3"><ResultPanel state={state} /></div>
          </div>
        </Stage>

        {/* EVIDENCE */}
        <Stage id="evidence" index={4} title="Tables and independence test"
          intro="The full tables behind the result, and whether rain and soil category are statistically independent.">
          <div className="grid gap-6">
            <section aria-labelledby="ts-h" className="rounded-lg border border-line bg-card p-6">
              <h3 id="ts-h" className="font-display text-2xl font-semibold">Soil wetness, 2022 to 2025</h3>
              <div className="mt-4"><SoilTimeline series={series} error={seriesError} /></div>
            </section>
            <TablesPanel tables={tables} error={tablesError} onReload={loadTables} />
            <IndependencePanel info={tables?.independence} />
            <FigureGallery />
          </div>
        </Stage>

      </main>
      <Footer />
    </>
  );
}
