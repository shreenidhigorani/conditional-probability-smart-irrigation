// One presentation stage = one full-height section.
export default function Stage({ id, index, title, intro, children }) {
  return (
    <section id={id} aria-labelledby={`${id}-h`} className="mx-auto flex min-h-screen max-w-6xl scroll-mt-14 flex-col justify-center px-5 py-16">
      <header className="mb-8 max-w-3xl">
        {index != null && <p className="mb-1 text-base font-semibold text-clay">Step {index}</p>}
        <h2 id={`${id}-h`} className="font-display text-4xl font-semibold sm:text-5xl">{title}</h2>
        {intro && <p className="mt-3 text-xl text-muted">{intro}</p>}
      </header>
      {children}
    </section>
  );
}
