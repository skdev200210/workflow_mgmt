from typing import Literal

from pydantic import BaseModel


class FieldSpec(BaseModel):
    """One editable field of an agent type's metadata form."""

    name: str
    label: str
    kind: Literal["text", "textarea", "list"]
    required: bool
    role: Literal["template", "input_vars", "output_vars", "plain"]


class AgentTypeRef(BaseModel):
    """A child agent type within a category."""

    key: str
    label: str


class CategoryCatalog(BaseModel):
    """A base category (e.g. calling / message) with its child types + fields."""

    key: str
    label: str
    types: list[AgentTypeRef]
    fields: list[FieldSpec]


class AgentCatalog(BaseModel):
    """Response for GET /agent-types."""

    categories: list[CategoryCatalog]
