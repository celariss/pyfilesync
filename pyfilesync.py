#!/usr/bin/env python3
__author__      = "Jérôme Cuq"
__copyright__   = "Copyright 2026, Jérôme Cuq"
__license__     = "BSD-3-Clause"
__version__     = "1.1.0"

import argparse
import fnmatch
import sys, os
from syncconfig import *
from helpers import *
from dirsyncer import *


class FolderPairsSyncResults:
    def __init__(self):
        self.pairs_cmpdata:dict[str,tuple[PairSection,CmpData]] = {}
        self.pairs_syncdata:dict[str,tuple[PairSection,SyncData]] = {}
        
        # cumulated results of all pairs
        self.cmpdata = CmpData()
        self.syncdata = SyncData()
        self.errors:set = set()
        self.warnings:set = set()
        self.nb_left_only:int = 0
        self.nb_right_only:int = 0
        self.nb_equal:int = 0
        self.nb_different:int = 0

    def update(self, pair:PairSection, pair_cmpdata:CmpData, pair_syncdata:SyncData):
        self.nb_left_only  += len(pair_cmpdata.left_only_files)+len(pair_cmpdata.left_only_empty_dirs)
        self.nb_right_only += len(pair_cmpdata.right_only_files)+len(pair_cmpdata.right_only_files_in_dirs)+len(pair_cmpdata.right_only_dirs)
        self.nb_equal      += len(pair_cmpdata.equal_files)
        self.nb_different  += len(pair_cmpdata.different_files)
        self.cmpdata.update(pair_cmpdata)
        self.errors.update(pair_cmpdata.errors)
        self.warnings.update(pair_cmpdata.warnings)
        self.pairs_cmpdata[pair.name] = (pair, pair_cmpdata)
        if pair_syncdata:
            self.syncdata.update(pair_syncdata)
            self.warnings.update(pair_syncdata.warnings)
            self.pairs_syncdata[pair.name] = (pair, pair_syncdata)


def set_root_dir(data:set, root:str) -> set:
    return set({os.path.join(root,e) for e in data})


def log_compare_result(cmpdata, verbose):
    if verbose:
        if cmpdata.left_only_files or cmpdata.left_only_empty_dirs:
            log("  Files only in left folder:")
            for f in sorted(cmpdata.left_only_files):
                log("   | ."+os.path.sep+f)
            for f in sorted(cmpdata.left_only_empty_dirs):
                log("   | ."+os.path.sep+f+os.path.sep)
            log('')
        if cmpdata.right_only_files or cmpdata.right_only_dirs:
            log("  Files only in right folder:")
            for f in sorted(cmpdata.right_only_files):
                log("   | ."+os.path.sep+f)
            for f in sorted(cmpdata.right_only_dirs):
                log("   | ."+os.path.sep+f+os.path.sep)
            log('')
        if cmpdata.different_files:
            log("  Files that are different between left and right folders:")
            for f in sorted(cmpdata.different_files):
                log("   | ."+os.path.sep+f)
            log('')
    log("  Comparison results:")
    blog = False
    nbfiles = len(cmpdata.left_only_files)+len(cmpdata.left_only_empty_dirs)
    if nbfiles:
        blog = True
        log("    Left only: %d files" % nbfiles)
    nbfiles = len(cmpdata.right_only_files)+len(cmpdata.right_only_files_in_dirs)+len(cmpdata.right_only_dirs)
    if nbfiles:
        blog = True
        log("    Right only: %d files" % nbfiles)
    if len(cmpdata.equal_files):
        blog = True
        log("    Equal: %d files" % len(cmpdata.equal_files))
    if len(cmpdata.different_files):
        blog = True
        log("    Different: %d files" % len(cmpdata.different_files))
    if not blog:
        log('    -- No files found in source ! --')


