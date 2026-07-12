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
    """Simulated SMS channel. Shares the message field shape for now."""

    agent_type = "sms"

    def execute(self, context: Mapping[str, Any]) -> ExecutionResult:
        self._check_inputs(context)

        body = self._render(self.metadata.message, context)
        actions = [
            "[SIMULATED SMS] dispatch SMS",
            f"send text: {body!r}",
        ]
        return ExecutionResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status="simulated",
            actions=actions,
            rendered={"message": body},
            outputs={},
        )


class RcsExecutor(MessageExecutor):
    """Simulated RCS channel. Shares the message field shape for now."""

    agent_type = "rcs"

    def execute(self, context: Mapping[str, Any]) -> ExecutionResult:
        self._check_inputs(context)

        body = self._render(self.metadata.message, context)
        actions = [
            "[SIMULATED RCS] dispatch RCS message",
            f"send rich text: {body!r}",
        ]
        return ExecutionResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status="simulated",
            actions=actions,
            rendered={"message": body},
            outputs={},
        )


class WhatsAppExecutor(MessageExecutor):
    """Simulated WhatsApp channel. Shares the message field shape for now."""

    agent_type = "whatsapp"

    def execute(self, context: Mapping[str, Any]) -> ExecutionResult:
        self._check_inputs(context)

        body = self._render(self.metadata.message, context)
        actions = [
            "[SIMULATED WHATSAPP] dispatch WhatsApp message",
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
