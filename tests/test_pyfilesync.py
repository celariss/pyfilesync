from pyfilesync import *
from tests.common import *
from tests.fsmock import FSMock
from tests.fstree import FSTree
from tests.test_historymode import create_history_files_set


class TestPyFileSync:
    def test_main(self):
        assert main([]) == 1
        # bad config file
        assert main(['tests/config2.json', '-v']) == 3
        assert main(['tests/config1.json', 'bad_action', '-v']) == 2
        # bad pair name
        assert main(['tests/config1.json', '-p', 'bad_pair', '-v']) == 4
        # left folders do not exist
        assert main(['tests/config1.json', '-v']) == 4
        # bad 'file_max_saved_size' value in config file
        assert main(['{"global":{"history_mode": {"depth": 0, "file_max_saved_size":"100fkb"}},"pairs":[]}']) == 3

        assert main(['-V']) == 0
        assert main(['tests/config1.json', 'list']) == 0
        assert main(['tests/config1.json', 'show_history']) == 0
        assert main(['tests/config1.json', 'clean_history']) == 0
        assert main(['{"pairs":[{"name":"pair_1","left":"left1","right":"right1","include":["*.mp4","*.txt"]},\
                                {"name":"pair_2","left":"left2","right":"right2"}]}', 'list']) == 0
        
        
        test_cases = [
            (2, 0, set({('file1', 4), ('dir1/file2.txt', 5), ('dir1/dir2/file3.txt', 3)})),
        ]

        with FSMock():
            for maxnbfiles, maxsize, files_data in test_cases:
                files, history = create_history_files_set(files_data)
                for fs_style in [False, True]:
                    FSMock.clean_sync_data()
                    FSMock.set_os_fs_style(fs_style)
                    FSMock.set_fsmock_data(FSTree(), FSTree(files | history), None)
                    assert main(['{"pairs":[{"name":"pair_1","left":"left","right":"right","history_mode": {"depth": 0},"include":["*.mp4","*.txt"]}]}', 'show_history', '-p', 'pair_1']) == 0
                    assert main(['{"pairs":[{"name":"pair_1","left":"left","right":"right","history_mode": {"depth": 0},"include":["*.mp4","*.txt"]}]}', 'clean_history', '-p', 'pair_1', '-v']) == 0


    def test_syncfolderpairs1(self):
        config:SyncConfig = SyncConfig()
        assert not config.load_file('tests/config1.json')

        with FSMock():
            FSMock.set_fsmock_data(
                FSTree(set({'dir1/', 'dir2/file1.mp4', 'dir2/dir3/file2.txt', 'file3'})),
                FSTree(set({'dir1/', 'dir2/file1.mp4', 'dir2/dir3/file2.txt'}))
            )
            FSMock.set_os_fs_style(False)

            # TEST CASE #1 (error) : 'tests/config1.json' - Right folder does not exist in compare
            nb = 1
            FSMock.clean_sync_data()
            FSMock.os_path_exists_values['right1'] = False
            res:FolderPairsSyncResults = sync_folders_pairs(config, 'compare', verbose = True)
            assert len(res.errors) == 1 and check_errors_format(res.errors)

            # TEST CASE #2 (OK) : 'tests/config1.json' - Use of create flag when right folder does not exist
            nb += 1
            FSMock.clean_sync_data()
            FSMock.os_path_exists_values['right1'] = False
            res:FolderPairsSyncResults = sync_folders_pairs(config, 'compare', create_root=True, verbose = True)
            assert not res.errors
            assert not res.warnings
            
            # TEST CASE #3 (error) : 'tests/config1.json' - bad action given
            nb += 1
            FSMock.clean_sync_data()
            res:FolderPairsSyncResults = sync_folders_pairs(config, 'bad_action', verbose = True)
            assert len(res.errors) == 1 and check_errors_format(res.errors)

            # TEST CASE #4 (OK) : 'tests/config1.json' - sync action via main()
            nb += 1
            FSMock.clean_sync_data()
            FSMock.os_path_exists_values['tests/config1.json'] = True
            assert main(['tests/config1.json', 'sync']) == 0
            assert FSMock.copied == set({('left2/file3', 'right2/file3')})
            assert FSMock.removed == set()
            assert FSMock.removed_dirs == set({'right1/dir1'})
            assert FSMock.created_dirs == set()

            # TEST CASE #5 (OK) : 'tests/config1.json' - compare
            nb += 1
            FSMock.clean_sync_data()
            res:FolderPairsSyncResults = sync_folders_pairs(config, 'compare', verbose = True)
            assert not res.errors
            assert not res.warnings
            assert res.nb_different ==  0
            assert res.nb_equal == 4
            assert res.nb_left_only == 1
            assert res.nb_right_only == 1
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
            
            # TEST CASE #6 (Error) : 'tests/config1.json' - bad pair name given for compare action
            nb += 1
            FSMock.clean_sync_data()
            res:FolderPairsSyncResults = sync_folders_pairs(config, 'compare', ['bad_pair_name'], verbose = True)
            assert len(res.errors) == 1 and check_errors_format(res.errors)

            # TEST CASE #7 (OK) : 'tests/config1.json' - compare only pair_2
            nb += 1
            FSMock.clean_sync_data()
            res:FolderPairsSyncResults = sync_folders_pairs(config, 'compare', [config.pairs[1].name], verbose = True)
            assert not res.errors
            assert not res.warnings
            assert res.nb_different ==  0
            assert res.nb_equal == 2
            assert res.nb_left_only == 1
            assert res.nb_right_only == 0
            assert FSMock.copied == set()
            assert FSMock.removed == set()
            assert FSMock.removed_dirs == set()
            assert FSMock.created_dirs == set()
            assert not res.pairs_syncdata
            assert len(res.pairs_cmpdata) == 1
            assert 'pair_2' in res.pairs_cmpdata and\
                are_cmpdata_equal(res.pairs_cmpdata['pair_2'][1],
                                CmpData(equal_files=set({'left2/dir2/file1.mp4', 'left2/dir2/dir3/file2.txt'}),
                                        left_only_files=set({'left2/file3'})),
                                'test_syncfolderpairs:Test case #%d, pair_2' % nb)

            # TEST CASE #8 (OK) : 'tests/config1.json' - sync action
            nb += 1
            FSMock.clean_sync_data()
            res:FolderPairsSyncResults = sync_folders_pairs(config, 'sync', verbose = True)
            assert not res.errors
            assert FSMock.copied == set({('left2/file3', 'right2/file3')})
            assert FSMock.removed == set()
            assert FSMock.removed_dirs == set({'right1/dir1'})
            assert FSMock.created_dirs == set()
            assert 'pair_1' in res.pairs_syncdata
            assert not res.pairs_syncdata['pair_1'][1].warnings
            assert res.pairs_syncdata['pair_1'][1].nb_copied == 0
            assert res.pairs_syncdata['pair_1'][1].nb_deleted == 1
            assert res.pairs_syncdata['pair_1'][1].nb_updated == 0
            assert 'pair_2' in res.pairs_syncdata
            assert not res.pairs_syncdata['pair_2'][1].warnings
            assert res.pairs_syncdata['pair_2'][1].nb_copied == 1
            assert res.pairs_syncdata['pair_2'][1].nb_deleted == 0
            assert res.pairs_syncdata['pair_2'][1].nb_updated == 0

            # TEST CASE #9 (OK) : 'tests/config1.json' - sync action with warning on remove dir
            nb += 1
            FSMock.clean_sync_data()
            FSMock.os_rmdir_failure_paths['right1/dir1'] = False
            res:FolderPairsSyncResults = sync_folders_pairs(config, 'sync', ['pair_1'], verbose = True)
            assert not res.errors
            assert len(res.warnings) == 1 and check_errors_format(res.warnings)
            assert FSMock.copied == set()
            assert FSMock.removed == set()
            assert FSMock.removed_dirs == set()
            assert FSMock.created_dirs == set()
            assert 'pair_1' in res.pairs_syncdata
            assert len(res.pairs_syncdata['pair_1'][1].warnings) == 1
            assert res.pairs_syncdata['pair_1'][1].nb_copied == 0
            assert res.pairs_syncdata['pair_1'][1].nb_deleted == 0
            assert res.pairs_syncdata['pair_1'][1].nb_updated == 0

            # TEST CASE #10 (OK) : 'tests/config1.json' - sync action with warning on copy file
            nb += 1
            FSMock.clean_sync_data()
            FSMock.os_copy_failure_paths['right2/file3'] = False
            res:FolderPairsSyncResults = sync_folders_pairs(config, 'sync', ['pair_2'], verbose = True)
            assert not res.errors
            assert len(res.warnings) == 1 and check_errors_format(res.warnings)
            assert FSMock.copied == set()
            assert FSMock.removed == set()
            assert FSMock.removed_dirs == set()
            assert FSMock.created_dirs == set()
            assert 'pair_2' in res.pairs_syncdata
            assert len(res.pairs_syncdata['pair_2'][1].warnings) == 1
            assert res.pairs_syncdata['pair_2'][1].nb_copied == 0
            assert res.pairs_syncdata['pair_2'][1].nb_deleted == 0
            assert res.pairs_syncdata['pair_2'][1].nb_updated == 0

            # TEST CASE #11 (OK) : 'tests/config1.json' - sync action with warning on update file
            nb += 1
            FSMock.set_fsmock_data(
                FSTree(set({'dir1/', 'dir2/file1.mp4', 'dir2/dir3/file2.txt', 'file3'})),
                FSTree(set({'dir1/', 'dir2/file1.mp4', 'dir2/dir3/file2.txt', 'file3'})),
                {'right2/file3':DirSyncer.FileProperties(1,0)}
            )
            FSMock.clean_sync_data()
            FSMock.os_copy_failure_paths['right2/file3'] = False
            res:FolderPairsSyncResults = sync_folders_pairs(config, 'sync', ['pair_2'], verbose = True)
            assert not res.errors
            assert len(res.warnings) == 1 and check_errors_format(res.warnings)
            assert FSMock.copied == set()
            assert FSMock.removed == set()
            assert FSMock.removed_dirs == set()
            assert FSMock.created_dirs == set()
            assert 'pair_2' in res.pairs_syncdata
            assert len(res.pairs_syncdata['pair_2'][1].warnings) == 1
            assert res.pairs_syncdata['pair_2'][1].nb_copied == 0
            assert res.pairs_syncdata['pair_2'][1].nb_deleted == 0
            assert res.pairs_syncdata['pair_2'][1].nb_updated == 0

            # TEST CASE #12 (OK) : 'tests/config1.json' - compare action with a file to update
            nb += 1
            FSMock.set_fsmock_data(
                FSTree(set({'dir1/', 'dir2/file1.mp4', 'dir2/dir3/file2.txt', 'file3'})),
                FSTree(set({'dir1/', 'dir2/file1.mp4', 'dir2/dir3/file2.txt', 'file3'})),
                {'right2/file3':DirSyncer.FileProperties(1,0)}
            )
            FSMock.clean_sync_data()
            res:FolderPairsSyncResults = sync_folders_pairs(config, 'compare', ['pair_2'], verbose = True)
            assert not res.errors
            assert not res.warnings
            assert res.nb_different ==  1
            assert res.nb_equal == 2
            assert res.nb_left_only == 0
            assert res.nb_right_only == 0
            assert not res.pairs_syncdata
            assert len(res.pairs_cmpdata) == 1
            assert 'pair_2' in res.pairs_cmpdata and\
                are_cmpdata_equal(res.pairs_cmpdata['pair_2'][1],
                                CmpData(equal_files=set({'left2/dir2/file1.mp4', 'left2/dir2/dir3/file2.txt'}),
                                        different_files=set({'left2/file3'})),
                                'test_syncfolderpairs:Test case #%d, pair_2' % nb)
            
            # TEST CASE #13 (OK) : 'tests/config1.json' - sync action with a file to update
            nb += 1
            FSMock.set_fsmock_data(
                FSTree(set({'dir1/', 'dir2/file1.mp4', 'dir2/dir3/file2.txt', 'file3'})),
                FSTree(set({'dir1/', 'dir2/file1.mp4', 'dir2/dir3/file2.txt', 'file3'})),
                {'right2/file3':DirSyncer.FileProperties(1,0)}
            )
            FSMock.clean_sync_data()
            res:FolderPairsSyncResults = sync_folders_pairs(config, 'sync', ['pair_2'], verbose = True)
            assert not res.errors
            assert not res.warnings
            assert FSMock.copied == set({('left2/file3', 'right2/file3')})
            assert FSMock.removed == set()
            assert FSMock.removed_dirs == set()
            assert FSMock.created_dirs == set()
            assert 'pair_2' in res.pairs_syncdata
            assert len(res.pairs_syncdata['pair_2'][1].warnings) == 0
            assert res.pairs_syncdata['pair_2'][1].nb_copied == 0
            assert res.pairs_syncdata['pair_2'][1].nb_deleted == 0
            assert res.pairs_syncdata['pair_2'][1].nb_updated == 1

            # TEST CASE #14 (Error) : 'tests/config1.json' - sync action with error on include pattern
            nb += 1
            FSMock.clean_sync_data()
            save = config.pairs[1].include_regex.copy()
            config.pairs[1].include_regex.append('**')
            res:FolderPairsSyncResults = sync_folders_pairs(config, 'sync', verbose = True)
            assert len(res.errors) == 1 and check_errors_format(res.errors)
            config.pairs[1].include_regex = save

            # TEST CASE #13 (Error) : 'tests/config1.json' - sync action with error on exclude pattern
            nb += 1
            FSMock.clean_sync_data()
            save = config.pairs[1].exclude_regex.copy()
            config.pairs[1].exclude_regex.append('**')
            res:FolderPairsSyncResults = sync_folders_pairs(config, 'sync', verbose = True)
            assert len(res.errors) == 1 and check_errors_format(res.errors)
            config.pairs[1].exclude_regex = save
