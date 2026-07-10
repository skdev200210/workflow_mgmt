import { extractPlaceholders, parseVarList } from './placeholders.js'
import { PARAMS } from './constants.js'

// Which condition params an edge may use, based on its SOURCE node:
//   - Start / leaf node  -> the global input columns (PARAMS).
//   - Agent node         -> only that agent's configured output variables.
export function availableParams(sourceNode) {
  if (sourceNode?.data?.kind === 'agent') return sourceNode.data.outputVariables || []
  return PARAMS
}

// Lookups over the catalog returned by GET /agent-types:
//   { categories: [ { key, label, types:[{key,label}], fields:[{name,label,kind,required,role}] } ] }

export function categoryForType(catalog, agentType) {
  for (const c of catalog?.categories || []) {
    if (c.types.some((t) => t.key === agentType)) return c
  }
  return null
}

export function fieldsForType(catalog, agentType) {
  return categoryForType(catalog, agentType)?.fields || []
}

export function typeLabel(catalog, agentType) {
  for (const c of catalog?.categories || []) {
    for (const t of c.types) if (t.key === agentType) return t.label
  }
  return agentType
}

export function primaryTemplateField(fields) {
  return fields.find((f) => f.role === 'template')?.name
}

// Input variables declared but missing a {placeholder} in any template field.
export function missingVarsForValues(fields, values) {
  const iv = fields.find((f) => f.role === 'input_vars')
  if (!iv) return []
  const declared = parseVarList(values[iv.name])
  const present = new Set()
  for (const f of fields) {
    if (f.role === 'template') {
      for (const p of extractPlaceholders(values[f.name] || '')) present.add(p)
    }
  }
  return declared.filter((v) => !present.has(v))
}

// Build the agent_metadata object from field values.
export function metadataFromValues(fields, values) {
  const meta = {}
  for (const f of fields) {
    const raw = values[f.name]
    if (f.kind === 'list') {
      meta[f.name] = parseVarList(raw)
    } else {
      meta[f.name] = raw ?? ''
    }
  }
  return meta
}

// Inverse: seed editable field values from a stored agent_metadata dict.
export function valuesFromMetadata(fields, metadata) {
  const values = {}
  for (const f of fields) {
    const raw = metadata?.[f.name]
    values[f.name] = Array.isArray(raw) ? raw.join(', ') : raw ?? ''
  }
  return values
}

// A short preview string for an agent (its primary template field).
export function agentPreview(catalog, agent) {
  const fields = fieldsForType(catalog, agent.agent_type)
  const tf = primaryTemplateField(fields)
  return (agent.agent_metadata?.[tf] || '').trim()
}
