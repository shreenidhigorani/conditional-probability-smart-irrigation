import { zones } from "../lib/decision";

export default function ZoneGauge({ p, threshold }) {
  const { lower, upper } = zones(threshold);
  const pct = (x) => `${(x * 100).toFixed(1)}%`;
  return (
    <figure role="img" aria-label={`P ${pct(p)}; thresholds ${pct(lower)} and ${pct(upper)}`}>
      <div className="relative pt-7">
        <div className="absolute top-0 -translate-x-1/2 text-center text-sm font-semibold"
          style={{ left: pct(Math.min(Math.max(p, 0), 1)), transition: "left .6s ease" }}>
          <div>P = {p.toFixed(2)}</div>
          <div className="mx-auto h-3 w-0.5 bg-ink" />
        </div>
        <div className="flex h-8 w-full overflow-hidden rounded border border-ink/30">
          <div className="bg-field" style={{ width: pct(lower) }} />
          <div className="bg-wait" style={{ width: pct(upper - lower) }} />
          <div className="bg-water" style={{ width: pct(1 - upper) }} />
        </div>
        <div className="relative mt-1 h-5 text-sm text-muted">
          <span className="absolute left-0">0</span>
          <span className="absolute -translate-x-1/2" style={{ left: pct(lower) }}>t = {lower.toFixed(2)}</span>
          {upper > lower && <span className="absolute -translate-x-1/2" style={{ left: pct(upper) }}>{upper.toFixed(2)}</span>}
          <span className="absolute right-0">1</span>
        </div>
      </div>
      <figcaption className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-sm text-muted">
        <span><i className="mr-1.5 inline-block h-3 w-3 rounded-sm bg-field align-middle" />Don’t irrigate</span>
        <span><i className="mr-1.5 inline-block h-3 w-3 rounded-sm bg-wait align-middle" />Delay and re-check</span>
        <span><i className="mr-1.5 inline-block h-3 w-3 rounded-sm bg-water align-middle" />Irrigate now</span>
      </figcaption>
    </figure>
  );
}
