const RELATIONS = [
  {
    code: "SCP",
    label: "Spatial proximity",
    detail: "Nearby boxes ranked by 2-D distance from the tapped token.",
    active: true,
  },
  {
    code: "TSS",
    label: "Semantic similarity",
    detail: "Same-line / meaning-based token relations (active in rhyme kids mode).",
    active: true,
  },
  {
    code: "VA",
    label: "Visual affinity",
    detail: "Color/appearance grouping (active in rhyme kids mode).",
    active: true,
  },
];

export default function RelationLegend({ kidsMode = false }) {
  return (
    <ul className="relation-legend">
      {RELATIONS.map((relation) => {
        const active = kidsMode ? true : relation.code === "SCP";
        return (
          <li
            key={relation.code}
            className={active ? "is-active" : "is-roadmap"}
            title={relation.detail}
          >
            <span className="relation-dot" aria-hidden="true" />
            <span className="relation-code">{relation.code}</span>
            <span className="relation-label">{relation.label}</span>
          </li>
        );
      })}
    </ul>
  );
}
