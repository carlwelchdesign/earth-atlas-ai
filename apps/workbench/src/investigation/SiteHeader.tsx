export function SiteHeader({
  current,
}: {
  current: "case" | "investigate" | "explore" | "analyze";
}) {
  return (
    <header className="app-header investigation-header">
      <a className="mission-brand" href="/" aria-label="EchoAtlas home">
        <span className="brand-mark" aria-hidden="true">
          EA
        </span>
        <strong>EchoAtlas</strong>
      </a>
      <nav aria-label="Primary">
        <a
          aria-current={
            current === "investigate" || current === "case" ? "page" : undefined
          }
          href="/"
        >
          Nepal case
        </a>
        <a
          aria-current={current === "explore" ? "page" : undefined}
          href="/explore"
        >
          Explore
        </a>
        <a
          aria-current={current === "analyze" ? "page" : undefined}
          href="/analyze"
        >
          Analyze
        </a>
      </nav>
      <span className="status-pill status-success">Civilian research use</span>
    </header>
  );
}
