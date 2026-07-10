// Mirrors the backend's extract_placeholders: find named {placeholder} fields,
// ignoring {{ }} escapes and positional {} fields, reducing {a.b}/{a[0]} to root.
export function extractPlaceholders(template) {
  const names = new Set()
  const cleaned = String(template || '').replace(/\{\{|\}\}/g, '')
  const re = /\{([^{}]*)\}/g
  let m
  while ((m = re.exec(cleaned))) {
    const field = m[1].trim()
    if (!field) continue
    const root = field.split(/[.[]/)[0].trim()
    if (root) names.add(root)
  }
  return names
}

// Returns the input variables that are declared but missing from the template.
export function missingInputVars(template, inputVars) {
  const present = extractPlaceholders(template)
  return inputVars.filter((v) => !present.has(v))
}

// Parse a comma-separated variable list into a clean array.
export function parseVarList(text) {
  return String(text || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
}
