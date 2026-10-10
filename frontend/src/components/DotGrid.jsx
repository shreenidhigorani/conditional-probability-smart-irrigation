// "Out of 100 similar days": makes the conditional denominator visible.
export default function DotGrid({ p, asked }) {
  const k = Math.round(p * 100);
  const cond = asked ? `${asked.soil} soil and ${asked.rain} rain` : "these conditions";
  return (
    <figure>
      <div role="img" aria-label={`${k} of 100 days were followed by a dry day`}
        className="grid max-w-[280px] grid-cols-10 gap-1.5">
        {Array.from({ length: 100 }, (_, i) => (
          <span key={i} style={{ transitionDelay: `${i * 7}ms` }}
            className={`aspect-square rounded-full transition-colors duration-300 ${i < k ? "bg-clay" : "bg-line"}`} />
        ))}
      </div>
      <figcaption className="mt-3 max-w-[300px] text-sm text-muted">
        Of every 100 days with {cond}, about <strong className="text-ink">{k}</strong> were followed by a dry day
        (brown).
      </figcaption>
    </figure>
  );
}
