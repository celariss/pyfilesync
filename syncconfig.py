__author__      = "Jérôme Cuq"
__license__     = "BSD-3-Clause"

import fnmatch, os
import json
import re
from helpers import *


class GlobalSection:
    """Parameters in global section apply to all pair sections in configuration"""
    def __init__(self):
        self.cmp_files_content:bool = False
        # self.include_patterns is built from self.include_regex and self.include (not loaded from config file)
        self.include_patterns:list[str] = []
        # self.exclude_patterns is built from self.exclude_regex and self.exclude (not loaded from config file)
        self.exclude_patterns:list[str] = []
        self.include_regex:list[str] = []
        self.exclude_regex:list[str] = []
        self.include:list[str] = []
        self.exclude:list[str] = []
        self.history_mode_depth:int = 0
        self.history_mode_file_max_saved_size:int = 0

    def load(self, config:dict) -> list[str]:
        errors:list = []

        self.cmp_files_content = config.get('cmp_files_content', False)
        self.include = SyncConfig.check_list(config.get('include', []), 'global.include', errors)
        self.exclude = SyncConfig.check_list(config.get('exclude', []), 'global.exclude', errors)
        self.include_regex = SyncConfig.check_list(config.get('include_regex', []), 'global.include_regex', errors)
        self.exclude_regex = SyncConfig.check_list(config.get('exclude_regex', []), 'global.exclude_regex', errors)
        (self.include_patterns, self.exclude_patterns) = SyncConfig.get_patterns(config)
        history_data:dict = config.get('history_mode', {})
        if not isinstance(history_data, dict):
            errors.append("Config file is not valid, 'history_mode' must be a dictionary")
            self.history_mode_depth = 0
            self.history_mode_file_max_saved_size = -1
        else:
            self.history_mode_depth = history_data.get('depth', 0)
            self.history_mode_file_max_saved_size = history_data.get('file_max_saved_size', -1)
        if self.history_mode_file_max_saved_size != -1:
            self.history_mode_file_max_saved_size = value_with_unit_to_int(self.history_mode_file_max_saved_size, -1)
            if self.history_mode_file_max_saved_size == -1:
                errors.append("Config file is not valid, 'history_mode.file_max_saved_size' value is not valid : "+str(history_data.get('file_max_saved_size', '')))
        else:
            self.history_mode_file_max_saved_size = 0
        return errors
   

class PairSection:
    """a pair section contains synchronization parameters of a folders pair"""
    def __init__(self):
        self.name:str = ''
        self.left:str = ''
        self.right:str = ''
        self.cmp_files_content:bool = False
        self.include_patterns:list[str] = []
        self.exclude_patterns:list[str] = []
        self.include_regex:list[str] = []
        self.exclude_regex:list[str] = []
        self.include:list[str] = []
        self.exclude:list[str] = []
        self.history_mode_depth:int = 0
        self.history_mode_file_max_saved_size:int = 0

    def load(self, pairconfig: dict, globalconfig:GlobalSection) -> list[str]:
        errors:list = []

        """fill this instance fields from dictionary. The given global config is used to fill fields not defined in "pairconfig"."""
        self.name = pairconfig.get('name', '-')
        self.left = replace_env_variables(pairconfig['left'])
        self.right = replace_env_variables(pairconfig['right'])
        self.cmp_files_content = pairconfig.get('cmp_files_content', globalconfig.cmp_files_content)

        self.include = SyncConfig.check_list(pairconfig.get('include', []), self.name+'.include', errors)
        self.exclude = SyncConfig.check_list(pairconfig.get('exclude', []), self.name+'.exclude', errors)
        self.include_regex = SyncConfig.check_list(pairconfig.get('include_regex', []), self.name+'.include_regex', errors)
        self.exclude_regex = SyncConfig.check_list(pairconfig.get('exclude_regex', []), self.name+'.exclude_regex', errors)
        (self.include_patterns, self.exclude_patterns) = SyncConfig.get_patterns(pairconfig)
        self.include_patterns.extend(globalconfig.include_patterns)
        self.exclude_patterns.extend(globalconfig.exclude_patterns)

        history_data:dict = pairconfig.get('history_mode', {})
        if not isinstance(history_data, dict):
            errors.append("Config file is not valid, 'history_mode' must be a dictionary")
            self.history_mode_depth = 0
            self.history_mode_file_max_saved_size = -1
        else:
            self.history_mode_depth = history_data.get('depth', globalconfig.history_mode_depth)
            self.history_mode_file_max_saved_size = history_data.get('file_max_saved_size', -1)
        if self.history_mode_file_max_saved_size != -1:
            self.history_mode_file_max_saved_size = value_with_unit_to_int(self.history_mode_file_max_saved_size, -1)
            if self.history_mode_file_max_saved_size == -1:
                errors.append("Config file is not valid, 'history_mode.file_max_saved_size' value is not valid : "+str(history_data.get('file_max_saved_size', '')))
        else:
            self.history_mode_file_max_saved_size = globalconfig.history_mode_file_max_saved_size
        return errors

