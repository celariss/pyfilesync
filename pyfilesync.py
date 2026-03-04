#!/usr/bin/env python3
__author__      = "Jérôme Cuq"
__copyright__   = "Copyright 2026, Jérôme Cuq"
__license__     = "BSD-3-Clause"
__version__     = "1.0.1"

import argparse
import fnmatch
import sys, os
from syncconfig import *
from helpers import *
from dirsyncer import *

def sync_folder_pair(pair:PairSection, globalconfig: GlobalSection, action: str, create_root: bool = False,
                     restore:bool = False, ignore_target_only:bool = False, verbose: bool = False) -> set:
    """synchronize two folders in mirror mode (left to right only, left files remain unchanged)

    :param pair: dictionary containing parameters for a folder pair
    :param globalconfig: global configuration section loaded from config file
    :param action: action to perform, among 'sync' and 'compare'
    :param create_root: indicates whether the function must create right folder if it does not exist, defaults to False
    :param restore: indicates whether the function must restore right folder from left folder, defaults to False
    :param ignore_target_only: indicates whether the function must ignore files only in target folder, defaults to False
    :param verbose: indicates whether the function must be verbose, defaults to False
    """
    left = pair.right if restore else pair.left
    right = pair.left if restore else pair.right
    
    log(("Synchronizing" if action=='sync' else "Comparing") + " '"+pair.name+"' : <"+left+"> to <"+right+">...")

    if not os.path.exists(left):
         log_error("Left folder <"+left+"> does not exist")
         return {(left, "Left folder does not exist")}

    if not os.path.exists(right):
        if create_root:
            try:
                os.makedirs(right)
            except Exception as e:
                log_error("Could not create right folder : "+right)
                return {(right, str(e))}
        else:
            log_error("Right folder <"+right+"> does not exist")
            return {(right, "Right folder  does not exist")}

    errors = set()
    cmpres:CmpData = DirSyncer.compare_dirs(left, right, include=pair.include_regex+globalconfig.include_regex, exclude=pair.exclude_regex+globalconfig.exclude_regex,
                                            compare_file_content=pair.cmp_files_content, ignore_right_only=ignore_target_only)
    errors.update(cmpres.errors)

    if action=='compare':
        if verbose:
            if cmpres.left_only:
                log("  Files only in left folder:")
                for f in sorted(cmpres.left_only):
                    log("   | ."+os.path.sep+f)
                log('')
            if cmpres.right_only:
                log("  Files only in right folder:")
                for f in sorted(cmpres.right_only):
                    log("   | ."+os.path.sep+f)
                log('')
            if cmpres.different:
                log("  Files that are different between left and right folders:")
                for f in sorted(cmpres.different):
                    log("   | ."+os.path.sep+f)
                log('')
        log("  Comparison results:")
        log("    Left only: %d files" % len(cmpres.left_only))
        log("    Right only: %d files" % len(cmpres.right_only))
        log("    Equal: %d files" % len(cmpres.equal))
        log("    Different: %d files" % len(cmpres.different))

    if action=='sync':
        syncdata:SyncData = DirSyncer.sync_dirs(left, right, cmpres, verbose)
        errors.update( syncdata.errors )
        log("  Synchronization results:")
        log("    Copied: %d files (%d Mb)" % (syncdata.nb_copied, syncdata.size_copied/1024/1024))
        log("    Updated: %d files (%d Mb)" % (syncdata.nb_updated, syncdata.size_updated/1024/1024))
        log("    Deleted: %d files" % syncdata.nb_deleted)

    return errors

    
def sync_folders_pairs(config:SyncConfig, action: str, pairs2process:list[str], create_root:bool = False,
                       restore:bool = False, ignore_target_only:bool = False, verbose: bool = False):
    """synchronize folders pairs in mirror mode (left to right only, left files remain unchanged)

    :param config: config data as a dict, loaded from config file
    :param action: action to perform, among 'sync' and 'compare'
    :param pairs2process: list of dict containing 'left' and 'right' keys, representing folders pairs to synchronize
    :param create_root: indicates whether the function must create right folders if they do not exist, defaults to False
    :param restore: indicates whether the function must restore right folders from left folders, defaults to False
    :param ignore_target_only: indicates whether the function must ignore files only in target folders, defaults to False
    :param verbose: indicates whether the function must be verbose, defaults to False
    """
    if pairs2process is not None:
        for pair_name in pairs2process:
            if not any(pair['name'] == pair_name for pair in config.pairs):
                log_error("No pair with name '%s' found in config file" % pair_name, True)
                return

    errors = set()
    for pair in config.pairs:
        if (not pairs2process) or (pair.name in pairs2process):
            errors.update(sync_folder_pair(pair, config.globalconfig, action, create_root, restore, ignore_target_only, verbose))
            log('')
    log('All jobs done')

    if verbose:
        if errors:
            log_error("%d errors encountered during comparison/synchronization :" % len(errors))
            for error in errors:
                log_error("  "+str(error[1])+" : "+str(error[0]))
        else:
            log("No error encountered")
        

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
    argParser.add_argument("-c", "--create", help="create target folder if needed", action='store_true')
    argParser.add_argument("-r", "--restore", help="change sync direction to restore files (right -> left)", action='store_true')
    argParser.add_argument("-i", "--ignore-target-only", help="Ignore (preserve) files found only in target folder", action='store_true')
    argParser.add_argument("-v", "--verbose", help="verbose mode", action='store_true')
    argParser.add_argument("-V", "--version", help="show version and exit", action='store_true')
    args = argParser.parse_args()
    
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
        log_error('invalid action given : '+args.action, True)

    config:SyncConfig = SyncConfig()
    error = config.load_file(args.config_file)
    if error:
        log_error(error+" : "+args.config_file, True)
       
    if args.action == 'list':
        for pair in config.pairs:
            left = replace_env_variables(pair['left'])
            right = replace_env_variables(pair['right'])
            name = pair['name']
            log('')
            log('Pair "'+name+'" : ')
            log('  | Left : '+left)
            log('  | Right: '+right)
    else:
        sync_folders_pairs(config, args.action, args.pairs, args.create, args.restore, args.ignore_target_only, args.verbose)

if __name__ == "__main__":

   main(sys.argv[1:])
