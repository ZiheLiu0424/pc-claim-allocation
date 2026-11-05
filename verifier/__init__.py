"""Independent, pure, deterministic verification of structured source records."""
from contract import Task, Tool

from . import allocation
from .checks import result

TOOLS = {Tool.ALLOCATE_CLAIMS: allocation}
TASKS = {Task.ALLOCATE_CLAIMS: allocation.verify_task, Task.ALLOCATE_CLAIMS_LOCAL: allocation.verify_task}


def verify_input(tool, value):
    try:
        return TOOLS[Tool(tool)].verify_input(value)
    except (ValueError, TypeError, AttributeError, KeyError):
        return result(False, "unknown tool or malformed input")


def verify_output(tool, input_value, output_value, workspace):
    try:
        return TOOLS[Tool(tool)].verify_output(input_value, output_value, workspace)
    except (ValueError, TypeError, AttributeError, KeyError):
        return result(False, "unknown tool or malformed output")


def verify_task(task, arguments, output, reference, workspace):
    try:
        return TASKS[Task(task)](arguments, output, reference, workspace)
    except (ValueError, TypeError, AttributeError, KeyError):
        return result(False, "unknown task or malformed submission")
