from uuid import UUID

from core.hasher import Hasher
from core.test_session.execution_plan import ExecutionStep


def hash_session_execution_step(session_id: UUID, execution_step: ExecutionStep):
    """
    Generate a hash for an execution step and the session id. This hash can be used to uniquely identify the execution
    step in e.g. a database or filesystem.

    Uses :meth:`core.hasher.Hasher.hash` to hash a string representing the dynamic parts of the execution step into a
    hexadecimal format.

    :param session_id: the test session id
    :param execution_step: the execution step

    :return: the hash of a string representing the dynamic parts of the execution step
    """
    input_string = (
        f"{session_id}"
        f"/{execution_step.plan_repetition}"
        f"/{execution_step.step.order}"
        f"/{execution_step.step_repetition}"
    )

    if len(execution_step.test_cases) == 1:
        input_string += f"/{execution_step.test_cases[0].xctest_id}"

    return Hasher.hash(input_string)
