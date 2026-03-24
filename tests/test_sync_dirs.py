__author__      = "Jérôme Cuq"
__copyright__   = "Copyright 2026, Jérôme Cuq"
__license__     = "BSD-3-Clause"


from helpers import log
from dirsyncer import *
from tests.fsmock import FSMock
from tests.fstree import FSTree

class TestSyncDirs:
    def are_syncdata_equal(syncdata1:CmpData, syncdata2:CmpData, label:str) -> bool:
        res:bool = True
        if syncdata1.warnings != syncdata2.warnings:
            log(f'"warnings" differs in {label} : (1=result of sync_dirs, 2=expected result)')
            log(f"1> {syncdata1.warnings} != ")
            log(f"2> {syncdata2.warnings}")
            res = False
        if syncdata1.nb_copied != syncdata2.nb_copied:
            log(f'"nb_copied" differs in {label} : (1=result of sync_dirs, 2=expected result)')
            log(f"1> {str(syncdata1.nb_copied)} != ")
            log(f"2> {str(syncdata2.nb_copied)}")
            res = False
        if syncdata1.nb_updated != syncdata2.nb_updated:
            log(f'"nb_updated" differs in {label} : (1=result of sync_dirs, 2=expected result)')
            log(f"1> {str(syncdata1.nb_updated)} != ")
            log(f"2> {str(syncdata2.nb_updated)}")
            res = False
        if syncdata1.nb_deleted != syncdata2.nb_deleted:
            log(f'"nb_deleted" differs in {label} : (1=result of sync_dirs, 2=expected result)')
            log(f"1> {str(syncdata1.nb_deleted)} != ")
            log(f"2> {str(syncdata2.nb_deleted)}")
            res = False
        if syncdata1.size_copied != syncdata2.size_copied:
            log(f'"size_copied" differs in {label} : (1=result of sync_dirs, 2=expected result)')
            log(f"1> {str(syncdata1.size_copied)} != ")
            log(f"2> {str(syncdata2.size_copied)}")
            res = False
        if syncdata1.size_updated != syncdata2.size_updated:
            log(f'"size_updated" differs in {label} : (1=result of sync_dirs, 2=expected result)')
            log(f"1> {str(syncdata1.size_updated)} != ")
            log(f"2> {str(syncdata2.size_updated)}")
            res = False
        return res

    def test_sync(self):
        """
            Test cases for helpers.compare_dirs() function
        """
        # each test case is :
        # (CmpData,
        #  expected return value of DirSyncer.sync_dirs(),
        #  set of copied files/dirs : {(src,dest), ...},
        #  set of created dirs,
        #  set of removed files,
        #  set of removed dirs)
        dataset:list = [
            (CmpData(), SyncData(), set(), set(), set(), set()),
            
            (CmpData(left_only_files=set({'dir1/file1'})),
             SyncData(nb_copied=1),
             set({('left/dir1/file1', 'right/dir1/file1')}),
             set(),
             set(),
             set()
            ),

             (CmpData(left_only_files=set({'dir1/file1'}), left_only_empty_dirs=set({'dir2'})),
              SyncData(nb_copied=2),
              set({('left/dir1/file1', 'right/dir1/file1')}),
              set({'right/dir2'}),
              set(),
              set()
            ),

             (CmpData(right_only_files=set({'dir1/file1'}), right_only_dirs=set({'dir2', 'dir1/dir3'}), right_only_files_in_dirs=set({'dir2/toto', 'dir2/tata'})),
              SyncData(nb_deleted=3),
              set(),
              set(),
              set({'right/dir1/file1'}),
              set({'right/dir2', 'right/dir3'})
            ),

             (CmpData(different_files=set({'dir1/file1', 'file2', 'dir1/dir2/file3'})),
              SyncData(nb_updated=3),
              set({('left/dir1/file1', 'right/dir1/file1'), ('left/file2', 'right/file2'), ('left/dir1/dir2/file3', 'right/dir1/dir2/file3')}),
              set(),
              set(),
              set()
            ),
        ]
        
        TestSyncDirs._execute_test_cases_(dataset, 'test_sync')

    def _execute_test_cases_(dataset:list, funcname:str):
        FSMock.install_os_mock()
        FSMock.set_fsmock_data(FSTree(set({'dir2/'})), FSTree())
        nb:int = 0
        for cmp_data, sync_data, copied, created_dirs, removed, removed_dirs in dataset:
            nb += 1
            for FSMock.is_os_fs_windows_style in [False, True]:
                text = 'Windows' if FSMock.is_os_fs_windows_style else 'Linux'
                text = funcname+':Test case #%d (%s paths)' % (nb,text)
                FSMock.clean_sync_data()

                sync_result = DirSyncer.sync_dirs('left', 'right', cmp_data)
                assert TestSyncDirs.are_syncdata_equal(sync_result, sync_data, text)
                
                if FSMock.is_os_fs_windows_style: copied = set({(src.replace('/','\\'), dest.replace('/','\\')) for (src,dest) in copied})
                if FSMock.copied != copied:
                    log(f'"copied list" differs in {text} : (1=result of sync_dirs, 2=expected result)')
                    log(f"1> {str(FSMock.copied)} != ")
                    log(f"2> {str(copied)}")
                assert FSMock.copied == copied

                if FSMock.is_os_fs_windows_style: created_dirs = set({path.replace('/','\\') for path in created_dirs})
                if FSMock.created_dirs != created_dirs:
                    log(f'"created_dirs list" differs in {text} : (1=result of sync_dirs, 2=expected result)')
                    log(f"1> {str(FSMock.created_dirs)} != ")
                    log(f"2> {str(created_dirs)}")
                assert FSMock.created_dirs == created_dirs
        FSMock.uninstall_os_mock()