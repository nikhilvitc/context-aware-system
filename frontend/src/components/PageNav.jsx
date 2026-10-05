export default function PageNav({ page, pageCount, onChange }) {
  if (pageCount <= 1) return null;

  return (
    <div className="page-nav">
      <button
        type="button"
        className="page-nav-button"
        onClick={() => onChange(page - 1)}
        disabled={page <= 0}
      >
        ← Prev
      </button>
      <span className="page-nav-label">
        Page {page + 1} of {pageCount}
      </span>
      <button
        type="button"
        className="page-nav-button"
        onClick={() => onChange(page + 1)}
        disabled={page >= pageCount - 1}
      >
        Next →
      </button>
    </div>
  );
}
