import Uploader from "./Uploader.jsx";

const STEPS = [
  {
    title: "Upload",
    body: "Add a scanned page, a photo of a sign or textbook, or a PDF.",
  },
  {
    title: "Tap",
    body: "Tap any word. Its spatial neighbors are ranked and highlighted.",
  },
  {
    title: "Explain",
    body: "Gemini explains the selection using that resolved context.",
  },
];

export default function EmptyState({ onFilesSelected }) {
  return (
    <div className="empty-state">
      <div className="empty-state-intro">
        <h2>Bring a document</h2>
        <p>
          Scene text has no inherent sentence structure — tapping a word here
          resolves its real spatial neighbors instead of guessing from
          flattened OCR order.
        </p>
        <Uploader onFilesSelected={onFilesSelected} disabled={false} />
      </div>

      <ol className="how-it-works">
        {STEPS.map((step, i) => (
          <li key={step.title}>
            <span className="step-number">{i + 1}</span>
            <div>
              <strong>{step.title}</strong>
              <p>{step.body}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
