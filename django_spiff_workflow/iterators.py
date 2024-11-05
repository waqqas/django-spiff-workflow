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
    def __init__(self, workflow: BpmnWorkflow, task: SpiffBpmnTask, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.workflow = workflow
        self.task = task
        # Save task information immediately when the Task object is created
        self.info = self.get_info()

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
                    for attr in dir(input_item):
                        if not attr.startswith("_"):
                            value = getattr(input_item, attr)
                            if isinstance(value, list):
                                for item in value:
                                    if isinstance(item, BoundaryEvent):
                                        if hasattr(item, "event_definition") and isinstance(
                                                item.event_definition, SignalEventDefinition):
                                            signal_event = item.event_definition
                                            signal_ref = signal_event.name
                                            button_label = item.extensions.get("signalButtonLabel")
                                            if button_label:
                                                event = {
                                                    "signal": signal_ref,
                                                    "button_label": button_label,
                                                    "task_id": self.id,
                                                }
                                                events.append(event)
        return events

    @property
    def timer_boundary_events(self):
        timer_events = []
        task_spec = self.task.task_spec

        if hasattr(task_spec, "inputs"):
            inputs = getattr(task_spec, "inputs", [])
            for input_item in inputs:
                if isinstance(input_item, BoundaryEventSplit):
                    for attr in dir(input_item):
                        if not attr.startswith("_"):
                            value = getattr(input_item, attr)
                            if isinstance(value, list):
                                for item in value:
                                    if isinstance(item, BoundaryEvent):
                                        if hasattr(item, "event_definition") and isinstance(
                                                item.event_definition, DurationTimerEventDefinition):
                                            timer_event = item.event_definition
                                            timer_expression = timer_event.expression
                                            if timer_expression:
                                                event = {
                                                    "type": "timer",
                                                    "expression": timer_expression,
                                                    "task_id": self.id,
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
        filename = self.task.task_spec.extensions.get("properties", {}).get("formJsonSchemaFilename")
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

    def __str__(self):
        return self.description

    def get_info(self) -> dict:
        from workflow.models import TaskInfo
        """Retrieve the lane name, user_id, and workflow_id from the task."""
        lane = self.task.task_spec.lane if hasattr(self.task.task_spec, "lane") else None
        user_id = self.task.data.get("user_id") if hasattr(self.task, "data") else None
        workflow_id = self.task.data.get("workflow_id") if hasattr(self.task, "data") else None

        # Check if workflow_id is missing
        if workflow_id is None:
            return {
                "message": "workflow_id is missing. Task information was not saved.",
                "lane": lane,
                "user_id": user_id,
                "workflow_id": workflow_id,
            }

        # Check if the last task in this workflow has the same lane
        last_task = TaskInfo.objects.filter(workflow_id=workflow_id).order_by('-created_at').first()
        if last_task and last_task.lane == lane:
            return {
                "message": f"The lane '{lane}' is already the last recorded lane for workflow '{workflow_id}'.",
                "lane": lane,
                "user_id": user_id,
                "workflow_id": workflow_id,
            }

        # Save data to TaskInfo model if it doesn't exist consecutively
        TaskInfo.objects.create(
            workflow_id=workflow_id,
            lane=lane,
            user_id=user_id,
        )
        return {
            "lane": lane,
            "user_id": user_id,
            "workflow_id": workflow_id,
        }


    def run(self):
        self.task.run()
        print(self.info)
        return self.info

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
