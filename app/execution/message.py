from collections.abc import Mapping
from typing import Any

from app.execution.base import ExecutionResult, MessageExecutorBase


class MessageExecutor(MessageExecutorBase):
    """Simulated message agent.

    Renders the message template and reports the message it would send. A real
    channel (SMS/WhatsApp/email) would subclass MessageExecutorBase with the
    same ``execute`` contract and dispatch the actual message here.
    """

    agent_type = "message"

    def execute(self, context: Mapping[str, Any]) -> ExecutionResult:
        self._check_inputs(context)

        body = self._render(self.metadata.message, context)
        actions = [
            "[SIMULATED MESSAGE] dispatch message",
            f"send: {body!r}",
        ]
        return ExecutionResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status="simulated",
            actions=actions,
            rendered={"message": body},
            outputs={},
        )


class SmsExecutor(MessageExecutor):
    """SMS channel. Shares the message field shape for now."""

    agent_type = "sms"


class RcsExecutor(MessageExecutor):
    """RCS channel. Shares the message field shape for now."""

    agent_type = "rcs"


class WhatsAppExecutor(MessageExecutor):
    """WhatsApp channel. Shares the message field shape for now."""

    agent_type = "whatsapp"
