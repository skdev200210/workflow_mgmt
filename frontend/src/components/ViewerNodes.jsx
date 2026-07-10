import { Handle, Position } from '@xyflow/react'

function ViewNode({ data, selected }) {
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
