// Human-readable summary of a condition list, e.g. "dpd > 100 AND ptp is true".
export function summarizeConditions(conditions, match) {
  const parts = (conditions || [])
    .filter((c) => c.param && c.op)
    .map((c) => `${c.param} ${c.op} ${c.value}`)
  if (!parts.length) return ''
  return parts.join(match === 'any' ? ' OR ' : ' AND ')
}

// A decision node's label IS its consolidated condition.
export function decisionLabel(conditions, match) {
  return summarizeConditions(conditions, match) || 'Decision (set condition)'
}
