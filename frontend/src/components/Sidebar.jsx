import Uploader from "./Uploader.jsx";

function truncate(name, max = 26) {
  if (name.length <= max) return name;
  return name.slice(0, max - 1) + "…";
}

export default function Sidebar({
  documents,
  activeDocumentId,
  onSelectDocument,
  onFilesSelected,
  uploading,
  kidsMode,
  onToggleKidsMode,
  rhymes,
  onOpenRhyme,
  rhymesLoading,
}) {
  return (
    <aside className={`sidebar ${kidsMode ? "kids-mode" : ""}`}>
      <div className="sidebar-header">
        <div className="brand-name">
          Tap<span className="brand-accent">2</span>Explain
        </div>
        <div className="brand-tagline">
          {kidsMode ? "Rhyme book learning for kids" : "Context-aware document reasoning"}
        </div>
      </div>

      <label className="mode-toggle">
        <input
          type="checkbox"
          checked={kidsMode}
          onChange={(e) => onToggleKidsMode(e.target.checked)}
        />
        Kids rhyme mode
      </label>

      {!kidsMode && (
        <Uploader onFilesSelected={onFilesSelected} disabled={uploading} compact />
      )}
      {uploading && <p className="muted sidebar-status">Processing…</p>}

      {kidsMode && (
        <div className="library">
          <div className="library-heading">Rhyme books</div>
          {rhymesLoading && <p className="muted library-empty">Loading rhymes…</p>}
          {!rhymesLoading && rhymes.length === 0 && (
            <p className="muted library-empty">
              No rhymes yet. Run <code>python research/build_dataset.py</code>.
            </p>
          )}
          <ul className="library-list">
            {rhymes.map((rhyme) => (
              <li key={rhyme.rhyme_id}>
                <button
                  type="button"
                  className="library-item"
                  onClick={() => onOpenRhyme(rhyme.rhyme_id)}
                >
                  <span className="doc-badge image">RHY</span>
                  <span className="library-item-text">
                    <span className="library-item-name">{truncate(rhyme.title)}</span>
                    <span className="library-item-meta">
                      {rhyme.page_count} page{rhyme.page_count === 1 ? "" : "s"}
                    </span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="library">
        <div className="library-heading">Library</div>
        {documents.length === 0 && (
          <p className="muted library-empty">No documents yet.</p>
        )}
        <ul className="library-list">
          {documents.map((doc) => (
            <li key={doc.id}>
              <button
                type="button"
                className={`library-item ${doc.id === activeDocumentId ? "active" : ""} ${
                  doc.status === "error" ? "has-error" : ""
                }`}
                onClick={() => doc.status === "ready" && onSelectDocument(doc.id)}
                disabled={doc.status !== "ready"}
              >
                <span className={`doc-badge ${doc.docType || "pending"}`}>
                  {doc.status === "uploading"
                    ? "…"
                    : doc.mode === "rhyme_kids"
                      ? "RHY"
                      : (doc.docType || "?").toUpperCase()}
                </span>
                <span className="library-item-text">
                  <span className="library-item-name">{truncate(doc.filename)}</span>
                  <span className="library-item-meta">
                    {doc.status === "uploading" && "Uploading…"}
                    {doc.status === "error" && (doc.error || "Failed")}
                    {doc.status === "ready" &&
                      `${doc.pageCount} page${doc.pageCount === 1 ? "" : "s"}`}
                  </span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
}
