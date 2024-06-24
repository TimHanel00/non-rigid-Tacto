from typing import List     # should only be required in python3.8 and earlier

from core.log import Log
from core.datasample import DataSample
import core
from core.exceptions import SampleProcessingException

class PipelineBlock():
    """
    This class is a base class for all pipeline functions.
    To add some functionality to the pipeline, subclass
    this class and overwrite the relevant methods.
    """

    def __init__(
        self,
        inputs: List[str],
        outputs: List[str],
        optional_outputs: List[str] = [],
    ) ->None:
        """Init function for a PipelineBlock.
        
        When inheriting from this class, you must call this base constructor and pass
        the names of the inputs and outputs which the block expects (or produces).

        Args:
            inputs: A list of filenames which the PipelineBlock requires to already be
                present, in order to run correctly. May contain regex, which will be
                matched via :meth:`re.match`.
            outputs: A list of filenames which the PipelineBlock will definitely generate,
                if run successfully. May contain regex, which will be matched via
                :meth:`re.match` by later blocks.
            optional_outputs: A list of filenames for files that may be produced, but
                aren't necessarily produced for every sample.
        """
        self._id = None
        self._type_id = None
        self._inputs = inputs
        self._outputs = outputs
        self._optional_outputs = optional_outputs

    def set_block_id(
        self,
        id: int,
        type_id: int 
    ) ->None:
        """Sets the unique ids of the block in the pipeline.

        Should not be called manually.
        
        Args:
            _id: Unique ID for every block. Starts at zero and counts along the
                pipeline until the last block (N-1).
            _type_id: ID that counts blocks of the same type. For example: If two
                blocks of the same type are created in the pipeline, type_id ID will be 
                0 for the first and 1 for the second.
        """

        self._id = id
        self._type_id = type_id

    def run(
        self,
        sample: DataSample,
    ) ->None:
        """Runs this block on a given sample. 
        
        Note: subclasses _must_ re-implement this!
        
        Args:
            sample:

        Raises:
            NotImplementedError
        """
        Log.log(module="PipelineBlock", severity="FATAL",
            msg="PipelineBlock's subclasses must implement the run() method!")
        raise NotImplementedError

    @property
    def inputs(
        self
    ) ->None:
        if hasattr(self, '_inputs'):
            return self._inputs
        # If the inputs were not found, then the subclass is doing something wrong!
        msg = f"The block of type {type(self)} has no inputs defined.\n\t" +\
            "When subclassing PipelineBlock, you must call the PipelineBlock.__init__ " +\
            "function in your __init__, for example like this:\n\t" + \
            "super().__init__(inputs, outputs)\n\t" +\
            "If your block doesn't need inputs, 'inputs' may be an empty list ([])."
        Log.log(module="PipelineBlock", severity="FATAL", msg=msg)
        raise NotImplementedError

    @property
    def outputs(
        self
    ) ->None:
        if hasattr(self, '_outputs'):
            return self._outputs
        # If the inputs were not found, then the subclass is doing something wrong!
        msg = f"The block of type {type(self)} has no outputs defined.\n\t" +\
            "When subclassing PipelineBlock, you must call the PipelineBlock.__init__ " +\
            "function in your __init__, for example like this:\n\t" + \
            "super().__init__(inputs, outputs)\n\t" +\
            "If your block doesn't need inputs, 'inputs' may be an empty list ([])."
        Log.log(module="PipelineBlock", severity="FATAL", msg=msg)
        raise NotImplementedError

    @property
    def optional_outputs(
        self
    ) ->None:
        if hasattr(self, '_optional_outputs'):
            return self._optional_outputs
        # If the inputs were not found, then the subclass is doing something wrong!
        msg = f"The block of type {type(self)} has no optional outputs defined.\n\t" +\
            "When subclassing PipelineBlock, you must call the PipelineBlock.__init__ " +\
            "function in your __init__, for example like this:\n\t" + \
            "super().__init__(inputs, outputs, optional_outputs=optional_outputs)"
        Log.log(module="PipelineBlock", severity="FATAL", msg=msg)
        raise NotImplementedError

    def __str__(
        self
    ) ->str:
        return f"{self.unique_name} (ID: {self._id})"

    @property
    def unique_name(
            self
    ) -> str:
        """ Produce a unique name for this block, by appending an ID. """
        
        name = type(self).__name__  # Name of the specific subclass
        name += f"_{self._type_id}"
        return name

    def validate_sample(self, sample:DataSample) -> (bool, str):
        """
        Determine if a sample is processable after the actions performed by the block.

        Check for semantic issues with the sample, not processing errors (these are raised
        in run()).
        The definition of "processable" depends on the block. A sample can be considered not
        processable, for example, if triangles in the mesh become too big after a
        deformation block or if the displacements generated by a displacement block are
        larger than desired/not realistic.
        """
        # log(module="PipelineBlock", severity="INFO",
        #    msg=f"For the block of type {type(self)} no sample validation function has been implemented.")
        return True, ""



