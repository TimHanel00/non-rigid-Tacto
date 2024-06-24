import argparse
from datetime import datetime
import os
from typing import List, Tuple

import __main__
from utils.git_utils import GitRepo

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Log:

    # Static 
    level = 0    # by default, show everything!
    levels = [
        "DETAIL",
        "INFO",
        "SKIP",
        "WARN",
        "OK",
        "ERROR",
        "FATAL",
        ]
    truncate_long_error_messages = True

    # Store details about the current run
    run_config = {}

    @staticmethod
    def initialize(
            verbosity_level: str = "INFO",
            show_full_errors: bool = True, 
            **kwargs
    ):
        """ Configure the log (usually by passing the command line arguments)
        
        Args:
            show_full_errors: Print full error tracebacks when skipping samples
        """
        
        assert verbosity_level in Log.levels, \
            f"Given verbosity_level must be one of {Log.levels}, " +\
                    f" but was '{verbosity_level}'!"

        Log.level = Log.levels.index(verbosity_level)
        Log.truncate_long_error_messages = not show_full_errors
        Log.cache_run_config(**kwargs)


    @staticmethod
    def add_arguments(
        parser: argparse.ArgumentParser,
    ) ->None:
        """ Add the logging-specific parameters to the argument parser """

        group = parser.add_argument_group("Logging")
        group.add_argument("--verbosity_level", type=str, default="INFO",
                choices=Log.levels,
                help=f"Set minimum verbosity level. Must be one of:\n\t{Log.levels}")
        group.add_argument("--show_full_errors", action="store_true",
                help="Show full reasons for skipping samples (truncated by default)")


    @staticmethod
    def log(
        module, 
        msg: str, 
        severity: str = "DETAIL",
    ) ->None:
        """ Logging function that prints the given message to command line.
        
        Args:
            module:
            msg:
            severity:
        """

        assert severity in Log.levels, \
                f"Given severity must be one of {Log.levels}, but found {severity}!"

        # Only print messages with a equal or higher level than the currently configured one:
        level = Log.levels.index( severity )
        if level < Log.level:
            return

        col = ""
        end_col = ""
        if severity == "OK":
            col = bcolors.OKGREEN
        if severity == "WARN":
            col = bcolors.WARNING
        if severity == "SKIP":
            col = bcolors.WARNING
        elif severity == "ERROR":
            col = bcolors.ERROR
        elif severity == "FATAL":
            col = bcolors.ERROR + bcolors.BOLD

        # If we set a color, make sure to also unset it later:
        if col !=  "":
            end_col = bcolors.ENDC

        if severity == "SKIP" and Log.truncate_long_error_messages:
            num_lines = msg.count( "\n" )
            if num_lines > 2:
                index = msg.find("\n")  # first newline
                index = msg.find("\n", index+1) #second newline
                index = msg.find("\n", index+1) #second newline
                msg = msg[:index]
                msg += "\n\t... (Message truncated, run with --show_full_errors " +\
                        "to see full message!)"

        print( f"{col}[{severity}|{module}]{end_col} {msg}" )


    @staticmethod
    def create_timestamp() -> str:
        """ Creates a time stamp in the format "YYYY-MM-DD HH:MM:SS"
        """
        now = datetime.now()
        date = now.date()
        time = now.time()
        return f"{date} {time.isoformat(timespec='seconds')}"


    @staticmethod
    def cache_run_config(
            **kwargs
    ) -> None:
        """ Cache the run configuration to be able to save it later.

        Run configuration means how the calling script is configured for the current run:
        date, command line arguments, comment about the purpose of the pipeline run, etc.
        Properties of the pipeline object are not saved because the activity of
        PipelineBlocks on each DataSample is logged there.

        Caching needs to be done at the initialization because that is when
        command line arguments are passed on. Saving is done at the beginning of the
        pipeline run iff blocks are run on the DataSet (otherwise, there will be no changes
        to the content of the DataSet, e.g. when creating plots only).

        Args:
            **kwargs: All arguments passed on to the pipeline at initialization.

        """
        Log.run_config['date'] = Log.create_timestamp()
        if hasattr(__main__, '__file__'):
            Log.run_config['script'] = os.path.basename(__main__.__file__)
        else:
            Log.run_config['script'] = 'No script available, probably run from the interpreter'
        # avoid KeyError if run from the interpreter
        if 'comment' not in kwargs:
            kwargs['comment'] = None
        # obtain git directory
        has_git_repo = GitRepo.initialize()
        # if code has been copied instead of cloned we can't track code changes
        kwargs['has_git_repo'] = has_git_repo
        if not has_git_repo:
            Log.log(module="Logging", severity="WARN", msg="No git repository found! "
                    "Cannot track code for data creation")
        # filter cmd line args here for the ones that are interesting
        ignore_args = ['data_path', 'statistics_only', 'launch_sofa_gui']
        for key, value in kwargs.items():
            if key not in ignore_args:
                Log.run_config[key] = value


    @staticmethod
    def compile_run_log_entry() -> List[str]:
        return
        """ When the DataSet contents are manipulated, create a log entry
        with the current pipeline run details.

        Structure:
        ==========================
        YYYY-MM-DD HH:MM:SS Dataset created/modified
        [Purpose: <comment>]
        [Script run: <name of invoking script>]
        Code: Commit/Diff saved based on commit <commit-hex-sha>[, untracked files present]
              / No associated git repository
        --command_line_arg1 value
        --command_line_arg2 value
        --------------------------

        Returns:
            Lines (ending in \n) with a formatted log file entry about the
            current pipeline run.
        """
        # assemble log entry
        output = ["==========================\n"]
        output += [f"{Log.run_config['date']} Dataset created/modified\n"]

        # create commented optional argument logs as
        # "<Comment>: <argument value>"
        optional_args =          ['comment',  'script']
        optional_args_comments = ['Purpose:', 'Script run:']
        for arg, comment in zip(optional_args, optional_args_comments):
            if Log.run_config[arg] is not None:
                output += [f"{comment} "
                           f"{Log.run_config[arg]}\n"]

        # log info about code to help reproducibility
        if Log.run_config['has_git_repo']:
            commit = GitRepo.get_last_commit_sha()

            if GitRepo.is_repo_clean():
                # Code: Commit ejhqbanskfmnesbn
                output += [f"Code: Commit {commit}\n"]
            else:
                # warn about unclean directory
                Log.log(module="Logging", severity="WARN", msg="Uncommitted changes are present in "
                        "the repository! If pipeline is run without the --statistics-only flag, "
                        "changes to tracked files will be saved to diff folder, but untracked files "
                        "will be lost!")
                untracked = ''
                if GitRepo.has_untracked_files():
                    untracked = ', untracked files present'

                # tracked files only and with untracked files
                if GitRepo.has_tracked_file_changes():
                    # Code: Diff saved based on commit zujwhsaliwkhasdnfö[, untracked files present]
                    output += [f"Code: Diff saved based on commit {commit}{untracked}\n"]
                # only untracked files
                else:
                    # Code: Commit ejhqbanskfmnesbn, untracked files present
                    output += [f"Code: Commit {commit}{untracked}\n"]
        else:
            # Code: No associated git repository
            output += [f"Code: No associated git repository\n"]

        # ignore all keywords in run config that have been dealt with already
        ignore_keys = ['date', 'has_git_repo']
        ignore_keys += optional_args
        for key, value in Log.run_config.items():
            if key not in ignore_keys:
                output += [f"--{key} {value}\n"]
        output += ["--------------------------\n"]

        return output


    @staticmethod
    def compile_diff_file() -> Tuple[str, str]:
        """ Create a file name and the contents of a code git diff file.

        Collect necessary information to keep track of code used to generate the data.
        The timestamp relates the file to the corresponding entry in the DataSet-level
        history.log file. The commit SHA is also reported there, but repeated in the
        filename to keep the diff self-contained.
        The trailing newline is needed for git apply to recognize the file as uncorrupted.

        Returns:
            filename, diff
            filename: Name of the diff file in the format YYYY-MM-DD_HH:MM:SS_diff_to_<commit-hex-sha>.diff
            diff: Terminal output of the "git diff" command as a single string with a trailing newline.

        """
        date = Log.run_config['date'].replace(" ", "_")
        commit = GitRepo.get_last_commit_sha()
        filename = f"{date}_diff_to_{commit}.diff"
        return filename, GitRepo.get_diff()


    @staticmethod
    def is_diff_needed() -> bool:
        return False
        """Check if a code git diff file should be created.

        Second function: hide git specificities from the Pipeline class.
        Note that this ignores the presence of untracked files as we don't save them automatically
        for now.

        Returns:
            True if there is changes to tracked files, False otherwise.
        """
        # if repo is dirty but it's only untracked files, we don't save them
        # so we only ask for tracked file changes here
        return GitRepo.has_tracked_file_changes()

