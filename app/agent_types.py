"""Agent type registry — the single source of truth for agent categories,
their child types, and the field schema the frontend renders forms from.

Two base categories (calling, message) each have child types. For now every
type in a category shares that category's field shape and metadata model
(distinct per-channel fields can be added later without touching callers).
"""

from typing import Any

from pydantic import BaseModel

from app.schemas.agent import (
    AiCallingMetadata,
    AiCallingMetadataUpdate,
    MessageMetadata,
    MessageMetadataUpdate,
)

# Field specs are declarative data the frontend renders forms from.
# role: "template" (f-string), "input_vars"/"output_vars" (name lists), "plain".
# kind: "text" | "textarea" | "list".
CALLING_FIELDS: list[dict[str, Any]] = [
    {
        "name": "start_message",
        "label": "Start message",
        "kind": "text",
        "required": True,
        "role": "plain",
    },
    {
        "name": "end_message",
        "label": "End message",
        "kind": "text",
        "required": True,
        "role": "plain",
    },
    {
        "name": "system_instructions",
        "label": "System instructions",
        "kind": "textarea",
        "required": True,
        "role": "template",
    },
    {
        "name": "input_variables",
        "label": "Input variables",
        "kind": "list",
        "required": False,
        "role": "input_vars",
    },
    {
        "name": "output_variables",
        "label": "Output variables",
        "kind": "list",
        "required": False,
        "role": "output_vars",
    },
]
MESSAGE_FIELDS: list[dict[str, Any]] = [
    {
        "name": "message",
        "label": "Message",
        "kind": "textarea",
        "required": True,
        "role": "template",
    },
    {
        "name": "input_variables",
        "label": "Input variables",
        "kind": "list",
        "required": False,
        "role": "input_vars",
    },
]

CATEGORIES: dict[str, dict[str, Any]] = {
    "calling": {
        "label": "Calling",
        "fields": CALLING_FIELDS,
        "metadata_model": AiCallingMetadata,
        "update_model": AiCallingMetadataUpdate,
        "types": [
            {"key": "ai_calling", "label": "AI Calling Agent"},
            {"key": "blaster_calling", "label": "Blaster Calling Agent"},
        ],
    },
    "message": {
        "label": "Message",
        "fields": MESSAGE_FIELDS,
        "metadata_model": MessageMetadata,
        "update_model": MessageMetadataUpdate,
        "types": [
            {"key": "whatsapp", "label": "WhatsApp Message"},
            {"key": "sms", "label": "SMS"},
            {"key": "rcs", "label": "RCS Message"},
        ],
    },
}


def _type_to_category() -> dict[str, str]:
    index: dict[str, str] = {}
    for cat_key, cat in CATEGORIES.items():
        for t in cat["types"]:
            index[t["key"]] = cat_key
    return index


TYPE_TO_CATEGORY = _type_to_category()


def known_types() -> set[str]:
    return set(TYPE_TO_CATEGORY)


def category_for_type(agent_type: str) -> str:
    category = TYPE_TO_CATEGORY.get(agent_type)
    if category is None:
        raise ValueError(f"unknown agent_type: {agent_type!r}")
    return category


def metadata_model_for_type(agent_type: str) -> type[BaseModel]:
    return CATEGORIES[category_for_type(agent_type)]["metadata_model"]


def update_model_for_type(agent_type: str) -> type[BaseModel]:
    return CATEGORIES[category_for_type(agent_type)]["update_model"]


def build_catalog() -> dict[str, Any]:
    """The catalog served to the frontend: categories -> child types + fields."""
    return {
        "categories": [
            {
                "key": key,
                "label": cat["label"],
                "types": cat["types"],
                "fields": cat["fields"],
            }
            for key, cat in CATEGORIES.items()
        ]
    }
