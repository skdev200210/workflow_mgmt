
// --- settings (env defaults, overridable via the UI, persisted locally) ----- #
const LS_KEY = 'workflow-builder-settings'

export function loadSettings() {
  const fromEnv = {
    base: import.meta.env.VITE_API_BASE || 'http://localhost:8000',
    apiKey: import.meta.env.VITE_API_KEY || 'changeme-dev-key',
  }
  try {
    const saved = JSON.parse(localStorage.getItem(LS_KEY) || '{}')
    return { ...fromEnv, ...saved }
  } catch {
    return fromEnv
  }
}

export function saveSettings(settings) {
  localStorage.setItem(LS_KEY, JSON.stringify(settings))
}

// --- low-level fetch --------------------------------------------------------- #
async function apiFetch(settings, path, { method = 'GET', body } = {}) {
  const res = await fetch(`${settings.base}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': settings.apiKey,
    },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    let detail
    try {
      detail = JSON.stringify((await res.json()).detail)
    } catch {
      detail = await res.text()
    }
    throw new Error(`${res.status} ${res.statusText}: ${detail}`)
  }
  return res.status === 204 ? null : res.json()
}

// --- agent-type catalog + agent library ------------------------------------- #
export function getAgentTypes(settings) {
  return apiFetch(settings, '/agent-types')
}

export function listAgents(settings) {
  return apiFetch(settings, '/agents?limit=500')
}

export function createAgent(settings, body) {
  return apiFetch(settings, '/agents', { method: 'POST', body })
}

export function updateAgent(settings, agentId, body) {
  return apiFetch(settings, `/agents/${agentId}`, { method: 'PATCH', body })
}

export function deleteAgent(settings, agentId) {
  return apiFetch(settings, `/agents/${agentId}`, { method: 'DELETE' })
}

export function listWorkflows(settings) {
  return apiFetch(settings, '/workflows?limit=500')
}

export function getWorkflow(settings, workflowId) {
  return apiFetch(settings, `/workflows/${workflowId}`)
}

export function getAgent(settings, agentId) {
  return apiFetch(settings, `/agents/${agentId}`)
}

import { availableParams } from './catalog.js'

// --- condition completeness -------------------------------------------------- #
// A single condition is complete when it has param + op + a value. Booleans are
// always "present" (false is valid); other types must be non-empty.
export function conditionComplete(c) {
  if (!c || !c.param || !c.op) return false
  if (c.valueType === 'boolean') {
    return c.value === true || c.value === false || c.value === 'true' || c.value === 'false'
  }
  return c.value !== '' && c.value !== null && c.value !== undefined
}

// An edge is complete when every present condition is complete, AND it has at
// least one condition whenever its source node exposes params to branch on.
// (A source with no params — e.g. a message agent — may be unconditional.)
export function edgeComplete(edge, sourceNode) {
  const conds = edge.data?.conditions || []
  if (conds.some((c) => !conditionComplete(c))) return false
  if (availableParams(sourceNode).length > 0 && conds.length === 0) return false
  return true
}

// --- value coercion for conditions ------------------------------------------ #
function coerceValue(value, valueType) {
  if (valueType === 'number') {
    const n = Number(value)
    if (Number.isNaN(n)) throw new Error(`condition value "${value}" is not a number`)
    return n
  }
  if (valueType === 'boolean') {
    return value === true || value === 'true'
  }
  return String(value)
}

// --- main save: reference existing agents, assemble the graph, POST it ------ #
// Agents are created/managed separately (Agents tab); the builder only
// references them by agent_id — no agent creation happens here.
export async function saveWorkflow(settings, { name, nodes, edges, callingConfig }) {
  const startNodes = nodes.filter((n) => n.data.kind === 'leaf' && n.data.role === 'start')
  if (startNodes.length !== 1) {
    throw new Error(`Exactly one Start node is required (found ${startNodes.length}).`)
  }
  const startId = startNodes[0].id

  // Every agent node must reference an existing agent.
  const unset = nodes.filter((n) => n.data.kind === 'agent' && !n.data.agentId)
  if (unset.length) {
    throw new Error(`${unset.length} agent node(s) have no agent selected.`)
  }

  // Every edge's conditions must be complete (source-aware).
  const nodeById = Object.fromEntries(nodes.map((n) => [n.id, n]))
  const badEdges = edges.filter((e) => !edgeComplete(e, nodeById[e.source]))
  if (badEdges.length) {
    const list = badEdges.map((e) => `${e.source} → ${e.target}`).join(', ')
    throw new Error(
      `${badEdges.length} edge(s) have a missing/incomplete condition: ${list}`,
    )
  }

  // Group edges by source node and assemble the nodes map.
  const nodesDef = {}
  for (const node of nodes) {
    const isAgent = node.data.kind === 'agent'
    nodesDef[node.id] = {
      type: isAgent ? 'execute_agent' : 'leaf_node',
      label: node.data.label,
      node_config: isAgent ? { agent_id: node.data.agentId } : {},
      edges: [],
    }
  }
  for (const edge of edges) {
    if (!nodesDef[edge.target] || !nodesDef[edge.source]) continue
    const conds = edge.data?.conditions || []
    nodesDef[edge.source].edges.push({
      id: edge.id,
      target: edge.target,
      match: edge.data?.match || 'all',
      conditions: conds.map((c) => ({
        param: c.param,
        op: c.op,
        value: coerceValue(c.value, c.valueType),
      })),
    })
  }

  // 3. Build and POST the workflow definition.
  const definition = {
    workflow_start: startId,
    nodes: nodesDef,
  }
  if (callingConfig && Object.keys(callingConfig).length) {
    definition.calling_config = callingConfig
  }
  return apiFetch(settings, '/workflows', {
    method: 'POST',
    body: { name, definition },
  })
}
