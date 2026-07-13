from collections.abc import Mapping
from typing import Any

from app.core.enums import AgentType, ExecutorStatus
from app.execution.base import CallingExecutor, ExecutionResult


class AiCallingExecutor(CallingExecutor):
    """Simulated AI calling agent.

    Renders the start/system/end templates and reports the call it would place.
    A real provider (e.g. a voice API) would subclass CallingExecutor with the
    same ``execute`` contract and place the actual call here.
    """

    agent_type = AgentType.AI_CALLING.value

    def execute(self, context: Mapping[str, Any]) -> ExecutionResult:
        self._check_inputs(context)

        start = self._render(self.metadata.start_message, context)
        instructions = self._render(self.metadata.system_instructions, context)
        end = self._render(self.metadata.end_message, context)

        actions = [
            "[SIMULATED CALL] initiate AI call",
            f"say start_message: {start!r}",
            "drive conversation with system_instructions",
            f"say end_message: {end!r}",
            f"would capture output_variables: {self.metadata.output_variables}",
        ]
        return ExecutionResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status=ExecutorStatus.SIMULATED.value,
            actions=actions,
            rendered={
                "start_message": start,
                "system_instructions": instructions,
                "end_message": end,
            },
            outputs={name: None for name in self.metadata.output_variables},
        )


class BlasterCallingExecutor(CallingExecutor):
    """Simulated blaster (broadcast) calling agent.

    Shares the calling field shape but models a pre-recorded broadcast: it plays
    the rendered start/end messages rather than driving an interactive
    conversation. A real provider would subclass CallingExecutor and place the
    blast here.
    """

    agent_type = AgentType.BLASTER_CALLING.value

    def execute(self, context: Mapping[str, Any]) -> ExecutionResult:
        self._check_inputs(context)

        start = self._render(self.metadata.start_message, context)
        instructions = self._render(self.metadata.system_instructions, context)
        end = self._render(self.metadata.end_message, context)

        actions = [
            "[SIMULATED BLASTER CALL] broadcast pre-recorded call",
            f"play start_message: {start!r}",
            f"play end_message: {end!r}",
            f"would capture output_variables: {self.metadata.output_variables}",
        ]
        return ExecutionResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status=ExecutorStatus.SIMULATED.value,
            actions=actions,
            rendered={
                "start_message": start,
                "system_instructions": instructions,
                "end_message": end,
            },
            outputs={name: None for name in self.metadata.output_variables},
        )
