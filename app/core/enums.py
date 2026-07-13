"""Central enumerations — the single source of truth for every fixed-value
string used across the app (statuses, callback contracts, node/agent types,
condition operators).

All are :class:`enum.StrEnum`, so each member IS its string value: it compares
equal to the raw string (``ExecutionStatus.PENDING == "pending"``), serializes
to that string in JSON/SQL, and formats to it in f-strings. That means these
can be dropped in anywhere a literal was used — DB columns, Pydantic fields,
dict keys — without changing behaviour, while giving one place to change a
value or add a member.
"""
from enum import StrEnum


class ExecutionStatus(StrEnum):
    """Lifecycle of a workflow_execution row (which doubles as the queue)."""

    PENDING = "pending"        # waiting to be claimed/dispatched
    PROCESSING = "processing"  # claimed by a worker, mid-dispatch
    IN_FLIGHT = "in_flight"    # dispatched, awaiting a provider callback
    # terminal states:
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class AgentExecutionStatus(StrEnum):
    """Lifecycle of an agent_execution receipt (per agent fire)."""

    DISPATCHED = "dispatched"                # fired, correlation id issued
    CALLBACK_RECEIVED = "callback_received"  # provider reported an outcome
    FAILED = "failed"                        # provider reported failure
    STALE = "stale"                          # late callback; run had moved on
    TIMED_OUT = "timed_out"                  # swept before any callback arrived


class CallbackOutcome(StrEnum):
    """Normalized provider outcome that drives the engine."""

    SUCCESS = "success"  # merge outputs, advance to the next node
    RETRY = "retry"      # re-schedule the SAME node, bounded by max_attempts
    FAILURE = "failure"  # fail the run


class CallbackSource(StrEnum):
    """Which channel a provider callback came from."""

    CALLING = "calling"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    RCS = "rcs"


class NodeType(StrEnum):
    """Workflow graph node kinds (the JSON ``type`` discriminator)."""

    LEAF = "leaf_node"
    EXECUTE_AGENT = "execute_agent"
    DECISION = "decision"


class AgentCategory(StrEnum):
    """Base agent categories; each groups one or more channel types."""

    CALLING = "calling"
    MESSAGE = "message"


class AgentType(StrEnum):
    """Concrete agent/channel types routed to executors."""

    AI_CALLING = "ai_calling"
    BLASTER_CALLING = "blaster_calling"
    MESSAGE = "message"  # legacy generic message channel
    SMS = "sms"
    RCS = "rcs"
    WHATSAPP = "whatsapp"


class ExecutorStatus(StrEnum):
    """Status reported by an executor's ``execute`` (dispatch simulation)."""

    SIMULATED = "simulated"
    SUCCESS = "success"
    FAILED = "failed"


class ResolveKind(StrEnum):
    """What ``resolve_next_actionable`` walked to."""

    AGENT = "agent"  # next execute_agent node to dispatch
    END = "end"      # a terminal leaf was reached
    NONE = "none"    # no edge matched / hop cap hit (branch ends)


class ConditionOperator(StrEnum):
    """Operators allowed in a decision condition."""

    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
    EQ = "=="
    NEQ = "!="
    IS = "is"


class MatchMode(StrEnum):
    """How a decision node combines its conditions."""

    ALL = "all"  # AND
    ANY = "any"  # OR
