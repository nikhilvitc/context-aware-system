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

function RelationChips({ relations }) {
  if (!relations?.length) return null;
  return (
    <span className="relation-chips">
      {relations.map((rel) => (
        <span key={rel.code} className={`rel-chip rel-${rel.code.toLowerCase()}`}>
          {rel.code} {(rel.score * 100).toFixed(0)}
        </span>
      ))}
    </span>
  );
}

export default function ContextPanel({
  selection,
  explanation,
  explanationLoading,
  explanationError,
  showRelations,
  onToggleRelations,
  kidsMode = false,
}) {
  if (!selection) {
    return (
      <div className="context-panel empty">
        <p>
          {kidsMode
            ? "Tap a rhyme word or a picture (like a monkey!) to hear what it means."
            : "Tap a word or line on the image to see its spatial context."}
        </p>
      </div>
    );
  }

  const typeLabel = selection.selectedType === "object" ? "Picture" : "Word";

  return (
    <div className="context-panel">
      <section className="panel-block">
        <h3>Selected {typeLabel.toLowerCase()}</h3>
        <p className="selected-text">"{selection.selectedText}"</p>
        {selection.selectedType === "object" && selection.objectMeta?.relation_hint && (
          <p className="muted">Hint: {selection.objectMeta.relation_hint}</p>
        )}
      </section>

      <section className="panel-block">
        <div className="panel-block-header">
          <h3>{kidsMode ? "Related words (TSS · SCP · VA)" : "Spatial neighbors (SCP)"}</h3>
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
            <li key={idx}>
              <span className="neighbor-rank">#{idx + 1}</span>
              <span className="neighbor-text">{item.text}</span>
              <RelationChips relations={item.relations} />
            </li>
          ))}
        </ol>
      </section>

      <section className="panel-block">
        <h3>{kidsMode ? "Kid explanation" : "Explanation (Gemini)"}</h3>
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
