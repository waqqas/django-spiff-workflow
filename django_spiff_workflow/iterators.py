import json
import os
from typing import Iterable, Iterator, Optional
from uuid import UUID

from django.conf import settings
from django.template import Context, Template
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.spiff.specs.defaults import ManualTask, ScriptTask, UserTask
from SpiffWorkflow.spiff.specs.spiff_task import SpiffBpmnTask


class Task:
    @property
    def id(self) -> UUID:
        return self.task.id

    @property
    def description(self) -> str:
        return self.task.description

    @property
    def instructions(self) -> str:
        template = self.task.task_spec.extensions.get("instructionsForEndUser", "")
        template = Template(template)
        context = Context(self.data)
        return template.render(context)

    @property
    def state(self) -> str:
        return self.task.get_state_name()

    @property
    def type(self) -> str:
        return (
            "MANUAL"
            if isinstance(self.task.task_spec, ManualTask)
            else (
                "USER"
                if isinstance(self.task.task_spec, UserTask)
                else (
                    "SCRIPT"
                    if isinstance(self.task.task_spec, ScriptTask)
                    else "UNKNOWN"
                )
            )
        )

    @property
    def is_ready(self) -> bool:
        return self.state == "READY"

    @property
    def is_waiting(self) -> bool:
        return self.state == "WAITING"

    @property
    def is_manual(self) -> bool:
        """Either Manual or User Task (that needs manual input)"""
        return self.task.task_spec.manual

    @property
    def schema(self) -> Optional[dict]:
        filename = self.task.task_spec.extensions.get("properties", {}).get(
            "formJsonSchemaFilename"
        )
        if not filename:
            return None
        return json.load(open(os.path.join(settings.BPMN_PATH, filename)))

    @property
    def data(self):
        return self.task.data

    @data.setter
    def data(self, data):
        self.task.set_data(**data)

    @property
    def spec_name(self):
        return self.task.task_spec.name

    @property
    def lane(self) -> Optional[str]:
        return self.task.task_spec.lane

    @property
    def name(self) -> Optional[str]:
        return self.task.task_spec.bpmn_name or "N/A"

    def __init__(self, workflow: BpmnWorkflow, task: SpiffBpmnTask, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.workflow = workflow
        self.task = task

    def __str__(self):
        return self.description

    def run(self):
        self.task.run()

    def set_data(self, data):
        self.task.set_data(**data)


class BaseIterator(Iterable):
    def __init__(self, iterable: Iterator):
        self.iterable = iterable
        self._iterator = None

    def __iter__(self) -> Iterator:
        self._iterator = iter(self.iterable)
        return self

    def __next__(self):
        return next(self._iterator)


class TaskIterator(BaseIterator):
    def __init__(self, workflow: BpmnWorkflow, iterable: Iterator):
        super().__init__(iterable)
        self.workflow = workflow

    def __next__(self) -> Task:
        return Task(self.workflow, next(self._iterator))
