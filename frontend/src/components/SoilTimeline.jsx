import { useMemo } from "react";

// Soil wetness 2022-2025 with Dry / Moderate / Wet bands and rain days marked.
// Everything is drawn from the data sent by GET /timeseries.
const W = 1000, H = 340, L = 66, R = 104, T = 16, B = 70;

export default function SoilTimeline({ series, error }) {
  const m = useMemo(() => {
    if (!series?.soil_wetness?.length) return null;
    const { dates, soil_wetness: v, rain_cat, dry_max, moderate_max } = series;
    const n = v.length;
    const y0 = Math.floor(Math.min(...v) * 20) / 20;
    const y1 = Math.min(1, Math.ceil(Math.max(...v) * 20) / 20);
    const x = (i) => L + (i / (n - 1)) * (W - L - R);
    const y = (val) => T + (1 - (val - y0) / (y1 - y0)) * (H - T - B);
    const path = v.map((val, i) => `${i ? "L" : "M"}${x(i).toFixed(1)} ${y(val).toFixed(1)}`).join(" ");
    const cat = (val) => (val <= dry_max ? 0 : val <= moderate_max ? 1 : 2);
    let same = 0;
    for (let i = 0; i < n - 1; i++) if (cat(v[i]) === cat(v[i + 1])) same++;
    const years = dates.map((d, i) => ({ d, i })).filter(({ d, i }) => d.endsWith("-01-01") || i === 0);
    const step = y1 - y0 > 0.3 ? 0.1 : 0.05;
    const ticks = [];
    for (let t = Math.ceil(y0 / step - 1e-9) * step; t <= y1 + 1e-9; t += step) ticks.push(Math.round(t * 100) / 100);
    return { n, y0, y1, x, y, path, persistence: (same / (n - 1)) * 100, years, ticks, rain_cat, dry_max, moderate_max };
  }, [series]);

  if (error) return <p role="alert" className="text-red-800">{error}</p>;
  if (!m) return <p className="text-muted">Loading the soil record…</p>;

  const bands = [
    { name: "Dry", from: m.y0, to: m.dry_max, color: "var(--color-clay)" },
    { name: "Moderate", from: m.dry_max, to: m.moderate_max, color: "var(--color-wait)" },
    { name: "Wet", from: m.moderate_max, to: m.y1, color: "var(--color-water)" },
  ];
  const stripBottom = H - B + 46;

  return (
    <figure>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" className="h-auto w-full"
        aria-label="Line chart of soil wetness from 2022 to 2025 with Dry, Moderate and Wet bands and rain days marked underneath">
        {bands.map((b) => (
          <g key={b.name}>
            <rect x={L} width={W - L - R} y={m.y(b.to)} height={Math.max(0, m.y(b.from) - m.y(b.to))} fill={b.color} opacity="0.14" />
            <text x={W - R + 8} y={(m.y(b.from) + m.y(b.to)) / 2 + 5} fontSize="15" fontWeight="600" fill="var(--color-ink)">{b.name}</text>
          </g>
        ))}

        {m.ticks.map((t) => (
          <g key={t}>
            <line x1={L} x2={W - R} y1={m.y(t)} y2={m.y(t)} stroke="var(--color-line)" strokeWidth="1" />
            <text x={L - 8} y={m.y(t) + 5} textAnchor="end" fontSize="14" fill="var(--color-muted)">{t.toFixed(2)}</text>
          </g>
        ))}
        <text x="14" y={(T + H - B) / 2} fontSize="14" fill="var(--color-muted)" transform={`rotate(-90 14 ${(T + H - B) / 2})`} textAnchor="middle">Soil wetness (0 to 1)</text>

        <path d={m.path} fill="none" stroke="var(--color-ink)" strokeWidth="2" strokeLinejoin="round" />

        {m.years.map(({ d, i }) => (
          <g key={d}>
            <line x1={m.x(i)} x2={m.x(i)} y1={T} y2={H - B} stroke="var(--color-line)" strokeDasharray="3 4" />
            <text x={m.x(i) + 4} y={H - B + 18} fontSize="14" fill="var(--color-muted)">{d.slice(0, 4)}</text>
          </g>
        ))}

        {/* rain strip: short tick = light rain, tall tick = heavy rain */}
        {m.rain_cat.map((c, i) =>
          c === "None" ? null : (
            <line key={i} x1={m.x(i)} x2={m.x(i)} y1={stripBottom} y2={stripBottom - (c === "Heavy" ? 22 : 9)}
              stroke="var(--color-water)" strokeWidth="1.3" opacity={c === "Heavy" ? 1 : 0.55} />
          )
        )}
        <line x1={L} x2={W - R} y1={stripBottom} y2={stripBottom} stroke="var(--color-ink)" strokeWidth="1" />
        <text x={L} y={stripBottom + 16} fontSize="14" fill="var(--color-muted)">Rain days (short = light, tall = heavy)</text>
      </svg>

      <figcaption className="mt-3 max-w-3xl text-lg">
        {series.mock && <span className="mr-2 rounded bg-wait px-2 py-0.5 text-sm font-semibold text-white">MOCK DATA</span>}
        Soil wetness rises and falls once a year with the monsoon, so it changes slowly. On{" "}
        <strong>{m.persistence.toFixed(1)}%</strong> of days the soil category was the same as the next day’s. That is
        why a Dry day is almost always followed by another Dry day.
      </figcaption>
    </figure>
  );
}
