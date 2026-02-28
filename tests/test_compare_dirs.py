import fnmatch
from pathlib import WindowsPath

import pytest

from helpers import compare_dirs, CmpData, log
import os 

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
            'file7', 'file8.ini', 'item'
        ],
        'dir3':[],
        'item':[]
    }
]

class FSMock:
    # static variables to handle os.walk mocking
    system_os_walk  = os.walk
    system_os_isdir = os.path.isdir
    left_filetree:FSMock = None
    right_filetree:FSMock = None

    def __init__(self, filetree):
        """ filetree can be an instance of list (tree node), FSMock or set (fileset, each item is a path to a file/dir) """
        self.filetree:list = None
        if isinstance(filetree, FSMock):
            self.filetree = filetree.rootnode()
        elif isinstance(filetree, set):
            # convert fileset to filetree
            self.filetree = FSMock.from_fileset(filetree).rootnode()
        elif isinstance(filetree, list):
            self.filetree = filetree

    def rootnode(self) -> list:
        return self.filetree
    
    def from_fileset(fileset:set) -> FSMock:
        filelist:list = list(fileset)
        filelist.sort(key=lambda x: x.count('/'))
        filetree:list = []
        cur_node:list = filetree
        if filelist:
            cur_level:int = 0
            for file in filelist:
                level = file.count('/')
                while level>cur_level:
                    # we are going down in the tree, we need to create a new subtree
                    dirname = file.split('/')[cur_level]
                    cur_node.append({dirname: []})
                    cur_node = cur_node[-1][dirname]
                    cur_level += 1
                else:
                    cur_node.append(file.split('/')[-1])
        return FSMock(filetree)
    
    def _get_dirs_node_(node):
        for item in node:
            if isinstance(item, dict):
                return item
        return {}
    
    def to_fileset(self, root:str='') -> set:
        fileset:set = set()
        if root:
            root = root+'/'
        for node in self.filetree:
            if isinstance(node, dict):
                for dir, subtree in node.items():
                    subdirs = FSMock(subtree).to_fileset(root+dir)
                    if not subdirs:
                        fileset.add(root+dir)
                    fileset.update(subdirs)
            else:
                fileset.add(root+node)
        return fileset
    
    def install_os_mock():
        os.walk = FSMock._os_walk_mock_
        os.path.isdir = FSMock._os_isdir_mock_

    def uninstall_os_mock():
        os.walk = FSMock.system_os_walk
        os.path.isdir = FSMock.system_os_isdir

    def set_os_mock_filetrees(left_filetree:FSMock, right_filetree:FSMock):
        FSMock.left_filetree = left_filetree
        FSMock.right_filetree = right_filetree

    def _find_dirs_node_(treenode:list) -> dict:
        for item in treenode:
            if isinstance(item,dict):
                return item
        return {}
    
    def _os_isdir_mock_(path:str) -> bool:
        # If path is not a string, it means that it is called from pytest, we call the real os.path.isdir on it
        if not isinstance(path, str):
            return FSMock.system_os_isdir(path)
        
        node:list = None
        if path.startswith('left'):
            path = os.path.relpath(path, 'left')
            node = FSMock.left_filetree.rootnode()
        else:
            path = os.path.relpath(path, 'right')
            node = FSMock.right_filetree.rootnode()
        spath:list = path.split('/')
        for idx in range(0,len(spath)):
            curdir:str = spath[idx]
            if idx==len(spath)-1:
                isfile = curdir in node
                if not isfile:
                    # is it in node directories ?
                    return curdir in FSMock._find_dirs_node_(node)
                return False
            else:
                dirs:dict = FSMock._find_dirs_node_(node)
                if curdir in dirs:
                    node = dirs[curdir]
                else:
                    # Error : the given path is not in filetree
                    return False
        # we should never reach this point
        return False

        

    def _os_walk_mock_(path:str, filetree:list=None) -> list[tuple]:
        #log(f"os_walk_mock called with path: {path}")
        if filetree is None:
            if path == 'left':
                filetree = FSMock.left_filetree.rootnode()
            elif path == 'right':
                filetree = FSMock.right_filetree.rootnode()
        cur_root = path
        cur_node:list = filetree
        result = []
        files:list = []
        dirs:list = []
        for node in cur_node:
            if isinstance(node, dict):
                # this node contains the directories
                for dir in node.keys():
                    dirs.append(dir)
                    result.extend(FSMock._os_walk_mock_(cur_root+'/'+dir, node[dir]))
            else:
                # this node is a file
                files.append(node)
        result.insert(0, (cur_root, dirs, files))
        # (root, dirs, files)
        return result

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
            # each test case is : (left_filetree, right_filetree, include, exclude, expected_result)
            #   -> expected_result is a CmpData(left_only, right_only, equal, different, errors)
            (testtree, [], [], [], CmpData(FSMock(testtree).to_fileset(), set(), set(), set(), set())),
            (testtree, [], ['*.txt'], [], CmpData(set({'file2.txt', 'dir1/file4.txt'}), set(), set(), set(), set())),
            (testtree, [], ['item/'], [], CmpData(set({'item'}), set(), set(), set(), set())),
            (testtree, [], ['item'], [], CmpData(set({'dir2/item'}), set(), set(), set(), set())),
        ]

        TestCompareDirs._execute_test_cases_(dataset)

    def test_compare_dirs_left_only_and_equal(self):
        """
            Test cases for helpers.compare_dirs() function
        """
        dataset:list = [
            # each test case is : (left_filetree, right_filetree, include, exclude, expected_result)
            #   -> expected_result is a CmpData(left_only, right_only, equal, different, errors)
            (testtree, set({'dir1/file3'}), [], [], CmpData(FSMock(testtree).to_fileset().difference({'dir1/file3'}), set(), set({'dir1/file3'}), set(), set())),
            (testtree, set({'dir3'}), [], [], CmpData(FSMock(testtree).to_fileset().difference({'dir3'}), set(), set({'dir3'}), set(), set())),
            (testtree, set({'dir1/file4.txt'}), ['*.txt'], [], CmpData(set({'file2.txt'}), set(), set({'dir1/file4.txt'}), set(), set())),
        ]

        TestCompareDirs._execute_test_cases_(dataset)

    def test_compare_dirs_other(self):
        """
            Test cases for helpers.compare_dirs() function
        """
        dataset:list = [
            # each test case is : (left_filetree, right_filetree, include, exclude, expected_result)
            #   -> expected_result is a CmpData(left_only, right_only, equal, different, errors)
            (testtree, set({'dir3', 'dir1/file4.txt'}), ['*.txt'], [], CmpData(set({'file2.txt'}), set({'dir3'}), set({'dir1/file4.txt'}), set(), set())),
        ]

        TestCompareDirs._execute_test_cases_(dataset)
    
    def _execute_test_cases_(dataset:list):
        FSMock.install_os_mock()
        nb:int = 0
        for left_filetree, right_filetree, include, exclude, expected in dataset:
            nb += 1
            FSMock.set_os_mock_filetrees(FSMock(left_filetree), FSMock(right_filetree))
            assert TestCompareDirs.are_cmpdata_equal(
                compare_dirs('left', 'right', [fnmatch.translate(x) for x in include],
                [fnmatch.translate(x) for x in exclude]), expected, 'Test case #%d' % nb
            )
        FSMock.uninstall_os_mock()