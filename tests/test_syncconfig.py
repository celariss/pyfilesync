from syncconfig import *


class TestSyncConfig:
    def test_syncconfig(self):
        config:SyncConfig = SyncConfig()
        assert 'JSON' in config.load_json_string('{toto}')
        assert 'dict' in config.load_json_string('[]')
        assert 'pairs' in config.load_json_string('{}')
        assert 'list' in config.load_json_string('{"pairs":""}')
        assert 'list' in config.load_json_string('{"global":{"include_regex":{}},"pairs":[]}')
        assert config.load_json_string('{"global":{"include_regex":[], "exclude_regex":[]}, "pairs":[{"name":"test"}]}')
        assert config.load_json_string('{"pairs":[]}') == None # simpliest valid config
        assert config.load_json_string('{"pairs":[]}') == None
        assert config.load_json_string('{"global":{},"pairs":[{"left":"","right":""}]}') == None
        assert config.load_json_string('{"global":{"include_regex":[], "exclude_regex":[]}, "pairs":[]}') == None
        assert config.load_json_string('{"pairs":[{"name":"#@", "left":"", "right":""}]}') # bad name
        assert config.load_json_string('{"pairs":[{"left":{}, "right":""}]}') # bad left/right type
        assert config.load_json_string('{"pairs":[{"left":"", "right":[]}]}') # bad left/right type
        assert config.load_json_string('{""') # bad json data

        assert config.load_json_string('{"global":{"history_mode": {"depth": 0}},"pairs":[]}') == None
        assert config.load_json_string('{"global":{"history_mode": {"depth": 0, "file_max_saved_size":"100kb"}},"pairs":[]}') == None
        assert config.load_json_string('{"pairs":[{"left":"", "right":"", "history_mode": {"depth": 0, "file_max_saved_size":"100kb"}}]}') == None

        assert config.load_json_string('{"global":{"include":["*.bat"], "exclude":["*.py"], "include_regex":["..*$"], "exclude_regex":["^[a-z]"]}, "pairs":[{"left":"","right":""}]}') == None
        assert len(config.pairs) == 1
        assert set(config.pairs[0].include_regex) == set({fnmatch.translate("*.bat"), "..*$"})
        assert set(config.pairs[0].exclude_regex) == set({fnmatch.translate("*.py"), "^[a-z]"})

        assert config.load_json_string('{"global":{"include":["*.bat"], "exclude":["*.py"], "include_regex":["..*$"], "exclude_regex":["^[a-z]"]},\
                                       "pairs":[{"left":"","right":"","include":["*.gif"], "exclude":["*.txt"], "include_regex":["/W*$"], "exclude_regex":["^[0-9]"]}]}') == None
        assert len(config.pairs) == 1
        assert len(config.pairs[0].name) > 0
        assert config.pairs[0].cmp_files_content == False
        assert set(config.pairs[0].include_regex) == set({fnmatch.translate("*.bat"), fnmatch.translate("*.gif"), "..*$", "/W*$"})
        assert set(config.pairs[0].exclude_regex) == set({fnmatch.translate("*.py"), fnmatch.translate("*.txt"), "^[a-z]", "^[0-9]"})

        assert config.load_json_string('{"global":{"cmp_files_content": true}, "pairs":[{"left":"","right":""}]}') == None
        assert config.pairs[0].cmp_files_content == True

        assert config.load_json_string('{"global":{"cmp_files_content": true}, "pairs":[{"left":"","right":"","cmp_files_content": false}]}') == None
        assert config.pairs[0].cmp_files_content == False