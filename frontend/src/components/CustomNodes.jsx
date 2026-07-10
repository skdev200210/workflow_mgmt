import { Handle, Position } from '@xyflow/react'

const CATEGORY_META = {
  calling: { icon: '📞', className: 'node node--calling' },
  message: { icon: '💬', className: 'node node--message' },
}

export function AgentNode({ data, selected }) {
  const meta = CATEGORY_META[data.category] || { icon: '⚙', className: 'node node--calling' }
  const preview = (data.preview || '').trim() || '(no template)'
  return (
    <div className={`${meta.className} ${selected ? 'node--selected' : ''}`}>
      <Handle type="target" position={Position.Top} />
      <div className="node__header">
        <span className="node__icon">{meta.icon}</span>
        <span className="node__title">{data.label}</span>
      </div>
      <div className="node__badge">{data.typeLabel}</div>
      <div className="node__preview">{preview}</div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}

export function LeafNode({ data, selected }) {
  const isStart = data.role === 'start'
  const isEnd = data.role === 'end'
  return (
    <div
      className={`node node--leaf ${isStart ? 'node--start' : ''} ${isEnd ? 'node--end' : ''} ${
        selected ? 'node--selected' : ''
      }`}
    >
      {!isStart && <Handle type="target" position={Position.Top} />}
      <div className="node__header">
        <span className="node__icon">{isStart ? '▶' : isEnd ? '⏹' : '◻'}</span>
        <span className="node__title">{data.label}</span>
      </div>
      {!isEnd && <Handle type="source" position={Position.Bottom} />}
    </div>
  )
}

// Stable reference — required by React Flow (do not recreate each render).
export const nodeTypes = { agent: AgentNode, leaf: LeafNode }
