const foundationBoundaries = [
  "No source imagery is loaded",
  "No change detection is running",
  "No analyst conclusions are generated",
] as const;

export function App() {
  return (
    <main className="foundation-shell">
      <section className="foundation-card" aria-labelledby="foundation-title">
        <p className="eyebrow">Repository foundation</p>
        <h1 id="foundation-title">EchoAtlas</h1>
        <p className="summary">
          The development environment is ready for a planned, evidence-first SAR
          analyst workbench.
        </p>

        <div className="status" role="status">
          Foundation only — operational capabilities have not been implemented.
        </div>

        <section aria-labelledby="boundaries-title">
          <h2 id="boundaries-title">Current boundaries</h2>
          <ul>
            {foundationBoundaries.map((boundary) => (
              <li key={boundary}>{boundary}</li>
            ))}
          </ul>
        </section>
      </section>
    </main>
  );
}
