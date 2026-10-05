# Tap2Explain Frontend

React + Vite UI for the Tap2Explain backend.

## What it does

- Upload images (JPG/PNG) or multi-page PDFs — one or several at a time,
  via drag-and-drop or the sidebar (`POST /api/document`). Each upload
  appears in a document library in the sidebar; switch between them anytime.
- Multi-page PDFs get a page navigator; each page shows whether its text
  came from the PDF's native text layer or from OCR fallback (scanned pages).
- Renders every detected text box over the page, preserving real 2-D layout
  instead of a flattened token list.
- Click a point on the page to select the nearest text token
  (`POST /api/context`), highlighting it plus its spatial neighbors and
  drawing the relation graph between them.
- Fetches a Gemini-generated explanation for the selected token in its
  spatial context (`POST /api/explain`).

`.docx`/Word documents aren't supported yet — they don't carry the visual
2-D layout this tool reasons over without a page-rendering step (e.g. via
LibreOffice), which hasn't been added.

The relation legend in the header reflects what the backend currently
implements: **SCP** (spatial context proximity) is active; **TSS** (semantic
similarity) and **VA** (visual affinity) are shown as roadmap items so the UI
doesn't claim relations the backend doesn't compute yet.

## Setup

```bash
cd frontend
npm install
cp .env.example .env   # adjust VITE_API_BASE_URL if the backend isn't on :8000
npm run dev
```

Open http://localhost:5173. Make sure the backend is running first:

```bash
cd backend
uvicorn main:app --reload
```

The backend's CORS config allows `http://localhost:5173` by default.
