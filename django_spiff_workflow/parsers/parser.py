from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer
from SpiffWorkflow.spiff.parser.process import SpiffBpmnParser
from SpiffWorkflow.spiff.serializer.config import SPIFF_CONFIG

from ..registry import create_registry
from ..stores import ModelDataStoreSpecification


class DjangoSpiffBpmnParser(SpiffBpmnParser):
    DATA_STORE_CLASSES = {
        "model_store": ModelDataStoreSpecification,
    }


def create_serializer():
    # SPIFF_CONFIG["data_specs"].append(ModelDataStoreReferenceConverter)
    wf_spec_converter = BpmnWorkflowSerializer.configure(
        SPIFF_CONFIG, registry=create_registry()
    )
    return BpmnWorkflowSerializer(wf_spec_converter)


def create_parser():
    parser = DjangoSpiffBpmnParser()

    return parser