class SyncConfig:
    def __init__(self):
        self.globalconfig:GlobalSection = GlobalSection()
        self.pairs:list[PairSection] = []

    def load_file(self, path: str) -> list[str]:
        """load config from file

        :param path: path to config file
        :return: error text if any error occured
        """
        result:dict = {}
        if not os.path.exists(path):
            return "Config file <"+path+"> does not exist"

        with open(path, 'r', encoding='utf8') as f:
            errors = self.load_json_string(f.read())
            if errors:
                return errors
        return []
    
    def save_file(self, path: str) -> str:
        """save config to a file
        :param path: path to config file
        :return: error text if any error occured
        """
        try:
            with open(path, 'w', encoding='utf8') as f:
                json.dump(self.to_dict(), f, indent=4, ensure_ascii=False)
        except Exception as exc:
            return "Error while saving config file: " + str(exc)
        return None
    
    def to_dict(self) -> dict:
        """convert this config to a dict that can be easily converted to json"""
        return {
            'global': {
                'cmp_files_content': self.globalconfig.cmp_files_content,
                'include_regex': self.globalconfig.include_regex,
                'exclude_regex': self.globalconfig.exclude_regex,
                'include': self.globalconfig.include,
                'exclude': self.globalconfig.exclude,
                'history_mode': {
                    'depth': self.globalconfig.history_mode_depth,
                    'file_max_saved_size': self.globalconfig.history_mode_file_max_saved_size
                }
            },
            'pairs': [
                {
                    'name': pair.name,
                    'left': pair.left,
                    'right': pair.right,
                    'cmp_files_content': pair.cmp_files_content,
                    'include_regex': pair.include_regex,
                    'exclude_regex': pair.exclude_regex,
                    'include': pair.include,
                    'exclude': pair.exclude,
                    'history_mode': {
                        'depth': pair.history_mode_depth,
                        'file_max_saved_size': pair.history_mode_file_max_saved_size
                    }
                } for pair in self.pairs
            ]
        }

    def load_json_string(self, config:str) -> list[str]:
        """load config from a string

        :param config: string containing the configuration in json format
        :return: error text if any error occured
        """
        try:
            result = json.loads(config)
        except json.JSONDecodeError as exc:
            return ["Config file is not a valid JSON file"]
        if not isinstance(result, dict):
            return ["Config file is not valid, it must contain a dictionary : {...}"]
        return self.load_dict(result)

    def load_dict(self, config:dict) -> list[str]:
        """load config from a python dict

        :param config: dict containing the configuration data
        :return: error text if any error occured
        """
        errors:list = []
        
        self.globalconfig = GlobalSection()
        if 'global' in config:
            errors = self.globalconfig.load(config['global'])

        if 'pairs' not in config or not isinstance(config['pairs'], list):
            errors.append("Config file is not valid, it must contain a 'pairs' key with a list of folders pairs to synchronize")
            config['pairs'] = []
        for paircfg in config['pairs']:
            if 'left' not in paircfg or not isinstance(paircfg['left'],str):
                errors.append( "Config file is not valid, each pair must contain 'left' string key")
                paircfg['left'] = ''
            if 'right' not in paircfg or not isinstance(paircfg['right'],str):
                errors.append( "Config file is not valid, each pair must contain 'right' string key")
                paircfg['right'] = ''
        
        self.pairs = []
        idx = 0
        for paircfg in config.get('pairs', []):
            idx += 1
            if paircfg.get('name', '') == '':
                paircfg['name'] = 'pair_%d' % idx
            pair_name = paircfg.get('name', '')
            if not re.match("^[A-Za-z0-9_-]*$", pair_name):
                errors.append("Invalid pair name '%s' : pair names may only contain '-', '_' and alphanumeric characters" % pair_name)
            pair = PairSection()
            errors.extend( pair.load(paircfg, self.globalconfig) )
            self.pairs.append(pair)
        return errors
 
    def check_list(obj:any, name:str=None, errors:list=None) -> list:
        """Check that the given object is a list, and raise SyncConfig.Error if not"""
        if not isinstance(obj, list):
            if errors is not None:
                errors.append("Invalid config file : '"+str(name)+"' key must be a list")
            return []
        return obj
    
    def check_list_and_replace_envars(obj:any, name:str=None, errors:list=None) -> list:
        """Check that the given object is a list, and raise SyncConfig.Error if not"""
        return [replace_env_variables(x) for x in SyncConfig.check_list(obj, name, errors)]


    def get_patterns(config:dict) -> tuple[list,list,str]:
        """
        convert include/exclude glob patterns to regex and concatenate them with include/exclude regex.
        env vars are replaced by their respecting values.
        :return: (include_patterns list, exclude_patterns list)
        """
        exclude_patterns:list = SyncConfig.check_list_and_replace_envars(config.get('exclude_regex', []))
        include_patterns:list = SyncConfig.check_list_and_replace_envars(config.get('include_regex', []))

        exclude:list = SyncConfig.check_list_and_replace_envars(config.get('exclude', []))
        include:list = SyncConfig.check_list_and_replace_envars(config.get('include', []))
        
        # -> we use include patterns (if any) by converting them to regex
        if len(include)>0:
            include_patterns.extend([r'|'.join([fnmatch.translate(x) for x in include])])
        if len(exclude)>0:
            exclude_patterns.extend([r'|'.join([fnmatch.translate(x) for x in exclude])])

        return (include_patterns, exclude_patterns)