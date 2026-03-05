from __future__ import annotations # needed for python3 older than 3.14

__author__      = "Jérôme Cuq"
__copyright__   = "Copyright 2026, Jérôme Cuq"
__license__     = "BSD-3-Clause"

import fnmatch
import re
from helpers import log
from dirsyncer import *
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
            'file7', 'file8.ini', 'item',
            {
                'dir1':['file5.txt']
            }
        ],
        'dir3':[],
        'item':['item2']
    }
]

class FSMock:
    # static variables to handle os.walk mocking
    system_os_walk  = os.walk
    system_os_isdir = os.path.isdir
    system_os_isfile = os.path.isfile
    actual_get_file_properties = DirSyncer.__get_file_properties__
    left_filetree:FSMock = None
    right_filetree:FSMock = None
    file_properties:dict[str,DirSyncer.FileProperties] = {}
    is_os_walk_mock_windows_style:bool = False

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
    
    def _find_node_(tree:list, path:str, create:bool = False) -> list:
        isdir = path.endswith('/')
        pathitems:list
        if isdir:
            pathitems = path.split('/')[0:-1]
        else:
            pathitems = path.split('/')
        node:list = tree
        num = 0
        for item in pathitems:
            num +=1
            dirsnode:dict =FSMock._get_dirs_node_(node)
            if num == len(pathitems):
                if (isdir and item in node) or ((not isdir) and item in dirsnode):
                    # Error, it is file and it should be a dir (and vice versa)
                    return None
                if isdir:
                    if (not item in dirsnode) and create:
                        dirsnode[item] = []
                    return dirsnode.get(item, [])
                else:
                    if (not item in node) and create:
                        node.append(item)
                    return node
            if (not item in dirsnode) and create:
                dirsnode[item] = []
            if not item in dirsnode:
                # error, path does not exist in tree
                return None
            node = dirsnode[item] 
        return node
    
    def from_fileset(fileset:set) -> FSMock:
        filelist:list = list(fileset)
        filelist.sort(key=lambda x: x.count('/'))
        filetree:list = []
        cur_node:list = filetree
        if filelist:
            cur_level:int = 0
            for file in filelist:
                cur_node = FSMock._find_node_(filetree, file, True)
        return FSMock(filetree)
    
    def _get_dirs_node_(node:list) -> dict:
        for item in node:
            if isinstance(item, dict):
                return item
        node.append({})
        return node[len(node)-1]
    
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
        os.path.isfile = FSMock._os_isfile_mock_
        DirSyncer.__get_file_properties__ = FSMock._get_file_properties_mock_

    def uninstall_os_mock():
        os.walk = FSMock.system_os_walk
        os.path.isdir = FSMock.system_os_isdir
        os.path.isfile = FSMock.system_os_isfile
        DirSyncer.__get_file_properties__ = FSMock.actual_get_file_properties

    def set_os_mock_filetrees(left_filetree:FSMock, right_filetree:FSMock, file_properties = {}):
        FSMock.left_filetree = left_filetree
        FSMock.right_filetree = right_filetree
        FSMock.file_properties = file_properties

    def _find_dirs_node_(treenode:list) -> dict:
        for item in treenode:
            if isinstance(item,dict):
                return item
        return {}
    
    def _os_isdirorfile_mock_(path:str, dir:bool) -> bool:        
        node:list = None
        if path.startswith('left'):
            path = os.path.relpath(path, 'left')
            node = FSMock.left_filetree.rootnode()
        else:
            path = os.path.relpath(path, 'right')
            node = FSMock.right_filetree.rootnode()
        spath:list =  re.split(r'[\\/\s]+', path)
        for idx in range(0,len(spath)):
            curdir:str = spath[idx]
            if idx==len(spath)-1:
                isfile = curdir in node
                if dir:
                    if not isfile:
                        # is it in node directories ?
                        return curdir in FSMock._find_dirs_node_(node)
                    return False
                else:
                    if isfile:
                        return curdir in node
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
    
    def _os_isdir_mock_(path:str) -> bool:
        # If path is not a string, it means that it is called from pytest, we call the real os.path.isdir on it
        if not isinstance(path, str):
            return FSMock.system_os_isdir(path)
        return FSMock._os_isdirorfile_mock_(path, True)
    
    def _os_isfile_mock_(path:str) -> bool:
        # If path is not a string, it means that it is called from pytest, we call the real os.path.isfile on it
        if not isinstance(path, str):
            return FSMock.system_os_isfile(path)
        return FSMock._os_isdirorfile_mock_(path, False)
    
    def _get_file_properties_mock_(path:str, errors:list = []) -> DirSyncer.FileProperties:
        path = path.replace('\\', '/')
        if path in FSMock.file_properties:
            return FSMock.file_properties[path]
        return DirSyncer.FileProperties(0,0)
    
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
        # We convert path to windows FS style if asked
        if FSMock.is_os_walk_mock_windows_style:
            cur_root = cur_root.replace('/','\\')
            dirs = [d.replace('/','\\') for d in dirs]
            files = [f.replace('/','\\') for f in files]
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
            # each test case is : (left_filetree, right_filetree, include, exclude, file properties, ignore_right_only, expected_result)
            #   -> expected_result is a CmpData(left_only, right_only, equal, different, errors)
            (testtree, [], [], [], {}, False, CmpData(FSMock(testtree).to_fileset(), set(), set(), set(), set())),
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
            (testtree, [], [], ['/dir1/dir11/file5'], {}, False, CmpData(FSMock(testtree).to_fileset().difference({'dir1/dir11/file5'}), set(), set(), set(), set())),
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
                CmpData(FSMock(testtree).to_fileset().difference({'dir1/file3'}), set(), set({'dir1/file3'}), set(), set())),
            (testtree, set({'dir3/'}), [], [], {}, False,
                CmpData(FSMock(testtree).to_fileset().difference({'dir3'}), set(), set({'dir3'}), set(), set())),
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
                CmpData(FSMock(testtree).to_fileset().difference({'dir3', 'dir1/file4.txt', 'dir2/file7'}), set({'dir9', 'dir10/toto.bat'}), set({'dir3', 'dir1/file4.txt', 'dir2/file7'}), set(), set())),
            (testtree, set({'dir3/', 'dir1/file4.txt', 'dir2/file7', 'dir9/', 'dir10/toto.bat'}), ['*'], [], {}, True,
                CmpData(FSMock(testtree).to_fileset().difference({'dir3', 'dir1/file4.txt', 'dir2/file7'}), set(), set({'dir3', 'dir1/file4.txt', 'dir2/file7'}), set(), set())),
            
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
            FSMock.set_os_mock_filetrees(FSMock(left_filetree), FSMock(right_filetree), fileproperties)
            FSMock.is_os_walk_mock_windows_style = False
            assert TestCompareDirs.are_cmpdata_equal(
                DirSyncer.compare_dirs('left', 'right', [fnmatch.translate(x) for x in include],
                [fnmatch.translate(x) for x in exclude], ignore_right_only=ignore_right_only), expected, funcname+':Test case #%d' % nb
            )
            FSMock.is_os_walk_mock_windows_style = True
            assert TestCompareDirs.are_cmpdata_equal(
                DirSyncer.compare_dirs('left', 'right', [fnmatch.translate(x) for x in include],
                [fnmatch.translate(x) for x in exclude], ignore_right_only=ignore_right_only), expected, funcname+':Test case #%d' % nb
            )
        FSMock.uninstall_os_mock()