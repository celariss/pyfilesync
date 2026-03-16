__author__      = "Jérôme Cuq"
__copyright__   = "Copyright 2026, Jérôme Cuq"
__license__     = "BSD-3-Clause"

import fnmatch
from helpers import log
from dirsyncer import *
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
    
    def normalize_cmpdata(cmpdata:CmpData) -> CmpData:
        return CmpData(
            left_only = set({item.replace('\\','/') for item in cmpdata.left_only}),
            right_only = set({item.replace('\\','/') for item in cmpdata.right_only}),
            equal = set({item.replace('\\','/') for item in cmpdata.equal}),
            different = set({item.replace('\\','/') for item in cmpdata.different}),
            errors = cmpdata.errors
        )
    
    def are_cmpdata_equal(cmpdata1:CmpData, cmpdata2:CmpData, label:str) -> bool:
        cmpdata1 = TestCompareDirs.normalize_cmpdata(cmpdata1)
        cmpdata2 = TestCompareDirs.normalize_cmpdata(cmpdata2)
        res:bool = True
        if cmpdata1.left_only != cmpdata2.left_only:
            log(f"left_only differ in {label} : (1=result of compare_dirs, 2=expected result)")
            log(f"1> {cmpdata1.left_only} != ")
            log(f"2> {cmpdata2.left_only}")
            res = False
        if cmpdata1.right_only != cmpdata2.right_only:
            log(f"right_only differ in {label}: (1=result of compare_dirs, 2=expected result)")
            log(f"1> {cmpdata1.right_only} != ")
            log(f"2> {cmpdata2.right_only}")
            res = False
        if cmpdata1.equal != cmpdata2.equal:
            log(f"equal differ in {label}: (1=result of compare_dirs, 2=expected result)")
            log(f"1> {cmpdata1.equal} != ")
            log(f"2> {cmpdata2.equal}")
            res = False
        if cmpdata1.different != cmpdata2.different:
            log(f"different differ in {label}: (1=result of compare_dirs, 2=expected result)")
            log(f"1> {cmpdata1.different} != ")
            log(f"2> {cmpdata2.different}")
            res = False
        if cmpdata1.errors != cmpdata2.errors:
            log(f"errors differ in {label}: (1=result of compare_dirs, 2=expected result)")
            log(f"1> {cmpdata1.errors} != ")
            log(f"2> {cmpdata2.errors}")
            res = False
        return res
    
    def test_compare_dirs_left_only(self):
        """
            Test cases for helpers.compare_dirs() function
        """
        dataset:list = [
            # each test case is : (left_filetree, right_filetree, include, exclude, file properties, ignore_right_only, expected_result)
            #   -> expected_result is a CmpData(left_only, right_only, equal, different, errors)            
            (testtree, [], [], [], {}, False, CmpData(FSTree(testtree).to_fileset(), set(), set(), set(), set())),
            (testtree, [], ['*.txt'], [], {}, False, CmpData(set({'file2.txt', 'dir1/file4.txt', 'dir2/dir1/file5.txt'}), set(), set(), set(), set())),
            (testtree, [], ['file?.txt'], [], {}, False, CmpData(set({'file2.txt', 'dir1/file4.txt', 'dir2/dir1/file5.txt'}), set(), set(), set(), set())),
            (testtree, [], ['*/dir1/file?.txt'], [], {}, False, CmpData(set({'dir1/file4.txt', 'dir2/dir1/file5.txt'}), set(), set(), set(), set())),
            (testtree, [], ['/dir1/file?.txt'], [], {}, False, CmpData(set({'dir1/file4.txt'}), set(), set(), set(), set())),
            (testtree, [], ['item'], [], {}, False, CmpData(set({'dir2/item'}), set(), set(), set(), set())),
            (testtree, [], ['*/item/*'], [], {}, False, CmpData(set({'item/item2'}), set(), set(), set(), set())),
            (testtree, [], ['*/item/'], [], {}, False, CmpData(set({'item/item2'}), set(), set(), set(), set())),
            (testtree, [], ['/dir1/*'], [], {}, False, CmpData(set({'dir1/file3', 'dir1/dir11/file5', 'dir1/dir11/file6.py', 'dir1/file4.txt'}), set(), set(), set(), set())),
            (testtree, [], ['/dir1/'], [], {}, False, CmpData(set({'dir1/file3', 'dir1/dir11/file5', 'dir1/dir11/file6.py', 'dir1/file4.txt'}), set(), set(), set(), set())),
            (testtree, [], ['*/dir1/*'], [], {}, False, CmpData(set({'dir1/file3', 'dir1/dir11/file5', 'dir1/dir11/file6.py', 'dir1/file4.txt', 'dir2/dir1/file5.txt'}), set(), set(), set(), set())),
            (testtree, [], ['*/dir1/'], [], {}, False, CmpData(set({'dir1/file3', 'dir1/dir11/file5', 'dir1/dir11/file6.py', 'dir1/file4.txt', 'dir2/dir1/file5.txt'}), set(), set(), set(), set())),
            (testtree, [], ['*/dir1/*.txt'], [], {}, False, CmpData(set({'dir1/file4.txt', 'dir2/dir1/file5.txt'}), set(), set(), set(), set())),
            (testtree, [], ['/dir1/*.txt'], [], {}, False, CmpData(set({'dir1/file4.txt'}), set(), set(), set(), set())),
            (testtree, [], ['/dir1/dir11/'], [], {}, False, CmpData(set({'dir1/dir11/file5', 'dir1/dir11/file6.py'}), set(), set(), set(), set())),
            (testtree, [], ['/dir2/file7/'], [], {}, False, CmpData(set(), set(), set(), set(), set())),
            (testtree, [], ['/dir2/file7'], [], {}, False, CmpData(set({'dir2/file7'}), set(), set(), set(), set())),
            (testtree, [], ['*/dir11/file5'], [], {}, False, CmpData(set({'dir1/dir11/file5'}), set(), set(), set(), set())),
            (testtree, [], [], ['*/dir1/'], {}, False, CmpData(set({'file2.txt', 'file1', 'dir2/file7', 'dir2/file8.ini', 'dir2/item', 'dir3', 'item/item2'}), set(), set(), set(), set())),
            (testtree, [], [], ['*/dir1/*'], {}, False, CmpData(set({'file2.txt', 'file1', 'dir2/file7', 'dir2/file8.ini', 'dir2/item', 'dir3', 'item/item2'}), set(), set(), set(), set())),
            (testtree, [], [], ['/dir1/'], {}, False, CmpData(set({'file2.txt', 'file1', 'dir2/file7', 'dir2/file8.ini', 'dir2/item', 'dir3', 'item/item2', 'dir2/dir1/file5.txt'}), set(), set(), set(), set())),
            (testtree, [], [], ['/dir1/dir11/file5'], {}, False, CmpData(FSTree(testtree).to_fileset().difference({'dir1/dir11/file5'}), set(), set(), set(), set())),
            (testtree, [], ['/dir1/'], ['*.py'], {}, False, CmpData(set({'dir1/file3', 'dir1/dir11/file5', 'dir1/file4.txt'}), set(), set(), set(), set())),
            (testtree, [], ['/dir1/'], ['*/dir11/'], {}, False, CmpData(set({'dir1/file3', 'dir1/file4.txt'}), set(), set(), set(), set())),
            (set({'dir1/dir2/dir3/file1', 'dir1/dir4/dir5/dir3/file2', 'dir1/dir4/dir5/dir3/dir6/', 'dir1/dir4/dir5/dir3/dir6/', 'dir2/dir3/'}), [], [], ['*/dir3/'], {}, False,
                CmpData(set({'dir2', 'dir1/dir2', 'dir1/dir4/dir5'}), set(), set(), set(), set())),
        ]
        
        TestCompareDirs._execute_test_cases_(dataset, 'test_compare_dirs_left_only')

    def test_compare_dirs_left_only_and_equal(self):
        """
            Test cases for helpers.compare_dirs() function
        """
        dataset:list = [
            # each test case is : (left_filetree, right_filetree, include, exclude, file properties, ignore_right_only, expected_result)
            #   -> expected_result is a CmpData(left_only, right_only, equal, different, errors)
            (testtree, set({'dir1/file3'}), [], [], {}, False,
                CmpData(FSTree(testtree).to_fileset().difference({'dir1/file3'}), set(), set({'dir1/file3'}), set(), set())),
            (testtree, set({'dir3/'}), [], [], {}, False,
                CmpData(FSTree(testtree).to_fileset().difference({'dir3'}), set(), set({'dir3'}), set(), set())),
            (testtree, set({'dir1/file4.txt', 'dir2/dir1/file5.txt'}), ['*.txt'], [], {}, False,
                CmpData(set({'file2.txt'}), set(), set({'dir1/file4.txt', 'dir2/dir1/file5.txt'}), set(), set())),
            (testtree, set({'dir1/file4.txt'}), ['*.txt'], [], {}, False,
                CmpData(set({'file2.txt', 'dir2/dir1/file5.txt'}), set(), set({'dir1/file4.txt'}), set(), set())),
        ]

        TestCompareDirs._execute_test_cases_(dataset, 'test_compare_dirs_left_only_and_equal')

    def test_compare_dirs_other(self):
        """
            Test cases for helpers.compare_dirs() function
        """
        dataset:list = [
            # each test case is : (left_filetree, right_filetree, include, exclude, file properties, ignore_right_only, expected_result)
            #   -> expected_result is a CmpData(left_only, right_only, equal, different, errors)
            (set({'dir1/', 'dir2/dir3/'}), set({'dir1/', 'dir2/dir3/'}), [], [], {}, False,
                CmpData(set(), set(), set({'dir1', 'dir2/dir3'}), set(), set())),
            (testtree, set({'dir3/', 'dir1/file4.txt', 'dir2/file7', 'dir9/', 'dir10/toto.bat'}), ['*'], [], {}, False,
                CmpData(FSTree(testtree).to_fileset().difference({'dir3', 'dir1/file4.txt', 'dir2/file7'}), set({'dir9', 'dir10/toto.bat'}), set({'dir3', 'dir1/file4.txt', 'dir2/file7'}), set(), set())),
            (testtree, set({'dir3/', 'dir1/file4.txt', 'dir2/file7', 'dir9/', 'dir10/toto.bat'}), ['*'], [], {}, True,
                CmpData(FSTree(testtree).to_fileset().difference({'dir3', 'dir1/file4.txt', 'dir2/file7'}), set(), set({'dir3', 'dir1/file4.txt', 'dir2/file7'}), set(), set())),
            
            (testtree, set({'dir3/', 'dir1/file4.txt'}), ['*.txt'], [], {}, False,
                CmpData(set({'file2.txt', 'dir2/dir1/file5.txt'}), set({'dir3'}), set({'dir1/file4.txt'}), set(), set())),
            (testtree, set({'dir3/', 'dir1/file4.txt'}), ['*.txt'], [], {}, True,
                CmpData(set({'file2.txt', 'dir2/dir1/file5.txt'}), set(), set({'dir1/file4.txt'}), set(), set())),
            
            (testtree, set({'dir3/', 'dir1/file4.txt', 'dir2/file7', 'dir2/dir1/file5.txt'}), ['*.txt'], [], {}, False,
                CmpData(set({'file2.txt'}), set({'dir3', 'dir2/file7'}), set({'dir1/file4.txt', 'dir2/dir1/file5.txt'}), set(), set())),
            (testtree, set({'dir3/', 'dir1/file4.txt', 'dir2/file7', 'dir2/dir1/file5.txt'}), ['*.txt'], [], {}, True,
                CmpData(set({'file2.txt'}), set(), set({'dir1/file4.txt', 'dir2/dir1/file5.txt'}), set(), set())),
            
            (testtree, set({'dir3/', 'dir1/file4.txt', 'dir2/file7', 'dir2/dir1/file5.txt'}), ['*.txt'], [], {'left/dir1/file4.txt':DirSyncer.FileProperties(1,0)}, False,
                CmpData(set({'file2.txt'}), set({'dir3', 'dir2/file7'}), set({'dir2/dir1/file5.txt'}), set({'dir1/file4.txt'}), set())),
            (testtree, set({'dir3/', 'dir1/file4.txt', 'dir2/file7', 'dir2/dir1/file5.txt'}), ['*.txt'], [], {'left/dir1/file4.txt':DirSyncer.FileProperties(1,0)}, True,
                CmpData(set({'file2.txt'}), set(), set({'dir2/dir1/file5.txt'}), set({'dir1/file4.txt'}), set()))
        ]

        TestCompareDirs._execute_test_cases_(dataset, 'test_compare_dirs_other')
    
    def _execute_test_cases_(dataset:list, funcname:str):
        FSMock.install_os_mock()
        nb:int = 0
        for left_filetree, right_filetree, include, exclude, fileproperties, ignore_right_only, expected in dataset:
            nb += 1
            FSMock.set_os_mock_filetrees(FSTree(left_filetree), FSTree(right_filetree), fileproperties)
            FSMock.is_os_walk_mock_windows_style = False
            assert TestCompareDirs.are_cmpdata_equal(
                DirSyncer.compare_dirs('left', 'right', [fnmatch.translate(x) for x in include],
                [fnmatch.translate(x) for x in exclude], ignore_right_only=ignore_right_only), expected, funcname+':Test case #%d (Linux paths)' % nb
            )
            FSMock.is_os_walk_mock_windows_style = True
            assert TestCompareDirs.are_cmpdata_equal(
                DirSyncer.compare_dirs('left', 'right', [fnmatch.translate(x) for x in include],
                [fnmatch.translate(x) for x in exclude], ignore_right_only=ignore_right_only), expected, funcname+':Test case #%d (Windows paths)' % nb
            )
        FSMock.uninstall_os_mock()