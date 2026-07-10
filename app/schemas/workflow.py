import uuid
from datetime import datetime
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator


# --------------------------------------------------------------------------- #
# Edge conditions
# --------------------------------------------------------------------------- #
class Condition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    param: str = Field(..., min_length=1)
    op: Literal[">", "<", ">=", "<=", "==", "!=", "is"]
    # bool is listed first so JSON ``true``/``false`` stays a bool under
    # Pydantic v2's left-to-right union coercion (bool <-> int otherwise).
    value: bool | int | float | str


class Edge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)
    # Optional legacy/safety-net agent reference; the canonical reference for an
    # execute_agent node lives in node_config.agent_id.
    agent_id: uuid.UUID | None = None
    # Edges carry NO conditions — all branching happens at decision nodes.
    # ``branch`` is set on edges LEAVING a decision node (which outcome this
    # edge represents); other nodes have a single, unconditional outgoing edge.
    branch: bool | None = None


# --------------------------------------------------------------------------- #
# Nodes (discriminated union on `type`)
# --------------------------------------------------------------------------- #
class ExecuteAgentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # The real UUID of an existing agent to execute at this node.
    agent_id: uuid.UUID


class LeafNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["leaf_node"]
    label: str
    node_config: dict[str, Any] = Field(default_factory=dict)
    input_data: str | None = None
    edges: list[Edge] = Field(default_factory=list)


class ExecuteAgentNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["execute_agent"]
    label: str
    node_config: ExecuteAgentConfig
    input_data: str | None = None
    edges: list[Edge] = Field(default_factory=list)


class DecisionNode(BaseModel):
    """A flowchart diamond: evaluate ``conditions`` (combined by ``match``) to a
    single True/False, then route via the outgoing edge whose ``branch`` matches.
    Lets you chain if/elif/else without repeating conditions on every edge.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["decision"]
    label: str
    node_config: dict[str, Any] = Field(default_factory=dict)
    match: Literal["all", "any"] = "all"
    conditions: list[Condition] = Field(..., min_length=1)
    input_data: str | None = None
    edges: list[Edge] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_branches(self) -> "DecisionNode":
        branches = [e.branch for e in self.edges]
        if any(b is None for b in branches):
            raise ValueError(
                "every edge from a decision node must set branch (true/false)."
            )
        if len(set(branches)) != len(branches):
            raise ValueError(
                "a decision node's edges must have distinct branches "
                "(at most one true and one false)."
            )
        return self


WorkflowNode = Annotated[
    Union[LeafNode, ExecuteAgentNode, DecisionNode], Field(discriminator="type")
]


# --------------------------------------------------------------------------- #
# Workflow definition (the graph stored in the JSONB column)
# --------------------------------------------------------------------------- #
class WorkflowDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Internal label carried inside the JSON; not the DB primary key.
    workflow_id: str | None = None
    workflow_start: str = Field(..., min_length=1)
    calling_config: dict[str, Any] | None = None
    nodes: dict[str, WorkflowNode] = Field(..., min_length=1)

    @model_validator(mode="after")
    def check_graph(self) -> "WorkflowDefinition":
        if self.workflow_start not in self.nodes:
            raise ValueError(
                f"workflow_start '{self.workflow_start}' is not a node in nodes."
            )
        for node_id, node in self.nodes.items():
            for edge in node.edges:
                if edge.target not in self.nodes:
                    raise ValueError(
                        f"edge '{edge.id}' on node '{node_id}' targets "
                        f"unknown node '{edge.target}'."
                    )
        # Cycles / self-loops are allowed by design (workflows can loop).
        return self


def collect_agent_ids(definition: WorkflowDefinition) -> set[uuid.UUID]:
    """Every agent UUID referenced by the workflow.

    Canonical source is each execute_agent node's ``node_config.agent_id``;
    any edge-level ``agent_id`` present is included as a safety net. Pure and
    DB-free so it can be unit-tested without a database.
    """
    ids: set[uuid.UUID] = set()
    for node in definition.nodes.values():
        if isinstance(node, ExecuteAgentNode):
            ids.add(node.node_config.agent_id)
        for edge in node.edges:
            if edge.agent_id is not None:
                ids.add(edge.agent_id)
    return ids


# --------------------------------------------------------------------------- #
# Request / response schemas
# --------------------------------------------------------------------------- #
class WorkflowCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    definition: WorkflowDefinition


class WorkflowUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    definition: WorkflowDefinition | None = None


class WorkflowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    seq_id: int
    workflow_id: uuid.UUID
    name: str | None = None
    definition: WorkflowDefinition
    created_at: datetime
    updated_at: datetime
