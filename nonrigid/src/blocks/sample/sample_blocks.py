
from core.pipeline_block import PipelineBlock
from core.log import Log
from core.exceptions import SampleProcessingException

class SampleBlock1(PipelineBlock):
    """
    Testing some I/O, exceptions and validation.
    Sample 0: no problems
    Sample 1: does not pass validation
    Sample 2: raises processing error
    Sample 3: raises processing error and does not pass validation
    """

    def __init__(self):
        inputs = []
        outputs = ["test.yaml"]
        super().__init__(inputs, outputs)

    def run(self, sample):

        sample.write("test.yaml", {"DATA":sample.id})
        sample.add_statistic(self, "mod3", sample.id % 3)
        sample.add_statistic(self, "plus3", sample.id + 3)
        sample.set_config_value(self, "id", sample.id)
        sample.set_config_value(self, "eps-minus-id", 0.3-sample.id )
        sample.add_statistic(self,key="id_plus_three", value=(sample.id+3))
        #msg = f"Running SampleBlock on sample {sample.id}"
        #Log.log(module="SampleBlock", msg=msg)
        if sample.id == 2:
            raise SampleProcessingException(self, sample, "Testing exceptions - refusing to parse sample with ID == 2")
        elif sample.id == 3:
            raise SampleProcessingException(self, sample, "Testing exception combination with validation - refusing to "
                                                          "parse sample with ID == 3")

    def validate_sample(self, sample):
        if sample.id == 1:
            return False, "Sample 1: validation failed because I want it to. Testing validation exception on its own"
        elif sample.id == 3:
            return False, "This should not appear anywhere. Testing validation problem in combination with a" \
                          " processing error"
        else:
            return True, ""

class SampleBlock2(PipelineBlock):

    def __init__(self):
        inputs = ["test.yaml"]
        outputs = ["test_2.yaml"]
        super().__init__(inputs, outputs)

    def run(self, sample):

        data_list = list(sample.read_all(self.inputs[0]))
        if len(data_list) == 0:
            raise SampleProcessingException(self, sample,
                    f"Could not load mesh from file {self.inputs[0]}")
        elif len(data_list) > 1:
            raise SampleProcessingException(self, sample,
                    f"Expected one file matching {self.inputs[0]}, found {len(data_list)}")
        else:
            data = data_list[0][1]

        data["DATA2"] = f"additional info {sample.id*2}"

        sample.write(self.outputs[0], data)

        sample.set_config_value(self, "2-plus-id", 2+sample.id)

        #msg = f"Running SampleBlock on sample {sample.id}"
        #Log.log(module="SampleBlock", msg=msg)

