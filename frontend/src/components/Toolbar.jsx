import { useState } from 'react'

import { categoryForType, typeLabel } from '../catalog.js'

export default function Toolbar({
  name,
  onName,
  catalog,
  agents,
  onAddAgent,
  onAddLeaf,
  onSave,
  saving,
  settings,
  onSettings,
}) {
  const [showSettings, setShowSettings] = useState(false)

  return (
    <header className="toolbar">
      <div className="toolbar__row">
        <strong className="toolbar__brand">🛠️ Workflow Builder</strong>
        <input
          className="toolbar__name"
          value={name}
          onChange={(e) => onName(e.target.value)}
          placeholder="Workflow name"
        />
        <div className="toolbar__spacer" />

        {!catalog && <span className="muted">loading…</span>}
        {catalog?.categories.map((cat) => {
          const inCat = agents.filter(
            (a) => categoryForType(catalog, a.agent_type)?.key === cat.key,
          )
          return (
            <details key={cat.key} className="dropdown">
              <summary className="btn">+ {cat.label} agent ▾</summary>
              <div className="dropdown__menu">
                {inCat.length === 0 ? (
                  <div className="muted dropdown__empty">
                    No {cat.label} agents yet — create them in the Agents tab.
                  </div>
                ) : (
                  inCat.map((a) => (
                    <button
                      key={a.agent_id}
                      className="dropdown__item"
                      onClick={(e) => {
                        onAddAgent(a)
                        e.currentTarget.closest('details').open = false
                      }}
                    >
                      {a.name || '(unnamed)'}
                      <span className="muted"> · {typeLabel(catalog, a.agent_type)}</span>
                    </button>
                  ))
                )}
              </div>
            </details>
          )
        })}

        {catalog &&
          (() => {
            const other = agents.filter((a) => !categoryForType(catalog, a.agent_type))
            if (!other.length) return null
            return (
              <details className="dropdown">
                <summary className="btn">+ Other agent ▾</summary>
                <div className="dropdown__menu">
                  {other.map((a) => (
                    <button
                      key={a.agent_id}
                      className="dropdown__item"
                      onClick={(e) => {
                        onAddAgent(a)
                        e.currentTarget.closest('details').open = false
                      }}
                    >
                      {a.name || '(unnamed)'}
                      <span className="muted"> · {a.agent_type}</span>
                    </button>
                  ))}
                </div>
              </details>
            )
          })()}

        <button className="btn btn--ghost" onClick={onAddLeaf}>+ Leaf</button>
        <button className="btn btn--ghost" onClick={() => setShowSettings((s) => !s)}>⚙ Settings</button>
        <button className="btn btn--primary" onClick={onSave} disabled={saving || !catalog}>
          {saving ? 'Saving…' : 'Save workflow'}
        </button>
      </div>

      {showSettings && (
        <div className="toolbar__settings">
          <label className="field field--inline">
            <span className="field__label">API base</span>
            <input value={settings.base} onChange={(e) => onSettings({ ...settings, base: e.target.value })} />
          </label>
          <label className="field field--inline">
            <span className="field__label">API key (X-API-Key)</span>
            <input value={settings.apiKey} onChange={(e) => onSettings({ ...settings, apiKey: e.target.value })} />
          </label>
        </div>
      )}
    </header>
  )
}
