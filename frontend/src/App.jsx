import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  MarkerType,
  ConnectionLineType,
  addEdge,
  useNodesState,
  useEdgesState,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import { nodeTypes } from './components/CustomNodes.jsx'
import Toolbar from './components/Toolbar.jsx'
import Inspector from './components/Inspector.jsx'
import WorkflowViewer from './components/WorkflowViewer.jsx'
import AgentsManager from './components/AgentsManager.jsx'
import {
  loadSettings,
  saveSettings,
  saveWorkflow,
  edgeComplete,
  getAgentTypes,
  listAgents,
} from './api.js'
import { agentPreview, categoryForType, typeLabel } from './catalog.js'
import { decisionLabel } from './conditionText.js'

// Every node/edge id is a UUID — these become the node keys (and
// workflow_start / executable_node_id) in the stored definition.
const newId = () => crypto.randomUUID()

const makeInitialNodes = () => [
  { id: newId(), type: 'leaf', deletable: false, position: { x: 320, y: 20 }, data: { kind: 'leaf', label: 'Start', role: 'start' } },
  { id: newId(), type: 'leaf', deletable: false, position: { x: 320, y: 460 }, data: { kind: 'leaf', label: 'End', role: 'end' } },
]

// Node data for a graph node that references an existing agent.
function agentNodeData(catalog, agent) {
  const label = agent.name || typeLabel(catalog, agent.agent_type)
  return {
    kind: 'agent',
    agentId: agent.agent_id,
    agentType: agent.agent_type,
    category: categoryForType(catalog, agent.agent_type)?.key,
    typeLabel: typeLabel(catalog, agent.agent_type),
    agentName: agent.name,
    preview: agentPreview(catalog, agent),
    // Output variables this agent produces — the only params its outgoing
    // edges may condition on.
    outputVariables: agent.agent_metadata?.output_variables || [],
    label,
  }
}

