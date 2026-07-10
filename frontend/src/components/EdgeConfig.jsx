// Edges carry no conditions. Edges from a decision node show their True/False
// branch (set by the output they were drawn from); all others are unconditional.
export default function EdgeConfig({ edge, sourceKind }) {
  if (sourceKind === 'decision') {
    const branch = edge.data?.branch
    return (
      <div className="config">
        <p className="muted">
          Edge <b>{edge.source}</b> → <b>{edge.target}</b>.
        </p>
        <div className={`branch-tag branch-tag--${branch ? 'true' : 'false'}`}>
          {branch === true ? 'True branch' : branch === false ? 'False branch' : 'branch not set'}
        </div>
        <p className="muted">
          Set by which output you connected from. To change it, delete this edge and
          draw from the decision's other output.
        </p>
      </div>
    )
  }
  return (
    <div className="config">
      <p className="muted">
        Edge <b>{edge.source}</b> → <b>{edge.target}</b>.
      </p>
      <div className="muted">
        This edge is unconditional. To branch on a condition, insert a <b>Decision</b> node.
      </div>
    </div>
  )
}
