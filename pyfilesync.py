#!/usr/bin/env python3
__author__      = "Jérôme Cuq"
__copyright__   = "Copyright 2026, Jérôme Cuq"
__license__     = "BSD-3-Clause"

import argparse
import fnmatch
import sys, os, json
from helpers import *

def check_list(obj, name:str):
    if not isinstance(obj, list):
        log_error("Invalid config file : '"+name+"' key must be a list", True)
    
class GlobalConfig:
    """Global configuration for the script, loaded from config file"""
    def __init__(self, config: dict):
        self.exclude:list = config.get('exclude', [])
        self.include:list = config.get('include', [])
        self.exclude_regex:list = config.get('exclude_regex', [])
        self.include_regex:list = config.get('include_regex', [])
        self.cmp_files_content:bool = config.get('cmp_files_content', False)
        check_list(self.exclude, 'global.exclude')
        check_list(self.include, 'global.include')
        check_list(self.exclude_regex, 'global.exclude_regex')
        check_list(self.include_regex, 'global.include_regex')


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
    if not isinstance(result, dict):
        log_error("Config file <"+config_file+"> is not valid, it must contain a di[ctionary : {...}", True)
        return
    if 'pairs' not in result:
        log_error("Config file <"+config_file+"> is not valid, it must contain a 'pairs' key with a list of folders pairs to synchronize", True)
        return
    for pair in result['pairs']:
        if 'source' not in pair or 'target' not in pair:
            log_error("Config file <"+config_file+"> is not valid, each pair must contain 'source' and 'target' keys", True)
            return
        if not isinstance(pair['source'],str) or not isinstance(pair['target'],str):
            log_error("Config file <"+config_file+"> is not valid, 'source' and 'target' values must be strings", True)
            return

    return result

def sync_folder_pair(pair:dict, globalconfig: GlobalConfig, action: str, create_target: bool = False, verbose: bool = False) -> set:
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
    cmp_content = pair.get('cmp_files_content', globalconfig.cmp_files_content)
    
    log(("Synchronizing" if action=='sync' else "Comparing") + " <"+source+"> to <"+target+">...")

    if not os.path.exists(source):
         log_error("Source folder <"+source+"> does not exist")
         return

    if not os.path.exists(target):
        if create_target:
            os.makedirs(target)
        else:
            log_error("Target folder <"+target+"> does not exist")
            return
        
    check_list(pair.get('include', []), 'include')
    check_list(pair.get('exclude', []), 'exclude')
    check_list(pair.get('include_regex', []), 'include_regex')
    check_list(pair.get('exclude_regex', []), 'exclude_regex')
    
    # preparing the list of include regex patterns
    includes_regex = pair.get('include_regex', []) + globalconfig.include_regex
    # -> we use include patterns (if any) by converting them to regex
    includes=pair.get('include', [])
    if includes:
        includes_regex.extend([r'|'.join([fnmatch.translate(x) for x in includes])])
    
    # preparing the list of exclude regex patterns
    excludes_regex = pair.get('exclude_regex', []) + globalconfig.exclude_regex
    # -> we use exclude patterns (if any) by converting them to regex
    excludes=pair.get('exclude', [])
    if excludes:
        excludes_regex.extend([r'|'.join([fnmatch.translate(x) for x in excludes])])

    errors = set()
    cmpres = compare_dirs(source, target, include=includes_regex, exclude=excludes_regex, compare_file_content=cmp_content)
    errors.update(cmpres.errors)

    if action=='compare':
        if verbose:
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
        log("  Comparison results:")
        log("    Left only: %d files" % len(cmpres.left_only))
        log("    Right only: %d files" % len(cmpres.right_only))
        log("    Equal: %d files" % len(cmpres.equal))
        log("    Different: %d files" % len(cmpres.different))
        log('')

    if action=='sync':
        syncdata:SyncData = sync_dirs(source, target, cmpres, verbose)
        errors.update( syncdata.errors )
        log("  Synchronization results:")
        log("    Copied: %d files (%d Mb)" % (syncdata.nb_copied, syncdata.size_copied/1024/1024))
        log("    Updated: %d files (%d Mb)" % (syncdata.nb_updated, syncdata.size_updated/1024/1024))
        log("    Deleted: %d files" % syncdata.nb_deleted)
        log('')

    return errors

    
def sync_folders_pairs(config: dict, action: str, create_target: bool = False, verbose: bool = False):
    """synchronize folders pairs in mirror mode (left to right only, left files remain unchanged)

    :param pairs: list of dict containing 'source' and 'target' keys, representing folders pairs to synchronize
    :type pairs: list
    :param create_target: indicates whether the function must create target folders if they do not exist, defaults to False
    :type create_target: bool, optional
    """
    if 'global' in config:
        globalconfig = GlobalConfig(config['global'])
    else:
        globalconfig = GlobalConfig({})
    pairs:list = config.get('pairs', [])
    errors = set()
    for pair in pairs:
        errors.update(sync_folder_pair(pair, globalconfig, action, create_target, verbose))
    log('All jobs done')

    if errors:
        log_error("%d errors encountered during comparison/synchronization :" % len(errors))
        for error in errors:
            log_error("  "+str(error[1])+" : "+str(error[0]))
    else:
        log("No error encountered")
        

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