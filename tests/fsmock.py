from __future__ import annotations # needed for python3 older than 3.14
__author__      = "Jérôme Cuq"
__license__     = "BSD-3-Clause"

import os
import re
import traceback
from tests.fstree import FSTree
import shutil 
from dirsyncer import DirSyncer
from tests.fstree import FSTree 


class FSMock:
    """This class is used to mock some system apis from "os" module"""

    def __init__(self):
        """constructor, installs os mock when creating an instance of FSMock
        to be used with "with" statement, to automatically uninstall os mock at the end of the "with" block, or by calling close() method"""
        pass
    def close(self):
        FSMock.uninstall_os_mock()
    def __enter__(self):
        FSMock.install_os_mock()
        return self
    def __exit__(self, *a):
        self.close()

        
    # static variables to handle os.walk mocking
    #system_os_sep = os.path.sep
    system_os_walk  = os.walk
    system_os_isdir = os.path.isdir
    system_os_isfile = os.path.isfile
    system_os_split = os.path.split
    system_os_join = os.path.join
    system_os_relpath = os.path.relpath
    system_os_normpath = os.path.normpath
    system_os_dirname = os.path.dirname
    system_os_exists = os.path.exists
    system_os_islink = os.path.islink
    system_os_getsize = os.path.getsize
    system_os_remove = os.remove
    system_shutil_rmtree = shutil.rmtree
    system_os_mkdir = os.mkdir
    system_os_makedirs = os.makedirs
    system_shutil_copy2 = shutil.copy2
    system_shutil_move = shutil.move
    system_os_stat = os.stat
    system_os_chmod = os.chmod
    system_os_scandir = os.scandir
    actual_get_file_properties = DirSyncer.__get_file_properties__

    left_filetree:FSTree = FSTree()
    right_filetree:FSTree = FSTree()
    file_properties:dict[str,DirSyncer.FileProperties] = {}
    is_os_fs_windows_style:bool = False
    os_path_sep:str = ''
    os_path_exists_values:dict[str,bool] = {}
    os_rmdir_failure_paths:dict[str,bool] = {}
    os_copy_failure_paths:dict[str,bool] = {}
    copied:set = set()
    removed:set = set()
    removed_dirs:set = set()
    created_dirs:set = set()
    
    def install_os_mock():
        os.walk = FSMock._os_walk_mock_
        os.path.isdir = FSMock._os_isdir_mock_
        os.path.isfile = FSMock._os_isfile_mock_
        os.path.split = FSMock._os_split_mock_
        os.path.join = FSMock._os_join_mock_
        os.path.relpath = FSMock._os_relpath_mock_
        os.path.normpath = FSMock._os_normpath
        os.path.dirname = FSMock._os_dirname_mock_
        os.path.exists = FSMock._os_exists
        os.path.islink = FSMock._os_islink
        os.path.getsize = FSMock._os_getsize
        os.remove = FSMock._os_remove
        shutil.rmtree = FSMock._shutil_rmtree
        os.mkdir = FSMock._os_mkdir
        os.makedirs = FSMock._os_makedirs
        shutil.copy2 = FSMock._shutil_copy2
        shutil.move = FSMock._shutil_move
        os.stat = FSMock._os_stat
        os.chmod = FSMock._os_chmod
        os.scandir = FSMock._os_scandir_mock
        DirSyncer.__get_file_properties__ = FSMock._get_file_properties_mock_
        FSMock.left_filetree = FSTree()
        FSMock.right_filetree = FSTree()
        FSMock.file_properties = {}
        FSMock.clean_sync_data()
        FSMock.set_os_fs_style(os.path.sep == '\\')

    def clean_sync_data():
        FSMock.copied = set()
        FSMock.removed = set()
        FSMock.removed_dirs = set()
        FSMock.created_dirs = set()
        FSMock.os_path_exists_values.clear()
        FSMock.os_rmdir_failure_paths.clear()
        FSMock.os_copy_failure_paths.clear()

    def uninstall_os_mock():
        os.walk = FSMock.system_os_walk
        os.path.isdir = FSMock.system_os_isdir
        os.path.isfile = FSMock.system_os_isfile
        os.path.split = FSMock.system_os_split
        os.path.join = FSMock.system_os_join
        os.path.relpath = FSMock.system_os_relpath
        os.path.normpath = FSMock.system_os_normpath
        os.path.dirname = FSMock.system_os_dirname
        os.path.exists = FSMock.system_os_exists
        os.path.islink = FSMock.system_os_islink
        os.path.getsize = FSMock.system_os_getsize
        os.remove = FSMock.system_os_remove
        shutil.rmtree = FSMock.system_shutil_rmtree
        os.mkdir = FSMock.system_os_mkdir
        os.makedirs = FSMock.system_os_makedirs
        shutil.copy2 = FSMock.system_shutil_copy2
        shutil.move = FSMock.system_shutil_move
        os.stat = FSMock.system_os_stat
        os.chmod = FSMock.system_os_chmod
        os.scandir = FSMock.system_os_scandir
        DirSyncer.__get_file_properties__ = FSMock.actual_get_file_properties
        FSMock.left_filetree = FSTree()
        FSMock.right_filetree = FSTree()
        FSMock.file_properties = {}

    def set_fsmock_data(left_filetree:FSTree, right_filetree:FSTree, file_properties:dict = None):
        FSMock.left_filetree = left_filetree
        FSMock.right_filetree = right_filetree
        FSMock.file_properties = file_properties if file_properties else {}

    def set_os_fs_style(is_windows_style:bool):
        """sets the os filesystem style to windows or unix, this will change the path separator and case sensitivity use in mocked os functions"""
        FSMock.is_os_fs_windows_style = is_windows_style
        FSMock.os_path_sep = '\\' if is_windows_style else '/'

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
        if FSMock._called_from_outside(path):
            return FSMock.system_os_isdir(path)
        return FSMock._os_isdirorfile_mock_(path, True)
    
    def _os_isfile_mock_(path:str) -> bool:
        if FSMock._called_from_outside(path):
            return FSMock.system_os_isfile(path)
        return FSMock._os_isdirorfile_mock_(path, False)
    
    def _os_split_mock_(path:str) -> tuple[str, str]:
        if FSMock._called_from_outside(path):
            return FSMock.system_os_split(path)
        path = path.replace('\\', '/')
        if '/' in path:
            idx = path.rindex('/')
            return path[0:idx].replace('/', FSMock.os_path_sep), path[idx+1:]
        else:
            return '', path
    
    def _os_join_mock_(path, *paths) -> str:
        if FSMock._called_from_outside(path):
            return FSMock.system_os_join(path, *paths)
        path = path.replace('\\', os.path.sep).replace('/', os.path.sep)
        paths2:tuple = (p.replace('\\', os.path.sep).replace('/', os.path.sep) for p in paths)
        if FSMock.is_os_fs_windows_style:
            return FSMock.system_os_join(path, *paths2).replace('/', '\\')
        else:
            return FSMock.system_os_join(path, *paths2).replace('\\', '/')
        
    def _os_relpath_mock_(path1:str, path2:str) -> str:
        if FSMock._called_from_outside(path1):
            return FSMock.system_os_relpath(path1, path2)
        if FSMock.is_os_fs_windows_style:
            sep = '\\'
        else:
            sep = '/'
        p1 = path1.split(sep)
        p2 = path2.split(sep)
        p = sep.join(p1[len(p2):])
        return p
    
    def _called_from_outside(path:str) -> bool:
        if (not isinstance(path, str)) or os.path.isabs(path):
            return True
        return False
    
    def _os_normpath(path:str) -> str:
        if FSMock._called_from_outside(path):
            return FSMock.system_os_normpath(path)
        path = path.replace('\\', os.path.sep).replace('/', os.path.sep)
        if FSMock.is_os_fs_windows_style:
            return FSMock.system_os_normpath(path).replace('/', '\\')
        else:
            return FSMock.system_os_normpath(path).replace('\\', '/')
        
    def _os_dirname_mock_(path:str) -> str:
        if FSMock._called_from_outside(path):
            return FSMock.system_os_dirname(path)
        path = path.replace('\\', os.path.sep).replace('/', os.path.sep)
        if FSMock.is_os_fs_windows_style:
            return FSMock.system_os_dirname(path).replace('/', '\\')
        else:
            return FSMock.system_os_dirname(path).replace('\\', '/')
        
    def _get_file_properties_mock_(path:str, errors:list) -> DirSyncer.FileProperties:
        path = path.replace('\\', '/')
        if path in FSMock.file_properties:
            return FSMock.file_properties[path]
        return DirSyncer.FileProperties(0,0)
    
    def _remove_first_level(path:str)->str:
        folders:list = path.replace('\\', '/').split('/')
        if len(folders)<2:
            return ''
        if FSMock.is_os_fs_windows_style:
            return '/'.join(folders[1:])
        else:
            return '\\'.join(folders[1:])
    
    def _os_walk_mock_(path:str, filetree:list=None, topdown:bool=True) -> list[tuple]:
        if FSMock._called_from_outside(path):
            return FSMock.system_os_walk(path)
        #log(f"os_walk_mock called with path: {path}")
        cur_node:list = None
        if filetree is None:
            if path.startswith('left'):
                filetree = FSMock.left_filetree.rootnode()
            elif path.startswith('right'):
                filetree = FSMock.right_filetree.rootnode()
            if FSMock.is_os_fs_windows_style:
                sep = '\\'
            else:
                sep = '/'
            if sep in path:
                subpath = os.path.join(*(path.split(sep)[1:]))
                cur_node = FSTree.find_node(filetree, subpath+'/')
        cur_root = path
        if cur_node is None:
            cur_node = filetree
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
        if FSMock.is_os_fs_windows_style:
            cur_root = cur_root.replace('/','\\')
            dirs = [d.replace('/','\\') for d in dirs]
            files = [f.replace('/','\\') for f in files]
        result.insert(0, (cur_root, dirs, files))
        # (root, dirs, files)
        return result

    def _os_exists(path:str) -> bool:
        if FSMock._called_from_outside(path):
            return FSMock.system_os_exists(path)
        if path in FSMock.os_path_exists_values:
            return FSMock.os_path_exists_values[path]
        relpath = FSMock._remove_first_level(path)
        if path.startswith('left') or (FSMock.is_os_fs_windows_style and path.lower().startswith('left')):
            return relpath=='' or FSMock.left_filetree.exists(relpath, case_sensitive=not FSMock.is_os_fs_windows_style)
        if path.startswith('right') or (FSMock.is_os_fs_windows_style and path.lower().startswith('right')):
            return relpath=='' or FSMock.right_filetree.exists(relpath, case_sensitive=not FSMock.is_os_fs_windows_style)
        return FSMock.system_os_exists(path)
    
    def _os_islink(path:str) -> bool:
        if FSMock._called_from_outside(path):
            return FSMock.system_os_islink(path)
        return False
    
    def _os_getsize(path:str) -> int:
        if FSMock._called_from_outside(path):
            return FSMock.system_os_getsize(path)
        path = path.replace('\\', '/')
        if path in FSMock.file_properties:
            return FSMock.file_properties[path].st_size
        return 0
    
    def _os_remove(path):
        if FSMock._called_from_outside(path):
            return FSMock.system_os_remove(path)
        FSMock.removed.add(path)

    def _shutil_rmtree(path, ignore_errors=False):
        if FSMock._called_from_outside(path):
            FSMock.system_shutil_rmtree(path)
        if path in FSMock.os_rmdir_failure_paths and not ignore_errors:
            FSMock._raise_permission_error('(FSMock) shutil.rmtreee simulated error', path)
        FSMock.removed_dirs.add(path)
    
    def _os_mkdir(path, mode=0o777, *, dir_fd=None):
        if FSMock._called_from_outside(path):
            FSMock.system_os_mkdir(path, mode=mode, dir_fd=dir_fd)
        FSMock.created_dirs.add(path)
    
    def _os_makedirs(name, mode=0o777, exist_ok=False):
        if FSMock._called_from_outside(name):
            FSMock.system_os_makedirs(name,mode=mode,exist_ok=exist_ok)
    
    def _shutil_copy2(src, dest):
        if FSMock._called_from_outside(src):
            return FSMock.system_shutil_copy2(src, dest)
        if src in FSMock.os_copy_failure_paths:
            FSMock._raise_permission_error('(FSMock) shutil.copy2 simulated error', src)
        if dest in FSMock.os_copy_failure_paths:
            FSMock._raise_permission_error('(FSMock) shutil.copy2 simulated error', dest)
        FSMock.copied.add((src,dest))

    def _shutil_move(src, dest):
        return
    
    def _os_stat(path, *, dir_fd=None, follow_symlinks=True) -> any:
        if FSMock._called_from_outside(path):
            return FSMock.system_os_stat(**locals())
        res = type('TMP', (object,), {'st_size': 0})()
        return res
    
    def _os_chmod(path, mode: int, *, dir_fd: int | None = None, follow_symlinks: bool = True):
        if FSMock._called_from_outside(path):
            FSMock.system_os_chmod(path,dir_fd=dir_fd,follow_symlinks=follow_symlinks)
        
    def _os_scandir_mock(path:str):
        if FSMock._called_from_outside(path):
            return FSMock.system_os_scandir(path)
        path = path.replace('\\', '/')
        if path.startswith('left'):
            filetree = FSMock.left_filetree
            relpath = os.path.relpath(path, 'left')
        elif path.startswith('right'):
            filetree = FSMock.right_filetree
            relpath = os.path.relpath(path, 'right')
        else:
            return FSMock.system_os_scandir(path)
        if relpath=='.':
            relpath = ''
        if not filetree.exists(relpath, case_sensitive=not FSMock.is_os_fs_windows_style):
            raise FileNotFoundError(f"(FSMock) os.scandir simulated error: the given path '{path}' does not exist")
        if not filetree.exists(relpath, create=False, case_sensitive=not FSMock.is_os_fs_windows_style):
            raise NotADirectoryError(f"(FSMock) os.scandir simulated error: the given path '{path}' is not a directory")
        fileset = filetree.to_fileset(relpath)
        entries:list = []
        for file in fileset:
            entries.append(file)
        return FSMock._ScandirEntriesMock_(entries)
        
    def _raise_permission_error(text:str, path:str):
        err = PermissionError(text)
        err.strerror = text
        err.filename = path
        raise err

    class _ScandirEntriesMock_:
        def __init__(self, entries:list[str]):
            self.entries:list = entries
            self.i:int = 0
        
        def __iter__(self):
            self.i = 0
            return iter(self.entries[0])

        def __next__(self):
            self.i += 1
            return iter(self.entries[self.i])
        
        def close(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass