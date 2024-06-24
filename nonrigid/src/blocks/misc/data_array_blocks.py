import os

from core.pipeline_block import PipelineBlock
from core.log import Log
from core.exceptions import SampleProcessingException
import utils.vtkutils as vtkutils

class RemapArraysBlock(PipelineBlock):
    """
    """

    def __init__(self, geometry_input, data_input,
            output_filename="displacement.vtu"):

        self.output_filename = output_filename
        self.geometry_input = geometry_input
        self.data_input = data_input

        inputs = [self.geometry_input, self.data_input]
        outputs = [self.output_filename]
        super().__init__(inputs, outputs)

    def run(self, sample):
        try:
            geometry, data = read_geometry_and_data(sample, self.geometry_input, self.data_input)
        except AssertionError as e:
            raise SampleProcessingException(self, sample, f"Loading inputs failed: {e}")

        result = vtkutils.remap_arrays( geometry, data )

        sample.write(self.output_filename, result)

class CopyArraysBlock(PipelineBlock):
    """
    """

    def __init__(self, geometry_input, data_input,
            output_filename="displacement.vtu"):

        self.output_filename = output_filename
        self.geometry_input = geometry_input
        self.data_input = data_input

        inputs = [self.geometry_input, self.data_input]
        outputs = [self.output_filename]
        super().__init__(inputs, outputs)

    def run(self, sample):

        try:
            geometry, data = read_geometry_and_data(sample, self.geometry_input, self.data_input)
        except AssertionError as e:
            raise SampleProcessingException(self, sample, f"Loading inputs failed: {e}")

        result = vtkutils.copy_arrays( geometry, data )

        sample.write(self.output_filename, result)

def read_geometry_and_data(
        sample,
        geometry_input: str,
        data_input: str
) -> (object, object):
    """Utility for reading geometry and data input somewhat robustly for CopyArraysBlock and RemapArraysBlock."""

    geometry_list = list(sample.read_all(geometry_input))
    assert len(geometry_list) > 0, f"Could not load mesh from file {geometry_input}"
    assert len(geometry_list) <= 1, f"Expected one file matching {geometry_input}, found {len(geometry_list)}"
    geometry = geometry_list[0][1]

    data_list = list(sample.read_all(data_input))
    assert len(data_list) > 0, f"Could not load mesh from file {data_input}"
    assert len(data_list) <= 1, f"Expected one file matching {data_input}, found {len(data_list)}"
    data = data_list[0][1]

    return geometry, data

