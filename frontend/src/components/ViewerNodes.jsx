import { Handle, Position } from '@xyflow/react'

function ViewNode({ data, selected }) {
  if (data.nodeType === 'decision') {
    return (
      <div className={`diamond-wrap ${selected ? 'diamond-wrap--selected' : ''}`}>
        <Handle type="target" position={Position.Top} />
        <div className="diamond-shape" />
        <div className="diamond-label">{data.label}</div>
        <Handle type="source" id="true" position={Position.Bottom} className="handle-true" />
        <Handle type="source" id="false" position={Position.Right} className="handle-false" />
        <span className="diamond-tag diamond-tag--true">T</span>
        <span className="diamond-tag diamond-tag--false">F</span>
      </div>
    )
  }
  const isAgent = data.nodeType === 'execute_agent'
  const icon = isAgent ? '⚙' : data.role === 'start' ? '▶' : data.role === 'end' ? '⏹' : '◻'
  return (
    <div
      className={`node ${isAgent ? 'node--calling' : 'node--leaf'} ${
        data.role === 'start' ? 'node--start' : ''
      } ${data.role === 'end' ? 'node--end' : ''} ${selected ? 'node--selected' : ''}`}
    >
      {data.role !== 'start' && <Handle type="target" position={Position.Top} />}
      <div className="node__header">
        <span className="node__icon">{icon}</span>
        <span className="node__title">{data.label}</span>
      </div>
      {isAgent && <div className="node__badge">execute_agent</div>}
      {isAgent && data.agentId && (
        <div className="node__preview">{String(data.agentId).slice(0, 8)}…</div>
      )}
      {data.role !== 'end' && <Handle type="source" position={Position.Bottom} />}
    </div>
  )
}

export const viewerNodeTypes = { view: ViewNode }
