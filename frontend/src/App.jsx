import { useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import ImageStage from "./components/ImageStage.jsx";
import PageNav from "./components/PageNav.jsx";
import ContextPanel from "./components/ContextPanel.jsx";
import RelationLegend from "./components/RelationLegend.jsx";
import EmptyState from "./components/EmptyState.jsx";
import { uploadDocument, documentPageUrl, getContext, getExplanation } from "./api.js";

let localIdCounter = 0;
function makeLocalId() {
  localIdCounter += 1;
  return `doc-${Date.now()}-${localIdCounter}`;
}

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [activeDocumentId, setActiveDocumentId] = useState(null);
  const [uploadWarning, setUploadWarning] = useState(null);

  const [clickPoint, setClickPoint] = useState(null);
  const [selection, setSelection] = useState(null);
  const [contextError, setContextError] = useState(null);

  const [explanation, setExplanation] = useState(null);
  const [explanationLoading, setExplanationLoading] = useState(false);
  const [explanationError, setExplanationError] = useState(null);

  const [showRelations, setShowRelations] = useState(true);

  const patchDocument = (localId, patch) => {
    setDocuments((prev) =>
      prev.map((doc) => (doc.id === localId ? { ...doc, ...patch } : doc))
    );
  };

  const resetSelectionState = () => {
    setClickPoint(null);
    setSelection(null);
    setContextError(null);
    setExplanation(null);
    setExplanationError(null);
  };

  const handleFilesSelected = (accepted, rejected) => {
    if (rejected.length > 0) {
      setUploadWarning(
        `Skipped unsupported file${rejected.length === 1 ? "" : "s"}: ${rejected.join(", ")}`
      );
    } else {
      setUploadWarning(null);
    }

    accepted.forEach((file) => {
      const localId = makeLocalId();

      setDocuments((prev) => [
        ...prev,
        {
          id: localId,
          documentId: null,
          filename: file.name,
          docType: file.type === "application/pdf" ? "pdf" : "image",
          status: "uploading",
          pageCount: 0,
          pages: [],
          page: 0,
        },
      ]);

      uploadDocument(file)
        .then((data) => {
          patchDocument(localId, {
            documentId: data.document_id,
            filename: data.filename,
            docType: data.doc_type,
            pageCount: data.page_count,
            pages: data.pages,
            page: 0,
            status: "ready",
          });
          setActiveDocumentId(localId);
          resetSelectionState();
        })
        .catch((err) => {
          patchDocument(localId, {
            status: "error",
            error: err.message || "Upload failed.",
          });
        });
    });
  };

  const handleSelectDocument = (localId) => {
    if (localId === activeDocumentId) return;
    setActiveDocumentId(localId);
    resetSelectionState();
  };

  const handlePageChange = (nextPage) => {
    if (!activeDocumentId) return;
    patchDocument(activeDocumentId, { page: nextPage });
    resetSelectionState();
  };

  const activeDocument = documents.find((doc) => doc.id === activeDocumentId) || null;
  const activePageData = activeDocument?.pages?.[activeDocument.page] || null;

  const handleImageClick = (x, y) => {
    if (!activeDocument?.documentId) return;
    const documentId = activeDocument.documentId;
    const page = activeDocument.page;

    setClickPoint([x, y]);
    setContextError(null);
    setExplanation(null);
    setExplanationError(null);
    setExplanationLoading(true);

    getContext(documentId, page, x, y)
      .then((data) => {
        if (!data.selected_text) {
          setSelection(null);
          setContextError("No text found near that point.");
          return;
        }
        setSelection({
          selectedText: data.selected_text,
          bbox: data.bbox,
          context: data.context,
        });
      })
      .catch((err) => {
        setSelection(null);
        setContextError(err.message || "Could not resolve context.");
      });

    getExplanation(documentId, page, x, y)
      .then((data) => setExplanation(data.explanation))
      .catch((err) => setExplanationError(err.message || "Could not generate explanation."))
      .finally(() => setExplanationLoading(false));
  };

  const isUploading = documents.some((doc) => doc.status === "uploading");

  return (
    <div className="app-shell">
      <Sidebar
        documents={documents}
        activeDocumentId={activeDocumentId}
        onSelectDocument={handleSelectDocument}
        onFilesSelected={handleFilesSelected}
        uploading={isUploading}
      />

      <div className="app-content">
        <header className="content-header">
          <div>
            <h1>Context-aware document reasoning</h1>
            <p className="subtitle">
              Tap a word to see its spatial context, ahead of multimodal fusion.
            </p>
          </div>
          <RelationLegend />
        </header>

        {uploadWarning && <p className="error-text warning-banner">{uploadWarning}</p>}

        {!activeDocument && <EmptyState onFilesSelected={handleFilesSelected} />}

        {activeDocument && activeDocument.status === "uploading" && (
          <div className="status-stage">
            <p className="muted">Processing "{activeDocument.filename}"…</p>
          </div>
        )}

        {activeDocument && activeDocument.status === "error" && (
          <div className="status-stage">
            <p className="error-text">{activeDocument.error}</p>
          </div>
        )}

        {activeDocument && activeDocument.status === "ready" && activePageData && (
          <div className="workspace">
            <div className="stage-column">
              <div className="stage-toolbar">
                <span className="token-count">
                  {activePageData.results.length} token
                  {activePageData.results.length === 1 ? "" : "s"} ·{" "}
                  <span className={`source-tag ${activePageData.source}`}>
                    {activePageData.source === "text_layer" ? "text layer" : "OCR"}
                  </span>
                </span>
                <PageNav
                  page={activeDocument.page}
                  pageCount={activeDocument.pageCount}
                  onChange={handlePageChange}
                />
              </div>

              <ImageStage
                imageUrl={documentPageUrl(activeDocument.documentId, activeDocument.page)}
                ocrResults={activePageData.results}
                selection={selection}
                showRelations={showRelations}
                clickPoint={clickPoint}
                onImageClick={handleImageClick}
                isBusy={false}
              />
              {contextError && <p className="error-text">{contextError}</p>}
            </div>

            <ContextPanel
              selection={selection}
              explanation={explanation}
              explanationLoading={explanationLoading}
              explanationError={explanationError}
              showRelations={showRelations}
              onToggleRelations={setShowRelations}
            />
          </div>
        )}
      </div>
    </div>
  );
}
