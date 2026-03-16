__author__      = "Jérôme Cuq"
__copyright__   = "Copyright 2026, Jérôme Cuq"
__license__     = "BSD-3-Clause"

import fnmatch
import json
import re
from helpers import *


class GlobalSection:
    """Parameters in global section apply to all pair sections in configuration"""
    def __init__(self):
        self.cmp_files_content:bool = False
        self.include_regex:list[str] = []
        self.exclude_regex:list[str] = []

    def load(self, config:dict) -> str:
        self.cmp_files_content = config.get('cmp_files_content', False)
        try:
            (self.include_regex, self.exclude_regex) = SyncConfig.get_patterns(config, 'global')
        except SyncConfig.Error as exc:
            return exc.error_text
        return None
        

class PairSection:
    """a pair section contains synchronization parameters of a folders pair"""
    def __init__(self):
        self.name:str
        self.left:str
        self.right:str
        self.cmp_files_content:bool = False
        self.include_regex:list[str] = []
        self.exclude_regex:list[str] = []

    def load(self, pairconfig: dict, globalconfig:GlobalSection) -> str:
        """fill this instance fields from dictionary. The given global config is used to fill fields not defined in "pairconfig"."""
        self.name = pairconfig.get('name', '-')
        self.left = replace_env_variables(pairconfig['left'])
        self.right = replace_env_variables(pairconfig['right'])
        self.cmp_files_content = pairconfig.get('cmp_files_content', globalconfig.cmp_files_content)
        try:
            (self.include_regex, self.exclude_regex) = SyncConfig.get_patterns(pairconfig, self.name)
        except SyncConfig.Error as exc:
            return exc.error_text
        self.include_regex.extend(globalconfig.include_regex)
        self.exclude_regex.extend(globalconfig.exclude_regex)
        return None

class SyncConfig:
    class Error(Exception):
        def __init__(self, error_text:str):
            self.error_text:str = error_text

    def __init__(self):
        self.globalconfig:GlobalSection = GlobalSection()
        self.pairs:list[PairSection] = []

    def load_file(self, path: str) -> str:
        """load config from file

        :param path: path to config file
        :return: error text if any error occured
        """
        result:dict = {}
        if not os.path.exists(path):
            return ("Config file <"+path+"> does not exist")

        with open(path, 'r') as f:
            error = self.load_json_string(f.read())
            if error:
                return error
        return None
           
    def load_json_string(self, config:str) -> str:
        """load config from a string

        :param config: string containing the configuration in json format
        :return: error text if any error occured
        """
        try:
            result = json.loads(config)
        except json.JSONDecodeError:
            return ("Config file is not a valid JSON file")
        if not isinstance(result, dict):
            return ("Config file is not valid, it must contain a dictionary : {...}")
        error = self.load_dict(result)
        if error:
            return error
        return None

    def load_dict(self, config:dict) -> str:
        """load config from a python dict

        :param config: dict containing the configuration data
        :return: error text if any error occured
        """
        if 'pairs' not in config or not isinstance(config['pairs'], list):
            return ("Config file is not valid, it must contain a 'pairs' key with a list of folders pairs to synchronize")
        for paircfg in config['pairs']:
            if 'left' not in paircfg or 'right' not in paircfg:
                return ("Config file is not valid, each pair must contain 'left' and 'right' keys")
            if not isinstance(paircfg['left'],str) or not isinstance(paircfg['right'],str):
                return ("Config file is not valid, 'left' and 'right' values must be strings")
        
        self.globalconfig = GlobalSection()
        if 'global' in config:
            error = self.globalconfig.load(config['global'])
            if error:
                return error
        
        self.pairs = []
        idx = 0
        for paircfg in config.get('pairs', []):
            idx += 1
            if not 'name' in paircfg:
                paircfg['name'] = 'pair_%d' % idx
            pair_name = paircfg.get('name', '')
            if not re.match("^[A-Za-z0-9_-]*$", pair_name):
                return ("Invalid pair name '%s' : pair names may only contain '-', '_' and alphanumeric characters" % pair_name)
            pair = PairSection()
            error = pair.load(paircfg, self.globalconfig)
            if error:
                return error
            self.pairs.append(pair)
        return None
 
    
    def check_list(obj, name:str):
        """Check that the given object is a list, and raise SyncConfig.Error if not"""
        if not isinstance(obj, list):
            raise SyncConfig.Error("Invalid config file : '"+name+"' key must be a list")

    def get_patterns(config:dict, logkey:str) -> tuple[list,list]:
        """extract and prepare include and exclude patterns
        :return: (include_regex list, exclude_regex list)
        """
        SyncConfig.check_list(config.get('exclude_regex', []), logkey+'.exclude_regex')
        SyncConfig.check_list(config.get('include_regex', []), logkey+'.include_regex')
        exclude_regex:list = [replace_env_variables(x) for x in config.get('exclude_regex', [])]
        include_regex:list = [replace_env_variables(x) for x in config.get('include_regex', [])]

        SyncConfig.check_list(config.get('exclude', []), logkey+'.exclude')
        SyncConfig.check_list(config.get('include', []), logkey+'.include')
        # -> we use include patterns (if any) by converting them to regex
        include=[replace_env_variables(x) for x in config.get('include', [])]
        if len(include)>0:
            include_regex.extend([r'|'.join([fnmatch.translate(x) for x in include])])
        exclude=[replace_env_variables(x) for x in config.get('exclude', [])]
        if len(exclude)>0:
            exclude_regex.extend([r'|'.join([fnmatch.translate(x) for x in exclude])])
        return (include_regex, exclude_regex)