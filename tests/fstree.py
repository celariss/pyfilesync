from __future__ import annotations # needed for python3 older than 3.14

__author__      = "Jérôme Cuq"
__copyright__   = "Copyright 2026, Jérôme Cuq"
__license__     = "BSD-3-Clause"


def is_present(item, iterable, case_sensitive:bool = True)->bool:
    for i in iterable:
        if i == item:
            return True
        if (not case_sensitive) and isinstance(i,str) and i.lower() == item.lower():
            return True
    return False

class FSTree:
    """simulate file system content using a tree"""
    
    def __init__(self, filetree=None):
        """ filetree can be an instance of list (tree node), FSMock or set (fileset, each item is a path to a file/dir) """
        self.filetree:list = None
        if isinstance(filetree, FSTree):
            self.filetree = filetree.rootnode()
        elif isinstance(filetree, set):
            # convert fileset to filetree
            self.filetree = FSTree.from_fileset(filetree).rootnode()
        elif isinstance(filetree, list):
            self.filetree = filetree
        else:
            self.filetree = []

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
                cur_node = FSTree.find_node(filetree, file, True)
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
    
    def exists(self, path:str, create:bool = False, case_sensitive:bool = False) -> bool:
        path = path.replace('\\', '/')
        res = FSTree.find_node(self.filetree, path, create, case_sensitive)
        if not res:
            res = FSTree.find_node(self.filetree, path+'/', create, case_sensitive)
        return res != None
    
    def find_node(tree:list, path:str, create:bool = False, case_sensitive:bool = True) -> list:
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
            item_in_node:bool = is_present(item, node, case_sensitive)
            item_in_dirsnode:bool = is_present(item, dirsnode.keys(), case_sensitive)
            if num == len(pathitems):
                if (isdir and item_in_node) or ((not isdir) and item_in_dirsnode):
                    # Error, it is file and it should be a dir (and vice versa)
                    return None
                if isdir:
                    if (not item_in_dirsnode) and create:
                        dirsnode[item] = []
                    return dirsnode.get(item, None)
                else:
                    if (not item_in_node):
                        if create:
                            node.append(item)
                        else:
                            return None
                    return node
            if (not item_in_dirsnode) and create:
                dirsnode[item] = []
            if not is_present(item, dirsnode.keys(), case_sensitive):
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
