#!/usr/bin/env python3
__author__      = "Jérôme Cuq"
__copyright__   = "Copyright 2026, Jérôme Cuq"
__license__     = "BSD-3-Clause"

import argparse
import fnmatch
import sys, os, json
from helpers import *


def load_config(config_file: str) -> dict:
    """load config file

    :param config_file: path to config file
    :type config_file: str
    :return: config as a dict
    :rtype: dict
    """
    result:dict = {}
    if not os.path.exists(config_file):
         log_error("Config file <"+config_file+"> does not exist", True)
         return

    with open(config_file, 'r') as f:
        try:
            result = json.load(f)
        except json.JSONDecodeError:
            log_error("Config file <"+config_file+"> is not a valid JSON file", True)
            return
    if not isinstance(result, list):
        log_error("Config file <"+config_file+"> is not valid, it must contain a list : [...]", True)
        return
    for pair in result:
        if 'source' not in pair or 'target' not in pair:
            log_error("Config file <"+config_file+"> is not valid, each pair must contain 'source' and 'target' keys", True)
            return
        if not isinstance(pair['source'],str) or not isinstance(pair['target'],str):
            log_error("Config file <"+config_file+"> is not valid, 'source' and 'target' values must be strings", True)
            return

    return result

def sync_folder_pair(pair:dict, action: str, create_target: bool = False, verbose: bool = False):
    """synchronize two folders in mirror mode (left to right only, left files remain unchanged)

    :param source: path to source folder
    :type source: str
    :param target: path to target folder
    :type target: str
    :param create_target: indicates whether the function must create target folder if it does not exist, defaults to False
    :type create_target: bool, optional
    """
    source = replace_env_variables(pair['source'])
    target = replace_env_variables(pair['target'])
    cmp_content = pair.get('cmp_files_content', False)
    
    log(("Synchronizing" if action=='sync' else "Comparing") + " <"+source+"> to <"+target+">...")

    if not os.path.exists(source):
         log_error("Source folder <"+source+"> does not exist", True)
         return

    if not os.path.exists(target):
        if create_target:
            os.makedirs(target)
        else:
            log_error("Target folder <"+target+"> does not exist", True)
            return
    
    includes_regex = pair.get('include_regex', [])
    if len(includes_regex)==0:
        # if no include regex is given, we use include patterns instead (if any) by converting them to regex
        includes=pair.get('include', [])
        includes_regex = [r'|'.join([fnmatch.translate(x.replace('/',os.sep)) for x in includes])]
    excludes_regex = pair.get('exclude_regex', [])
    if len(excludes_regex)==0:
        # if no exclude regex is given, we use exclude patterns instead (if any) by converting them to regex
        excludes=pair.get('exclude', [])
        excludes_regex = [r'|'.join([fnmatch.translate(x.replace('/',os.sep)) for x in excludes])]
    
    cmpres = compare_dirs(source, target, include=includes_regex, exclude=excludes_regex, compare_file_content=cmp_content)
    
    if action=='compare' or verbose:
        log("  Comparison results:")
        log("    Left only: " + str(len(cmpres.left_only)))
        log("    Right only: " + str(len(cmpres.right_only)))
        log("    Equal: " + str(len(cmpres.equal)))
        log("    Different: " + str(len(cmpres.different)))
        log('')

    if action=='compare':
        if cmpres.left_only:
            log("  Files only in source folder:")
            for f in sorted(cmpres.left_only):
                log("   | ."+os.path.sep+f)
            log('')
        if cmpres.right_only:
            log("  Files only in target folder:")
            for f in sorted(cmpres.right_only):
                log("   | ."+os.path.sep+f)
            log('')
        if cmpres.different:
            log("  Files that are different between source and target folders:")
            for f in sorted(cmpres.different):
                log("   | ."+os.path.sep+f)
            log('')

    if len(cmpres.errors)>0:
        log("")
        for error in cmpres.errors:
            log_error("  "+str(error[1])+" : "+str(error[0]))

    if action=='sync':
        sync_dirs(source, target, cmpres, verbose)
    

    
def sync_folders_pairs(pairs: list, action: str, create_target: bool = False, verbose: bool = False):
    """synchronize folders pairs in mirror mode (left to right only, left files remain unchanged)

    :param pairs: list of dict containing 'source' and 'target' keys, representing folders pairs to synchronize
    :type pairs: list
    :param create_target: indicates whether the function must create target folders if they do not exist, defaults to False
    :type create_target: bool, optional
    """
    for pair in pairs:
        sync_folder_pair(pair, action, create_target, verbose)
        log("")
        

def main(argv):
    argParser = argparse.ArgumentParser(description="This script synchronize folders pairs from a config file, in mirror mode (left to right only, left files remain unchanged). It can also be used to show differences between folders pairs, without synchronizing them.")
    argParser.add_argument("config_file", help="path to config file")
    argParser.add_argument("action", help="action, among ['sync', 'compare']. 'sync': actually synchronizes folders (default action). 'compare': only shows differences between folders", nargs='?')
    argParser.add_argument("-c", "--create", help="create target folders if do not exist", action='store_true')
    argParser.add_argument("-v", "--verbose", help="verbose mode", action='store_true')
    args = argParser.parse_args()

    if (args.action is None):
        args.action = 'sync'
    elif (args.action not in ['sync', 'compare']):
        log_error('invalid action given : '+args.action, True)

    config = load_config(args.config_file)
    if config is not None:
        sync_folders_pairs(config, args.action, args.create, args.verbose)

if __name__ == "__main__":
   main(sys.argv[1:])