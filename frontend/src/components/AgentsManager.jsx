import { useState } from 'react'

import AgentForm from './AgentForm.jsx'
import { createAgent, deleteAgent, updateAgent } from '../api.js'
import {
  agentPreview,
  categoryForType,
  fieldsForType,
  metadataFromValues,
  missingVarsForValues,
  typeLabel,
  valuesFromMetadata,
} from '../catalog.js'

function emptyValues(catalog, agentType) {
  const values = {}
  for (const f of fieldsForType(catalog, agentType)) values[f.name] = ''
  return values
}

function validateDraft(catalog, draft) {
  const fields = fieldsForType(catalog, draft.agentType)
  const miss = missingVarsForValues(fields, draft.values)
  if (miss.length) {
    throw new Error(`Template is missing {placeholders} for: ${miss.join(', ')}`)
  }
  const req = fields.filter((f) => f.required && !String(draft.values[f.name] ?? '').trim())
  if (req.length) {
    throw new Error(`Missing required field(s): ${req.map((f) => f.label).join(', ')}`)
  }
  return metadataFromValues(fields, draft.values)
}

export default function AgentsManager({ settings, catalog, agents, onRefresh }) {
  const [draft, setDraft] = useState(null) // {agentId|null, agentType, name, values}
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  function startCreate() {
    setError(null)
    const first = catalog?.categories?.[0]?.types?.[0]?.key
    if (!first) return
    setDraft({ agentId: null, agentType: first, name: '', values: emptyValues(catalog, first) })
  }

  function changeType(agentType) {
    setDraft((d) => ({ ...d, agentType, values: emptyValues(catalog, agentType) }))
  }

  function startEdit(agent) {
    setError(null)
    const fields = fieldsForType(catalog, agent.agent_type)
    setDraft({
      agentId: agent.agent_id,
      agentType: agent.agent_type,
      name: agent.name || '',
      values: valuesFromMetadata(fields, agent.agent_metadata),
    })
  }

  async function save() {
    setSaving(true)
    setError(null)
    try {
      const agent_metadata = validateDraft(catalog, draft)
      const name = draft.name.trim() || null
      if (draft.agentId) {
        await updateAgent(settings, draft.agentId, { name, agent_metadata })
      } else {
        await createAgent(settings, { name, agent_type: draft.agentType, agent_metadata })
      }
      setDraft(null)
      await onRefresh()
    } catch (e) {
      setError(String(e.message || e))
    } finally {
      setSaving(false)
    }
  }

  async function remove(agent) {
    if (!window.confirm(`Delete agent "${agent.name || agent.agent_id}"?`)) return
    setError(null)
    try {
      await deleteAgent(settings, agent.agent_id)
      if (draft?.agentId === agent.agent_id) setDraft(null)
      await onRefresh()
    } catch (e) {
      setError(String(e.message || e))
    }
  }

  return (
    <div className="agents">
      <aside className="agents__list">
        <div className="agents__list-head">
          <strong>Agents</strong>
          <div>
            <button className="btn btn--primary btn--sm" onClick={startCreate}>+ New agent</button>
            <button className="btn btn--ghost btn--sm" onClick={onRefresh}>↻</button>
          </div>
        </div>

        {(catalog?.categories || []).map((cat) => {
          const inCat = agents.filter((a) => categoryForType(catalog, a.agent_type)?.key === cat.key)
          return (
            <div key={cat.key} className="agents__group">
              <div className="agents__group-head">
                <span>{cat.label}</span>
              </div>
              {inCat.length === 0 && <div className="muted agents__empty">No agents yet.</div>}
              {inCat.map((a) => (
                <div
                  key={a.agent_id}
                  className={`agent-item ${draft?.agentId === a.agent_id ? 'agent-item--active' : ''}`}
                  onClick={() => startEdit(a)}
                >
                  <div className="agent-item__name">{a.name || <i>(unnamed)</i>}</div>
                  <div className="agent-item__meta">{typeLabel(catalog, a.agent_type)}</div>
                  <div className="agent-item__preview">{agentPreview(catalog, a) || '—'}</div>
                  <button
                    className="agent-item__del"
                    onClick={(e) => {
                      e.stopPropagation()
                      remove(a)
                    }}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )
        })}
      </aside>

      <div className="agents__editor">
        {error && <div className="banner banner--err">{error}</div>}
        {!draft ? (
          <div className="viewer__empty">
            Select an agent to edit, or use “+ New” to create one.
          </div>
        ) : (
          <>
            <div className="inspector__head">
              <h3>
                {draft.agentId ? 'Edit' : 'New'} {typeLabel(catalog, draft.agentType)}
              </h3>
              <div>
                <button className="btn" onClick={() => setDraft(null)}>Cancel</button>
                <button className="btn btn--primary" onClick={save} disabled={saving}>
                  {saving ? 'Saving…' : draft.agentId ? 'Save changes' : 'Create agent'}
                </button>
              </div>
            </div>
            {!draft.agentId && (
              <div className="type-picker">
                <div className="field__label">Agent type</div>
                {(catalog?.categories || []).map((c) => (
                  <div key={c.key} className="type-picker__group">
                    <span className="type-picker__cat">{c.label}</span>
                    {c.types.map((t) => (
                      <button
                        key={t.key}
                        className={`chip ${draft.agentType === t.key ? 'chip--active' : ''}`}
                        onClick={() => changeType(t.key)}
                      >
                        {t.label}
                      </button>
                    ))}
                  </div>
                ))}
              </div>
            )}
            <AgentForm
              catalog={catalog}
              agentType={draft.agentType}
              name={draft.name}
              values={draft.values}
              onName={(v) => setDraft((d) => ({ ...d, name: v }))}
              onValues={(patch) => setDraft((d) => ({ ...d, values: { ...d.values, ...patch } }))}
            />
          </>
        )}
      </div>
    </div>
  )
}
