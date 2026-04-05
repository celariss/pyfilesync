from historymode import *

class TestDatasaver:
    def test_get_nb_history_files_to_keep(self):
        test_cases = [
            (100, [], 5, 10, -1),
            (100, [], 5, 1000, 0),

            (100, [], 0, 10, -1),
            (100, [], 0, 100, -1),

            (100, [10, 20, 30], 1, 50, -1),
            (100, [10, 20, 30], 1, 100, 0),
            (100, [10, 20, 30], 1, 110, 0),
            (100, [10, 20, 30], 1, 1000, 0),
            (100, [10, 20, 30], 1, 0, 0),

            (100, [10, 20, 30], 2, 50, -1),
            (100, [10, 20, 30], 2, 100, 0),
            (100, [10, 20, 30], 2, 110, 1),
            (100, [10, 20, 30], 2, 130, 1),
            (100, [10, 20, 30], 2, 1000, 1),
            (100, [10, 20, 30], 2, 0, 1),

            (100, [10, 20, 30], 5, 50, -1),
            (100, [10, 20, 30], 5, 105, 0),
            (100, [10, 20, 30], 5, 110, 1),
            (100, [10, 20, 30], 5, 120, 1),
            (100, [10, 20, 30], 5, 130, 2),
            (100, [10, 20, 30], 5, 159, 2),
            (100, [10, 20, 30], 5, 160, 3),
            (100, [10, 20, 30], 5, 1000, 3),
            (100, [10, 20, 30], 5, 0, 3),
        ]

        for test_case in test_cases:
            filetosavesize, historyfilesizes, maxnbhistoryfiles, maxhistorysize, expected = test_case
            assert HistoryMode.get_nb_history_files_to_keep(filetosavesize, historyfilesizes, maxnbhistoryfiles, maxhistorysize) == expected

    def test_get_history_filepath(self):
        test_cases = [
            ('basedir', 'basedir/file', 1, 'basedir/'+HISTORY_DIR+'/file'+HISTORY_PATTERN.format(1)),
            ('root/base1/base2', 'root/base1/base2/subdir1/file', 12, 'root/base1/base2/'+HISTORY_DIR+'/subdir1/file'+HISTORY_PATTERN.format(12)),
        ]

        for test_case in test_cases:
            basedir, file, num, expected = test_case
            assert HistoryMode.get_history_filepath(basedir.replace('/', os.sep), file.replace('/', os.sep), num) == expected.replace('/', os.sep)