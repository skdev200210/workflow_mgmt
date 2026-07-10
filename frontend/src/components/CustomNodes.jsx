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

export function DecisionNode({ data, selected }) {
  // Two dedicated outputs: True (bottom) and False (right). The branch is set by
  // which handle an edge is drawn from. Handles sit on the wrapper (not the
  // clip-path shape) so they aren't clipped.
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

// Stable reference — required by React Flow (do not recreate each render).
export const nodeTypes = { agent: AgentNode, leaf: LeafNode, decision: DecisionNode }
