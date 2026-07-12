import { OPERATORS, VALUE_TYPES } from '../constants.js'

const EMPTY = { param: '', op: '', value: '', valueType: 'number' }

function defaultValueType(op) {
  if (op === 'is') return 'boolean'
  if (op === '==' || op === '!=') return 'string'
  return 'number'
}

// A decision node holds exactly ONE condition — compound logic is built by
// stacking decision nodes. Props keep the (conditions, match, onChange) shape
// used by NodeConfig; only conditions[0] is ever edited.
export default function ConditionsEditor({ conditions, match, params, onChange }) {
  const c = conditions[0] || EMPTY
  const update = (patch) => onChange([{ ...c, ...patch }], match || 'all')

  return (
    <>
      <div className="cond-row">
        <div className="cond-row__head">
          <span className="field__label">Condition</span>
        </div>
        <select value={c.param || ''} onChange={(e) => update({ param: e.target.value })}>
          <option value="">— column —</option>
          {params.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
        <div className="cond-row__opval">
          <select
            value={c.op || ''}
            onChange={(e) => update({ op: e.target.value, valueType: defaultValueType(e.target.value) })}
          >
            <option value="">op</option>
            {OPERATORS.map((op) => (
              <option key={op} value={op}>{op}</option>
            ))}
          </select>
          <select value={c.valueType || 'number'} onChange={(e) => update({ valueType: e.target.value })}>
            {VALUE_TYPES.map((vt) => (
              <option key={vt} value={vt}>{vt}</option>
            ))}
          </select>
          {c.valueType === 'boolean' ? (
            <select
              value={String(c.value ?? 'true')}
              onChange={(e) => update({ value: e.target.value === 'true' })}
            >
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          ) : (
            <input
              type={c.valueType === 'number' ? 'number' : 'text'}
              placeholder="value"
              value={c.value ?? ''}
              onChange={(e) => update({ value: e.target.value })}
            />
          )}
        </div>
      </div>
      <p className="muted">
        One condition per decision — stack decision nodes for compound logic
        (e.g. chain two diamonds for “a &gt; b AND a % b == 0”).
      </p>
    </>
  )
}
