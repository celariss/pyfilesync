from pyfilesync import *
from tests.common import are_cmpdata_equal
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

        nb = 1
        config:SyncConfig = SyncConfig()
        assert not config.load_file('tests/config1.json')
        res:FolderPairsSyncResults = sync_folders_pairs(config, 'compare', verbose = True)
        assert res.success
        assert not res.errors
        assert FSMock.copied == set()
        assert FSMock.removed == set()
        assert FSMock.removed_dirs == set()
        assert FSMock.created_dirs == set()
        assert not res.pairs_syncdata
        assert len(res.pairs_cmpdata) == 2
        assert 'pair_1' in res.pairs_cmpdata and\
            are_cmpdata_equal(res.pairs_cmpdata['pair_1'][1],
                              CmpData(equal_files=set({'left1/dir2/file1.mp4', 'left1/dir2/dir3/file2.txt'}),
                                      right_only_dirs=set({'right1/dir1'})),
                              'test_syncfolderpairs:Test case #%d, pair_1' % nb)
        assert 'pair_2' in res.pairs_cmpdata and\
            are_cmpdata_equal(res.pairs_cmpdata['pair_2'][1],
                              CmpData(equal_files=set({'left2/dir2/file1.mp4', 'left2/dir2/dir3/file2.txt'}),
                                      left_only_files=set({'left2/file3'})),
                              'test_syncfolderpairs:Test case #%d, pair_2' % nb)

        nb += 1
        FSMock.clean_sync_data()
        res:FolderPairsSyncResults = sync_folders_pairs(config, 'sync', verbose = True)
        assert res.success
        assert not res.errors
        assert FSMock.copied == set({('left2/file3', 'right2/file3')})
        assert FSMock.removed == set()
        assert FSMock.removed_dirs == set({'right1/dir1'})
        assert FSMock.created_dirs == set()
        assert 'pair_1' in res.pairs_syncdata
        assert not res.pairs_syncdata['pair_1'][1].errors
        assert res.pairs_syncdata['pair_1'][1].nb_copied == 0
        assert res.pairs_syncdata['pair_1'][1].nb_deleted == 1
        assert res.pairs_syncdata['pair_1'][1].nb_updated == 0
        assert 'pair_2' in res.pairs_syncdata
        assert not res.pairs_syncdata['pair_2'][1].errors
        assert res.pairs_syncdata['pair_2'][1].nb_copied == 1
        assert res.pairs_syncdata['pair_2'][1].nb_deleted == 0
        assert res.pairs_syncdata['pair_2'][1].nb_updated == 0
        
        nb += 1
        FSMock.clean_sync_data()
        assert main(['tests/config1.json', 'sync']) == 0
        assert FSMock.copied == set({('left2/file3', 'right2/file3')})
        assert FSMock.removed == set()
        assert FSMock.removed_dirs == set({'right1/dir1'})
        assert FSMock.created_dirs == set()

        FSMock.uninstall_os_mock()