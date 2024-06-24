import os
import hashlib
import random
import re
from typing import List, Optional, Union, Dict, Any, Generator, Tuple

import copy
import natsort
import vtk

from vtkmodules import vtkCommonDataModel

from core.log import Log
import core.io
from core.exceptions import SampleProcessingException
from core.objects.baseobject import BaseObject
import utils.conversions

class DataSample():
    """
    This class is responsible for reading and writing data for a single given sample.
    Reading and writing into a sample folder should only be done through instances of this
    class.
    In this way, the class can keep a state for each file and track whether a block
    needs to be called in order to update it or whether it's still up to date (all still
    on the TODO list).

    WARNING: If the pipeline is aborted or a sample fails to process then some files in the
    directory may remain in an invalid state.
    """

    def __init__(
        self, 
        path: str, 
        int_id: int, 
        cache_data: bool = True,
    ):
        """ 

        Args:
            path: Path to the folder in which all of this sample's files will be stored.
                Usually contains the ID of the sample.
            int_id: The ID of the sample as a positive, unique integer
            cache_data: Set to True if you want to use caching. If enabled, the read() and 
                write() functions will work slightly different - they'll never write to disk
                and only read from disk if the data has not been cached by a previous write()
                call.
                Note: If cache_data is on, :meth:`DataSample.flush_data` _must_ be called
                after the sample is finished processing. This should be handled by the
                Pipeline and the Dataset.
                See also DataSample.read() and DataSample.write() functions.
                For debugging purposes, we recommend switching this off (cache_data=False).
        """

        self.id = int_id
        self.path = path
        self.cache_data = cache_data

        # The list index is later filled with an index which will make it easier to re-find
        # this sample in the dataset:
        self.dataset_list_index = -1

        self._cache = {}

        self.issues_filename = "issues.log"
        self.processing_errors = []

        # This will be set to True if there are issues encountered during processing
        self._has_issues = False

        # Check if we had any issues in the previous run:
        self._had_prev_issues = False
        issues = self.prev_issues
        if issues and len(issues) > 0:
            self._had_prev_issues = True


        self._log_filename = "log.log"
        self._statistics_filename = "statistics.yaml"
        self._config_filename = "config.yaml"

        # Note that if there's a log file from a previous run, then this will _not_
        # be automatically cleared. Only if "write_log()" is called.
        self.cleared_previous_log = False

        # Initialize config. Load any previous config if possible:
        self._config = {}
        self.load_config()

        # Initialize statistics. Load any previous statistics if possible:
        self._statistics = {}
        self._load_statistics()

        self._random = random.Random(self.id)

        self.scene_objects = []

    def set_successfully_processed(
        self,
        block: "PipelineBlock"
    ) -> None:
        """ Mark the sample  as having been processed successfully by the block """

        filename = f"Successful_{block.unique_name}.log"
        self.write( filename, "", cache=False )

    def get_successfully_processed(
        self,
        block: "PipelineBlock"
    ) -> None:
        """ See if this block has already sucessfully run (processing _and_ validation!) on this sample.
       
        Intended as a check whether this block needs to run on this sample, or whether a previous run
        has already successfully completed this block for this sample.
        However, the success could stem from a previous run or the current one.
        """
        
        filename = f"Successful_{block.unique_name}.log"
        return self.has_files( [filename] )

    def clear_successfully_processed(
        self,
        block: "PipelineBlock"
    ) -> None:
        """ Make sure the block is no longer marked as successful for this sample """
        filename = f"Successful_{block.unique_name}.log"
        self.clear_files([filename])

    def sample_scene_objects(
        self,
        scene_object_factories: list
    ) ->None:

        # Clear any previous config variables:
        sample.clear_config( self )

        for factory in scene_object_factories:
            obj = factory.produce( self )
            # If 'ex_likelihood' is lower than one, it's possible that the object is not
            # created and None is returned. Otherwise, append to list of objects for 
            # this sample:
            if obj is not None:
                self.scene_objects.append( obj )

    def get_scene_objects(
        self
    ) ->List[BaseObject]:
        """ Retrieve the scene objects for this sample

        Note: Before this list is valid, sample_scene_objects() must have been called
            (done automatically be the Pipeline class)
        """

        return self.scene_objects

    def _insert_value( self,
        dictionary: dict,
        block: "PipelineBlock",
        key: str,
        value: "Pickable Object",
        category_key: Optional[str]=None,
    ) ->None:
        """ Internal function for inserting a value into (nested) config or stats dicts.

        Args:
            dictionary: The dict in which to insert the data. Should be either
                self._config or self._statistics.
            block: The :class:`PipelineBlock` in/for which the value was chosen
            key: Unique name (within this block) for the config value
            value: Any value you want to store. This must be pickable, as it will
                be written to a file later on.
            category_key: Optional sub-category under which to store the value. This
                should be used when writing config values for scene objects, by
                passing the scene object filename, but can also be used for other
                sub-categories if needed.
        """
        block_name = DataSample.key_for_object( block )

        if not block_name in dictionary:
            dictionary[block_name] = {}

        if category_key is not None:
            if not category_key in dictionary[block_name]:
                dictionary[block_name][category_key] = {}
            
            if key in dictionary[block_name][category_key]:
                Log.log(severity="WARN", msg=f"Parameter {block_name}|{category_key}|{key} was already set. Not overwriting.", 
                        module="DataSample")
            else:
                dictionary[block_name][category_key][key] = value
        else:
            if key in dictionary[block_name]:
                Log.log(severity="WARN", msg=f"Parameter {block_name}|{key} was already set. Not overwriting.", 
                        module="DataSample")
            else:
                dictionary[block_name][key] = value

    def _get_item( self,
        dictionary,
        block: "PipelineBlock", 
        key: str,
        category_key: Optional[str] = None,
    ) -> "PickableObject":
        """ Internal function for accessing config or statistics.

        Note: Should not be called by users. Instead, call get_config_value or
            get_statistics.
        """

        block_name = DataSample.key_for_object( block )

        if not block_name in dictionary.keys():
            raise KeyError(f"No entry for {block_name}|{key}!")
        
        if category_key is not None:
            return dictionary[block_name][category_key][key]
        else:
            return dictionary[block_name][key]

    def set_config_value(
        self,
        block: "PipelineBlock",
        key: str,
        value: "Pickable Object",
        category_key: Optional[str]=None,
    ) ->None:
        """
        Specify a certain config value that you chose for this :class:`DataSample`.

        The main purpose of this function is to store config values so that one
        can later reproduce what happened with this sample. If you want to write
        a value for a subsequent statistical analysis, use
        :meth:`DataSample.add_statistic` instead, which is conceptually similar,
        but is meant for result values rather than chosen input values.

        The config values can be retrieved using :meth:`DataSample.get_config_value`.

        Args:
            block: The :class:`PipelineBlock` in/for which the value was chosen. Note:
                in rare occasions, this can be an instance of a non-PipelineBlock class.
            key: Unique name (within this block) for the config value
            value: Any value you want to store. This must be pickable, as it will
                be written to a file later on.
            category_key: Optional sub-category under which to store the value. This
                should be used when writing config values for scene objects, by
                passing the scene object filename, but can also be used for other
                sub-categories if needed.

        Note: When passed a tuple as 'value', this function will turn the tuple
            into a list.
        """

        if isinstance(value, tuple):
            value = list(value)

        self._insert_value( self._config, block, key, value, category_key )

    def get_config_value(
        self, 
        block: "PipelineBlock", 
        key: str,
        category_key: Optional[str] = None,
    ) -> "PickableObject":
        """ Retrieve a previously added config value.

        Args:
            block: Either an instance of a PipelineBlock or the class name of the
                block for which the value was previously written.
            key: The unique name for the config value to retrieve
            category_key: Optional name of the sub-category. This is mostly used
                when getting config values for a specific scene object, in which
                case the scene object's filename should be passed.
        Returns:
            The value, if present, otherwise raises a KeyError.
        """
        return self._get_item( self._config, block, key, category_key )

    def save_config(
        self
    ) ->None:
        """Writes the config values to file. Should be handled by the pipeline.
        """
        if self.cache_data:
            self._cache[self._config_filename] = self._config
        else:
            f = os.path.join(self.path, self._config_filename)
            core.io.write(f, self._config)

    def load_config(
            self
    ) -> None:
        """Load config from previous run.
        """

        # Load any previous config values if possible:
        c = self._read(self._config_filename)
        if c is not None:
            self._config = c

    def add_statistic(
        self,
        block: "PipelineBlock",
        key: str,
        value: "Pickable Object",
        category_key: Optional[str]=None,
    ) ->None:
        """
        Add a value which will end up in the DataSet's statistics.

        Note:
            Where possible, all DataSamples should have the same statistics written to them!

        Args:
            block: The PipelineBlock which calculated this statistics. Will be used to 
                group values and identify them uniquely. Note: in rare occasions, this
                can be an instance of a non-PipelineBlock class.
            key: Unique name for this statistic. For example: 'max_displacement' or
                'root_mean_square_error'.
            value: Any number (or string)
            category_key: Optional sub-category in which to place the value.
        """
        self._insert_value( self._statistics, block, key, value, category_key )

    def get_statistic(
        self, 
        block: "PipelineBlock", 
        key: str,
        category_key: Optional[str] = None,
    ) -> "PickableObject":
        """ Retrieve a previously added statistics value.

        Args:
            block: Either an instance of a PipelineBlock or the class name of the
                block for which the value was previously written.
            key: The unique name for the config value to retrieve
            category_key: Optional name of the sub-category. This is mostly used
                when getting values for a specific scene object, in which
                case the scene object's filename should be passed.
        Returns:
            The value, if present, otherwise raises a KeyError.
        """
        return self._get_item( self._statistics, block, key, category_key )



    def add_timing(
        self,
        block: "PipelineBlock",
        time: float
    ) -> None:
        """
        Record time taken for a particular block.

        Note: time will be saved in statistics!

        Args:
            block: PipelineBlock which was timed.
            time: Time in seconds it took to run the block on this sample.
        """
        self._insert_value( self._statistics, block, "Timing", time )

    def save_statistics(
        self,
    ) ->None:
        """
        Store the statistics at the end. Should not be called by the user.
        """
        if self.cache_data:
            # filename handling like in write()
            # when flushing, self.path is prepended
            self._cache[self._statistics_filename] = self._statistics
        else:
            f = os.path.join(self.path, self._statistics_filename)
            core.io.write(f, self._statistics)

    def _load_statistics(
            self
    ) -> None:
        """Load statistics from previous run.
        """

        # Load any previous config values if possible:
        s = self._read(self._statistics_filename)
        if s is not None:
            self._statistics = s


    def add_processing_error(
        self, 
        exception: SampleProcessingException,
    ) ->None:
        """Let the sample know that there was a processing error (and stop processing it).

        Called when a SampleProcessingException or SampleValidationException is thrown for this sample.

        In both cases, the function records the issue for possible further analysis and
        sets the sample to 'invalid' so that the pipeline knows not to process it further.

        Args:
            exception:
        """
        if exception.delete_block_outputs:
            # for SampleProcessingException:
            # Make sure that this block's outputs are removed - they are no longer valid!
            self.clear_files(
                    exception.pipeline_block.outputs +
                    [self._statistics_filename])
        # else for SampleValidationException:
        # keep outputs for debugging

        error_msg = f"{exception.pipeline_block}: {exception.message}"

        self.processing_errors.append(error_msg)

        f = os.path.join(self.path, self.issues_filename)
        core.io.write(f, self.processing_errors)

        # Also add the error to the normal log:
        self.write_log("Error: " + error_msg)

        # Make sure this sample is not processed further:
        self._has_issues = True

       

    @property
    def processable(
        self
    ) ->bool:
        """ True if the sample can be processed further, False if an issue occurred.

        This property will be set to "False" automatically as soon as a processing
        error is encountered in one of the blocks or when a sample fails the block's
        validation step. In this case, the sample will not be passed on to further
        blocks in the pipeline.

        Returns:
            True if all blocks that ran on and validated this sample in this run
            were successful, False if any of them failed.
        """
     
        return (not self._has_issues)

    @property
    def had_previous_issues(
        self
    ) -> bool:
        """ True if an issue occurred in a previous run, indicated by the existence of
        an issues.log file.

        Utility for dataset analysis decoupled from a current pipeline run. This is needed
        because every datasample is set to processable=True at initialisation of the
        dataset. If only statistics are aggregated in the pipeline run, the sample
        will not be invalidated in that run.

        Returns:
            False if all blocks that ran on this sample in the previous run were successful,
            True if any of them failed.
        """
        return self._had_prev_issues

    def write_log(
        self,
        message:str
    ) ->None:
        """ Append a message to this :class:`DataSample`'s log file.
        """

        # We're trying to write a log message, but there might still be a log from a
        # previous run? Then clear it!
        filename = os.path.join(self.path, self._log_filename)
        if not self.cleared_previous_log:
            if os.path.exists(filename) and os.path.isfile(filename):
                os.remove(filename)     # Remove previous file
            self.cleared_previous_log = True    # Don't clear again!
        
        with open(filename, 'a') as f:
            if isinstance(message, list):
                f.writelines("\n".join(message) + "\n")
            else:
                f.writelines(message)

    def write_log_new_section(
        self,
        section_name:str,
    ) ->None:
        """
        Start a new section in the log file by inserting a section title
        """
        msg = []
        msg.append("")  # empty line
        msg.append("==========================")
        msg.append(section_name)
        msg.append("--------------------------")

        self.write_log(msg)

    def write_log_new_subsection(
        self,
        section_name:str,
    ) ->None:
        """
        Start a new subsection in the log file by inserting a subsection title
        """
        msg = []
        msg.append("")  # empty line
        msg.append("-------------")
        msg.append(section_name)
        msg.append("-------------")

        self.write_log(msg)


    def success(
        self
    ):
        """ Record a successful run of this sample.
        Called when the last block has been successfully run on this sample.
        Deletes any previously recorded errors for this sample and stores the statistics.
        Should not be called manually.
        """

        self._has_issues = False
        self._had_prev_issues = False

        self.clear_files([self.issues_filename])

    def _read(
        self,
        filename : str
    ) ->Union[vtk.vtkDataSet, dict, None]:
        """ 
        Read data from the given file within this :class:`DataSample`'s folder.

        If the DataSample was created with cache_data = True, it will use 
        caching. In this case, if a previous call was made to 
        :meth:`DataSample.write` with the same filename, then this data will
        be returned and no disk I/O will be performed.

        Args:
            filename: Name of the file to read. If this file doesn't exist,
                None will be returned.

        Returns:
            The read content of the file, or None. The type of data returned depends
            on the file extension - a .yaml file will usually return a dict, a .vtu
            file will return a vtk.vtkUnstructuredGrid, a .stl file will return a
            vtk.vtkPolyData and so on. See :mod:`core.io` for details.
        """

        #if not self._valid:
        #    raise RuntimeError("Trying to read() from datasample {self.id}, " +\
        #            "which is no longer valid.")

        if filename in self._cache.keys():
            data = self._retrieve_from_cache(filename)
            return data
        else:
            f = os.path.join(self.path, filename)
            if os.path.exists(f):
                data = core.io.read(f)
                return data
        return None

    def find_matching_files(
        self,
        pattern: str,
    ) ->List[str]:
        """ Finds and returns all files matching the pattern for this sample.

        Will check in the folder, but also in the cache.

        Args:
            pattern: file pattern in the style used by the 're' regex python module

        Returns:
            List of found filenames in alphabetical order. Empty list if nothing matched.

        Will return the files in alphabetical order.
        """
    
        matches = []

        # Get all file names in the sample's folder:
        all_filenames = os.listdir(self.path)
        # Add the cache files:
        if self.cache_data:
            all_filenames += self._cache.keys()
        # Sort the files alphabetically:
        all_filenames = natsort.natsorted(all_filenames)

        for name in all_filenames:
            # Todo: consider using re.fullmatch
            if re.match(pattern, name):
                matches.append( name )

        return matches

    def clear_config( self,
            block
    ) -> None:
        """ Clear all config for a certain block.

        Should be called if a previous block was re-run, because that usually means that
        this block's config and output is no longer valid.

        Args:
            block: Instance who's class-name is used as the key, i.e. the object which
                was previously used when storing config values. This is usually an
                instance of a (subclass of a) PipelineBlock, but doesn't have to be.
        """

        block_name = DataSample.key_for_object( block )
        if block_name in self._config.keys():
            del self._config[block_name]

    def clear_statistics( self,
            block
    ) -> None:
        """ Clear all statistics for a certain block.

        Should be called if a previous block was re-run, because that usually means that
        this block's config and output is no longer valid.
        """

        block_name = DataSample.key_for_object( block )
        if block_name in self._statistics.keys():
            del self._statistics[block_name]


    def read_all(
        self, 
        filename: str,
        id: Optional[str] = None,
        frame: Optional[int] = None,
        all_ids: bool = True,
        all_frames: bool = True,
    ) -> Generator[Tuple[str, Any, str, int, str], None, None]:
        """
        Read all files matching the given filename (and id/frame if provided) in a generator fashion.

        If no frame and/or id are given, read all files matching the filename  with any id and frame.

        Keep in sync with `self.get_formatted_filename`, `self.extract_file_info`, `self.find_last_file`,
        `self.has_files` and `self.get_formatted_filepattern`.

        Args:
            filename: File name that will be looked for. All the files whose filename matches
                the input (potentially including an additional ID and frame) will be read.
            id: Scene object identifier.
            frame: Time frame index in time series.

        Yields:
            name, data, id, frame, base_name
            name: Full name of the matching file, e.g. 'ligament_B_f4.vtu'.
            data: Data loaded from the file.
            id: Scene object identifier extracted from `name`, e.g. 'B'.
            frame: Time frame index extracted from `name`, e.g. 4.
            base_name: Basic file name without extension and without any ID or frame information, e.g. 'ligament'.
        """
        _, base_name, ext = self.get_formatted_filename(filename)
        file_pattern = self.get_formatted_filepattern(f"{base_name}{ext}", id=id, frame=frame,
                                                      all_ids=all_ids, all_frames=all_frames)
        matching_filenames = self.find_matching_files(file_pattern)

        for name in matching_filenames:
            data = self._read(name)
            id, frame = self.extract_file_info(name)
            if data is not None:
                yield name, data, id, frame, base_name

    def write(
        self,
        filename: str,
        data: object,
        cache: bool = True,
        **kwargs
    ) ->str:
        """ Write the object to a file within this :class:`DataSample`'s folder.

        To write the data, a corresponding writer and reader must be available
        to the :mod:`core.io` module. This writer will be picked automatically
        depending on the file type. See the module for details.

        If the DataSample was created with cache_data = True, it will use
        caching. In this case, the data will not be written to disk, but
        will instead stay in memory and subsequent calls to
        :meth:`DataSample.read` will return this cached value.
        At the end of the run, the pipeline will call
        :meth:`DataSample.flush_data`, which writes the files to disk.

        If a scene object ID or time series frame index are provided, they
        are added to the filename automatically. To do this, provide 'id' or 'frame'
        entries through the kwargs.

        Note:
            To disable caching, run the pipeline with --disable_caching.

        Args:
            filename: Name of the file to write to
            data: Corresponding data. Must fit to the extension given in the
                filename, for example a dict could be written to a file
                ending in '.yaml', a vtk.vtkPolyData object could be written
                to a .stl file. See :mod:`core.io` for details.
            id (int): ID of the data to write, if multiple. Will be used in
                creating the full file name.
            frame (int): Frame number of the data to write. Will be used in
                creating the full file name.
            cache: Optionally set this to False on files that always need to
                be written. Should only be used for special files, not for
                normal data. To disable all caching, use the --disable_caching
                command line flag instead.
                Default: True

        Returns:
            filename: Name that the data was saved to, potentially including
                      scene object ID and frame index.
        """

        #if not self._valid:
        #    raise RuntimeError("Trying to write() on datasample {self.id}, " +\
        #            "which is no longer valid.")

        # if id and/or frame are provided, add them to the file name
        if "id" in kwargs or "frame" in kwargs:
            filename, _, _ = self.get_formatted_filename(filename, **kwargs)

        if self.cache_data and cache:
            if isinstance( data, vtk.vtkDataSet ):
                copy = data.NewInstance()
                copy.DeepCopy( data )
                self._cache[filename] = copy
            else:
                self._cache[filename] = data
        else:
            f = os.path.join(self.path, filename)
            core.io.write(f, data)
        return filename

    def __str__(
        self,
    ) ->str:
        """ Returns a string which reflects the state of this DataSample.
        """
        return f"DataSample {self.id} (processable: {self.processable}, " +\
                f"prev. issues: {self._had_prev_issues})"

    def print_state(
        self
    ) ->None:
        """ Print a human-readable state using the :mod:`core.log` module.
        """

        if self.processable:
            Log.log(severity="OK", msg=f"Sample {self.id}", module="DataSample")
        else:
            msg = f"Sample {self.id} encountered errors:"
            for e in self.processing_errors:
                msg += "\n\t" + e
            Log.log(severity="ERROR", msg=msg, module="DataSample")

    @property
    def prev_issues(
        self,
    ) ->List[str]:
        """ Returns a list of issues that were encountered.

        Note: These issues may come from a previous run, not the current one!
            Previous issues are only deleted once the pipeline has run successfully on
            a sample (i.e. DataSample.success() has been called).

        Returns:
            List of strings, each of which an issue that was encountered.
        """

        issues = self._read(self.issues_filename)
        return issues

    @property
    def statistics(
        self
    ) ->dict:
        """ Returns the statistics recorded via :meth:`DataSample.add_statistic`.

        Returns:
            The previously recorded statistics for this DataSample.
        """
        return self._statistics

    @property
    def config(
        self
    ) ->dict:
        """ Returns the config recorded via :meth:`DataSample.set_config_value`.

        Returns:
            The previously recorded config for this DataSample.
        """
        return self._config


    def has_files(
        self,
        filenames: List[str],
    ) ->bool:
        """
        Check if the given files exist for this sample. If yes, it may be possible to skip
        a block, thus saving processing times.

        Note:
            This function uses regex matching (via re.match). This means that if a
            filename is given in the form of a regex, the function will check if *any*
            file exists which matches the regex.
            It also automatically checks for files with a scene object identifier or a
            time series index (similarly to `self.read_all`). Keep in sync with
            `self.get_formatted_filename`, `self.extract_file_info`, `self.find_last_file`,
            `self.read_all` and `self.get_formatted_filepattern`.

        Args:
            filenames:

        Returns:
            True, if all files exists, False if at least one does not exist.
        """
        existing_files = [f for f in os.listdir(self.path)]
        for filename in filenames:
            found = False
            _, base_name, ext = self.get_formatted_filename(filename)
            file_pattern = f"{base_name}(_[A-Z])*(_f[0-9]+)*\\{ext}"

            for ef in existing_files:
                if re.match(filename, ef):
                    found = True
                    break
                elif re.match(file_pattern, ef):
                    found = True
                    break
            if not found:
                return False
        return True

    @property
    def random(
        self,
    ) ->random.Random:
        """ Instance of random.Random(), seeded with the (unique) ID of this sample.

        Use this instead of the random module when sampling random values for this sample.
        This will ensure determinism of the pipeline.
        """
        return self._random

    def clear_files(
        self,
        filenames: List[str],
    ) ->None:
        """ Clear all files matching filenames.

        This function can be used to remove files from a previous run. For example,
        if PipelineBlock1 is run, but there are still results (from a previous run)
        from PipelineBlock2, then the output files of PipelineBlock2 should be deleted
        before running PipelineBlock1.

        Args:
            List of filenames (without path) to clear for this sample

        Note:
            TODO: Use Regex to clear also all files matching a certain string
        """
        for filename in filenames:
            # clear files written to disk
            p = os.path.join(self.path, filename)
            if os.path.exists(p):
                os.remove(p)
            # also remove these files from cache
            if filename in self._cache.keys():
                del self._cache[filename]

    def print_md5sums(
        self
    ):
        for obj in os.listdir(self.path):
            filepath = os.path.join(self.path, obj)
            if os.path.isfile(filepath):
                with open(filepath, 'br') as f:
                    md5sum = hashlib.md5(f.read()).hexdigest()
                    msg = f"{filepath} {md5sum}"
                    Log.log( module="DataSample", msg=msg )

    def flush_data(self,
            filenames:List[str] = None,
            regex: str=None
            ):
        """ When caching is on, call this to force writing of the data to disk.

        Args:
            filenames: If given, flush only these files. Takes precedence over regex.
                       If None (default) and regex is None, flush all files.
            regex: If given, flush only files matching the pattern.
                   If None (default) and filenames is None, flush all files.

        Note: This function also clears the cache of any written files.
        """
        new_cache = {}
        if self.cache_data:
            for filename, data in self._cache.items():
                # Check if this file should be flushed:
                write = False
                if filenames == None and regex is None:   # No filenames or regex given? Flush all files!
                    write = True
                elif filenames:  # Check whether to flush this file based on filename list
                    if filename in filenames:
                        write = True
                elif regex:  # Check whether to flush this file based on regex
                    if re.match(regex, filename):
                        write = True

                if write:
                    f = os.path.join(self.path, filename)
                    Log.log( module="DataSample", msg=f"Flush data: filename {f}" )
                    core.io.write(f, data)
                else:
                    # Keep this data:
                    new_cache[filename] = data

        # Remove flushed data from cache:
        self._cache = new_cache

    def _retrieve_from_cache(
        self,
        filename: str
    ) -> Union[vtk.vtkDataSet, dict]:
        """When caching is on, create a deep copy of an element from the cache before returning it.

        Takes care of different object types for the deep copy. Needs to be kept up to date with object types
        handled by io.py.
        """
        data = self._cache[filename]
        # make a deep copy
        # for vtk objects, copy.deepcopy doesn't work
        if isinstance(data, vtkCommonDataModel.vtkDataObject):
            ret_data = data.__class__()
            ret_data.DeepCopy(data)
            return ret_data
        elif type(data) == dict:
            return copy.deepcopy(data)
        else:
            msg = f"For data of type {type(data)} cache retrieval has not been defined.\n\t" + \
                  "When adding object types to the :mod:`core.io` module, you must define how a " + \
                  "deep copy of the object can be created in :meth:`DataSample._retrieve_from_cache`. " + \
                  "Trying to copy with :meth:`copy.deepcopy`."
            Log.log(module="DataSample", severity="WARN", msg=msg)
            return copy.deepcopy(data)

    @property
    def full_config(
        self
    ) -> dict:
        """ Get all previously set config values.

        Note: If only a few specific values are needed, consider using :meth:`DataSample.get_config_value` instead.

        Returns: A (nested) dictionary of all configuration values associated with the sample.
        """
        return self._config

    @staticmethod
    def key_for_object( o ):
        # Import the PipelineBlock here because importing it at the beginning would introduce
        # an unresolvable circular dependency, and it's only required at this point
        from core.pipeline_block import PipelineBlock

        # Use the block's class name as a key
        if isinstance( o, PipelineBlock ):
            # In case of a pipeline block, make sure to uniquely identify them if there
            # are more than one block of the same type:
            name = o.unique_name
        else:
            # Simply use the class name:
            name = type(o).__name__

        return name



    @staticmethod
    def get_formatted_filename(
            filename: str,
            id: Optional[str] = None,
            frame: Optional[int] = None
    ) -> (str, str, str):
        """ Combine filename, scene object ID and timeseries frame into a new filename.

        Utility to name output files for blocks that produce several
        files of the same type per sample, e.g. time series, while specifying only the umbrella output filename (e.g.
        "deformed.vtu" -> "deformed_f1.vtu", "deformed_f2.vtu", etc. This method ensures that the control of how filenames
        are constructed remains within the data sample that will manage the file.

        Keep in sync with `self.read_all`, `self.extract_file_info`, `self.find_last_file`, `self.has_files` and
        `self.get_formatted_filepattern`.

        Args:
            filename: Umbrella filename for a block's output files including file extension.
            id: Scene object identifier.
            frame: Identifier for the file at the specific time frame. If default None, return filename.

        Returns:
            full_filename, base_name, ext

        """
        name, ext = os.path.splitext(filename)
        # add ID as scene object specifier
        if id is not None:
            assert type(id) == str, f"ID {id} passed to file {filename} has to be a character!"
            assert len(id) == 1, f"ID {id} passed to file {filename} cannot have more than one character!"
            assert id.isupper(), f"ID {id} passed to file {filename} has to be uppercase!"
            id = f"_{id}"
        else:
            id = ""

        # add frame index from time series
        if frame is not None:
            assert type(frame) == int, f"Frame index {frame} passed to file {filename} has to be an integer!"
            frame = f"_f{frame}"
        else:
            frame = ""

        return f"{name}{id}{frame}{ext}", name, ext


    @staticmethod
    def extract_file_info(
            filename: str
    ) -> (str, int):
        """ Extract the ID character and time frame index from a filename that has been constructed with
        `self.get_formatted_filename`.

        Utility to find the ID and time frame of output files from blocks that produce output for several scene objects
        and/or several
        files of the same type per sample, e.g. time series, while specifying only the umbrella output filename (e.g.
        "deformed.vtu" -> "deformed_A_f1.vtu", "deformed_A_f2.vtu", etc.

        Keep in sync with `self.read_all` `self.get_formatted_filename`, `self.find_last_file`, `self.has_files` and
        `self.get_formatted_filepattern`.

        Args:
            filename: Filename of a specific output file identified by ID and frame index as
                      f"{filename_name}_{id}_f{frame}{filename_extension}". This pattern may change.

        Returns:
            id, frame: ID character and time frame index if found. None for either or both otherwise.
        """
        #id_match = re.search(r"_([A-Z]{0-1})[_\.]", filename)  # without specifying trailing . or _ the frame f is matched
        id_match = re.search(r"_([A-Z]+)", filename)  # without specifying trailing . or _ the frame f is matched
        #id_match = re.search(r"_([A-Z]?)[_\.]", filename)  # without specifying trailing . or _ the frame f is matched
        #id_match = re.search(r"_([A-Z]{0-1})[_\.]", filename)  # without specifying trailing . or _ the frame f is matched
        #id_match = re.search(r"_([A-Z]+)", filename)  # without specifying trailing . or _ the frame f is matched
        # if there is an ID, extract it
        if id_match is not None:
            # get rid of decorations used to locate it
            id = id_match.group(1)
        # otherwise return None -> using `self.get_formatted_filename` on this will give the correct result
        else:
            id = None
        # when otherwise numbered filenames come into play, consider using only the last number instead, e.g.
        # last_match = re.findall(r"[0-9]+", filename)[-1]
        frame_match = re.search(r"f([0-9]+)", filename)
        # if an integer is in the filename, extract it
        if frame_match is not None:
            # get rid of decorations used to locate it
            frame = int(frame_match.group(1))
        # otherwise return None -> using `self.get_formatted_filename` on this will give the correct result
        else:
            frame = None

        return id, frame

    def find_last_file(
            self,
            filename: str,
            files: Dict[str, Any] = None,
            id: Optional[str] = None
    ) -> Union[str, None]:
        """ Utility to find the name of the last file of an indexed series (as returned by
        `self.get_formatted_filename`).

        If `files` is provided, find the last file of the indexed series in `files`. Otherwise, read all files
        matching `filename` and find the last file of those. Note that no files are read automatically if `files` is
        passed. If there is both files like "deformed.vtu" and "deformed_f0.vtu", "deformed_f1.vtu", the filename
        containing the highest number will be returned.

        If there is more than one object of a type, this is meant to be used with the ID of a scene object.
        If id is not provided, out of the files with the
        highest frame number over all scene objects matching `filename`, the one alphabetically last will be returned.

        Keep in sync with `self.read_all` `self.get_formatted_filename`, `self.extract_file_info`, `self.has_files`
        and `self.get_formatted_filepattern`.

        Args:
            filename: Name of the file/file group to read/that has been read.
            files: dict of previously read files where keys are the filenames of the loaded files and values are
                   the loaded data.
            id: Scene object identifier.

        Returns:
            Filename of the last file in the indexed series in all files matching `filename` or in `files` (if `files`
            is provided). None if no file matches.

        Todo: add processing of a list returned by the read_all generator besides the dictionary option

        """
        # if files are not provided, read them first
        if files is None:
            files_found = False
            cur_frame = 0
            for name, _, _, frame, _ in self.read_all(filename, id=id):
                files_found = True
                if frame > cur_frame:
                    last_mesh = name
            if not files_found:
                msg = f"Could not find {filename} in files of DataSample {self.id}."
                Log.log(severity="WARN", module="DataSample", msg=msg)
                return None
        # if provided, exclude files that don't match the file pattern
        else:
            name, ext = os.path.splitext(filename)
            filtered_files = {}
            for fname, data in files.items():
                # not using f"{name}.+{ext}" so that if there is only one output without ID, that one can be returned
                if re.match(f"{name}.*{ext}", fname):
                    filtered_files[fname] = data
            files = filtered_files
            if not files:
                msg = f"None of the provided files matches requested {filename} (DataSample {self.id})."
                Log.log(severity="WARN", module="DataSample", msg=msg)
                return None
            # find last file, sorted by frame
            last_mesh = sorted(files, key=lambda fname:
                               self.extract_file_info(fname)[1] if self.extract_file_info(fname)[1] is not None
                               else 0)[-1]

        return last_mesh

    def convert_file(
        self,
        filename_in: str,
        filename_out: str
    ) -> None:
        """Convert between file types. If caching is on, use the cache.

        Can be used to deal with input/output format requirements of different libraries,
        writing only to disk if needed by calling self.flush(filename_out) afterwards.
        """
        # read
        mesh = self.read(filename_in)

        # convert
        # query which data type the writer needs
        out_type = core.io.find_writer_input_type(filename_out)
        # convert into that data type
        mesh_new = utils.conversions.convert(mesh, out_type)

        # if caching is on, put it in cache
        self.write(filename_out, mesh_new)

    def convert_all(
        self,
        filename_in: str,
        ext_out: str,
        id: Optional[str] = None,
        frame: Optional[int] = None,
    ) -> None:
        """
        Converts all files matching the given input filename regex into the filetype described
        by the output extension, preserving the filename before the extension.

        This function works in the same way as DataSample.convert_file() except that it converts
        the content from all files which match the filename regex.

        Args:
            filename_in: File pattern that will be looked for. All files whose filename matches
                the pattern will be converted.
            ext_out: File extension for the desired output file format. The name of the output
                files is given by os.path.splitext(match_to_filename_in)[0] + ext_out.
            id: optional string, see DataSample.read_all
            frame: optional frame integer, see DataSample.read_all
        """
        # convert
        if not ext_out[0] == ".":
            ext_out = "." + ext_out
        # query which data type the writer needs
        out_type = core.io.find_writer_input_type(ext_out)

        for filename, data, id, frame, base_name in self.read_all( filename_in, id, frame ):

            # convert into that data type
            mesh_new = utils.conversions.convert(data, out_type)
            # if caching is on, put it in cache
            name_stripped = os.path.splitext(filename)[0]
            self.write(name_stripped+ext_out, mesh_new)

    @staticmethod
    def get_formatted_filepattern(
        filename: str,
        id: Optional[str] = None,
        frame: Optional[int] = None,
        all_ids: Optional[bool] = False,
        all_frames: Optional[bool] = False
    ) -> str:
        """
        Create a regular expression file pattern to use with `self.find_matching_files` or `self.flush_data`.

        For finding/flushing specific files, specify the scene object ID and/or the frame index of interest
        in the time series.
        If no frame and/or id are given, behaviour depends on the `all_ids` and `all_frames`flags.
        If they are (partly) True, return a pattern for all files matching the filename with any
        id and/or frame, respectively.

        Keep in sync with `self.get_formatted_filename`, `self.extract_file_info`, `self.find_last_file`,
        `self.has_files` and `self.read_all`.

        Args:
            filename: File name as base of the pattern, e.g. 'deformed.vtu'.
            id: Scene object identifier. The pattern will match only files referring to this scene object.
            frame: Time frame index in time series. The pattern will match only files referring to this frame.
            all_ids: With or without given frame, generate a pattern that matches all respective scene objects.
            all_frames: With or without given scene object ID, generate a pattern that matches all respective
                time frames.

        Returns:
            A string that can be used as a regular expression with `re.match` to specify which files should be
            processed.
        """
        base_name, ext = os.path.splitext(filename)
        if id and frame:
            file_pattern = f"{base_name}_{id}_f{frame}\\{ext}"
        elif id:
            if all_frames:
                file_pattern = f"{base_name}_{id}(_f[0-9]+)*\\{ext}"
            else:
                file_pattern = f"{base_name}_{id}\\{ext}"
        elif frame:
            if all_ids:
                file_pattern = f"{base_name}(_[A-Z])*_f{frame}\\{ext}"
            else:
                file_pattern = f"{base_name}_f{frame}\\{ext}"
        elif all_ids and all_frames:
            file_pattern = f"{base_name}(_[A-Z])*(_f[0-9]+)*\\{ext}"
        elif not id and all_frames:
            file_pattern = f"{base_name}(_f[0-9]+)*\\{ext}"
        elif not frame and all_ids:
            file_pattern = f"{base_name}(_[A-Z])*\\{ext}"
        else:
            file_pattern = f"{base_name}\\{ext}"

        return file_pattern

    def find_scene_object(
            self,
            tag: str = None,
            scene_object_type: type = None
    ) -> Union[List[BaseObject], None]:
        """
        Find one or more scene objects in the DataSample's internal storage of
        scene objects to be created. Objects can be queried by tag or by organ type
        specified by the subclass of `core.objects.baseobject.BaseObject`,
        searching for the object tag takes precedence over searching by organ type.

        Args:
            tag: User given tag of the specific scene object you are looking for.
            scene_object_type: Type of scene object(s) you are looking for.
                Subclass of `core.objects.baseobject.BaseObject`.

        Returns:
            A list of scene objects that match the specified type or tag. A list
            with a single element for tag searches. None if no objects match.

        """
        # search by tag
        if tag is not None:
            for obj in self.scene_objects:
                if hasattr(obj, "tag"):
                    # tags are unique, so only one result is expected
                    if obj.tag == tag:
                        return [obj]
            msg = (f"DataSample {self.id} does not hold a scene object with the tag {tag}."
                  "Did you specify it via SceneObjectGeneratorBlock.add_object_template"
                  "and has the block run?")
            Log.log(severity="WARN", module="DataSample", msg=msg)
            return None

        # search by scene object type
        if scene_object_type is not None:
            # check proper input
            if not issubclass(scene_object_type, BaseObject):
                msg= (f"Requested scene object type has to be a subclass of "
                     f"core.objects.baseobject.BaseObject! You requested {scene_object_type}."
                     f"Is this implemented in core.objects.sceneobjects?")
                Log.log(severity="WARN", module="DataSample", msg=msg)
                return None

            # a sample can hold several scene objects of the same type
            found_objs = []
            for obj in self.scene_objects:
                if isinstance(obj, scene_object_type):
                    found_objs.append(obj)
            if len(found_objs) > 0:
                return found_objs
            else:
                msg= (f"No scene object of type {scene_object_type} listed in "
                     f"DataSample {self.id}, did you specify it via "
                     f"SceneObjectGeneratorBlock.add_object_template and has the block run?")
                Log.log(severity="WARN", module="DataSample", msg=msg)
                return None

        msg = f"Please specify a tag or scene object type you want to search by."
        Log.log(severity="WARN", module="DataSample", msg=msg)
        return None

