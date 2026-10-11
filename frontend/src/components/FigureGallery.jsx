// Graphs made by the analysis script (results/figures). Files live in public/figures/.
// To refresh after re-running the analysis, copy the new PNGs over the old ones.
const FIGURES = [
  {
    src: "/figures/observed-vs-expected.png",
    title: "Observed vs expected counts",
    alt: "Two heatmaps of day counts by soil and rain category: observed, and expected if rain and soil were independent",
    caption: "If rain and soil were unrelated, the two panels would match. They differ strongly, which is why the chi-square test rejects independence.",
  },
  {
    src: "/figures/std-residuals.png",
    title: "Standardised residuals",
    alt: "Heatmap of standardised residuals for each soil and rain combination",
    caption: "Cells far from zero show where the data depart most from independence: wet soil goes with rain, dry soil with no rain.",
  },
  {
    src: "/figures/decision-chart.png",
    title: "Chance of dry soil tomorrow, three scenarios",
    alt: "Bar chart of the probability of dry soil tomorrow for three scenarios, with the two decision thresholds",
    caption: "Only Dry soil with no rain clears the irrigate cut-off. The other two scenarios sit at about zero, below the cost threshold.",
  },
];

export default function FigureGallery() {
  return (
    <section aria-labelledby="fig-h" className="rounded-lg border border-line bg-card p-6">
      <h3 id="fig-h" className="font-display text-2xl font-semibold">Evidence from the analysis</h3>
      <div className="mt-5 grid gap-8 lg:grid-cols-2">
        {FIGURES.map((f, i) => (
          <figure key={f.src} className={i === 0 ? "lg:col-span-2" : ""}>
            <img src={f.src} alt={f.alt} loading="lazy" className="w-full rounded border border-line bg-white" />
            <figcaption className="mt-2 text-lg">
              <strong>{f.title}.</strong> <span className="text-muted">{f.caption}</span>
            </figcaption>
          </figure>
        ))}
      </div>
    </section>
  );
}
