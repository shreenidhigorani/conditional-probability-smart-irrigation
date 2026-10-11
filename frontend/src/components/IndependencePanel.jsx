// Reads an OPTIONAL `independence` object from GET /tables:
// { chi2, df, p_value, alpha, conclusion }. Nothing is hard-coded here.
export default function IndependencePanel({ info }) {
  return (
    <section aria-labelledby="i-h" className="rounded-lg border border-line bg-card p-6">
      <h3 id="i-h" className="font-display text-2xl font-semibold">Are rain and soil independent?</h3>
      <p className="mt-2 text-muted">H0: rainfall category and soil category are independent. H1: they are associated. Tested with a chi-square test.</p>
      {!info ? (
        <p className="mt-4 rounded bg-paper p-4 text-muted">The API did not send a chi-square result yet. Ask Member 4 to add an <code>independence</code> object to /tables.</p>
      ) : (
        <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-5">
          {[["χ²", info.chi2], ["Degrees of freedom", info.df], ["p-value", info.p_value], ["Significance level", info.alpha ?? 0.05], ["Cramér’s V", info.cramers_v]].map(([k, v]) => (
            <div key={k} className="rounded border border-line p-3"><dt className="text-sm text-muted">{k}</dt>
              <dd className="font-display text-3xl font-semibold tabular-nums">{typeof v === "number" ? Number(v.toPrecision(4)) : v ?? "–"}</dd></div>
          ))}
          {info.conclusion && <p className="col-span-full text-lg">{info.conclusion}</p>}
        </dl>
      )}
    </section>
  );
}
