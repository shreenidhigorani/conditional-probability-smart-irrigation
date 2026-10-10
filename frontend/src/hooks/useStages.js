import { useEffect, useState } from "react";

export const STAGES = [
  { id: "problem", label: "Problem" },
  { id: "data", label: "Data" },
  { id: "method", label: "Method" },
  { id: "decision", label: "Live decision" },
  { id: "evidence", label: "Tables & test" },
];

// Tracks the visible stage and lets arrow keys step through them (presentation mode).
export default function useStages() {
  const [active, setActive] = useState(STAGES[0].id);

  useEffect(() => {
    const obs = new IntersectionObserver(
      (entries) => entries.forEach((e) => e.isIntersecting && setActive(e.target.id)),
      { rootMargin: "-45% 0px -50% 0px" }
    );
    STAGES.forEach((s) => { const el = document.getElementById(s.id); el && obs.observe(el); });
    return () => obs.disconnect();
  }, []);

  useEffect(() => {
    const onKey = (e) => {
      const tag = e.target.tagName;
      if (["INPUT", "SELECT", "TEXTAREA"].includes(tag)) return;
      const i = STAGES.findIndex((s) => s.id === active);
      if (e.key === "ArrowRight" || e.key === "PageDown") go(i + 1);
      if (e.key === "ArrowLeft" || e.key === "PageUp") go(i - 1);
    };
    const go = (i) => {
      const s = STAGES[Math.max(0, Math.min(STAGES.length - 1, i))];
      document.getElementById(s.id)?.scrollIntoView({ behavior: "smooth", block: "start" });
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [active]);

  return active;
}
