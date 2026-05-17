__author__      = "Jérôme Cuq"
__license__     = "BSD-3-Clause"

from syncconfig import *


class TestSyncConfig:
    def test_syncconfig(self):
        config:SyncConfig = SyncConfig()
        assert 'JSON' in config.load_json_string('{toto}')[0]
        assert 'dict' in config.load_json_string('[]')[0]
        assert 'pairs' in config.load_json_string('{}')[0]
        assert 'list' in config.load_json_string('{"pairs":""}')[0]
        assert 'list' in config.load_json_string('{"global":{"include_regex":{}},"pairs":[]}')[0]
        assert config.load_json_string('{"global":{"include_regex":[], "exclude_regex":[]}, "pairs":[{"name":"test"}]}')
        assert config.load_json_string('{"pairs":[]}') == [] # simpliest valid config
        assert config.load_json_string('{"pairs":[]}') == []
        assert config.load_json_string('{"global":{},"pairs":[{"left":"","right":""}]}') == []
        assert config.load_json_string('{"global":{"include_regex":[], "exclude_regex":[]}, "pairs":[]}') == []
        assert config.load_json_string('{"pairs":[{"name":"#@", "left":"", "right":""}]}') # bad name
        assert config.load_json_string('{"pairs":[{"left":{}, "right":""}]}') # bad left/right type
        assert config.load_json_string('{"pairs":[{"left":"", "right":[]}]}') # bad left/right type
        assert config.load_json_string('{""') # bad json data

        assert config.load_json_string('{"global":{"history_mode": ""},"pairs":[]}') # bad type for history_mode
        assert config.load_json_string('{"global":{"history_mode": {"depth": 0}},"pairs":[]}') == []
        assert config.load_json_string('{"global":{"history_mode": {"depth": 0, "file_max_saved_size":"100kb"}},"pairs":[]}') == []
        assert config.load_json_string('{"global":{"history_mode": {"depth": 0, "file_max_saved_size":"100fkb"}},"pairs":[]}') # bad unit in file_max_saved_size
        assert config.load_json_string('{"pairs":[{"left":"", "right":"", "history_mode": ""}]}') # bad type for history_mode
        assert config.load_json_string('{"pairs":[{"left":"", "right":"", "history_mode": {"depth": 0, "file_max_saved_size":"100kb"}}]}') == []
        assert config.load_json_string('{"pairs":[{"left":"", "right":"", "history_mode": {"depth": 0, "file_max_saved_size":"100fM"}}]}') # bad unit in file_max_saved_size
        

        assert config.load_json_string('{"global":{"include":["*.bat"], "exclude":["*.py"], "include_regex":["..*$"], "exclude_regex":["^[a-z]"]}, "pairs":[{"left":"","right":""}]}') == []
        assert len(config.pairs) == 1
        assert set(config.pairs[0].include_patterns) == set({fnmatch.translate("*.bat"), "..*$"})
        assert set(config.pairs[0].exclude_patterns) == set({fnmatch.translate("*.py"), "^[a-z]"})

        assert config.load_json_string('{"global":{"include":["*.bat"], "exclude":["*.py"], "include_regex":["..*$"], "exclude_regex":["^[a-z]"]},\
                                       "pairs":[{"left":"","right":"","include":["*.gif"], "exclude":["*.txt"], "include_regex":["/W*$"], "exclude_regex":["^[0-9]"]}]}') == []
        assert len(config.pairs) == 1
        assert len(config.pairs[0].name) > 0
        assert config.pairs[0].cmp_files_content == False
        assert set(config.pairs[0].include_patterns) == set({fnmatch.translate("*.bat"), fnmatch.translate("*.gif"), "..*$", "/W*$"})
        assert set(config.pairs[0].exclude_patterns) == set({fnmatch.translate("*.py"), fnmatch.translate("*.txt"), "^[a-z]", "^[0-9]"})

        assert config.load_json_string('{"global":{"cmp_files_content": true}, "pairs":[{"left":"","right":""}]}') == []
        assert config.pairs[0].cmp_files_content == True

        assert config.load_json_string('{"global":{"cmp_files_content": true}, "pairs":[{"left":"","right":"","cmp_files_content": false}]}') == []
        assert config.pairs[0].cmp_files_content == False