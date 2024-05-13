from SpiffWorkflow.bpmn.util.task import BpmnTaskFilter
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.task import TaskState


class SimpleBpmnRunner:
    def __init__(self, parser, serializer, script_engine=None, handlers=None):
        self.parser = parser
        self.serializer = serializer
        self.script_engine = script_engine
        self.handlers = handlers or {}
        self.workflow = None

    def parse(self, name, bpmn_files, dmn_files=None, collaboration=False):
        self.parser.add_bpmn_files(bpmn_files)
        if dmn_files:
            self.parser.add_dmn_files(dmn_files)

        if collaboration:
            top_level, subprocesses = self.parser.get_collaboration(name)
        else:
            top_level = self.parser.get_spec(name)
            subprocesses = self.parser.get_subprocess_specs(name)
        self.workflow = BpmnWorkflow(
            top_level, subprocesses, script_engine=self.script_engine
        )

    def deserialize(self, json_data):
        self.workflow = self.serializer.deserialize_json(json_data)
        if self.script_engine is not None:
            self.workflow.script_engine = self.script_engine

    def serialize(self) -> str:
        return self.serializer.serialize_json(self.workflow)

    def get_task_description(self, task, include_state=True):
        task_spec = task.task_spec
        lane = f"{task_spec.lane}" if task_spec.lane is not None else "-"
        name = task_spec.bpmn_name if task_spec.bpmn_name is not None else "-"
        description = (
            task_spec.description if task_spec.description is not None else "Task"
        )
        state = f"{task.get_state_name()}" if include_state else ""
        return f"[{lane}] {name} ({description}: {task_spec.bpmn_id}) {state}"

    def advance(self, lane=None):
        engine_tasks = [t for t in self.get_ready_tasks(lane) if not t.task_spec.manual]
        while len(engine_tasks) > 0:
            for task in engine_tasks:
                task.run()
            self.workflow.refresh_waiting_tasks()
            engine_tasks = [
                t for t in self.get_ready_tasks(lane) if not t.task_spec.manual
            ]

    def refresh_tasks(self):
        self.workflow.refresh_waiting_tasks()

    def is_completed(self):
        return self.workflow.is_completed()

    def get_tasks(self, task_state):
        return self.workflow.get_tasks(task_state)

    def get_task_from_id(self, task_id):
        return self.workflow.get_task_from_id(task_id)

    def get_task_from_spec_name(self, name):
        return self.workflow.get_task_from_spec_name(name)

    def get_ready_tasks(self, lane=None):
        """Returns a list of tasks that are READY for user action"""
        return [
            t
            for t in self.workflow.get_tasks(
                task_filter=BpmnTaskFilter(state=TaskState.READY)
            )
            if t.task_spec.lane == lane or t.task_spec.lane is None
        ]

    def get_waiting_tasks(self):
        return self.workflow.get_waiting_tasks()

    def get_catching_tasks(self):
        return self.workflow.get_waiting_tasks()

    def cancel(self):
        return self.workflow.cancel()

    def catch(self, event):
        return self.workflow.catch(event)
