import { OPERATORS, VALUE_TYPES } from '../constants.js'

const EMPTY = { param: '', op: '', value: '', valueType: 'number' }

function defaultValueType(op) {
  if (op === 'is') return 'boolean'
  if (op === '==' || op === '!=') return 'string'
  return 'number'
}

// Reusable multi-condition editor (used by decision nodes and by edges leaving
// a start/agent node). `params` is the list of selectable columns/variables.
export default function ConditionsEditor({ conditions, match, params, onChange }) {
  const setAll = (conds, m = match) => onChange(conds, m)
  const updateAt = (i, patch) =>
    setAll(conditions.map((c, idx) => (idx === i ? { ...c, ...patch } : c)))
  const addCondition = () => setAll([...conditions, { ...EMPTY }])
  const removeAt = (i) => setAll(conditions.filter((_, idx) => idx !== i))

  return (
    <>
      {conditions.length > 1 && (
        <label className="field field--inline">
          <span className="field__label">Match</span>
          <select value={match} onChange={(e) => setAll(conditions, e.target.value)}>
            <option value="all">All (AND)</option>
            <option value="any">Any (OR)</option>
          </select>
        </label>
      )}

      {conditions.map((c, i) => (
        <div key={i} className="cond-row">
          <div className="cond-row__head">
            <span className="field__label">Condition {i + 1}</span>
            <button className="cond-row__del" onClick={() => removeAt(i)}>×</button>
          </div>
          <select value={c.param || ''} onChange={(e) => updateAt(i, { param: e.target.value })}>
            <option value="">— column —</option>
            {params.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
          <div className="cond-row__opval">
            <select
              value={c.op || ''}
              onChange={(e) => updateAt(i, { op: e.target.value, valueType: defaultValueType(e.target.value) })}
            >
              <option value="">op</option>
              {OPERATORS.map((op) => (
                <option key={op} value={op}>{op}</option>
              ))}
            </select>
            <select value={c.valueType || 'number'} onChange={(e) => updateAt(i, { valueType: e.target.value })}>
              {VALUE_TYPES.map((vt) => (
                <option key={vt} value={vt}>{vt}</option>
              ))}
            </select>
            {c.valueType === 'boolean' ? (
              <select
                value={String(c.value ?? 'true')}
                onChange={(e) => updateAt(i, { value: e.target.value === 'true' })}
              >
                <option value="true">true</option>
                <option value="false">false</option>
              </select>
            ) : (
              <input
                type={c.valueType === 'number' ? 'number' : 'text'}
                placeholder="value"
                value={c.value ?? ''}
                onChange={(e) => updateAt(i, { value: e.target.value })}
              />
            )}
          </div>
        </div>
      ))}

      <button className="btn btn--ghost btn--sm" onClick={addCondition}>+ Add condition</button>
      {conditions.length === 0 && <div className="warning">Add at least one condition.</div>}
    </>
  )
}
