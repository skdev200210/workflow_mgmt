import dagre from '@dagrejs/dagre'

// Turn a stored workflow definition into React Flow nodes/edges, positioned by
// dagre's hierarchical (Sugiyama) layout — clean top-to-bottom ranks with
// non-overlapping nodes and sensible edge routing. Cycles/self-loops are handled
// by dagre (it breaks cycles for ranking).

const AGENT_SIZE = { width: 210, height: 92 }
const LEAF_SIZE = { width: 160, height: 56 }

function conditionsLabel(conditions, match) {
  const parts = (conditions || [])
    .filter((c) => c.param && c.op)
    .map((c) => `${c.param} ${c.op} ${c.value}`)
  if (!parts.length) return undefined
  return parts.join(match === 'any' ? ' OR ' : ' AND ')
}

function nodeSize(node) {
  return node.data.nodeType === 'execute_agent' ? AGENT_SIZE : LEAF_SIZE
}

export function definitionToFlow(definition) {
  const nodesDef = definition.nodes || {}
  const startId = definition.workflow_start
  const allIds = Object.keys(nodesDef)

  // Build nodes (positions filled in by dagre below).
  const nodes = allIds.map((id) => {
    const node = nodesDef[id]
    const role =
      id === startId
        ? 'start'
        : node.type === 'leaf_node' && (node.edges || []).length === 0
          ? 'end'
          : ''
    return {
      id,
      type: 'view',
      position: { x: 0, y: 0 },
      data: {
        nodeType: node.type,
        label: node.label,
        role,
        agentId: node.node_config?.agent_id,
      },
    }
  })

  const edges = []
  for (const id of allIds) {
    for (const e of nodesDef[id].edges || []) {
      if (!nodesDef[e.target]) continue
      edges.push({
        id: e.id || `${id}->${e.target}`,
        source: id,
        target: e.target,
        label: conditionsLabel(e.conditions, e.match),
        data: { conditions: e.conditions || [], match: e.match || 'all' },
      })
    }
  }

  // --- dagre layout ---
  const g = new dagre.graphlib.Graph()
  g.setGraph({ rankdir: 'TB', nodesep: 70, ranksep: 100, marginx: 24, marginy: 24 })
  g.setDefaultEdgeLabel(() => ({}))
  for (const n of nodes) {
    const { width, height } = nodeSize(n)
    g.setNode(n.id, { width, height })
  }
  for (const e of edges) {
    if (e.source !== e.target) g.setEdge(e.source, e.target) // self-loops don't affect ranks
  }
  dagre.layout(g)

  const positioned = nodes.map((n) => {
    const gn = g.node(n.id)
    const { width, height } = nodeSize(n)
    return { ...n, position: { x: gn.x - width / 2, y: gn.y - height / 2 } }
  })

  return { nodes: positioned, edges }
}
