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
                    'file5', 'file6.txt',
                ]
            }
        ],
        'dir2':[
            'file7', 'file8.txt',
        ],
        'dir3':[]
    }
]

class FSMock:
    # static variables to handle os.walk mocking
    system_os_walk = os.walk
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
    
    def to_fileset(self, root:str='') -> set:
        fileset:set = set()
        if root:
            root = root+'/'
        for node in self.filetree:
            if isinstance(node, dict):
                for dir, subtree in node.items():
                    fileset.add(root+dir)
                    fileset.update(FSMock(subtree).to_fileset(root+dir))
            else:
                fileset.add(root+node)
        return fileset
    
    def install_os_walk_mock():
        os.walk = FSMock._os_walk_mock_

    def uninstall_os_walk_mock():
        os.walk = FSMock.system_os_walk

    def set_os_mock_filetrees(left_filetree:FSMock, right_filetree:FSMock):
        FSMock.left_filetree = left_filetree
        FSMock.right_filetree = right_filetree

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
    
    def are_cmpdata_equal(cmpdata1:CmpData, cmpdata2:CmpData) -> bool:
        cmpdata1 = TestCompareDirs.normalize_cmpdata(cmpdata1)
        cmpdata2 = TestCompareDirs.normalize_cmpdata(cmpdata2)
        if cmpdata1.left_only != cmpdata2.left_only:
            log(f"left_only differ:")
            log(f"> {cmpdata1.left_only} != ")
            log(f"> {cmpdata2.left_only}")
            return False
        if cmpdata1.right_only != cmpdata2.right_only:
            log(f"right_only differ:")
            log(f"> {cmpdata1.right_only} != ")
            log(f"> {cmpdata2.right_only}")
            return False
        if cmpdata1.equal != cmpdata2.equal:
            log(f"equal differ:")
            log(f"> {cmpdata1.equal} != ")
            log(f"> {cmpdata2.equal}")
            return False
        if cmpdata1.different != cmpdata2.different:
            log(f"different differ:")
            log(f"> {cmpdata1.different} != ")
            log(f"> {cmpdata2.different}")
            return False
        if cmpdata1.errors != cmpdata2.errors:
            log(f"errors differ:")
            log(f"> {cmpdata1.errors} != ")
            log(f"> {cmpdata2.errors}")
            return False
        return True
    
    def test_compare_dirs(self):
        """
            Test cases for helpers.compare_dirs() function
        """
        FSMock.install_os_walk_mock()
        dataset:list = [
            # each test case is : (left_filetree, right_filetree, include, exclude, expected_result)
            (testtree, [], [], [], CmpData(FSMock(testtree).to_fileset(), set(), set(), set(), set())),
            (testtree, set({'dir1/file3'}), [], [], CmpData(FSMock(testtree).to_fileset().difference({'dir1','dir1/file3'}), set(), set({'dir1','dir1/file3'}), set(), set())),
            (testtree, set({'dir3'}), [], [], CmpData(FSMock(testtree).to_fileset().difference({'dir3'}), set(), set({'dir3'}), set(), set())),
        ]
        for left_filetree, right_filetree, include, exclude, expected in dataset:
            FSMock.set_os_mock_filetrees(FSMock(left_filetree), FSMock(right_filetree))
            assert TestCompareDirs.are_cmpdata_equal(compare_dirs('left', 'right', include, exclude), expected)
        FSMock.uninstall_os_walk_mock()