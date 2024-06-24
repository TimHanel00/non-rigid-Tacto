import sys, os, psutil, time
from concurrent.futures import ProcessPoolExecutor as Pool # requires python 3.8
from concurrent.futures import as_completed
from concurrent.futures.process import BrokenProcessPool
import traceback
import vtk
import re
from typing import Optional, List, Tuple
import argparse
import statistics

from core.pipeline_block import PipelineBlock
from core.dataset import Dataset
from core.datasample import DataSample
from core.log import Log
import core.io
from core.exceptions import SampleProcessingException, SampleValidationException
import core.plot_statistics as plot_statistics
from utils import dict_utils

class Pipeline():
    """Main pipeline class.

    The main purpose of this class is to store, configure and run a list of PipelineBlock's.
    These blocks should be added in the correct order by calling Pipeline.append_block.
    The pipeline handles some recoverable exceptions that could occur while running so
    that the process can keep running if non-fatal errors are thrown for some samples.
    """

    def __init__(self, 
            force_run_blocks: Optional[bool] = None, 
            do_not_retry_blocks: Optional[bool] = None,
            statistics_only: bool = False, 
            run_sequential: bool = False,
            launch_sofa_gui: bool = False,
            pre_existing_files: List[str] = [],
            max_processes: int = os.cpu_count()-1,
            **kwargs
    ):
        """Initializes the pipeline class.

        Args:
            force_run_blocks: List of 
            do_not_retry_blocks: .
            statistics_only:.
            run_sequential:.
            **kwargs
        """
 
        self.only_aggregate_statistics = statistics_only

        self.pipeline_blocks = []
        #self.all_filenames = []

        self.run_parallel = not run_sequential
        self.launch_sofa_gui = launch_sofa_gui

        self.force_run_blocks = []
        self.do_not_retry_blocks = []

        self.pre_existing_files = pre_existing_files

        if force_run_blocks:
            self.force_run_blocks = force_run_blocks
        if len(self.force_run_blocks) > 0:
            msg = "Will force recalculation for the following blocks: " +\
                    f"{self.force_run_blocks}"
            Log.log(module="Pipeline", msg=msg)

        if do_not_retry_blocks:
            self.do_not_retry_blocks = do_not_retry_blocks
        if len(self.do_not_retry_blocks) > 0:
            msg = "Will avoid recalculation for the following blocks, even if " +\
                    f"their output is missing: {self.do_not_retry_blocks}."
            Log.log(module="Pipeline", msg=msg)

        for b in self.do_not_retry_blocks:
            if b in self.force_run_blocks:
                raise ValueError(f"Block {b} is in list of skipped blocks AND in list " +\
                        "of forced recalculation blocks, but block cannot be skipped " +\
                        "AND recalculated!")

        if not(self.run_parallel) and launch_sofa_gui:
            Log.log(module="Pipeline",
                    msg="SOFA GUI can be launched only in parallel mode", severity="WARN")
            self.launch_sofa_gui = False

        self.max_workers = max_processes
        self.mem = {"main":[], "children":[], "total":[]}

        # result plotting
        self.plots = []

        #vtk.vtkObject.GlobalWarningDisplayOff()

    def append_block(
        self,
        block:PipelineBlock
    ) ->None:
        """
        Append a block to the end of the pipeline. Block must inherit from PipelineBlock.
        """

        assert isinstance(block, PipelineBlock), "Blocks added to a pipeline must inherit" +\
                " from PipelineBlock!"

        # Check what previously created blocks produce and consume:
        prev_outputs = self.pre_existing_files
        prev_inputs = []
        for b in self.pipeline_blocks:
            prev_outputs += b.outputs
            prev_inputs += b.inputs

        abort = False
        for inp in block.inputs:
            found = False
            for p in prev_outputs:
                # DEBUG
                # print(f"matching {p} against {inp}:")
                # print(f"\twith match inp->p: {re.match(inp, p)}")
                # print(f"\twith match p->inp: {re.match(p, inp)}")
                # print(f"\twith equality: {p == inp}")
                if p == inp or re.match(inp, p) or re.match(p, inp):
                    found = True
                    break
            if not found:
                msg = f"Block {block} requires input '{inp}', but no previous block " +\
                        "produced this!"
                Log.log(module="Pipeline", severity="FATAL", msg=msg)
                abort = True
        for out in block.outputs:
            if out in prev_outputs:
                msg = f"Block {block} wants to create output '{out}', but another " +\
                        "block already produces this!\n\tPlease use unique filenames."
                Log.log(module="Pipeline", severity="FATAL", msg=msg)
                abort = True
        #if len(block.outputs) == 0:
        #    msg = f"Block {block} wants to create no outputs files. " +\
        #            "This is currently not supported."
        #    Log.log(module="Pipeline", severity="FATAL", msg=msg)
        #    abort = True
        if abort:
            msg = "Could not configure pipeline. Aborting."
            Log.log(module="Pipeline", severity="FATAL", msg=msg)
            sys.exit(1)

        # Count existing blocks o the same type:
        type_id = 0
        for i, b in enumerate( self.pipeline_blocks ):
            if type(b) == type(block):
                type_id += 1

        self.pipeline_blocks.append(block)
        block.set_block_id(len(self.pipeline_blocks)-1, type_id)

        # For each block, also plot its timing:
        #block_name = type(block).__name__ 
        #self.histogram_keys.append( "Timing_" + block_name )   # TODO
        #self.all_filenames += block.outputs

    def add_plot( self, plot_config ):
        self.plots.append( plot_config )

    def run(
        self,
        dataset: Dataset,
    ) ->None:
        """Run the whole pipeline, on each sample.
        
        Currently, the pipeline is run for each sample in sequence, i.e. sample 1 is finished before sample 2 is started.
        TODO: Threading of blocks!

        Args:
            dataset:
        """

        self.print_pipeline()

        if len(dataset) == 0:
            Log.log(module="Pipeline", severity="ERROR",
                    msg="Dataset contains no samples. " +\
                    "(Maybe use --num_samples to force creation of new samples.)")
            return

        all_block_names =[block.unique_name for block in self.pipeline_blocks]
        for block_name in self.force_run_blocks:
            if not block_name in all_block_names:
                raise ValueError(f"Cannot force execution of block {block_name}, " +\
                        f" not found!\nAvailable are: {all_block_names}")
        for block_name in self.do_not_retry_blocks:
            if not block_name in all_block_names:
                raise ValueError(f"Cannot skip execution of block {block_name}, " +\
                        f" not found!\nAvailable are: {all_block_names}")

        if not self.only_aggregate_statistics:

            # save run details and purpose/comment in dataset
            msg = Log.compile_run_log_entry()
            dataset.append_to_log(msg)
            # if there is uncommitted changes to the code, save them for reproducibility
            if Log.is_diff_needed():
                filename, content = Log.compile_diff_file()
                dataset.write(filename, content, subfolder=dataset.diff_path)

            if self.run_parallel:
                Log.log(module="Pipeline", severity="INFO",
                        msg=f"Using {self.max_workers} sub-processes.")
            else:
                Log.log(module="Pipeline", severity="WARN", msg=f"Using 0 sub-processes.")


            start_time = time.time()

            # Data-sequential:
            if not self.run_parallel:
                for sample in dataset:
                    self.run_sample(sample)
            else:

                # Note: The following may be slightly confusing. We use
                # ProcessExecuterPool 'pool' to run multiple instances of the "run_sample"
                # function in parallel. Each run_sample instance is passed a single
                # DataSample to process. However, if a pool is created for the full
                # dataset, the processes keep accumulating memory, an issue which we've
                # not found a solution for yet.
                # The workaround is to split the dataset into chunks of size
                # "samples_per_iteration" and create a pool for each of these chunks
                # (sequentially). The slowdown due to this is minor, but it seems to fix
                # the memory leak.
                total_samples = len(dataset)
                done_samples = 0
                samples_per_iteration = self.max_workers*5

                while done_samples < total_samples:

                    # Data-parallel:
                    with Pool(max_workers=self.max_workers) as pool:
                        try:
                            samples_to_run = min(samples_per_iteration, total_samples - done_samples)
                            subset = dataset[done_samples:done_samples+samples_to_run]
                            # Map each sample to a process which will run the 'run_sample'
                            # function on it:
                            futures = [pool.submit(self.run_sample, s) for s in subset]

                            for future in as_completed(futures):
                                # Get result:
                                result_sample = future.result()
                                # The processes worked on copies of the samples, so return them back
                                # into the original dataset:
                                dataset.replace_sample(result_sample)
                                # Keep track of current memory usage:
                                self.print_memory_usage()

                            # The processes worked on copies of the samples, so return them back
                            # into the original dataset:
                            #for i, sample in enumerate(results):
                            #    dataset.replace_sample(i, sample)
                        except BrokenProcessPool as e:
                            msg="BrokenProcessPool! " +\
                                "Something within a sub-process went wrong. The following error message " +\
                                f"was received: {e}"
                            Log.log( module="Pipeline", severity="FATAL", msg=msg )
                            raise Exception( msg )
                    done_samples += samples_to_run


            end_time = time.time()
            speed = len(dataset)/(end_time-start_time)
            Log.log(module="Pipeline", severity="OK",
                    msg="Pipeline processed all samples.")
            Log.log(module="Pipeline", severity="OK",
                    msg=f"Average processing speed was: {speed} samples/second")
            if len(self.mem['total']) > 0:
                Log.log(module="Pipeline", severity="OK",
                        msg=f"Max memory consumption (RSS)): {max(self.mem['total'])} GB")
        else:
            Log.log(module="Pipeline", msg="Only calculating statistics")

        stats, configs = dataset.aggregate_configs_and_statistics( )

        self.plot_results(
                stats = stats,
                configs = configs,
                dataset = dataset,
                plots = self.plots
                )

        # Count the valid samples:
        successful_samples = 0
        for sample in dataset:
            if sample.processable and not sample.had_previous_issues:
                successful_samples += 1
       
        # Percentage of successful samples:
        pct = successful_samples/len(dataset)*100

        msg = f"Pipeline finished."
        msg += f" {successful_samples} of {len(dataset)} ({pct}%)"
        msg += " samples processed successfully"
        Log.log(module="Pipeline", severity="OK", msg=msg)

    def run_sample(
        self,
        sample: DataSample,
    ) ->DataSample:
        """
        Args:
            sample:
        
        Returns:
            DataSample
        """
        first_block_triggered = False
        for block in self.pipeline_blocks:
            if sample.processable:    # Only run if the sample has not encountered an error

                # Check if the output files for this block already exist.
                # If so, there's no need to re-run this block for this sample:
                #requires_calculation = not sample.has_files(block.outputs)
                # Check if a previous run has already successfuly processed _and validated_ this block
                # for the current sample:
                requires_calculation = not sample.get_successfully_processed( block )
                # Check if the recalculation has been forced manually:
                block_name = block.unique_name
                # Check if a block needs to re-run or should be skipped.
                # Note that these two conditions are mutually exclusive!
                forced = block_name in self.force_run_blocks
                if forced and not requires_calculation:
                    msg = f"Forced recalculation of '{block_name}'"
                    Log.log(module="Pipeline", severity="WARN", msg=msg)
                has_outputs = len(block.outputs) > 0

                if first_block_triggered or requires_calculation or forced or not has_outputs:
                    # Before running, make sure previous output/config is deleted:
                    self.remove_results(sample, block)

                    if has_outputs:
                        # If we run this block, make sure that all the following blocks
                        # know that they need re-calculation:
                        self.remove_results_of_successors(sample, block)
                        # Remember that a block has been run, so that all future blocks will also need to be
                        # run:
                        first_block_triggered = True

                    # Run block:
                    self._safe_run(block, sample)

        sample.save_config()
        sample.save_statistics()

        if sample.processable:
            # Delete previously recorded errors and store statistics:
            sample.success()

        sample.flush_data()

        return sample

    def _safe_run(
        self,
        block: PipelineBlock,
        sample: DataSample,
    ) ->None:
        """Run the PipelineBlock "block" with the DataSample "sample" in a safe way, i.e.
        catch and process all expected errors the block may raise.
        
        Args:
            block:
            sample: 
        """

        start_time = time.process_time()
        block_name = block.unique_name
        
        try:
            
            do_not_retry_block = block_name in self.do_not_retry_blocks
            if do_not_retry_block:
                msg = f"Block '{block_name}' would need recalculation, but it was " +\
                        "placed in the list of blocks that should not be re-calculated."
                raise SampleProcessingException(block, sample, msg)

            msg = f"Running {block} on {sample}."
            Log.log(module="Pipeline", severity="INFO", msg=msg)
            sample.write_log_new_section(str(block))
            block.run(sample)
            remains_processable, reason = block.validate_sample(sample)
            if not remains_processable:
                msg = f"Sample {sample.id} failed the validation step. " +\
                    reason
                raise SampleValidationException(block, sample, msg)
            # If processing _and_ validation went well, mark this sample to have been successfully processed
            # by the current block:
            sample.set_successfully_processed( block )
        except (SampleProcessingException, SampleValidationException) as e:
            msg = f"Block {block} stopped parsing {sample}.\n>\t"
            error_message = e.message.replace("\n", "\n>")
            msg += f"Skipping Sample. Reason: '{error_message}'."
            Log.log(module="Pipeline", severity="SKIP", msg=msg)
        except NotImplementedError as e:
            msg = "A block's function was not implemented correctly.\n\t"
            msg += f"Block type: {block}\n\t"
            msg += f"Traceback:\n\t{traceback.format_exc()}"
            Log.log(module="Pipeline", severity="FATAL", msg=msg)

        end_time = time.process_time()
        sample.add_timing( block, end_time - start_time )

    def print_memory_usage(self):

        pid = os.getpid()
        try:
            process = psutil.Process()
            mem = process.memory_info()
            main = mem.rss
            children = 0
            for child in process.children(recursive=True):
                mem = child.memory_info()
                children += mem.rss
            total = main + children

            msg = "-----------------------------------\n"
            msg += f"PID: {pid}\n"
            msg += f"Memory: rss: {total/1e9} GB\n"
            msg += "-----------------------------------\n"
            Log.log( module="Pipeline", msg=msg )
        except psutil.NoSuchProcess:
            total = 0
            main = 0
            children = 0
            Log.log( module="Pipeline", severity="WARN",
                    msg="Could not obtain memory usage from process: psutils.NoSuchProcess")
        self.mem["total"].append(total/1e9)
        self.mem["main"].append(main/1e9)
        self.mem["children"].append(children/1e9)

    def remove_results(
        self,
        sample: DataSample,
        block: PipelineBlock,
    ) -> None:
        sample.clear_successfully_processed(block)
        sample.clear_files(block.outputs)
        sample.clear_config(block)
        sample.clear_statistics(block)


    def remove_results_of_successors(
        self,
        sample: DataSample,
        start_block: PipelineBlock,
    ) -> None:
        """  
        Args:
            sample:
            start_block:

        """
        found_start_block = False
        for block in self.pipeline_blocks:
            if found_start_block:
                sample.clear_files(block.outputs)
                sample.clear_config(block)
                sample.clear_statistics(block)
            if block == start_block:
                found_start_block = True

#    def aggregate_statistics(
#        self,
#        dataset: Dataset,
#    ) ->dict:
#        """ 
#        Args:
#            dataset: 
#        
#        Returns:
#
#        """
#        Log.log(module="Pipeline", msg="Aggregating statistics...")
#        all_stats = {}
#        for sample in dataset:
#            if sample.processable and not sample.had_previous_issues:
#                all_stats[sample.id] = sample.statistics
#        Log.log(module="Pipeline",
#                msg=f"Found {len(all_stats)} processable samples with statistics")
#        dataset.write("statistics.yaml", all_stats)
#        return all_stats
#
    # Todo: write issue to flatdict developers to fix nested dict with integer keys problem,
    #  then update sample ids back to integers here and everywhere that we use the output of
    #  this function in the meantime
    #def aggregate_configs(
    #        self,
    #        dataset: Dataset,
    #) -> dict:
    #    """
    #    Collect all config values set by the pipeline blocks for all processable samples in the dataset.
    #    This is a separate method in order to stay flexible in terms of separate treatment of statistics and
    #    configuration values.

    #    Args:
    #        dataset: Samples to collect the configuration values from.

    #    Returns:
    #        All configuration values of the samples with the sample's id as highest-level key.

    #    """
    #    Log.log(module="Pipeline", msg="Aggregating configs...")
    #    all_configs = {}
    #    for sample in dataset:
    #        if sample.processable and not sample.had_previous_issues:
    #            all_configs[sample.id] = sample.full_config
    #    Log.log(module="Pipeline",
    #            msg=f"Found {len(all_configs)} processable samples with config values")
    #    dataset.write("configs.yaml", all_configs)  # inspect distributions
    #    return all_configs

    def plot_results(
        self,
        stats: dict,
        configs: dict,
        dataset: Dataset,
        plots: List[dict],
    ) ->None:
        """
        Plot selected statistics of pipeline output.

        Args:
            stats: Nested dictionary of saved sample statistics as
                {sample.id: sample.statistics} = {sample.id: {key: value}}.
            configs: Nested dictionary of saved sample configs as
                {sample.id: sample.full_config} = {sample.id: {block type: {key: value}}} or
                {sample.id: {block type: {scene object: {key: value}}}}.
            dataset: Dataset to which folder results are plotted.
            plots: A list of plosts to generate.
                Each entry is a dictionary containing at least a "type", which is one of:
                "HISTOGRAM", "SCATTER", "LINE", "BOX"

        """

        stats_and_configs = dict_utils.combine_stats_and_configs( stats, configs )

        if len(plots) == 0:
            msg="No user-defined plots. " +\
                    "You can add your own plots via that Pipeline's 'plots' argument."
            Log.log( severity="WARN", module="Pipeline", msg=msg )

        # Add a plot for the timings:
        timing_keys = []
        timing_labels = []
        for block in self.pipeline_blocks:
            key = "stats|" + block.unique_name + "|Timing"
            timing_keys.append( key )
            timing_labels.append( block.unique_name )
        self.add_plot( {
                "type":"BOX",
                "keys":timing_keys,
                "name":"BlockTiming",
                "labels":timing_labels,
                "y_label":"sec",
            } )

        # Plot every plot that was previously added via Pipeline.add_plot():
        for p in plots:
            plot_statistics.create_plot(
                    plot_config=p,
                    data = stats_and_configs,
                    path = dataset.data_path )

        # Plot memory usage:
        # --------------------------
        #if len(self.mem["total"]) > 0:
        #    plot_statistics.plot_line( self.mem["total"],
        #            name="memory_total",
        #            ylabel="[GB]",
        #            path=dataset.data_path )
        #    plot_statistics.plot_line( self.mem["main"],
        #            name="memory_main",
        #            ylabel="[GB]",
        #            path=dataset.data_path )
        #    plot_statistics.plot_line( self.mem["children"],
        #            name="memory_children",
        #            ylabel="[GB]",
        #            path=dataset.data_path )

        # Plot timing: 
        # --------------------------
        # TODO: FIXME
        #timings = {}

        #for i, block in enumerate(self.pipeline_blocks):
        #    block_name = type(block).__name__
        #    timing_name = "Timing_" + block_name
        #    collected = utils.extract_statistic(stats, timing_name)

        #    if len(collected) > 0:
        #        avg = sum(collected)/len(collected)
        #        maxv = max(collected)
        #        median = statistics.median( collected )

        #        msg = f"Timing for block {block_name}: " +\
        #                f"Avg: {avg} s, median: {median} s, max: {maxv} s"
        #        Log.log(module="Pipeline", msg=msg)
        #        timings[block_name] = collected
        #if len(timings) > 0:
        #    plot_statistics.plot_boxplot( timings, "timing", path = dataset.data_path,
        #        y_label = "seconds" )
        #elif not self.only_aggregate_statistics:
        #    Log.log(severity="WARN", module="Pipeline", msg="No timings found for the configured blocks!")

    def print_pipeline(
        self
    ) ->None:
        """ Prints current pipeline configuration.
        """
        msg = "Current pipeline configuration:"
        prev_block_needs_rerun = False
        for i, block in enumerate(self.pipeline_blocks):
            msg += f"\n\tBlock: {block}"
            msg += f"\n\t\tUses:"
            for filename in block.inputs:
                msg += f" {filename}"
            msg += f"\n\t\tProduces:"
            for filename in block.outputs:
                msg += f" {filename}"
            if len(block.optional_outputs) > 0:
                msg += f"\n\t\tMay produce:"
                for filename in block.optional_outputs:
                    msg += f" {filename}"
            will_run = "\n\t\t"
            if block.unique_name in self.force_run_blocks:
                will_run += "(Will run, manually triggered via --force_run_blocks." +\
                        " Running will also trigger all downstream blocks.)"
            elif len(block.outputs) == 0:
                will_run += "(Will always run because the block creates no outputs." +\
                        " However, it won't trigger running of downstream blocks!)"
            else:
                will_run += "(Will run if outputs are not found." +\
                        " Running will also trigger all downstream blocks.)"

            msg += will_run


        Log.log(module="Pipeline", severity="INFO", msg=msg)

    @staticmethod
    def add_arguments(
        parser: argparse.ArgumentParser,
    ) ->None:
        """ Adds general Pipeline-related arguments to the given ArgumentParser instance.

        Args:
            parser: An already existing parser. The function will
                use this to add additional pipeline-specific arguments.
        """
        group = parser.add_argument_group("General Pipeline arguments") 

        run_control_group = group.add_mutually_exclusive_group()
        run_control_group.add_argument("--force_run_blocks", nargs="+",
                help="Name of blocks which the pipeline should execute despite their" +\
                        " outputs already being present.")
        run_control_group.add_argument("--statistics_only", action="store_true",
                help="Only aggregate statistics from all samples, do not re-calculate" +\
                        " any of the other blocks. This could be useful if you combine" +\
                        " results from multiple runs into a single dataset folder.")
        group.add_argument("--do_not_retry_blocks", nargs="+",
                help="List of blocks to skip despite their outputs not being present.")
        group.add_argument("--run_sequential", action="store_true",
                help="Disable parallel running. Useful for debugging, but much slower!")
        group.add_argument("--launch_sofa_gui", action="store_true",
                help="Launches the simulation with SOFA GUI. Useful for debugging, but much slower!")
        group.add_argument("--max_processes", type=int, default=os.cpu_count()-1,
                help="Number of worker processes to use. Default: Number of CPU cores minus 1.")