def log_sync_result(syncdata, verbose):
    if syncdata.nb_copied or syncdata.nb_updated or syncdata.nb_deleted:
        log("  Synchronization results:")
        if syncdata.nb_copied:
            log("    Copied: %d files (%d Mb)" % (syncdata.nb_copied, syncdata.size_copied/1024/1024))
        if syncdata.nb_updated:
            log("    Updated: %d files (%d Mb)" % (syncdata.nb_updated, syncdata.size_updated/1024/1024))
        if syncdata.nb_deleted:
            log("    Deleted: %d files" % syncdata.nb_deleted)


def sync_folder_pair(pair:PairSection, action: str, create_root: bool = False,
                     restore:bool = False, ignore_target_only:bool = False, verbose: bool = False) -> tuple[CmpData,SyncData]:
    """synchronize two folders in mirror mode (left to right or right to left, source files remain unchanged)

    :param pair: pair section containing parameters for a folder pair
    :param action: action to perform, among 'sync' and 'compare'
    :param create_root: indicates whether the function must create right folder if it does not exist, defaults to False
    :param restore: indicates whether the function must restore right folder from left folder, defaults to False
    :param ignore_target_only: indicates whether the function must ignore files only in target folder, defaults to False
    :param verbose: indicates whether the function must be verbose, defaults to False
    """
    left = pair.right if restore else pair.left
    right = pair.left if restore else pair.right
    
    log(("Synchronizing" if action=='sync' else "Comparing") + " '"+pair.name+"' : <"+left+"> to <"+right+">...")

    errors = None
    if not os.path.exists(left):
         log_error("Left folder <"+left+"> does not exist")
         errors=set({(left, "Left folder does not exist")})

    elif not os.path.exists(right):
        if create_root:
            try:
                os.makedirs(right)
            except Exception as e:
                log_error("Could not create right folder : "+right)
                errors=set({(right, str(e))})
        else:
            log_error("Right folder <"+right+"> does not exist")
            errors=set({(right, "Right folder  does not exist")})
    
    if errors:
        return (CmpData(errors=errors), None)

    cmpdata:CmpData = DirSyncer.compare_dirs(left, right, include=pair.include_regex, exclude=pair.exclude_regex,
                                            compare_file_content=pair.cmp_files_content, ignore_right_only=ignore_target_only)

    if action=='compare':
        log_compare_result(cmpdata, verbose)
    
    syncdata:SyncData = None
    if action=='sync' and not cmpdata.errors:
        syncdata = DirSyncer.sync_dirs(left, right, cmpdata, verbose)
        log_sync_result(syncdata, verbose)
    
    cmpdata.left_only_files = set_root_dir(cmpdata.left_only_files, left)
    cmpdata.left_only_empty_dirs = set_root_dir(cmpdata.left_only_empty_dirs, left)
    cmpdata.right_only_dirs = set_root_dir(cmpdata.right_only_dirs, right)
    cmpdata.right_only_files = set_root_dir(cmpdata.right_only_files, right)
    cmpdata.right_only_files_in_dirs = set_root_dir(cmpdata.right_only_files_in_dirs, right)
    cmpdata.equal_files = set_root_dir(cmpdata.equal_files, left)
    cmpdata.different_files = set_root_dir(cmpdata.different_files, left)
    
    return (cmpdata, syncdata)


