import { fieldsForType, missingVarsForValues } from '../catalog.js'

function Field({ label, hint, children }) {
  return (
    <label className="field">
      <span className="field__label">{label}</span>
      {children}
      {hint && <span className="field__hint">{hint}</span>}
    </label>
  )
}

// Renders the editable form for one agent: a name plus the type's fields,
// driven entirely by the backend field schema.
export default function AgentForm({ catalog, agentType, name, values, onName, onValues }) {
  const fields = fieldsForType(catalog, agentType)
  const missing = missingVarsForValues(fields, values)

  return (
    <div className="config">
      <Field label="Name">
        <input
          value={name || ''}
          placeholder="e.g. Collections opener call"
          onChange={(e) => onName(e.target.value)}
        />
      </Field>

      {fields.map((f) => (
        <div key={f.name}>
          <Field
            label={f.label + (f.required ? ' *' : '')}
            hint={
              f.role === 'template'
                ? 'Use {var} placeholders for each input variable.'
                : f.kind === 'list'
                  ? 'Comma-separated.'
                  : undefined
            }
          >
            {f.kind === 'textarea' ? (
              <textarea
                rows={5}
                value={values[f.name] || ''}
                onChange={(e) => onValues({ [f.name]: e.target.value })}
              />
            ) : (
              <input
                value={values[f.name] || ''}
                onChange={(e) => onValues({ [f.name]: e.target.value })}
              />
            )}
          </Field>
          {f.role === 'input_vars' && missing.length > 0 && (
            <div className="warning">
              Missing {'{placeholder}'} for input variable(s): <b>{missing.join(', ')}</b>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
