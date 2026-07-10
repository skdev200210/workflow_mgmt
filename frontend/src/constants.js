// Hardcoded columns available as condition parameters. Edit to taste.
export const PARAMS = [
  'dpd', // days past due
  'ptp', // promise to pay
  'amount',
  'outstanding',
  'attempts',
  'last_call_status',
  'language',
  'dpd_bucket',
]

// Condition operators — must match the backend Condition.op Literal.
export const OPERATORS = ['>', '<', '>=', '<=', '==', '!=', 'is']

// How the value field should be typed when serialized to JSON.
export const VALUE_TYPES = ['number', 'string', 'boolean']
