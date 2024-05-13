from SpiffWorkflow.bpmn.specs.data_spec import BpmnDataStoreSpecification


class ModelDataStoreSpecification(BpmnDataStoreSpecification):
    def get(self, my_task, **kwargs):
        raise NotImplementedError

    def set(self, my_task, **kwargs):
        raise NotImplementedError
