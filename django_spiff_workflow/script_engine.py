import os
from typing import Any, Dict, Optional

from SpiffWorkflow.bpmn.script_engine import PythonScriptEngine, TaskDataEnvironment


def create_script_engine(
    environment: Optional[Dict[Any, Any]] = None
) -> PythonScriptEngine:
    vars = globals()
    vars.update(os.environ.copy())
    if environment:
        vars.update(environment)
    custom_env = TaskDataEnvironment(vars)

    return PythonScriptEngine(environment=custom_env)
