import os
import re
from typing import List, Callable

from core.pipeline_block import PipelineBlock
from core.log import Log
from core.exceptions import SampleProcessingException
import core.io

class CopyFilesBlock(PipelineBlock):

    def __init__(
            self,
            path: str,
            input_file_pattern: str = "",
            output_file_pattern: str = "",
            distribute: bool = False,
            process: Callable[[str, str], List[List[str]]] = None
            ):
        """ Copy files from 'path' into all sample folders.

        This block will copy pre-existing data from a given location into the sample
        folders. If a folder is given, it will match contained files against
        input_file_pattern to determine which files to copy.

        Note: If input_file_pattern and output_file_pattern are given, they should have the
            same extension.

        Args:
            path: Path to a single file, or a directory. In case of a file, only this file
                is copied to each sample directory. In case of a directory, the directory is
                traversed recursively and all files matching the file names in file_patterns
                are copied.
            input_file_pattern: If path is a directory, determines which files in the
                directory should be processed.
            output_file_pattern: Name of the copied files. Defaults to the
                name of the input file unless manipulated by a process function.
            distribute: If False, the file at path will be copied into each sample. If True,
                files will be traversed and successively be copied into different
                sample, respectively. Source file name is tracked as a config value.
            process: Function that processes data before it is copied. Needs to accept
                the input filename and the output file pattern and return a nested list of
                [[output_filename, output_data]].

        """

        assert os.path.exists(path), f"Cannot copy files from '{path}', doesn't exist!"

        # 'inputs' will stay empty. The inputs used here are not from pipeline samples,
        # so they are otherwise ignored by the pipeline and do not need to be passed to the
        # PipelineBlock parent class.
        inputs = []
        # 'outputs' will be filled below, depending on the inputs:
        outputs = []

        files_found = []

        if os.path.isdir( path ):
            assert len( input_file_pattern ) > 0 and len(output_file_pattern), \
                    "When 'path' is a directory, input_file_pattern and output_file_pattern " +\
                    "must be given!"
            for root, dirs, files in os.walk(path):
                dirs.sort() # sort in-place to influence further processing by os.walk
                files.sort() # sort for consistent order
                # Iterate over every file found:
                for f in files:
                    # Check if the file matches the input pattern:
                    if re.match(input_file_pattern,f):
                        files_found.append( {
                            "path":root, 
                            "filename":f,
                            } )
            self.output_file_pattern = output_file_pattern
            assert len( files_found ) > 0, \
                    f"No files matching {input_file_pattern} found in {path}!"
        else:
            root, f = os.path.split( path )
            files_found.append( {
                "path":root,
                "filename":f,
                } )
            if len(output_file_pattern) > 0:
                self.output_file_pattern = output_file_pattern
            else:
                self.output_file_pattern = f
        
        outputs.append(self.output_file_pattern)

        # Check that we won't create multiple files in the same output directory with the
        # same name:
        assert distribute or len( files_found ) == 1, \
                    "Found multiple input files, but 'distribute' is False, so they " +\
                    "would all be written as {output_filename} into the same sample " +\
                    "folder. Enable 'distribute' or consider using multiple " +\
                    "CopyFilesBlocks with different 'input_file_pattern's."

        super().__init__(inputs, outputs)

        self.files = files_found
        self.distribute = distribute
        self.process = process

    def run(self, sample):

        if not self.distribute:
            # Copy the file into the sample directory
            for file_entry in self.files:   # Should only be one entry!
                # Reconstruct input path:
                file_path = os.path.join( file_entry["path"], file_entry["filename"] )
                self.copy(sample, file_path)
        else:
            # Select a single entry according to the sample's ID:
            entry_id = sample.id % len( self.files )
            file_entry = self.files[entry_id]
            # Reconstruct input path:
            file_path = os.path.join( file_entry["path"], file_entry["filename"] )
            self.copy(sample, file_path)
        # Save data provenance
        sample.set_config_value(self, "data_source", file_path)

    def copy(self, sample, file_path):
        """ Read input data at file_path, optionally process it and
        write it to the sample.
        """
        # Process data if desired
        if self.process:
            # process function needs to take care of data reading, processing
            # and output naming
            # should return a nested list of [[output_filename, output_data]]
            named_data = self.process(file_path, self.output_file_pattern)
            for filename, data in named_data:
                sample.write(filename, data)
        else:
            # Read the data:
            data = core.io.read(file_path)
            # Write the data back for this sample:
            sample.write(self.output_file_pattern, data)

