// Illustrative field slice. Moisture level and rain are driven by the selected
// categories. It is a picture of the INPUT, not a measured value.
const LEVEL = { Dry: 0.22, Moderate: 0.5, Wet: 0.8 };
const DROPS = { None: 0, Light: 9, Heavy: 24 };

export default function SoilCrossSection({ soil, rain }) {
  const W = 520, H = 340, ground = 130, bottom = 320, depth = bottom - ground;
  const drops = Array.from({ length: DROPS[rain] }, (_, i) => ({
    x: 20 + ((i * 479) % (W - 40)), y: 20 + ((i * 37) % 40), d: (i % 6) * 0.17,
  }));
  const canes = [150, 215, 280, 345];

  return (
    <svg viewBox={`0 0 ${W} ${H}`} role="img" className="h-auto w-full"
      aria-label={`Field cross-section: ${soil} soil, ${rain} rain`}>
      <rect width={W} height={ground} fill="var(--color-sky)" />
      {drops.map((d, i) => (
        <line key={i} className="drop" x1={d.x} y1={d.y} x2={d.x - 3} y2={d.y + 14}
          stroke="var(--color-water)" strokeWidth="2" strokeLinecap="round" style={{ animationDelay: `${d.d}s` }} />
      ))}

      {/* soil layers */}
      <rect y={ground} width={W} height={depth * 0.3} fill="#7b4a28" />
      <rect y={ground + depth * 0.3} width={W} height={depth * 0.4} fill="#6a3e20" />
      <rect y={ground + depth * 0.7} width={W} height={depth * 0.3} fill="#563219" />

      {/* moisture fills from the bottom up */}
      <rect y={ground} width={W} height={depth} fill="var(--color-water)" opacity="0.5"
        style={{ transformOrigin: `0px ${bottom}px`, transform: `scaleY(${LEVEL[soil]})`, transition: "transform .8s ease" }} />

      {/* sugarcane */}
      {canes.map((x, i) => (
        <g key={x} className="cane" style={{ animationDelay: `${i * 0.4}s` }}>
          <line x1={x} y1={ground} x2={x} y2={ground - 82} stroke="#3c7d3a" strokeWidth="5" strokeLinecap="round" />
          <path d={`M${x} ${ground - 60} q 30 -18 48 -4`} stroke="#4f9a4a" strokeWidth="3" fill="none" strokeLinecap="round" />
          <path d={`M${x} ${ground - 40} q -30 -16 -46 -2`} stroke="#4f9a4a" strokeWidth="3" fill="none" strokeLinecap="round" />
        </g>
      ))}
      {canes.map((x) => (
        <path key={`r${x}`} d={`M${x} ${ground} v 38 M${x} ${ground + 20} l -14 22 M${x} ${ground + 20} l 14 22`}
          stroke="#d9c3a5" strokeWidth="1.6" fill="none" opacity="0.8" />
      ))}

      <line x1="0" x2={W} y1={ground} y2={ground} stroke="var(--color-ink)" strokeWidth="1.5" />
      <text x="12" y={ground + 22} fill="#fff" fontSize="13" fontWeight="600">Topsoil</text>
      <text x="12" y={ground + depth * 0.3 + 22} fill="#fff" fontSize="13" fontWeight="600">Root zone</text>
      <text x="12" y={ground + depth * 0.7 + 22} fill="#fff" fontSize="13" fontWeight="600">Subsoil</text>
    </svg>
  );
}
