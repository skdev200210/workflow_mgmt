import NodeConfig from './NodeConfig.jsx'
import EdgeConfig from './EdgeConfig.jsx'
import { availableParams } from '../catalog.js'

export default function Inspector({
  selected,
  nodes,
  edges,
  catalog,
  agents,
  onLabel,
  onChangeAgent,
  onConditions,
  onDelete,
}) {
  if (!selected) {
    return (
      <aside className="inspector">
        <div className="inspector__empty">
          Select a node or an edge to configure it.
          <ul>
            <li>Add agent nodes from the toolbar (they reference agents from the Agents tab).</li>
            <li>Drag from a node's bottom dot to another node to create an edge.</li>
            <li>Click an edge to set its condition (column / operator / value).</li>
          </ul>
        </div>
      </aside>
    )
  }

  if (selected.type === 'node') {
    const node = nodes.find((n) => n.id === selected.id)
    if (!node) return null
    const canDelete = node.data.role !== 'start' && node.data.role !== 'end'
    return (
      <aside className="inspector">
        <div className="inspector__head">
          <h3>Node: {node.data.label}</h3>
          {canDelete && (
            <button className="btn btn--danger" onClick={() => onDelete(selected)}>
              Delete
            </button>
          )}
        </div>
        <NodeConfig
          node={node}
          catalog={catalog}
          agents={agents}
          onLabel={(v) => onLabel(node.id, v)}
          onChangeAgent={(agent) => onChangeAgent(node.id, agent)}
        />
      </aside>
    )
  }

  const edge = edges.find((e) => e.id === selected.id)
  if (!edge) return null
  const sourceNode = nodes.find((n) => n.id === edge.source)
  const params = availableParams(sourceNode)
  return (
    <aside className="inspector">
      <div className="inspector__head">
        <h3>Edge conditions</h3>
        <button className="btn btn--danger" onClick={() => onDelete(selected)}>
          Delete
        </button>
      </div>
      <EdgeConfig
        edge={edge}
        params={params}
        onConditions={(conds, match) => onConditions(edge.id, conds, match)}
      />
    </aside>
  )
}
