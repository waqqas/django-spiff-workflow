import json
import os
from typing import Iterable, Iterator, Optional
from uuid import UUID
from SpiffWorkflow.bpmn.specs.control import BoundaryEventSplit
from django.conf import settings
from django.template import Context, Template
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.spiff.specs.defaults import ManualTask, ScriptTask, UserTask
from SpiffWorkflow.spiff.specs.spiff_task import SpiffBpmnTask
from SpiffWorkflow.bpmn.specs.mixins.events.intermediate_event import BoundaryEvent
from SpiffWorkflow.bpmn.specs.event_definitions import (
    SignalEventDefinition,
    DurationTimerEventDefinition,
)


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
    def signal_boundary_events(self):
        events = []
        task_spec = self.task.task_spec

        # Check if task_spec has inputs attribute containing BoundaryEventSplit
        if hasattr(task_spec, "inputs"):
            inputs = getattr(task_spec, "inputs", [])
            for input_item in inputs:
                if isinstance(input_item, BoundaryEventSplit):
                    # Check all attributes of BoundaryEventSplit for potential boundary events
                    for attr in dir(input_item):
                        if not attr.startswith("_"):
                            value = getattr(input_item, attr)
                            if isinstance(value, list) or isinstance(value, dict):
                                if isinstance(value, list):
                                    for item in value:
                                        if isinstance(item, BoundaryEvent):
                                            if hasattr(
                                                item, "event_definition"
                                            ) and isinstance(
                                                item.event_definition,
                                                SignalEventDefinition,
                                            ):
                                                signal_event = item.event_definition
                                                signal_ref = (
                                                    signal_event.name
                                                )  # Adjust this line based on actual attribute
                                                button_label = item.extensions.get(
                                                    "signalButtonLabel"
                                                )
                                                if (
                                                    button_label
                                                ):  # Only include if button label is present
                                                    event = {
                                                        "signal": signal_ref,
                                                        "button_label": button_label,
                                                        "task_id": self.id,  # Include task ID
                                                    }
                                                    events.append(event)

        return events

    @property
    def timer_boundary_events(self):
        timer_events = []
        task_spec = self.task.task_spec

        # Check if task_spec has inputs attribute containing BoundaryEventSplit
        if hasattr(task_spec, "inputs"):
            inputs = getattr(task_spec, "inputs", [])
            for input_item in inputs:
                if isinstance(input_item, BoundaryEventSplit):
                    # Check all attributes of BoundaryEventSplit for potential boundary events
                    for attr in dir(input_item):
                        if not attr.startswith("_"):
                            value = getattr(input_item, attr)
                            if isinstance(value, list) or isinstance(value, dict):
                                if isinstance(value, list):
                                    for item in value:
                                        if isinstance(item, BoundaryEvent):
                                            # Check for DurationTimerEventDefinition
                                            if hasattr(
                                                item, "event_definition"
                                            ) and isinstance(
                                                item.event_definition,
                                                DurationTimerEventDefinition,
                                            ):
                                                timer_event = item.event_definition
                                                timer_expression = (
                                                    timer_event.expression
                                                )  # Extract the expression attribute
                                                if (
                                                    timer_expression
                                                ):  # Only include if timer expression is present
                                                    event = {
                                                        "type": "timer",
                                                        "expression": timer_expression,
                                                        "task_id": self.id,  # Include task ID
                                                    }
                                                    timer_events.append(event)

        return timer_events

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
