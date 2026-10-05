const RELATIONS = [
  {
    code: "SCP",
    label: "Spatial proximity",
    detail: "Nearby OCR boxes ranked by 2-D distance from the tapped token.",
    active: true,
  },
  {
    code: "TSS",
    label: "Semantic similarity",
    detail: "Meaning-based token relations, not yet wired into the backend.",
    active: false,
  },
  {
    code: "VA",
    label: "Visual affinity",
    detail: "Layout/appearance-based grouping, not yet wired into the backend.",
    active: false,
  },
];

export default function RelationLegend() {
  return (
    <ul className="relation-legend">
      {RELATIONS.map((relation) => (
        <li
          key={relation.code}
          className={relation.active ? "is-active" : "is-roadmap"}
          title={relation.detail}
        >
          <span className="relation-dot" aria-hidden="true" />
          <span className="relation-code">{relation.code}</span>
          <span className="relation-label">{relation.label}</span>
        </li>
      ))}
    </ul>
  );
}
