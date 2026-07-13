import uuid
from datetime import datetime
from string import Formatter
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


def extract_placeholders(template: str) -> set[str]:
    """Return the set of named ``{placeholder}`` fields in an f-string-style template.

    Uses the same parser the standard library uses for ``str.format`` so the
    result matches how the template would actually be rendered. Positional
    (``{}``) and index (``{0}``) fields are ignored; only named fields count.
    A leading attribute/index access such as ``{user.name}`` or ``{items[0]}``
    is reduced to its root name (``user`` / ``items``).
    """
    names: set[str] = set()
    for _, field_name, _, _ in Formatter().parse(template):
        if not field_name:
            continue
        root = field_name.replace("[", ".").split(".", 1)[0]
        if root:
            names.add(root)
    return names


def _assert_inputs_present(
    template: str, input_variables: list[str], field: str
) -> None:
    placeholders = extract_placeholders(template)
    missing = [v for v in input_variables if v not in placeholders]
    if missing:
        raise ValueError(
            f"{field} is missing placeholders for input variable(s): "
            f"{', '.join(missing)}. Every declared input variable must appear "
            f"as a {{placeholder}} in {field}."
        )


# --------------------------------------------------------------------------- #
# Metadata payloads (stored in the agent_metadata JSONB column)
# --------------------------------------------------------------------------- #
class AiCallingMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_message: str = Field(..., min_length=1)
    end_message: str = Field(..., min_length=1)
    input_variables: list[str] = Field(default_factory=list)
    output_variables: list[str] = Field(default_factory=list)
    system_instructions: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def check_input_variables_present(self) -> "AiCallingMetadata":
        _assert_inputs_present(
            self.system_instructions, self.input_variables, "system_instructions"
        )
        return self


class MessageMetadata(BaseModel):
    # Strict: only `message` and `input_variables` are permitted.
    model_config = ConfigDict(extra="forbid")

    message: str = Field(..., min_length=1)
    input_variables: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_input_variables_present(self) -> "MessageMetadata":
        _assert_inputs_present(self.message, self.input_variables, "message")
        return self


# Partial variants for PATCH (all fields optional; unknown fields rejected).
class AiCallingMetadataUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_message: str | None = Field(None, min_length=1)
    end_message: str | None = Field(None, min_length=1)
    input_variables: list[str] | None = None
    output_variables: list[str] | None = None
    system_instructions: str | None = Field(None, min_length=1)


class MessageMetadataUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str | None = Field(None, min_length=1)
    input_variables: list[str] | None = None


# --------------------------------------------------------------------------- #
# Create / Read schemas — generic over agent_type; metadata validated against
# the type's category model (see app.services.agent_types). Adding a new type/category
# is a registry change only, no new schema classes.
# --------------------------------------------------------------------------- #
class AgentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, max_length=255)
    agent_type: str
    agent_metadata: dict[str, Any]

    @model_validator(mode="after")
    def _validate_metadata(self) -> "AgentCreate":
        # Lazy import breaks the schemas <-> agent_types cycle.
        from app.services.agent_types import metadata_model_for_type

        model = metadata_model_for_type(self.agent_type)  # raises on unknown type
        validated = model.model_validate(self.agent_metadata)
        self.agent_metadata = validated.model_dump()
        return self


class AgentUpdate(BaseModel):
    """PATCH body: rename and/or partially update the metadata."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, max_length=255)
    agent_metadata: dict[str, Any] | None = None


class AgentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    seq_id: int
    agent_id: uuid.UUID
    name: str | None = None
    agent_type: str
    agent_metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime
