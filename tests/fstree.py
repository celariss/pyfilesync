from __future__ import annotations # needed for python3 older than 3.14

__author__      = "Jérôme Cuq"
__copyright__   = "Copyright 2026, Jérôme Cuq"
__license__     = "BSD-3-Clause"

class FSTree:
    """simulate file system content using a tree"""
    
    def __init__(self, filetree):
        """ filetree can be an instance of list (tree node), FSMock or set (fileset, each item is a path to a file/dir) """
        self.filetree:list = None
        if isinstance(filetree, FSTree):
            self.filetree = filetree.rootnode()
        elif isinstance(filetree, set):
            # convert fileset to filetree
            self.filetree = FSTree.from_fileset(filetree).rootnode()
        elif isinstance(filetree, list):
            self.filetree = filetree

    def rootnode(self) -> list:
        return self.filetree
    
    def from_fileset(fileset:set) -> FSTree:
        filelist:list = list(fileset)
        filelist.sort(key=lambda x: x.count('/'))
        filetree:list = []
        cur_node:list = filetree
        if filelist:
            cur_level:int = 0
            for file in filelist:
                cur_node = FSTree._find_node_(filetree, file, True)
        return FSTree(filetree)
    
    def to_fileset(self, root:str='', no_empty_dirs:bool = False) -> set:
        fileset:set = set()
        if root:
            root = root+'/'
        for node in self.filetree:
            if isinstance(node, dict):
                for dir, subtree in node.items():
                    subdirs = FSTree(subtree).to_fileset(root+dir)
                    if (not subdirs) and not no_empty_dirs:
                        fileset.add(root+dir)
                    fileset.update(subdirs)
            else:
                fileset.add(root+node)
        return fileset
    
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
            dirsnode:dict =FSTree._get_dirs_node_(node)
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
    
    def _get_dirs_node_(node:list) -> dict:
        for item in node:
            if isinstance(item, dict):
                return item
        node.append({})
        return node[len(node)-1]
