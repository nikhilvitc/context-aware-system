const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function parseErrorDetail(response) {
  try {
    const data = await response.json();
    return data.detail || response.statusText;
  } catch {
    return response.statusText;
  }
}

export async function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file);

  const response = await fetch(`${API_BASE}/api/document`, {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    throw new Error(await parseErrorDetail(response));
  }

  return response.json();
}

export function documentPageUrl(documentId, pageNumber) {
  return `${API_BASE}/api/document/${documentId}/page/${pageNumber}`;
}

export async function getContext(documentId, page, x, y) {
  const response = await fetch(`${API_BASE}/api/context`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      document_id: documentId,
      page,
      x: Math.round(x),
      y: Math.round(y),
    }),
  });

  if (!response.ok) {
    throw new Error(await parseErrorDetail(response));
  }

  return response.json();
}

export async function getExplanation(documentId, page, x, y) {
  const response = await fetch(`${API_BASE}/api/explain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      document_id: documentId,
      page,
      x: Math.round(x),
      y: Math.round(y),
    }),
  });

  if (!response.ok) {
    throw new Error(await parseErrorDetail(response));
  }

  return response.json();
}

export { API_BASE };
