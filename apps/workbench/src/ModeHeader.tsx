export function ModeHeader({
  mode,
  onExplore,
  onAnalyze,
  analyzeDetail,
}: {
  mode: "explore" | "analyze";
  onExplore?: () => void;
  onAnalyze?: () => void;
  analyzeDetail?: string;
}) {
  return (
    <header className="app-header">
      <div className="mission-brand">
        <span className="brand-mark" aria-hidden="true">
          EA
        </span>
        <strong>EchoAtlas</strong>
      </div>
      <nav aria-label="Primary">
        <button
          type="button"
          aria-current={mode === "explore" ? "page" : undefined}
          onClick={onExplore}
        >
          Explore
        </button>
        <button
          type="button"
          aria-current={mode === "analyze" ? "page" : undefined}
          onClick={onAnalyze}
        >
          Analyze{analyzeDetail ? <span> · {analyzeDetail}</span> : null}
        </button>
      </nav>
      <span className="status-pill status-success">Civilian research use</span>
    </header>
  );
}
