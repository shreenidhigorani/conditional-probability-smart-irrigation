// Expected-cost reasoning: irrigate when c_irr < P * c_stress.
export default function CostBalance({ p, cIrr, cStress }) {
  const left = cIrr;
  const right = p * cStress;
  const norm = Math.max(-1, Math.min(1, (right - left) / Math.max(left, right, 1e-9)));
  const angle = norm * 13;
  const verdict = right > left ? "Waiting costs more on average" : "Irrigating costs more on average";
  const fmt = (x) => (Number.isFinite(x) ? x.toFixed(2) : "–");

  const Pan = ({ x, title, value, color }) => (
    <g transform={`translate(${x} 0) rotate(${-angle})`} style={{ transition: "transform .8s ease" }}>
      <line x1="-38" y1="0" x2="-48" y2="62" stroke="var(--color-ink)" />
      <line x1="38" y1="0" x2="48" y2="62" stroke="var(--color-ink)" />
      <rect x="-62" y="62" width="124" height="46" rx="6" fill={color} />
      <text y="82" textAnchor="middle" fill="#fff" fontSize="12" fontWeight="600">{title}</text>
      <text y="100" textAnchor="middle" fill="#fff" fontSize="15" fontWeight="700">{value}</text>
    </g>
  );

  return (
    <figure>
      <svg viewBox="0 0 400 190" role="img" className="h-auto w-full max-w-[420px]"
        aria-label={`Cost balance: irrigating costs ${fmt(left)}, waiting costs on average ${fmt(right)}`}>
        <polygon points="200,60 180,176 220,176" fill="var(--color-ink)" />
        <rect x="150" y="176" width="100" height="8" rx="3" fill="var(--color-ink)" />
        <g style={{ transform: `rotate(${angle}deg)`, transformOrigin: "200px 60px", transition: "transform .8s ease" }}>
          <line x1="90" y1="60" x2="310" y2="60" stroke="var(--color-ink)" strokeWidth="5" strokeLinecap="round" />
          <Pan x={90} title="Irrigate (c_irr)" value={fmt(left)} color="var(--color-water)" />
          <Pan x={310} title="P × c_stress" value={fmt(right)} color="var(--color-clay)" />
        </g>
        <circle cx="200" cy="60" r="7" fill="var(--color-ink)" />
      </svg>
      <figcaption className="mt-1 text-sm text-muted">{verdict}: {fmt(left)} vs {fmt(p)} × {fmt(cStress)} = {fmt(right)}.</figcaption>
    </figure>
  );
}
