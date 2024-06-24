from git import Repo
from git.exc import InvalidGitRepositoryError


class GitRepo:
    """Wrapper for GitPython that only exposes our simple needs. Manages one repo object for the
     git repository that this code file resides in - ideally the nonrigid-data-generation-pipeline -
     and provides some status information."""

    # keep track of our repo
    repo = None

    @staticmethod
    def initialize() -> bool:
        """Initialize and keep a repo object to query later.

        Returns:
            True if a repository could be found in a parent directory of this file
            (when pipeline has been cloned). False otherwise (e.g. when code has simply
            been downloaded).
        """
        try:
            GitRepo.repo = Repo(__file__, search_parent_directories=True)
        except InvalidGitRepositoryError:
            return False

        return True

    @staticmethod
    def get_last_commit_sha() -> str:
        """Get the hex SHA of the most current commit (as found by git log -n 1)."""
        return GitRepo.repo.head.commit.hexsha

    @staticmethod
    def is_repo_clean() -> bool:
        """Check if there is any uncommitted changes (tracked files and untracked files)
        in the working directory."""
        return not GitRepo.repo.is_dirty()

    @staticmethod
    def get_diff() -> str:
        """Get the diff between the current status of the working directory and the most
        current commit.

        The result is suitable for use with git apply to reproduce the recorded changes
        on the reference commit.

        Returns:
            Text as it would be printed to the terminal by calling git diff, including
            a newline at the end, as a single string that can be written by a standard
            filestream.write() or filestream.writelines().
        """
        # use Git(gitdb.util.LazyMixin) class to call the Git binary
        # this command equals "git diff" in a terminal
        diff_content = GitRepo.repo.git.diff()
        # for creating a correct diff file, we need a trailing newline
        return ''.join([diff_content, "\n"])

    @staticmethod
    def has_untracked_files()-> bool:
        """Check for untracked files in the working directory."""
        return bool(GitRepo.repo.untracked_files)

    @staticmethod
    def has_tracked_file_changes() -> bool:
        """Check for uncommitted changes to tracked files in the working directory,
        including changes already submitted to the staging area."""
        # obtain diff between working directory and last commit
        diffs = GitRepo.repo.head.commit.diff(None)
        # returns a DiffIndex which behaves like a Python list, one entry per changed file
        return bool(diffs)