export default function App() {
  const initialNodes = useMemo(makeInitialNodes, [])
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [selected, setSelected] = useState(null)
  const [name, setName] = useState('My workflow')
  const [settings, setSettings] = useState(loadSettings)
  const [saving, setSaving] = useState(false)
  const [status, setStatus] = useState(null)
  const [mode, setMode] = useState('build') // 'build' | 'agents' | 'browse'
  const [catalog, setCatalog] = useState(null)
  const [agents, setAgents] = useState([])

  useEffect(() => {
    let cancelled = false
    Promise.all([getAgentTypes(settings), listAgents(settings)])
      .then(([c, a]) => {
        if (cancelled) return
        setCatalog(c)
        setAgents(a)
      })
      .catch((err) => !cancelled && setStatus({ type: 'err', msg: `Load failed: ${err.message}` }))
    return () => {
      cancelled = true
    }
  }, [settings.base, settings.apiKey])

  const refreshAgents = useCallback(async () => {
    try {
      setAgents(await listAgents(settings))
    } catch (e) {
      setStatus({ type: 'err', msg: String(e.message || e) })
    }
  }, [settings])

  const defaultEdgeOptions = useMemo(
    () => ({ type: 'step', markerEnd: { type: MarkerType.ArrowClosed }, animated: true }),
    [],
  )

  const displayEdges = useMemo(
    () =>
      edges.map((e) => {
        const src = nodes.find((n) => n.id === e.source)
        return edgeComplete(e, src)
          ? e
          : { ...e, label: '⚠ needs condition', style: { stroke: '#e0483d', strokeWidth: 2 } }
      }),
    [edges, nodes],
  )

  const onConnect = useCallback(
    (params) => {
      const src = nodes.find((n) => n.id === params.source)
      let data = {}
      let label
      if (src?.data.kind === 'decision') {
        // The branch is set by which output (True/False handle) you dragged from.
        const branch = params.sourceHandle !== 'false'
        data = { branch }
        label = branch ? 'True' : 'False'
      }
      setEdges((eds) => addEdge({ ...params, id: newId(), type: 'step', data, label }, eds))
    },
    [setEdges, nodes],
  )

  const addAgentNode = useCallback(
    (agent) => {
      const id = newId()
      const position = { x: 120 + Math.random() * 360, y: 160 + Math.random() * 160 }
      setNodes((nds) => nds.concat({ id, type: 'agent', position, data: agentNodeData(catalog, agent) }))
      setSelected({ type: 'node', id })
    },
    [setNodes, catalog],
  )

  const addLeafNode = useCallback(() => {
    const id = newId()
    const position = { x: 120 + Math.random() * 360, y: 160 + Math.random() * 160 }
    setNodes((nds) => nds.concat({ id, type: 'leaf', position, data: { kind: 'leaf', label: 'Step', role: '' } }))
    setSelected({ type: 'node', id })
  }, [setNodes])

  const addDecisionNode = useCallback(() => {
    const id = newId()
    const position = { x: 120 + Math.random() * 360, y: 160 + Math.random() * 160 }
    setNodes((nds) =>
      nds.concat({
        id,
        type: 'decision',
        position,
        data: {
          kind: 'decision',
          label: decisionLabel([], 'all'),
          match: 'all',
          conditions: [],
        },
      }),
    )
    setSelected({ type: 'node', id })
  }, [setNodes])

  const updateNodeConditions = useCallback(
    (id, conditions, match) =>
      setNodes((nds) =>
        nds.map((n) =>
          n.id === id
            ? { ...n, data: { ...n.data, conditions, match, label: decisionLabel(conditions, match) } }
            : n,
        ),
      ),
    [setNodes],
  )

  const updateLabel = useCallback(
    (id, label) =>
      setNodes((nds) => nds.map((n) => (n.id === id ? { ...n, data: { ...n.data, label } } : n))),
    [setNodes],
  )

  const changeNodeAgent = useCallback(
    (id, agent) =>
      setNodes((nds) =>
        nds.map((n) =>
          n.id === id
            ? { ...n, data: { ...n.data, ...agentNodeData(catalog, agent), label: n.data.label } }
            : n,
        ),
      ),
    [setNodes, catalog],
  )


  const deleteSelected = useCallback(
    (sel) => {
      if (sel.type === 'node') {
        setEdges((eds) => eds.filter((e) => e.source !== sel.id && e.target !== sel.id))
        setNodes((nds) => nds.filter((n) => n.id !== sel.id))
      } else {
        setEdges((eds) => eds.filter((e) => e.id !== sel.id))
      }
      setSelected(null)
    },
    [setNodes, setEdges],
  )

  const onSettings = useCallback((s) => {
    setSettings(s)
    saveSettings(s)
  }, [])

  const handleSave = useCallback(async () => {
    setSaving(true)
    setStatus(null)
    try {
      const result = await saveWorkflow(settings, { name, nodes, edges })
      setStatus({ type: 'ok', msg: `Saved. workflow_id = ${result.workflow_id}` })
    } catch (err) {
      setStatus({ type: 'err', msg: String(err.message || err) })
    } finally {
      setSaving(false)
    }
  }, [settings, name, nodes, edges])

  return (
    <div className="app">
      <nav className="tabs">
        {['build', 'agents', 'browse'].map((m) => (
          <button key={m} className={`tab ${mode === m ? 'tab--active' : ''}`} onClick={() => setMode(m)}>
            {m === 'build' ? 'Build' : m === 'agents' ? 'Agents' : 'Browse workflows'}
          </button>
        ))}
      </nav>

      {mode === 'agents' && (
        <AgentsManager settings={settings} catalog={catalog} agents={agents} onRefresh={refreshAgents} />
      )}
      {mode === 'browse' && <WorkflowViewer settings={settings} />}
      {mode === 'build' && (
        <>
          <Toolbar
            name={name}
            onName={setName}
            catalog={catalog}
            agents={agents}
            onAddAgent={addAgentNode}
            onAddDecision={addDecisionNode}
            onAddLeaf={addLeafNode}
            onSave={handleSave}
            saving={saving}
            settings={settings}
            onSettings={onSettings}
          />

          {status && (
            <div className={`banner ${status.type === 'ok' ? 'banner--ok' : 'banner--err'}`}>
              {status.msg}
              <button className="banner__close" onClick={() => setStatus(null)}>×</button>
            </div>
          )}

          <div className="main">
            <div className="canvas">
              <ReactFlow
                nodes={nodes}
                edges={displayEdges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                nodeTypes={nodeTypes}
                defaultEdgeOptions={defaultEdgeOptions}
                connectionLineType={ConnectionLineType.Step}
                onNodeClick={(_, node) => setSelected({ type: 'node', id: node.id })}
                onEdgeClick={(_, edge) => setSelected({ type: 'edge', id: edge.id })}
                onPaneClick={() => setSelected(null)}
                fitView
              >
                <Background />
                <Controls />
                <MiniMap pannable zoomable />
              </ReactFlow>
            </div>

            <Inspector
              selected={selected}
              nodes={nodes}
              edges={edges}
              catalog={catalog}
              agents={agents}
              onLabel={updateLabel}
              onChangeAgent={changeNodeAgent}
              onNodeConditions={updateNodeConditions}
              onDelete={deleteSelected}
            />
          </div>
        </>
      )}
    </div>
  )
}
