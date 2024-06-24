import argparse
import os
import re
import shutil
from typing import Tuple, List, Union

from core.log import Log
import core.io
from core.datasample import DataSample

class Dataset():
    """
    Main dataset class, keeps track of all available simulation samples.

    Each sample is stored in its own folder, usually with multiple files in the folder
    holding different stages of the simulation, such as preoperative surface, or deformed
    volume files. After instancing this dataset class it is intended to be used like a list
    to access samples via "sample = dataset[i]".

    Note:
        When using multiprocessing.Pool or similar to distribute samples, the modifications
        of the samples in the other processes are not reflected back automatically in
        the main thread. This is 'fixed' by returning the sample from the process and
        placing it back into the Dataset with :meth:`Dataset.replace_sample`.

    Note:
        Only the samples [start_sample:start_sample+num_samples-1] will be processed.
        This also means only those statistics will be aggregated at the end. If you
        want to aggregate all statistics after separating across multiple machines,
        for example, re-run your script with the '--statistics_only' argument.

    """

    def __init__(
        self,
        data_path: str ="data",
        num_samples: int = 0,
        start_sample: int = 0,
        disable_caching: bool = False,
        **kwargs
    ):
        """
        Args:
            data_path: Base path. Folder where all samples should be stored.
            num_samples: The number of samples to generate. Must be a positive integer or 
                zero. In the case of zero, the Dataset will automatically search base_path
                to find all previously initialized samples and will re-use these.
            start_sample: ID of first sample to process. Useful if you only want to re-run
                on a subset of a previous run, or want to manually distribute across
                multiple machines.

        """

        Log.log(module="Dataset",
                msg=f"Creating dataset  from path: '{data_path}'")

        if not os.path.exists(data_path):
            Log.log(module="Dataset",
                    msg=f"Folder {data_path} not found, creating.")
            os.makedirs(data_path)
        self.data_path = data_path

        # save date, command line arguments, comment, ... = "run configuration" about all
        # runs of the pipeline on the dataset here
        self._log_filename = "history.log"
        # create folder to save uncommitted code differences to last commit
        self.diff_path = "diffs"
        diff_folder = os.path.join(self.data_path, "diffs")
        if not os.path.exists(diff_folder):
            Log.log(module="Dataset",
                    msg=f"Folder for code diffs not found, creating.")
            os.makedirs(diff_folder)
        # keep track of non-DataSample-related subfolders
        self.subfolders = []
        self.subfolders.append(self.diff_path)

        self.start_sample = start_sample
        self.num_samples = num_samples

        # Dict of all available data samples:
        # The dictionary keys are unique integer IDs
        self._samples = {}
        # Another view into the _samples dictionary, this time as a list, ordered by
        # sample ID:
        self._samples_list = []

        self.use_caching = not disable_caching

        self._find_potential_samples()

        if num_samples > 0:
            self.populate(num_samples, start_sample)

    def populate(
        self,
        num_samples: int,
        start_sample: int = 0,
    ):
        """
        Create empty folders for those samples which do not yet exist.

        Creates samples in the range [start_sample:start_sample+num_samples-1]

        Args:
            num_samples:
            start_sample:
        """
        prev_num_samples = len(self._samples_list)
        for int_id in range(start_sample, start_sample+num_samples):
            if not int_id in self._samples.keys():
                int_str = Dataset.int_id_to_str( int_id )

                path = os.path.join( self.data_path, int_str )
                if not os.path.exists(path):    # it shouldn't
                    os.makedirs(path)
                
                sample = DataSample(path, int_id, cache_data=self.use_caching)

                self._samples[int_id] = sample
                self._samples_list.append( sample )
                sample.dataset_list_index = len(self._samples_list) - 1

        new_samples = len(self._samples_list) - prev_num_samples
        if new_samples > 0:
            msg = f"Created {new_samples} new, empty samples"
            Log.log(module="Dataset", msg=msg)


    def _find_potential_samples(
        self
    ):
        """Searches for previously existing folders in this Dataset's base path.

        This can be used to simply re-process _all_ samples which were defined in a
        previous run, without needing to know their IDs.
        """

        # Find all (direct) subdirectories:
        folders = [d for d in os.listdir(self.data_path)
                    if os.path.isdir(os.path.join(self.data_path, d))]
        for folder in folders:
            # Use only directories where the folder name is a positive integer (possibly
            # with leading zeros, which will be ignored):
            if re.fullmatch( "[0-9]+", folder ):
                int_id = int(folder)
              
                # Check if the sample lies within the range which we want to
                # generate, otherwise skip it:
                if self.num_samples > 0:    # ... but only if a range is given
                    if int_id < self.start_sample or \
                            int_id >= self.start_sample + self.num_samples:
                        continue

                int_str = Dataset.int_id_to_str( int_id )

                path = os.path.join( self.data_path, folder )
                
                sample = DataSample(path, int_id, cache_data=self.use_caching)

                self._samples[int_id] = sample
                self._samples_list.append( sample )
                sample.dataset_list_index = len(self._samples_list) - 1

        # Sort the samples list by the used ID:
        self._samples_list.sort( key=lambda s: s.id )


    def __getitem__(
        self,
        i: int,
    ):
        """
        Returns the ith sample. Note that this is not necessarily the item with ID 'i'!
        """
        return self._samples_list[i]

    def __len__(
        self
    ) ->int:
        """
        Returns the number of samples in this dataset.
        """

        return len(self._samples_list)

    def replace_sample(
        self,
        sample: DataSample,
    ):
        """
        Replaces an existing sample in the list of samples.

        This should not be called manually. The function exists only to re-collect
        samples that were previously distributed across multiple processes.
        """

        if sample.dataset_list_index >= 0:
            list_index = sample.dataset_list_index
        else:
            list_inds = [i for i,s in enumerate(self._samples_list) if s.id == sample.id]
            list_index = next([i for i,s in enumerate(self._samples_list) if s.id == sample.id])

        if list_index is None:
            raise ValueError(f"Trying to replace sample with ID {sample.id} in dataset, " +\
                    "but no sample with this ID was found!")

        self._samples_list[list_index] = sample

    @classmethod
    def int_id_to_str(
        cls, 
        id_as_int: int, 
        length: int = 6
    ) ->str:
        """
        Converts an integer id to the corresponding sample folder name.
        Note that this conversion does not guarantee that this folder exists!
        
        Args:
            id_as_int:
            length: Integer, gives the number of digits to use. String will be zero-padded if necessary

        Returns:
            name
        """
        assert type(id_as_int) == int, "int_id_to_str argument must be integer!"
        id_as_str = str( id_as_int )

        return id_as_str.zfill( length )

    def print_state(
        self
    ) ->None:
        """Logs the current state of the Dataset.
        """

        if len(self._samples_list) == 0:
            Log.log(module="Dataset", severity="WARN", msg="Dataset empty!")
            return

        # Count the valid samples:
        successful_samples = 0
        for sample in self._samples_list:
            if sample.processable:
                successful_samples += 1
       
        # Percentage of successful samples:
        pct = successful_samples/len(self._samples_list)*100

        msg = f"Dataset state:"
        msg += f"\n\tFound {len(self._samples_list)} samples"
        msg += f"\n\tOf these, {successful_samples} ({pct}%)"
        msg += " are currently valid for further processing"
        Log.log(module="Dataset", msg=msg)
 
    def print_all_issues(
        self
    ):
        """Prints all the issues with all the DataSample's known so far.
        """
        msg = "Encountered issues:"
        issue_msg = ""
        samples_with_issues = 0
        for sample in self._samples_list:
            issues = sample.prev_issues
            if issues and len(issues) > 0:
                samples_with_issues += 1
                issue_msg += f"\n{sample}\n"
                for issue in issues:
                    issue_msg += f"\t{issue}"
        if samples_with_issues == 0:
            msg += "\n\tNo issues found in any of the analyzed samples."
            Log.log(module="Dataset", msg=msg)
        else:
            msg += issue_msg
            Log.log(module="Dataset", msg=msg)
            msg = f"{samples_with_issues} samples encountered issues during generation and were not fully created."
            Log.log(module="Dataset", severity="WARN", msg=msg)
            fully_created_samples = len(self._samples_list) - samples_with_issues
            if fully_created_samples > 0:
                msg = f"{fully_created_samples} samples were created successfully."
                Log.log(module="Dataset", severity="OK", msg=msg)

    def count_issues_per_block(
        self
    ):
        """ Counts how many issues each block encountered, then prints the result (sorted by number of issues)
        """
        issues_per_block = {}
        total_issues_encountered = 0
        for sample in self._samples_list:
            issues = sample.prev_issues
            if issues:
                issues_str = "\n".join(issues)

                # The following matches for example: GmshMeshingBlock_0 (ID: 2):
                for block_name in re.findall( r'([^\s]+Block_[0-9]+) \(ID: [0-9]+\):', issues_str ):
                    if not block_name in issues_per_block.keys():
                        issues_per_block[block_name] = 0
                    issues_per_block[block_name] += 1
                    total_issues_encountered += 1

        blocks_with_issues = [(name,num_issues) for name, num_issues in issues_per_block.items()]
        blocks_with_issues_sorted = sorted(blocks_with_issues,
                key = lambda x: x[1],
                reverse=True )    # sort by num of issues
        msg = "Encountered issues per block:"
        for b in blocks_with_issues_sorted:
            msg += f"\n\t{b[0]}: {b[1]}"
        Log.log(module="Dataset", msg=msg)
        Log.log(module="Dataset", msg=f"Sum of encountered issues: {total_issues_encountered}")
 
    
    def write(
        self,
        filename: str,
        data: object,
        subfolder: str = ''
    ) -> None:
        """
        Writes 'data' into a file called 'filename' in the Dataset base path.

        Note: For this to work, str must end in a file-extension for which the
        :mod:`core.io` module has a registered handler and data must be of the
        corresponding type. For example, if filename ends in ".yaml", the data should
        be something pickable, likely a dictionary.

        Args:
            filename: Name of the target file without any folder path (this will be
            taken care of by the DataSet).
            data: Data to write.
            subfolder: Any subfolder below the DataSet level that the file should be sorted into.
        """
        if os.path.exists(os.path.join(self.data_path, subfolder)):
            f = os.path.join(self.data_path, subfolder, filename)
        else:
            Log.log(module="Dataset", severity="WARN", msg=f"Subfolder {subfolder} specified"
                    f"for storing {filename} does not exist! Saving at dataset root folder instead.")
            f = os.path.join(self.data_path, filename)
        core.io.write(f, data)

    def print_md5sums(self):
        for sample in self._samples_list:
            sample.print_md5sums()

    def load_configs(
            self
    ) -> None:
        """Load config from previous run. Should only be called if blocks do not perform
        any calculations afterwards, e.g. when the pipeline is in statistics_only mode.
        """
        for sample in self._samples_list:
            sample.load_config()

    def aggregate_configs_and_statistics(
            self,
    ) -> Tuple[dict, dict]:
        """ Collect all statistics and config values for all valid samples.

        Write the result to a "statistics.yaml" and "configs.yaml" file at the dataset base path.

        Returns:
            All stats and config values of the valid samples in two nested dictionaries.
            The samples' IDs are the highest-level key in the two dictionaries.
        """
        Log.log(module="Dataset", msg="Aggregating configs and statistics...")
        all_stats = {}
        all_configs = {}
        for sample in self._samples_list:
            if sample.processable and not sample.had_previous_issues:
                all_stats[sample.id] = sample.statistics
                all_configs[sample.id] = sample.config
        Log.log(module="Dataset", msg=f"Found {len(all_stats)} processable samples with statistics")
        self.write("statistics.yaml", all_stats)
        self.write("configs.yaml", all_configs)
        return all_stats, all_configs

    def append_to_log(
            self,
            message: Union[List[str], str]
    ) -> None:
        return
        """ Append an entry to the DataSet's log file.

        Args:
            message: Lines to append to the log file. Each line should already end with \n.
        """
        filename = os.path.join(self.data_path, self._log_filename)
        with open(filename, 'a') as f:
            f.writelines("\n")
            f.writelines(message)

    @staticmethod
    def add_arguments(
        parser: argparse.ArgumentParser,
    ) ->None:
        """ Add general Dataset-related arguments to the given ArgumentParser instance.

        Args:
            parser (argparse.ArgumentParser): An already existing parser. The function will
                use this to add additional dataset-specific arguments.
        """
        group = parser.add_argument_group("Dataset arguments") 
        group.add_argument("--data_path", type=str, default="data",
                help="Where to store the generated dataset. Relative path from "
                     "the folder that the script is run from.")
        group.add_argument("--num_samples", type=int, default=0,
                help="How many samples to generate. If 0 (default), generate all.")
        group.add_argument("--start_sample", type=int, default=0,
                help="Which sample to start with")
        group.add_argument("--disable_caching", action="store_true",
                help="No disk I/O caching for data samples. Might be slower, but useful " +\
                        "for debugging.")
        group.add_argument("--comment", type=str, default=None,
                help="State the purpose of the dataset generation so you can still recognize it "
                     "in two months (or be sure that it's safe to delete).")


