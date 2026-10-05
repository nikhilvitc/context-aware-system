function renderInlineMarkdown(text) {
  return text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g).map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return <em key={i}>{part.slice(1, -1)}</em>;
    }
    return <span key={i}>{part}</span>;
  });
}

function ExplanationText({ text }) {
  return text
    .split(/\n\s*\n/)
    .filter((para) => para.trim())
    .map((para, i) => (
      <p className="explanation-text" key={i}>
        {renderInlineMarkdown(para)}
      </p>
    ));
}

export default function ContextPanel({
  selection,
  explanation,
  explanationLoading,
  explanationError,
  showRelations,
  onToggleRelations,
}) {
  if (!selection) {
    return (
      <div className="context-panel empty">
        <p>Tap a word or line on the image to see its spatial context.</p>
      </div>
    );
  }

  return (
    <div className="context-panel">
      <section className="panel-block">
        <h3>Selected token</h3>
        <p className="selected-text">"{selection.selectedText}"</p>
      </section>

      <section className="panel-block">
        <div className="panel-block-header">
          <h3>Spatial neighbors (SCP)</h3>
          <label className="toggle">
            <input
              type="checkbox"
              checked={showRelations}
              onChange={(e) => onToggleRelations(e.target.checked)}
            />
            relation graph
          </label>
        </div>
        <ol className="neighbor-list">
          {selection.context.map((item, idx) => (
            <li key={idx} className={idx === 0 ? "is-self" : ""}>
              <span className="neighbor-rank">{idx === 0 ? "self" : `#${idx}`}</span>
              <span className="neighbor-text">{item.text}</span>
              <span className="neighbor-confidence">
                {(item.confidence * 100).toFixed(0)}%
              </span>
            </li>
          ))}
        </ol>
      </section>

      <section className="panel-block">
        <h3>Explanation (Gemini)</h3>
        {explanationLoading && <p className="muted">Generating explanation…</p>}
        {explanationError && <p className="error-text">{explanationError}</p>}
        {!explanationLoading && !explanationError && explanation && (
          <ExplanationText text={explanation} />
        )}
        {!explanationLoading && !explanationError && !explanation && (
          <p className="muted">No explanation yet.</p>
        )}
      </section>
    </div>
  );
}
