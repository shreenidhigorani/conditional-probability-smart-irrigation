import ZoneGauge from "./ZoneGauge";
import DotGrid from "./DotGrid";
import CostBalance from "./CostBalance";
import { styleFor } from "../lib/decision";
import useCountUp from "../hooks/useCountUp";

function Big({ label, value, suffix = "" }) {
  const v = useCountUp(value);
  return (
    <div className="rounded border border-line p-4">
      <p className="text-sm text-muted">{label}</p>
      <p className="font-display text-5xl font-semibold tabular-nums">{v.toFixed(suffix === "%" ? 1 : 2)}{suffix}</p>
    </div>
  );
}

export default function ResultPanel({ state }) {
  const { status, data, error, asked } = state;
  return (
    <section aria-labelledby="r-h" aria-live="polite" className="rounded-lg border border-line bg-card p-6">
      <h3 id="r-h" className="font-display text-2xl font-semibold">Result and decision</h3>

      {status === "idle" && <p className="mt-3 text-lg text-muted">Choose conditions and press Check.</p>}
      {status === "loading" && <p className="mt-3 text-lg text-muted">Calculating from the dataset…</p>}
      {status === "error" && (
        <div role="alert" className="mt-3 rounded border border-red-300 bg-red-50 p-4 text-red-900">
          <p className="font-semibold">Could not get a result</p><p className="mt-1">{error}</p>
        </div>
      )}

      {status === "done" && data && data.p_dry_tomorrow == null && (
        <div className="mt-4">
          <div className="rounded bg-muted p-5 text-white">
            <p className="text-sm opacity-90">Decision</p>
            <p className="font-display text-3xl font-semibold">Not enough data</p>
          </div>
          <p className="mt-4 text-lg">
            No days in the dataset had {asked.soil} soil with {asked.rain} rain, so the probability is undefined
            (not zero). Try a different condition.
          </p>
        </div>
      )}

      {status === "done" && data && data.p_dry_tomorrow != null && (
        <div className="mt-4">
          {data.mock && <p className="mb-3 inline-block rounded bg-wait px-2.5 py-1 text-sm font-semibold text-white">MOCK DATA: placeholder numbers, not from the dataset</p>}
          <div className={`rounded p-5 text-white ${styleFor(data.decision).bg}`}>
            <p className="text-sm opacity-90">Decision</p>
            <p className="font-display text-4xl font-semibold sm:text-5xl">{data.decision}</p>
          </div>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <Big label="P(dry tomorrow)" value={data.p_dry_tomorrow * 100} suffix="%" />
            <Big label="Threshold t" value={Number(data.threshold)} />
          </div>
          <p className="mt-4 text-lg">{data.reason}</p>
          {data.n != null && <p className="mt-1 text-sm text-muted">Based on {data.n} matching days.</p>}
          {data.low_support && <p className="mt-3 rounded border border-wait bg-amber-50 p-3 text-amber-900">Few matching days in the dataset, so treat this probability with caution.</p>}

          <div className="mt-8 grid items-start gap-8 md:grid-cols-2">
            <DotGrid p={data.p_dry_tomorrow} asked={asked} />
            <CostBalance p={data.p_dry_tomorrow} cIrr={asked.c_irr} cStress={asked.c_stress} />
          </div>
          <div className="mt-8"><ZoneGauge p={data.p_dry_tomorrow} threshold={Number(data.threshold)} /></div>
          {data.warning && <p className="mt-4 text-sm text-muted">{data.warning}</p>}
        </div>
      )}
    </section>
  );
}
