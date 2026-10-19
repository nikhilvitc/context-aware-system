import { useRef, useState } from "react";

function bboxToPoints(bbox) {
  return bbox.map((point) => point.join(",")).join(" ");
}

function bboxCenter(bbox) {
  const xs = bbox.map((p) => p[0]);
  const ys = bbox.map((p) => p[1]);
  return [
    xs.reduce((a, b) => a + b, 0) / xs.length,
    ys.reduce((a, b) => a + b, 0) / ys.length,
  ];
}

function sameBox(a, b) {
  if (!a || !b || a.length !== b.length) return false;
  return a.every((point, i) => point[0] === b[i][0] && point[1] === b[i][1]);
}

export default function ImageStage({
  imageUrl,
  ocrResults,
  objects = [],
  selection,
  showRelations,
  clickPoint,
  onImageClick,
  isBusy,
}) {
  const containerRef = useRef(null);
  const [naturalSize, setNaturalSize] = useState(null);

  const handleImageLoad = (event) => {
    setNaturalSize({
      width: event.target.naturalWidth,
      height: event.target.naturalHeight,
    });
  };

  const handleClick = (event) => {
    if (!naturalSize || isBusy) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const scaleX = naturalSize.width / rect.width;
    const scaleY = naturalSize.height / rect.height;
    const x = (event.clientX - rect.left) * scaleX;
    const y = (event.clientY - rect.top) * scaleY;
    onImageClick(x, y);
  };

  const selectedBbox = selection?.bbox || null;
  const contextItems = selection?.context || [];

  return (
    <div className="image-stage" ref={containerRef}>
      <div
        className={`image-frame ${isBusy ? "busy" : ""}`}
        onClick={handleClick}
      >
        <img src={imageUrl} onLoad={handleImageLoad} alt="Uploaded scene" draggable={false} />

        {naturalSize && (
          <svg
            className="overlay"
            viewBox={`0 0 ${naturalSize.width} ${naturalSize.height}`}
            preserveAspectRatio="none"
          >
            {ocrResults.map((item, idx) => {
              const isSelected = selectedBbox && sameBox(item.bbox, selectedBbox);
              const isContext =
                !isSelected &&
                contextItems.some((c) => sameBox(c.bbox, item.bbox) && c.text === item.text);

              let className = "ocr-box other";
              if (isSelected) className = "ocr-box selected";
              else if (isContext) className = "ocr-box context";

              return (
                <polygon key={idx} className={className} points={bboxToPoints(item.bbox)} />
              );
            })}

            {objects.map((obj, idx) => {
              const isSelected = selectedBbox && sameBox(obj.bbox, selectedBbox);
              return (
                <polygon
                  key={`obj-${idx}`}
                  className={isSelected ? "ocr-box selected object-box" : "ocr-box object-box"}
                  points={bboxToPoints(obj.bbox)}
                />
              );
            })}

            {showRelations &&
              selectedBbox &&
              contextItems.map((item, idx) => {
                if (sameBox(item.bbox, selectedBbox)) return null;
                const [x1, y1] = bboxCenter(selectedBbox);
                const [x2, y2] = bboxCenter(item.bbox);
                return (
                  <line
                    key={idx}
                    className="relation-line"
                    x1={x1}
                    y1={y1}
                    x2={x2}
                    y2={y2}
                  />
                );
              })}

            {clickPoint && (
              <circle
                className="tap-marker"
                cx={clickPoint[0]}
                cy={clickPoint[1]}
                r={Math.max(naturalSize.width, naturalSize.height) * 0.006}
              />
            )}
          </svg>
        )}
      </div>
    </div>
  );
}
