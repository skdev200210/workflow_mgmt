"""Edge condition evaluation for workflow routing.

Conditions are ``{"param": <name>, "op": <operator>, "value": <literal>}`` and
are evaluated against the run context (a dict of variables). Mirrors the
operators allowed by ``app.schemas.workflow.Condition``.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


class MissingParamError(Exception):
    """A condition references a param that is not present in the run context.

    Raised instead of silently evaluating False so a run whose context lacks a
    decision variable (e.g. the callback never captured it, or sent it under a
    different key) fails loudly instead of quietly taking the False branch.
    """

    def __init__(self, param: Any, context: dict[str, Any]):
        self.param = param
        super().__init__(
            f"decision condition references param {param!r} which is missing "
            f"from the run context (available params: {sorted(context.keys())})"
        )


def _num(x: Any) -> float | None:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def evaluate_condition(condition: dict[str, Any] | None, context: dict[str, Any]) -> bool:
    """Return whether ``condition`` holds for ``context``.

    A missing/None condition is treated as always-true (unconditional). A param
    absent from the context raises :class:`MissingParamError`. Numeric
    comparisons coerce both sides to float; ``==``/``!=`` compare by value;
    ``is`` compares booleans.
    """
    if not condition:
        return True

    param = condition.get("param")
    op = condition.get("op")
    expected = condition.get("value")

    if param not in context:
        raise MissingParamError(param, context)
    actual = context[param]

    if op in (">", "<", ">=", "<="):
        a, b = _num(actual), _num(expected)
        if a is None or b is None:
            return False
        if op == ">":
            return a > b
        if op == "<":
            return a < b
        if op == ">=":
            return a >= b
        return a <= b
    if op == "==":
        return actual == expected
    if op == "!=":
        return actual != expected
    if op == "is":
        return bool(actual) is bool(expected)

    logger.warning("unknown condition operator: %r", op)
    return False


def evaluate_conditions(
    conditions: list[dict[str, Any]] | None, match: str, context: dict[str, Any]
) -> bool:
    """Evaluate an edge's list of conditions combined by ``match``.

    "all" -> every condition must hold (AND); "any" -> at least one (OR).
    An empty/missing list is unconditional (always true).
    """
    if not conditions:
        return True
    results = [evaluate_condition(c, context) for c in conditions]
    return all(results) if match == "all" else any(results)


def select_next_edge(
    node: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any] | None:
    """Return the single outgoing edge to follow from ``node``.

    - ``decision`` node: evaluate the node's own conditions to True/False, then
      pick the outgoing edge whose ``branch`` matches that result.
    - other nodes: pick the edge whose own conditions pass. At most one should
      match; if several do we take the first and log a warning.
    Returns None when nothing matches (the branch ends here).
    """
    if node.get("type") == "decision":
        result = evaluate_conditions(node.get("conditions"), node.get("match", "all"), context)
        for edge in node.get("edges", []):
            if edge.get("branch") == result:
                return edge
        return None

    # Non-decision nodes have a single, unconditional outgoing edge.
    edges = node.get("edges", [])
    matches = edges[:1]
    if not matches:
        return None
    if len(matches) > 1:
        logger.warning(
            "node %r had %d matching edges; expected at most one — taking first (%r)",
            node.get("label"),
            len(matches),
            matches[0].get("id"),
        )
    return matches[0]
