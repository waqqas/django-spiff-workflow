from typing import Iterable, List

from django.db import models
from SpiffWorkflow.workflow import Workflow as SpiffWorkflow

from ims.models import ModelBase

from .iterators import Task, TaskIterator
from .parsers.parser import create_parser, create_serializer
from .runner import SimpleBpmnRunner
from .script_engine import create_script_engine


class WorkflowBase(ModelBase):
    state = models.TextField(null=True, default=None, blank=True)
    is_started = models.BooleanField(default=False)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["is_started"]),
        ]

    @property
    def is_completed(self):
        return self.runner.is_completed()

    @property
    def tasks(self) -> Iterable[Task]:
        return TaskIterator(
            self.runner.workflow, SpiffWorkflow.get_tasks_iterator(self.runner.workflow)
        )

    @property
    def manual_ready_tasks(self) -> List[Task]:
        return [t for t in self.tasks if t.is_manual and t.is_ready]

    @property
    def ready_tasks(self) -> List[Task]:
        return [t for t in self.tasks if t.is_ready]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.runner = SimpleBpmnRunner(
            parser=create_parser(),
            serializer=create_serializer(),
            script_engine=create_script_engine(self.get_apis()),
        )
        if self.state:
            self.deserialize()

    def __str__(self):
        return f"Workflow {self.id}"

    def parse(self, *args, **kwargs):
        self.runner.parse(*args, **kwargs)

    def deserialize(self):
        self.runner.deserialize(self.state)

    def serialize(self):
        self.state = self.runner.serialize()

    def catch(self, event):
        self.runner.catch(event)

    def advance(self, user=None):
        lane = user.current_group.name if user and user.current_group else None
        self.runner.advance(lane)
        self.runner.refresh_tasks()

    def save(self, *args, **kwargs) -> None:
        if not self.state:
            self.parse()
        self.serialize()

        return super().save(*args, **kwargs)

    def get_task_from_id(self, task_id) -> Task:
        return Task(self.runner.workflow, self.runner.get_task_from_id(task_id))

    def get_task_from_spec_name(self, name) -> Task:
        return Task(self.runner.workflow, self.runner.get_tasks_from_spec_name(name))

    def get_ready_tasks(self, lane) -> List[Task]:
        return [
            Task(self.runner.workflow, task)
            for task in self.runner.get_ready_tasks(lane)
        ]

    def get_waiting_tasks(self) -> List[Task]:
        return [
            Task(self.runner.workflow, task) for task in self.runner.get_waiting_tasks()
        ]

    def get_catching_tasks(self) -> List[Task]:
        return [
            Task(self.runner.workflow, task)
            for task in self.runner.get_catching_tasks()
        ]

    def cancel(self):
        self.runner.cancel()

    def get_apis(self):
        return {}