def sync_folders_pairs(config:SyncConfig, action: str, pairs2process:list[str] = None, create_root:bool = False,
                       restore:bool = False, ignore_target_only:bool = False, verbose: bool = False) -> bool:
    """synchronize folders pairs in mirror mode (left to right or right to left, source files remain unchanged)

    :param config: config data as a dict, loaded from config file
    :param action: action to perform, among 'sync' and 'compare'
    :param pairs2process: list of pair sections , representing folders pairs to synchronize
    :param create_root: indicates whether the function must create right folders if they do not exist, defaults to False
    :param restore: indicates whether the function must restore right folders from left folders, defaults to False
    :param ignore_target_only: indicates whether the function must ignore files only in target folders, defaults to False
    :param verbose: indicates whether the function must be verbose, defaults to False
    """
    res:FolderPairsSyncResults = FolderPairsSyncResults()

    if pairs2process is not None:
        for pair_name in pairs2process:
            if not any(pair.name == pair_name for pair in config.pairs):
                text = "No pair with name '%s' found in config file" % pair_name
                log_error(text)
                res.errors.add((pair_name, text))
                return res

    
    if action not in ['compare', 'sync']:
        text = "Invalid action given : '%s'" % action
        log_error(text)
        res.errors.add((action, text))
        return res

    for pair in config.pairs:
        if (not pairs2process) or (pair.name in pairs2process):
            (pair_cmpdata, pair_syncdata) = sync_folder_pair(pair, action, create_root, restore, ignore_target_only, verbose)
            res.update(pair, pair_cmpdata, pair_syncdata)
            log('')
    
    log('All jobs done, statistics :')
    if action=='compare':
        log("  Left only: %d files" % res.nb_left_only)
        log("  Right only: %d files" % res.nb_right_only)
        log("  Equal: %d files" % res.nb_equal)
        log("  Different: %d files" % res.nb_different)

    if action=='sync':
        log("  Copied: %d files (%d Mb)" % (res.syncdata.nb_copied, res.syncdata.size_copied/1024/1024))
        log("  Updated: %d files (%d Mb)" % (res.syncdata.nb_updated, res.syncdata.size_updated/1024/1024))
        log("  Deleted: %d files" % res.syncdata.nb_deleted)

    if verbose:
        log('')
        if res.warnings:
            log_error("%d warnings encountered during comparison/synchronization :" % len(res.warnings))
            for warning in res.warnings:
                log_error("  "+str(warning[1])+" : "+str(warning[0]))
        else:
            log("No warning encountered")
        if res.errors:
            log_error("%d errors encountered during comparison/synchronization :" % len(res.errors))
            for error in res.errors:
                log_error("  "+str(error[1])+" : "+str(error[0]))
        else:
            log("No error encountered")

    return res
        

def main(argv):
    argParser = argparse.ArgumentParser(
        description="This script synchronize folders pairs from a config file, in mirror mode (left to right only, left files remain unchanged). It can also be used to show differences between folders pairs, without synchronizing them.",
                                        formatter_class=argparse.RawTextHelpFormatter)
    argParser.add_argument("config_file", help="path to config file", nargs='?')
    argParser.add_argument("action", help='''action, among [list, sync, compare]
 > list: lists pairs in config file
 > sync: actually synchronizes folders
 > compare: (default) only shows differences between folders''', nargs='?')
    argParser.add_argument("-p", "--pair", help="select one (or more) specific pair(s) by name", nargs='+', dest='pairs', default=None)
    argParser.add_argument("-c", "--create", help="create root target folder of each pair if needed", action='store_true')
    argParser.add_argument("-r", "--restore", help="change sync direction to restore files (right -> left)", action='store_true')
    argParser.add_argument("-i", "--ignore-target-only", help="Ignore (preserve) files found only in target folder", action='store_true')
    argParser.add_argument("-v", "--verbose", help="verbose mode", action='store_true')
    argParser.add_argument("-V", "--version", help="show version and exit", action='store_true')
    args = argParser.parse_args(argv)
    
    version = os.path.basename(__file__)+" "+__version__
    if args.version:
        log(version)
        return 0
        
    if not args.config_file:
        log_error("the following argument is required: config_file")
        log("use -h flag to see full help")
        return 1

    if (args.action is None):
        args.action = 'compare'
    elif (args.action not in ['list', 'sync', 'compare']):
        log_error('invalid action given : '+args.action)
        return 2

    config:SyncConfig = SyncConfig()
    error = config.load_file(args.config_file)
    if error:
        log_error(error+" : "+args.config_file)
        return 3
       
    if args.action == 'list':
        for pair in config.pairs:
            left = replace_env_variables(pair.left)
            right = replace_env_variables(pair.right)
            name = pair.name
            log('')
            log('Pair "'+name+'" : ')
            log('  | Left : '+left)
            log('  | Right: '+right)
    else:
        res = sync_folders_pairs(config, args.action, args.pairs, args.create, args.restore, args.ignore_target_only, args.verbose)
        if res.errors:
            return 4
    
    return 0

if __name__ == "__main__":
   main(sys.argv[1:])
