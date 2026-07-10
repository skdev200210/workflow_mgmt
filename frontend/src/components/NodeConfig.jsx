import { typeLabel } from '../catalog.js'
import { PARAMS } from '../constants.js'
import ConditionsEditor from './ConditionsEditor.jsx'

function Field({ label, children }) {
  return (
    <label className="field">
      <span className="field__label">{label}</span>
      {children}
    </label>
  )
}

export default function NodeConfig({ node, catalog, agents, onLabel, onChangeAgent, onConditions }) {
  if (node.data.kind === 'decision') {
    // Branch on input columns or on any agent's output variables.
    const outputVars = [
      ...new Set((agents || []).flatMap((a) => a.agent_metadata?.output_variables || [])),
    ]
    const params = [...PARAMS, ...outputVars]
    return (
      <div className="config">
        <div className="config__role">Decision</div>
        <p className="muted">
          The node's label is its consolidated condition. It routes via its two
          outputs: <b>True</b> (bottom) and <b>False</b> (right).
        </p>
        <ConditionsEditor
          conditions={node.data.conditions || []}
          match={node.data.match || 'all'}
          params={params}
          onChange={onConditions}
        />
      </div>
    )
  }

  if (node.data.kind === 'leaf') {
    return (
      <div className="config">
        <div className="config__role">Role: <b>{node.data.role || 'intermediate'}</b></div>
        <Field label="Label">
          <input value={node.data.label} onChange={(e) => onLabel(e.target.value)} />
        </Field>
        {node.data.role === 'start' && (
          <p className="muted">This node is the workflow's entry point (workflow_start).</p>
        )}
      </div>
    )
  }

  // Agent node — a reference to an existing agent from the library.
  return (
    <div className="config">
      <div className="config__role">
        {node.data.typeLabel} <span className="muted">({node.data.agentType})</span>
      </div>
      <Field label="Node label">
        <input value={node.data.label} onChange={(e) => onLabel(e.target.value)} />
      </Field>

      <div className="ref-card">
        <div className="ref-card__name">{node.data.agentName || '(unnamed agent)'}</div>
        <div className="muted">{node.data.preview || '—'}</div>
      </div>

      <Field label="Change agent">
        <select
          value={node.data.agentId}
          onChange={(e) => {
            const a = agents.find((x) => x.agent_id === e.target.value)
            if (a) onChangeAgent(a)
          }}
        >
          {agents.map((a) => (
            <option key={a.agent_id} value={a.agent_id}>
              {(a.name || '(unnamed)') + ' — ' + typeLabel(catalog, a.agent_type)}
            </option>
          ))}
        </select>
      </Field>

      <p className="muted">Edit this agent's template in the Agents tab.</p>
    </div>
  )
}
