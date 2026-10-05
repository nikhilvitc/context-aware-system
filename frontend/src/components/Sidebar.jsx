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
}) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="brand-name">
          Tap<span className="brand-accent">2</span>Explain
        </div>
        <div className="brand-tagline">Context-aware document reasoning</div>
      </div>

      <Uploader onFilesSelected={onFilesSelected} disabled={uploading} compact />
      {uploading && <p className="muted sidebar-status">Processing…</p>}

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
                  {doc.status === "uploading" ? "…" : (doc.docType || "?").toUpperCase()}
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
