from pyfilesync import *
from tests.fsmock import FSMock
from tests.fstree import FSTree

class TestPyFileSync:
    def test_main(self):
        assert main([]) == 1
        assert main(['tests/config2.json']) == 3
        assert main(['tests/config1.json', 'bad_action']) == 2

        assert main(['-V']) == 0
        assert main(['tests/config1.json', 'list']) == 0

    def test_syncfolderpairs(self):
        FSMock.install_os_mock()
        FSMock.set_fsmock_data(
            FSTree(set({'dir1/', 'dir2/file1.mp4', 'dir2/dir3/file2.txt', 'file3'})),
            FSTree(set({'dir1/', 'dir2/file1.mp4', 'dir2/dir3/file2.txt'}))
        )
        FSMock.is_os_walk_mock_windows_style = False
        FSMock.clean_sync_data()

        config:SyncConfig = SyncConfig()
        assert not config.load_file('tests/config1.json')
        assert sync_folders_pairs(config, 'compare', verbose = True)
        assert sync_folders_pairs(config, 'sync', verbose = True)
        assert FSMock.copied == set({('left2/file3', 'right2/file3')})
        assert FSMock.removed == set()
        assert FSMock.removed_dirs == set({'right1/dir1'})
        assert FSMock.created_dirs == set()
        FSMock.uninstall_os_mock()