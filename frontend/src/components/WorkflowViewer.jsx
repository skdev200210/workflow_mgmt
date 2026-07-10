import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  MarkerType,
  useNodesState,
  useEdgesState,
} from '@xyflow/react'

import { viewerNodeTypes } from './ViewerNodes.jsx'
import { definitionToFlow } from '../layout.js'
import { getAgent, getWorkflow, listWorkflows } from '../api.js'

function DetailPanel({ detail }) {
  if (!detail) {
    return <div className="muted">Click a node or edge to see its details.</div>
  }
  if (detail.kind === 'edge') {
    const conds = detail.edge.data?.conditions || []
    const match = detail.edge.data?.match || 'all'
    return (
      <div className="config">
        <h4>Edge conditions</h4>
        {conds.length === 0 ? (
          <div className="config__preview">always (unconditional)</div>
        ) : (
          <>
            {conds.length > 1 && (
              <div className="muted">Match: {match === 'any' ? 'Any (OR)' : 'All (AND)'}</div>
            )}
            {conds.map((c, i) => (
              <div key={i} className="config__preview">
                {`${c.param} ${c.op} ${JSON.stringify(c.value)}`}
              </div>
            ))}
          </>
        )}
      </div>
    )
  }
  if (detail.kind === 'leaf') {
    return (
      <div className="config">
        <h4>{detail.node.data.label}</h4>
        <div className="muted">Role: {detail.node.data.role || 'intermediate'} (leaf_node)</div>
      </div>
    )
  }
  // agent
  const { node, agent } = detail
  if (agent?.error) {
    return <div className="banner banner--err">Failed to load agent: {agent.error}</div>
  }
  const m = agent?.agent_metadata || {}
  return (
    <div className="config">
      <h4>{node.data.label}</h4>
      <div className="muted">
        {agent?.agent_type} · {String(node.data.agentId).slice(0, 8)}…
      </div>
      {/* Render whatever metadata fields the type has (generic over agent type). */}
      {Object.entries(m).map(([key, value]) => (
        <Row
          key={key}
          label={key.replace(/_/g, ' ')}
          value={Array.isArray(value) ? value.join(', ') : value}
          pre={typeof value === 'string' && value.length > 40}
        />
      ))}
    </div>
  )
}

function Row({ label, value, pre }) {
  return (
    <div className="field">
      <span className="field__label">{label}</span>
      <div className={pre ? 'config__preview' : ''}>{value || <i className="muted">(empty)</i>}</div>
    </div>
  )
}

export default function WorkflowViewer({ settings }) {
  const [list, setList] = useState([])
  const [loadingList, setLoadingList] = useState(false)
  const [error, setError] = useState(null)
  const [selectedWf, setSelectedWf] = useState(null)
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [detail, setDetail] = useState(null)
  const [agentCache, setAgentCache] = useState({})

  const defaultEdgeOptions = useMemo(
    () => ({ type: 'step', markerEnd: { type: MarkerType.ArrowClosed } }),
    [],
  )

  const refresh = useCallback(async () => {
    setLoadingList(true)
    setError(null)
    try {
      setList(await listWorkflows(settings))
    } catch (e) {
      setError(String(e.message || e))
    } finally {
      setLoadingList(false)
    }
  }, [settings])

  useEffect(() => {
    refresh()
  }, [refresh])

  const openWorkflow = useCallback(
    async (id) => {
      setError(null)
      setDetail(null)
      try {
        const wf = await getWorkflow(settings, id)
        setSelectedWf(wf)
        const flow = definitionToFlow(wf.definition)
        setNodes(flow.nodes)
        setEdges(flow.edges)
      } catch (e) {
        setError(String(e.message || e))
      }
    },
    [settings, setNodes, setEdges],
  )

  const onNodeClick = useCallback(
    async (_, node) => {
      const agentId = node.data.agentId
      if (node.data.nodeType === 'execute_agent' && agentId) {
        let agent = agentCache[agentId]
        if (!agent) {
          try {
            agent = await getAgent(settings, agentId)
          } catch (e) {
            agent = { error: String(e.message || e) }
          }
          setAgentCache((c) => ({ ...c, [agentId]: agent }))
        }
        setDetail({ kind: 'agent', node, agent })
      } else {
        setDetail({ kind: 'leaf', node })
      }
    },
    [settings, agentCache],
  )

  return (
    <div className="viewer">
      <aside className="viewer__list">
        <div className="viewer__list-head">
          <strong>Workflows</strong>
          <button className="btn btn--ghost" onClick={refresh}>↻ Refresh</button>
        </div>
        {loadingList && <div className="muted">Loading…</div>}
        {!loadingList && list.length === 0 && <div className="muted">No workflows saved yet.</div>}
        <ul className="wf-list">
          {list.map((wf) => (
            <li
              key={wf.workflow_id}
              className={`wf-item ${
                selectedWf?.workflow_id === wf.workflow_id ? 'wf-item--active' : ''
              }`}
              onClick={() => openWorkflow(wf.workflow_id)}
            >
              <div className="wf-item__name">{wf.name || '(unnamed)'}</div>
              <div className="wf-item__meta">
                {Object.keys(wf.definition?.nodes || {}).length} nodes ·{' '}
                {new Date(wf.created_at).toLocaleString()}
              </div>
            </li>
          ))}
        </ul>
      </aside>

      <div className="viewer__canvas">
        {error && <div className="banner banner--err">{error}</div>}
        {!selectedWf ? (
          <div className="viewer__empty">Select a workflow on the left to view its diagram.</div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={viewerNodeTypes}
            defaultEdgeOptions={defaultEdgeOptions}
            nodesConnectable={false}
            onNodeClick={onNodeClick}
            onEdgeClick={(_, edge) => setDetail({ kind: 'edge', edge })}
            onPaneClick={() => setDetail(null)}
            fitView
          >
            <Background />
            <Controls />
            <MiniMap pannable zoomable />
          </ReactFlow>
        )}
      </div>

      <aside className="viewer__detail">
        <DetailPanel detail={detail} />
      </aside>
    </div>
  )
}
