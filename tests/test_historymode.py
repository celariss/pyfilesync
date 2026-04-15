from historymode import *
from tests.fsmock import FSMock
from tests.fstree import FSTree

def create_history_files_set(files_data:set[tuple[str,int]], nbversionstoremove:int = 0) -> tuple[set,set]:
        files:set = set()
        history:set = set()
        for file_data in files_data:
            file, nb = file_data
            basename, ext = os.path.splitext(file)
            basename = basename.replace('/', os.sep)
            files.add(file)
            for i in range(nbversionstoremove, nb):
                history_basename = os.path.join(HISTORY_DIR, basename)
                history.add((history_basename + HISTORY_FORMAT + ext).format(i+1).replace(os.sep, '/'))
        return files, history

class TestHistoryMode:
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

            (-1, [10, 20, 30], 0, 60, 0),
            (-1, [10, 20, 30], 1, 60, 1),
            (-1, [10, 20, 30], 2, 60, 2),
            (-1, [10, 20, 30], 3, 60, 3),

            (-1, [10, 20, 30], 0, 0, 0),
            (-1, [10, 20, 30], 1, 0, 1),
            (-1, [10, 20, 30], 1, 1, 0),
            (-1, [10, 20, 30], 0, 10, 0),
            (-1, [10, 20, 30], 1, 10, 1),
            (-1, [10, 20, 30], 2, 10, 1),
            (-1, [10, 20, 30], 2, 30, 2),
        ]

        for test_case in test_cases:
            filetosavesize, historyfilesizes, maxnbhistoryfiles, maxhistorysize, expected = test_case
            assert HistoryMode.get_nb_history_files_to_keep(filetosavesize, historyfilesizes, maxnbhistoryfiles, maxhistorysize) == expected

    def test_get_history_filepath(self):
        test_cases = [
            ('basedir', 'basedir/file', 1, 'basedir/'+HISTORY_DIR+'/file'+HISTORY_FORMAT.format(1)),
            ('root/base1/base2', 'root/base1/base2/subdir1/file', 12, 'root/base1/base2/'+HISTORY_DIR+'/subdir1/file'+HISTORY_FORMAT.format(12)),
        ]

        for test_case in test_cases:
            basedir, file, num, expected = test_case
            assert HistoryMode.get_history_filepath(basedir.replace('/', os.sep), file.replace('/', os.sep), num) == expected.replace('/', os.sep)

    def test_save_file_and_get_file_history(self):
        basedir = 'tests/historymode_test'
        file = os.path.join(basedir, 'file')

        shutil.rmtree(basedir, ignore_errors=True)
        TestHistoryMode._create_file(file, '###file###')

        paths, sizes = HistoryMode.get_file_history(basedir, file)
        assert len(paths) == 0
        assert len(sizes) == 0
        
        file1 = os.path.join(basedir, HISTORY_DIR, 'file'+HISTORY_FORMAT.format(1))
        TestHistoryMode._create_file(file1, 'test')
        paths, sizes = HistoryMode.get_file_history(basedir, file)
        assert len(paths) == 1
        assert len(sizes) == 1
        assert all(size == 4 for size in sizes)

        file2 = os.path.join(basedir, HISTORY_DIR, 'file'+HISTORY_FORMAT.format(2))
        TestHistoryMode._create_file(file2, 'test#')
        paths, sizes = HistoryMode.get_file_history(basedir, file)
        assert len(paths) == 2
        assert len(sizes) == 2
        assert sizes[0] == 4
        assert sizes[1] == 5

        HistoryMode.save_file(basedir, file, 3, 0, True)
        paths, sizes = HistoryMode.get_file_history(basedir, file)
        assert len(paths) == 3
        assert len(sizes) == 3
        assert sizes[0] == 10 # '###file###'
        assert sizes[1] == 4 # 'test'
        assert sizes[2] == 5 # 'test#'

        TestHistoryMode._create_file(file, '###file###__')
        HistoryMode.save_file(basedir, file, 2, 0, True)
        paths, sizes = HistoryMode.get_file_history(basedir, file)
        assert len(paths) == 2
        assert len(sizes) == 2
        assert sizes[0] == 12 # '###file###__'
        assert sizes[1] == 10 # '###file###'

        TestHistoryMode._create_file(file, '###file###__')
        HistoryMode.save_file(basedir, file, 2, 9, True)
        paths, sizes = HistoryMode.get_file_history(basedir, file)
        assert len(paths) == 0
        assert len(sizes) == 0

        shutil.rmtree(basedir, ignore_errors=True)
    
    def test_clean_history(self):
        test_cases = [
            (2, 0, set({('file1', 4), ('dir1/file2.txt', 5), ('dir1/dir2/file3.txt', 3)})),
        ]

        with FSMock():
            for maxnbfiles, maxsize, files_data in test_cases:
                expected:set = set()
                files, history = create_history_files_set(files_data)
                tmp, expected = create_history_files_set(files_data, maxnbfiles)
                expected = set({'right/'+item for item in expected})
                for fs_style in [False, True]:
                    FSMock.clean_sync_data()
                    FSMock.set_os_fs_style(fs_style)
                    FSMock.set_fsmock_data(FSTree(), FSTree(files | history), None)
                    HistoryMode.clean_history('right', maxnbfiles, maxsize)
                    expected = set({item.replace('/', FSMock.os_path_sep) for item in expected})
                    assert FSMock.removed == expected

    def _create_file(path, content='test'):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)