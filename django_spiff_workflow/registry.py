from datetime import date

from SpiffWorkflow.bpmn.serializer.helpers.registry import DefaultRegistry


def create_registry():
    registry = DefaultRegistry()
    registry.register(
        date,
        lambda v: {"value": v.isoformat()},
        lambda v: date.fromisoformat(v["value"]),
    )
    return registry
