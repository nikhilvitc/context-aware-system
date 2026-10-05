import { useRef, useState } from "react";

const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/jpg", "application/pdf"];

export default function Uploader({ onFilesSelected, disabled, compact = false }) {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFiles = (fileList) => {
    const files = Array.from(fileList || []);
    if (files.length === 0) return;

    const accepted = [];
    const rejected = [];

    for (const file of files) {
      if (ACCEPTED_TYPES.includes(file.type)) accepted.push(file);
      else rejected.push(file.name);
    }

    onFilesSelected(accepted, rejected);
  };

  if (compact) {
    return (
      <div className={`uploader compact ${disabled ? "disabled" : ""}`}>
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,application/pdf"
          multiple
          hidden
          onChange={(e) => {
            handleFiles(e.target.files);
            e.target.value = "";
          }}
          disabled={disabled}
        />
        <button
          type="button"
          className="upload-button"
          onClick={() => inputRef.current?.click()}
          disabled={disabled}
        >
          + Add document
        </button>
      </div>
    );
  }

  return (
    <div
      className={`uploader ${isDragging ? "dragging" : ""} ${disabled ? "disabled" : ""}`}
      onClick={() => !disabled && inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        if (!disabled) handleFiles(e.dataTransfer.files);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,application/pdf"
        multiple
        hidden
        onChange={(e) => {
          handleFiles(e.target.files);
          e.target.value = "";
        }}
        disabled={disabled}
      />
      <p className="uploader-title">Drop images or PDFs, or click to browse</p>
      <p className="uploader-hint">JPG, PNG, PDF · multi-page PDFs supported</p>
    </div>
  );
}
