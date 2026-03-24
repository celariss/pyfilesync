__author__      = "Jérôme Cuq"
__copyright__   = "Copyright 2026, Jérôme Cuq"
__license__     = "BSD-3-Clause"

import fnmatch

from helpers import log
from dirsyncer import *
from tests.common import are_cmpdata_equal
from tests.fsmock import FSMock
from tests.fstree import FSTree


testtree:list = [
    'file1', 'file2.txt',
    {
        'dir1':[
            'file3', 'file4.txt',
            {
                'dir11':[
                    'file5', 'file6.py',
                ]
            }
        ],
        'dir2':[
            'file7', 'file8.ini', 'item',
            {
                'dir1':['file5.txt']
            }
        ],
        'dir3':[],
        'item':['item2']
    }
]

class TestCompareDirs:
    def test_compare_dirs_left_only(self):
        """
            Test cases for helpers.compare_dirs() function
        """
        dataset:list = [
            # each test case is : (left_filetree, right_filetree, include, exclude, file properties, ignore_right_only, expected_result)
            #   -> expected_result is a CmpData(left_only_files, left_only_empty_dirs, right_only_files, right_only_dirs, right_only_files_in_dirs, equal, different, errors)
            (testtree, [], [], [], {}, False, CmpData(FSTree(testtree).to_fileset().difference({'dir3'}), set({'dir3'}))),
            (testtree, [], ['*.txt'], [], {}, False, CmpData(set({'file2.txt', 'dir1/file4.txt', 'dir2/dir1/file5.txt'}))),
            (testtree, [], ['file?.txt'], [], {}, False, CmpData(set({'file2.txt', 'dir1/file4.txt', 'dir2/dir1/file5.txt'}))),
            (testtree, [], ['*/dir1/file?.txt'], [], {}, False, CmpData(set({'dir1/file4.txt', 'dir2/dir1/file5.txt'}))),
            (testtree, [], ['/dir1/file?.txt'], [], {}, False, CmpData(set({'dir1/file4.txt'}))),
            (testtree, [], ['item'], [], {}, False, CmpData(set({'dir2/item'}))),
            (testtree, [], ['*/item/*'], [], {}, False, CmpData(set({'item/item2'}))),
            (testtree, [], ['*/item/'], [], {}, False, CmpData(set({'item/item2'}))),
            (testtree, [], ['/dir1/*'], [], {}, False, CmpData(set({'dir1/file3', 'dir1/dir11/file5', 'dir1/dir11/file6.py', 'dir1/file4.txt'}))),
            (testtree, [], ['/dir1/'], [], {}, False, CmpData(set({'dir1/file3', 'dir1/dir11/file5', 'dir1/dir11/file6.py', 'dir1/file4.txt'}))),
            (testtree, [], ['*/dir1/*'], [], {}, False, CmpData(set({'dir1/file3', 'dir1/dir11/file5', 'dir1/dir11/file6.py', 'dir1/file4.txt', 'dir2/dir1/file5.txt'}))),
            (testtree, [], ['*/dir1/'], [], {}, False, CmpData(set({'dir1/file3', 'dir1/dir11/file5', 'dir1/dir11/file6.py', 'dir1/file4.txt', 'dir2/dir1/file5.txt'}))),
            (testtree, [], ['*/dir1/*.txt'], [], {}, False, CmpData(set({'dir1/file4.txt', 'dir2/dir1/file5.txt'}))),
            (testtree, [], ['/dir1/*.txt'], [], {}, False, CmpData(set({'dir1/file4.txt'}))),
            (testtree, [], ['/dir1/dir11/'], [], {}, False, CmpData(set({'dir1/dir11/file5', 'dir1/dir11/file6.py'}))),
            (testtree, [], ['/dir2/file7/'], [], {}, False, CmpData(set())),
            (testtree, [], ['/dir2/file7'], [], {}, False, CmpData(set({'dir2/file7'}))),
            (testtree, [], ['*/dir11/file5'], [], {}, False, CmpData(set({'dir1/dir11/file5'}))),
            (testtree, [], [], ['*/dir1/'], {}, False, CmpData(set({'file2.txt', 'file1', 'dir2/file7', 'dir2/file8.ini', 'dir2/item', 'item/item2'}), set({'dir3'}))),
            (testtree, [], [], ['*/dir1/*'], {}, False, CmpData(set({'file2.txt', 'file1', 'dir2/file7', 'dir2/file8.ini', 'dir2/item', 'item/item2'}), set({'dir3'}))),
            (testtree, [], [], ['/dir1/'], {}, False, CmpData(set({'file2.txt', 'file1', 'dir2/file7', 'dir2/file8.ini', 'dir2/item', 'item/item2', 'dir2/dir1/file5.txt'}), set({'dir3'}))),
            (testtree, [], [], ['/dir1/dir11/file5'], {}, False, CmpData(FSTree(testtree).to_fileset().difference({'dir1/dir11/file5', 'dir3'}), set({'dir3'}))),
            (testtree, [], ['/dir1/'], ['*.py'], {}, False, CmpData(set({'dir1/file3', 'dir1/dir11/file5', 'dir1/file4.txt'}))),
            (testtree, [], ['/dir1/'], ['*/dir11/'], {}, False, CmpData(set({'dir1/file3', 'dir1/file4.txt'}))),
            (set({'dir1/dir2/dir3/file1', 'dir1/dir4/dir5/dir3/file2', 'dir1/dir4/dir5/dir3/dir6/', 'dir1/dir4/dir5/dir3/dir7/', 'dir2/'}), [], [], [], {}, False,
                CmpData(set({'dir1/dir2/dir3/file1', 'dir1/dir4/dir5/dir3/file2'}), set({'dir1/dir4/dir5/dir3/dir6', 'dir1/dir4/dir5/dir3/dir7', 'dir2'}))),
             (set({'dir1/dir2/dir3/file1', 'dir1/dir4/dir5/dir3/file2', 'dir1/dir4/dir5/dir3/dir6/', 'dir1/dir4/dir5/dir3/dir7/', 'dir2/dir3/'}), [], [], ['*/dir3/'], {}, False,
                CmpData(set(), set({'dir2', 'dir1/dir2', 'dir1/dir4/dir5'}))),
        ]
        
        TestCompareDirs._execute_test_cases_(dataset, 'test_compare_dirs_left_only')

    def test_compare_dirs_left_only_and_equal(self):
        """
            Test cases for helpers.compare_dirs() function
        """
        dataset:list = [                
            # each test case is : (left_filetree, right_filetree, include, exclude, file properties, ignore_right_only, expected_result)
            #   -> expected_result is a CmpData(left_only_files, left_only_empty_dirs, right_only_files, right_only_dirs, right_only_files_in_dirs, equal, different, errors)
            (testtree, set({'dir1/file3'}), [], [], {}, False,
                CmpData(FSTree(testtree).to_fileset().difference({'dir1/file3', 'dir3'}), set({'dir3'}), set(), set(), set(), set({'dir1/file3'}))),
            (testtree, set({'dir3/'}), [], [], {}, False,
                CmpData(FSTree(testtree).to_fileset().difference({'dir3'}))),
            (testtree, set({'dir1/file4.txt', 'dir2/dir1/file5.txt'}), ['*.txt'], [], {}, False,
                CmpData(set({'file2.txt'}), set(), set(), set(), set(), set({'dir1/file4.txt', 'dir2/dir1/file5.txt'}), set(), set())),
            (testtree, set({'dir1/file4.txt'}), ['*.txt'], [], {}, False,
                CmpData(set({'file2.txt', 'dir2/dir1/file5.txt'}), set(), set(), set(), set(), set({'dir1/file4.txt'}), set(), set())),
        ]

        TestCompareDirs._execute_test_cases_(dataset, 'test_compare_dirs_left_only_and_equal')

    def test_compare_dirs_other(self):
        """
            Test cases for helpers.compare_dirs() function
        """
        dataset:list = [
            # each test case is : (left_filetree, right_filetree, include, exclude, file properties, ignore_right_only, expected_result)
            #   -> expected_result is a CmpData(left_only_files, left_only_empty_dirs, right_only_files, right_only_dirs, right_only_files_in_dirs, equal, different, errors)
            (testtree, testtree, [], [], {}, False,
                CmpData(set(), set(), set(), set(), set(), FSTree(testtree).to_fileset(no_empty_dirs=True), set(), set())),
            (set({'dir1/', 'dir2/dir3/', 'dir4/', 'dir5/dir6/'}), set({'dir1/', 'dir2/dir3/'}), [], [], {}, False,
                CmpData(set(), set({'dir4', 'dir5/dir6'}), set(), set(), set(), set(), set(), set())),
            (testtree, set({'dir3/', 'dir1/file4.txt', 'dir2/file7', 'dir9/', 'dir10/toto.bat'}), ['*'], [], {}, False,
                CmpData(FSTree(testtree).to_fileset().difference({'dir3', 'dir1/file4.txt', 'dir2/file7'}), set(), set(), set({'dir9', 'dir10'}), set({'dir10/toto.bat'}), set({'dir1/file4.txt', 'dir2/file7'}))),
            (testtree, set({'dir3/', 'dir1/file4.txt', 'dir2/file7', 'dir9/', 'dir10/toto.bat'}), ['*'], [], {}, True,
                CmpData(FSTree(testtree).to_fileset().difference({'dir3', 'dir1/file4.txt', 'dir2/file7'}), set(), set(), set(), set(), set({'dir1/file4.txt', 'dir2/file7'}))),
            
            (testtree, set({'dir3/', 'dir1/file4.txt'}), ['*.txt'], [], {}, False,
                CmpData(set({'file2.txt', 'dir2/dir1/file5.txt'}), set(), set(), set({'dir3'}), set(), set({'dir1/file4.txt'}))),
            (testtree, set({'dir3/', 'dir1/file4.txt'}), ['*.txt'], [], {}, True,
                CmpData(set({'file2.txt', 'dir2/dir1/file5.txt'}), set(), set(), set(), set(), set({'dir1/file4.txt'}))),
            
            (testtree, set({'dir3/', 'dir1/file4.txt', 'dir2/file7', 'dir2/dir1/file5.txt'}), ['*.txt'], [], {}, False,
                CmpData(set({'file2.txt'}), set(), set({'dir2/file7'}), set({'dir3'}), set(), set({'dir1/file4.txt', 'dir2/dir1/file5.txt'}))),
            (testtree, set({'dir3/', 'dir1/file4.txt', 'dir2/file7', 'dir2/dir1/file5.txt'}), ['*.txt'], [], {}, True,
                CmpData(set({'file2.txt'}), set(), set(), set(), set(), set({'dir1/file4.txt', 'dir2/dir1/file5.txt'}))),
            
            (testtree, set({'dir3/', 'dir1/file4.txt', 'dir2/file7', 'dir2/dir1/file5.txt'}), ['*.txt'], [], {'left/dir1/file4.txt':DirSyncer.FileProperties(1,0)}, False,
                CmpData(set({'file2.txt'}), set(), set({'dir2/file7'}), set({'dir3'}), set(), set({'dir2/dir1/file5.txt'}), set({'dir1/file4.txt'}))),
            (testtree, set({'dir3/', 'dir1/file4.txt', 'dir2/file7', 'dir2/dir1/file5.txt'}), ['*.txt'], [], {'left/dir1/file4.txt':DirSyncer.FileProperties(1,0)}, True,
                CmpData(set({'file2.txt'}), set(), set(), set(), set(), set({'dir2/dir1/file5.txt'}), set({'dir1/file4.txt'}))),

            (set({'dir1/', 'dir2/file1.txt', 'dir2/dir3/file2.txt', 'dir2/dir4/file2.doc', 'dir2/dir4/dir5/file3.doc', 'dir6/toto.old'}),
             set({'dir1/', 'dir2/toto.txt', 'dir6/toto.txt', 'rdir1/rdir2/file1.txt', 'rdir1/rdir2/rdir3/file2.txt', 'rdir4/rdir5/file3.txt', 'rdir4/file4.txt'}), ['*.txt'], ['*.old'], {}, False,
             CmpData(set({'dir2/file1.txt', 'dir2/dir3/file2.txt'}), set(), set({'dir2/toto.txt'}), set({'dir1', 'dir6', 'rdir1', 'rdir4'}),
                     set({'dir6/toto.txt', 'rdir1/rdir2/file1.txt', 'rdir1/rdir2/rdir3/file2.txt', 'rdir4/rdir5/file3.txt', 'rdir4/file4.txt'})))
        ]

        TestCompareDirs._execute_test_cases_(dataset, 'test_compare_dirs_other')
    
    def _execute_test_cases_(dataset:list, funcname:str):
        FSMock.install_os_mock()
        nb:int = 0
        for left_filetree, right_filetree, include, exclude, fileproperties, ignore_right_only, expected in dataset:
            nb += 1
            FSMock.set_fsmock_data(FSTree(left_filetree), FSTree(right_filetree), fileproperties)
            for FSMock.is_os_fs_windows_style in [True, False]:
                text = 'Windows' if FSMock.is_os_fs_windows_style else 'Linux'
                compare_result = DirSyncer.compare_dirs(
                    'left', 'right', [fnmatch.translate(x) for x in include],
                    [fnmatch.translate(x) for x in exclude], ignore_right_only=ignore_right_only
                )
                assert are_cmpdata_equal(compare_result, expected, funcname+':Test case #%d (%s paths)' % (nb, text))
        FSMock.uninstall_os_mock()