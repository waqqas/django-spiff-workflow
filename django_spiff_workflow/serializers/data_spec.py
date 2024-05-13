from SpiffWorkflow.bpmn.serializer.helpers.spec import BpmnDataSpecificationConverter

from ..stores import ModelDataStoreSpecification


class ModelDataStoreReferenceConverter(BpmnDataSpecificationConverter):
    def __init__(self, registry):
        super().__init__(ModelDataStoreSpecification, registry)
