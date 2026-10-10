import { STAGES } from "../hooks/useStages";

export default function StageNav({ active, mock }) {
  const go = (id) => document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  return (
    <nav aria-label="Project stages" className="sticky top-0 z-20 border-b border-line bg-paper/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-4 overflow-x-auto px-5 py-2.5">
        <span className="font-display text-xl font-semibold">IrrigAI</span>
        <ul className="flex gap-1">
          {STAGES.map((s) => (
            <li key={s.id}>
              <button type="button" onClick={() => go(s.id)} aria-current={active === s.id ? "step" : undefined}
                className={`whitespace-nowrap rounded px-3 py-1.5 text-sm font-medium ${
                  active === s.id ? "bg-ink text-white" : "text-muted hover:bg-line/60"}`}>
                {s.label}
              </button>
            </li>
          ))}
        </ul>
        {mock && <span className="ml-auto whitespace-nowrap rounded bg-wait px-2 py-1 text-xs font-semibold text-white">MOCK MODE</span>}
        <span className="ml-auto hidden whitespace-nowrap text-xs text-muted lg:inline">Use ← → to move between steps</span>
      </div>
    </nav>
  );
}
