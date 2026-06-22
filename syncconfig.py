from __future__ import annotations # needed for python3 older than 3.14
__author__      = "Jérôme Cuq"
__license__     = "BSD-3-Clause"

import fnmatch, os
import json
import re
from helpers import *

CMP_FILE_CONTENT_DEFAULT = False
HISTORY_MODE_DEFAULT_DEPTH = 0
HISTORY_MODE_DEFAULT_FILE_MAX_SAVED_SIZE = 0

class SectionBase:
    """section base class"""
    def __init__(self):        
        self.cmp_files_content:bool = CMP_FILE_CONTENT_DEFAULT

        self.include_patterns_p:list[str] = []
        self.exclude_patterns_p:list[str] = []
        self.include_regex_raw:list[str] = []
        self.exclude_regex_raw:list[str] = []
        self.include_raw:list[str] = []
        self.exclude_raw:list[str] = []

        self.history_mode_depth_p:int = HISTORY_MODE_DEFAULT_DEPTH
        self.history_mode_depth_raw:int = HISTORY_MODE_DEFAULT_DEPTH
        self.history_mode_file_max_saved_size_p:int = HISTORY_MODE_DEFAULT_FILE_MAX_SAVED_SIZE
        self.history_mode_file_max_saved_size_raw:int = HISTORY_MODE_DEFAULT_FILE_MAX_SAVED_SIZE

    def load(self, config:dict, section_name:str, parent:SectionBase = None) -> list[str]:
        errors:list = []

        self.cmp_files_content = config.get('cmp_files_content', parent.cmp_files_content if parent else CMP_FILE_CONTENT_DEFAULT)

        self.include_raw = SyncConfig._check_list(config.get('include', []), section_name + '.include', errors)
        self.exclude_raw = SyncConfig._check_list(config.get('exclude', []), section_name + '.exclude', errors)
        self.include_regex_raw = SyncConfig._check_list(config.get('include_regex', []), section_name + '.include_regex', errors)
        self.exclude_regex_raw = SyncConfig._check_list(config.get('exclude_regex', []), section_name + '.exclude_regex', errors)
        
        history_data:dict = config.get('history_mode', {})
        if not isinstance(history_data, dict):
            errors.append("Config file is not valid, 'history_mode' must be a dictionary")
            self.history_mode_depth_raw = HISTORY_MODE_DEFAULT_DEPTH
            self.history_mode_file_max_saved_size_raw = HISTORY_MODE_DEFAULT_FILE_MAX_SAVED_SIZE
        else:
            self.history_mode_depth_raw = history_data.get('depth', HISTORY_MODE_DEFAULT_DEPTH)
            self.history_mode_file_max_saved_size_raw = history_data.get('file_max_saved_size', HISTORY_MODE_DEFAULT_FILE_MAX_SAVED_SIZE)
        
        self.on_raw_data_changed(errors, parent)

        return errors
    
    def to_dict(self) -> dict:
        """convert this config to a dict that can be easily converted to json"""
        res:dict = {}
        if self.cmp_files_content != CMP_FILE_CONTENT_DEFAULT:
            res['cmp_files_content'] = self.cmp_files_content
        if len(self.include_raw)>0:
            res['include'] = self.include_raw
        if len(self.exclude_raw)>0:
            res['exclude'] = self.exclude_raw
        if len(self.include_regex_raw)>0:
            res['include_regex'] = self.include_regex_raw
        if len(self.exclude_regex_raw)>0:
            res['exclude_regex'] = self.exclude_regex_raw
        
        if self.history_mode_depth_raw != HISTORY_MODE_DEFAULT_DEPTH or self.history_mode_file_max_saved_size_raw != HISTORY_MODE_DEFAULT_FILE_MAX_SAVED_SIZE:
            res['history_mode'] = {}
            if self.history_mode_depth_raw != HISTORY_MODE_DEFAULT_DEPTH:
                res['history_mode']['depth'] = self.history_mode_depth_raw
            if self.history_mode_file_max_saved_size_raw != HISTORY_MODE_DEFAULT_FILE_MAX_SAVED_SIZE:
                res['history_mode']['file_max_saved_size'] = self.history_mode_file_max_saved_size_raw
        return res
    
    def on_raw_data_changed(self, errors:list, parent:SectionBase = None):
        (self.include_patterns_p, self.exclude_patterns_p) = self._get_patterns()
        if parent:
            self.include_patterns_p.extend(parent.include_patterns_p)
            self.exclude_patterns_p.extend(parent.exclude_patterns_p)
        
        self.history_mode_depth_p = self.history_mode_depth_raw
        if self.history_mode_depth_p == HISTORY_MODE_DEFAULT_DEPTH and parent is not None:
            self.history_mode_depth_p = parent.history_mode_depth_p
        
        if isinstance(self.history_mode_file_max_saved_size_raw, str):
            self.history_mode_file_max_saved_size_p = value_with_unit_to_int(self.history_mode_file_max_saved_size_raw, -1)
            if self.history_mode_file_max_saved_size_p == -1:
                errors.append("Config file is not valid, 'history_mode.file_max_saved_size' value is not valid : "+self.history_mode_file_max_saved_size_raw)
                self.history_mode_file_max_saved_size_p = parent.history_mode_file_max_saved_size_p if parent else HISTORY_MODE_DEFAULT_FILE_MAX_SAVED_SIZE
        else:
            self.history_mode_file_max_saved_size_p = self.history_mode_file_max_saved_size_raw

    def _get_patterns(self) -> tuple[list,list,str]:
        """
        convert include/exclude glob patterns to regex and concatenate them with include/exclude regex.
        env vars are replaced by their respecting values.
        :return: (include_patterns list, exclude_patterns list)
        """
        exclude_patterns:list = SyncConfig._check_list_and_replace_envars(self.exclude_regex_raw)
        include_patterns:list = SyncConfig._check_list_and_replace_envars(self.include_regex_raw)

        exclude:list = SyncConfig._check_list_and_replace_envars(self.exclude_raw)
        include:list = SyncConfig._check_list_and_replace_envars(self.include_raw)
        
        # -> we use include patterns (if any) by converting them to regex
        if len(include)>0:
            include_patterns.extend([r'|'.join([fnmatch.translate(x) for x in include])])
        if len(exclude)>0:
            exclude_patterns.extend([r'|'.join([fnmatch.translate(x) for x in exclude])])

        return (include_patterns, exclude_patterns)


class GlobalSection(SectionBase):
    """Parameters in global section apply to all pair sections in configuration"""
    def __init__(self):
        super().__init__()
    
    def load(self, config: dict) -> list[str]:
        return super().load(config, 'global', None)
    
    def to_dict(self) -> dict:
        """convert this config to a dict that can be easily converted to json"""
        return super().to_dict()
    
    def on_raw_data_changed(self, errors:list, parent:SectionBase = None):
        super().on_raw_data_changed(errors, parent)
   

class PairSection(SectionBase):
    """a pair section contains synchronization parameters of a folders pair"""
    def __init__(self):
        super().__init__()
        self.name:str = ''

        self.left_raw:str = ''
        self.left_p:str = ''

        self.right_raw:str = ''
        self.right_p:str = ''

    def load(self, pairconfig: dict, globalconfig:GlobalSection) -> list[str]:
        """fill this instance fields from dictionary. The given global config is used to fill fields not defined in "pairconfig"."""
        self.name = pairconfig.get('name', '-')
        self.left_raw = pairconfig['left']
        self.right_raw = pairconfig['right']

        errors:list = super().load(pairconfig, self.name, globalconfig)
        self.on_raw_data_changed(errors, globalconfig)

        return errors
    
    def to_dict(self) -> dict:
        """convert this config to a dict that can be easily converted to json"""
        res:dict = super().to_dict()

        res.update({
            'name': self.name,
            'left': self.left_raw,
            'right': self.right_raw,
        })

        return res
    
    def on_raw_data_changed(self, errors:list, parent:SectionBase = None):
        self.left_p = replace_env_variables(self.left_raw)
        self.right_p = replace_env_variables(self.right_raw)
        super().on_raw_data_changed(errors, parent)


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
            return ["Config file <"+path+"> does not exist"]

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
        res = {
            'global': self.globalconfig.to_dict(),
            'pairs': [
                pair.to_dict() for pair in self.pairs
            ]
        }
        return res

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
    
    def on_raw_data_changed(self) -> list[str]:
        errors:list = []
        self.globalconfig.on_raw_data_changed(errors)
        for pair in self.pairs:
            pair.on_raw_data_changed(errors, self.globalconfig)
        return errors

    def _check_list(obj:any, name:str=None, errors:list=None) -> list:
        """Check that the given object is a list, and raise SyncConfig.Error if not"""
        if not isinstance(obj, list):
            if errors is not None:
                errors.append("Invalid config file : '"+str(name)+"' key must be a list")
            return []
        return obj
    
    def _check_list_and_replace_envars(obj:any, name:str=None, errors:list=None) -> list:
        """Check that the given object is a list, and raise SyncConfig.Error if not"""
        return [replace_env_variables(x) for x in SyncConfig._check_list(obj, name, errors)]