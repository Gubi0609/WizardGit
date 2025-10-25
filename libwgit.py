import argparse # Used for parsing CLI commands
import configparser # Used for reading and writing INI format
from datetime import datetime # Used for date/time manipulation
import grp, pwd # Used for reading user(pwd)/group(grp) database on Unix
from fnmatch import fnmatch # Used to match filenames against patterns (for .gitignore)
import hashlib # Used for Git SHA-1 function
from math import ceil # Used for ???
import os # Used for filesystem
import re # used for regular expressions
import sys # Used for accessing actual command-line arguments
import zlib # Used to compress

argparser = argparse.ArgumentParser(prog='WizardGit', description='A Git like program inspired by Wizardry')

# We need to handle subcommands (like init, commit and so on)
argsubparsers = argparser.add_subparsers(title="Commands", dest="command")
argsubparsers.required = True

def main(argv=sys.argv[1:]):
    args = argparser.parse_args(argv)
    match args.command:
        case "add"          : cmd_add(args)
        case "cat-file"     : cmd_cat_file(args)
        case "check-ignore" : cmd_check_ignore(args)
        case "checkout"     : cmd_checkout(args)
        case "commit"       : cmd_commit(args)
        case "hash-object"  : cmd_hash_object(args)
        case "init"         : cmd_init(args)
        case "log"          : cmd_log(args)
        case "ls-files"     : cmd_ls_files(args)
        case "ls-tree"      : cmd_ls_tree(args)
        case "rev-parse"    : cmd_rev_parse(args)
        case "rm"           : cmd_rm(args)
        case "show-ref"     : cmd_show_ref(args)
        case "status"       : cmd_status(args)
        case "tag"          : cmd_tag(args)
        # Wizard commmands
        case _              : print("Unrecognized command. Please use --help to see recognized commands")

class GitRepository (object):
    """A Git reposiository"""

    worktree = None
    gitdir = None
    conf = None

    def __init__(self, path, force=False):
        self.worktree = path
        self.gitdir = os.path.join(path, ".git")

        if not (force or os.path.isdir(self.gitdir)):
            raise Exception(f"Not a Git repository {path}")

        # Read configuration file in .git/config
        self.conf = configparser.ConfigParser()
        cf = repo_file(self, "config")

        if cf and os.path.exists(cf):
            self.conf.read([cf])
        elif not force:
            raise Exception("Configuration file missing")

        if not force:
            vers = int(self.conf.get("core", reposiositoryformatversion))
            if vers != 0:
                raise Exception(f"Unsupported reposiositoryformatversion: {vers}")


def repo_path(repo, *path):
    """
    Compute path under repo's gitdir.
    :param repo: The Git repository.
    :param *path: The path to build. * means that it can be given as multiple arguments.
    """
    return os.path.join(repo.gitdir, *path)

def repo_file(repo, *path, mkdir=False):
    """
    Same as repo_path, but create dirname(*path) if absent.  For example, repo_file(r, \"refs\", \"remotes\", \"origin\", \"HEAD\") will create .git/refs/remotes/origin.
    :param repo: The Git repository.
    :param path: The path to build. * means that it can be given as multiple arguments.
    :param mkdir: Whether to make directory or not. Should be parsed by name (eg. mkdir=True) since path is multiple arguments.
    """

    if repo_dir(repo, *path[:-1], mkdir=mkdir):
        return repo_path(repo, *path)

def repo_dir(repo, *path, mkdir=False):
    """
    Same as repo_path, but mkdir *path if absent is mkdir.
    :param repo: The Git repository.
    :param path: The path to build. * means that it can be given as multiple arguments.
    :param mkdir: Whether to make directory or not. Should be parsed by name (eg. mkdir=True) since path is multiple arguments.
    """

    path = repo_path(repo, *path)

    if os.path.exists(path):
        if (os.path.isdir(path)):
            return path
        else:
            raise Exception(f"Not a directory {path}")

    if mkdir:
        os.makedirs(path)
        return path
    else:
        return None

def repo_create(path):
    """
    Create a new repository at path.
    :param path: Path to new repository.
    """

    repo = GitRepository(path, True)

    # We first make sure, that the path either exists or is an epty dir.
    
    if os.path.exists(repo.worktree):
        if not os.path.isdir(repo.worktree):
            raise Exception(f"{path} is not a directory!")
        if os.path.exists(repo.gitdir) and os.listdir(repo.gitdir):
            raise Exception(f"{path} is not empty!")
    else:
        os.makedirs(repo.worktree)

    assert repo_dir(repo, "branches", mkdir=True)
    assert repo_dir(repo, "objects", mkdir=True)
    assert repo_dir(repo, "refs", "tags", mkdir=True)
    assert repo_dir(repo, "refs", "heads", mkdir=True)

    # .git/description
    with open(repo_file(repo, "descriotion"), "w") as f:
        f.write("Unnamed repository; edit this file 'description' to name the repository.\n")

    # .git/HEAD
    with open(repo_file(repo, "HEAD"), "w") as f:
        f.write("ref: refs/heads/master\n")

    # .git/config
    with open(repo_file(repo, "config"), "w") as f:
        config = repo_default_config()
        config.write(f)

    return repo

def repo_default_config():
    """
    Create a default repository config for WizardGit
    """
    ret = configparser.ConfigParser()

    ret.add_section("core")
    ret.set("core", "reposiositoryformatversion", "0") # WizardGit will only accept 0 as reposiositoryformatversion.
    ret.set("core", "filemode", "false")
    ret.set("core", "bare", "false")

    return ret

argsp = argsubparsers.add_parser("init", help="Initialize a new, empty repository.")
argsp.add_argument("path", metavar="directory", nargs="?", default=".", help="Where to create the repository.")

def cmd_init(args):
    repo_create(args.path)

