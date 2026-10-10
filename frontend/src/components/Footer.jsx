import { STAGES } from "../hooks/useStages";

const go = (id) => document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });

export default function Footer() {
  return (
    <footer className="border-t border-line bg-ink text-white">
      <div className="mx-auto grid max-w-6xl gap-10 px-5 py-12 md:grid-cols-3">
        <div>
          <p className="font-display text-3xl font-semibold">IrrigAI</p>
          <p className="mt-2 text-white/80">Should we irrigate today? Conditional probability in smart irrigation.</p>
          <p className="mt-4 text-sm text-white/70">Group 6 · Statistical Methods and Probability · IA1</p>
        </div>

        <div>
          <h2 className="text-sm font-semibold text-white/60">Data and method</h2>
          <ul className="mt-3 space-y-2 text-white/90">
            <li>NASA POWER daily data</li>
            <li>Kolhapur, Maharashtra, 2022–2025</li>
            <li>Joint, marginal and conditional probability</li>
            <li>Chi-square test of independence</li>
            <li>Cost threshold t = c_irr ÷ c_stress</li>
          </ul>
        </div>

        <div>
          <h2 className="text-sm font-semibold text-white/60">Jump to</h2>
          <ul className="mt-3 flex flex-wrap gap-2">
            {STAGES.map((s) => (
              <li key={s.id}>
                <button type="button" onClick={() => go(s.id)}
                  className="rounded border border-white/30 px-3 py-1.5 text-sm hover:bg-white hover:text-ink focus-visible:ring-2 focus-visible:ring-white">
                  {s.label}
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="border-t border-white/15">
        <p className="mx-auto max-w-6xl px-5 py-4 text-sm text-white/70">
          Soil wetness is modelled, not sensor-measured. Results show patterns in past data, not causes. Costs are illustrative.
        </p>
      </div>
    </footer>
  );
}
