from __future__ import annotations # needed for python3 older than 3.14
__author__      = "Jérôme Cuq"
__copyright__   = "Copyright 2026, Jérôme Cuq"
__license__     = "BSD-3-Clause"

import os
import re
from tests.fstree import FSTree
import shutil 
from dirsyncer import DirSyncer
from tests.fstree import FSTree 


class FSMock:
    """This class is used to mock some system apis from "os" module"""
        
    # static variables to handle os.walk mocking
    system_os_walk  = os.walk
    system_os_isdir = os.path.isdir
    system_os_isfile = os.path.isfile
    system_os_join = os.path.join
    system_os_relpath = os.path.relpath
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
        os.path.join = FSMock._os_join_mock_
        os.path.relpath = FSMock._os_relpath_mock_
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
        FSMock.os_path_exists_values.clear()
        FSMock.os_rmdir_failure_paths.clear()
        FSMock.os_copy_failure_paths.clear()

    def uninstall_os_mock():
        os.walk = FSMock.system_os_walk
        os.path.isdir = FSMock.system_os_isdir
        os.path.isfile = FSMock.system_os_isfile
        os.path.join = FSMock.system_os_join
        os.path.relpath = FSMock.system_os_relpath
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

    def clean_sync_data():
        FSMock.copied = set()
        FSMock.removed = set()
        FSMock.removed_dirs = set()
        FSMock.created_dirs = set()
        FSMock.os_path_exists_values.clear()
        FSMock.os_rmdir_failure_paths.clear()
        FSMock.os_copy_failure_paths.clear()
    
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
    
    def _os_join_mock_(path1, *paths) -> str:
         # If path is not a string, it means that it is called from pytest, we call the real os.path.isfile on it
        if not isinstance(path1, str):
            return FSMock.system_os_join(path1, *paths)
        path1 = path1.replace('\\', os.path.sep).replace('/', os.path.sep)
        paths2:tuple = (p.replace('\\', os.path.sep).replace('/', os.path.sep) for p in paths)
        if FSMock.is_os_fs_windows_style:
            return FSMock.system_os_join(path1, *paths2).replace('/', '\\')
        else:
            return FSMock.system_os_join(path1, *paths2).replace('\\', '/')
        
    def _os_relpath_mock_(path1:str, path2:str) -> str:
         # If path is not a string, it means that it is called from pytest, we call the real os.path.isfile on it
        if not isinstance(path1, str):
            return FSMock.system_os_relpath(path1, path2)
        if FSMock.is_os_fs_windows_style:
            sep = '\\'
        else:
            sep = '/'
        p1 = path1.split(sep)
        p2 = path2.split(sep)
        p = sep.join(p1[len(p2):])
        return p
        
    def _os_dirname_mock_(path:str) -> str:
        # If path is not a string, it means that it is called from pytest, we call the real os.path.isfile on it
        if not isinstance(path, str):
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
    
    def _os_walk_mock_(path:str, filetree:list=None) -> list[tuple]:
        if not isinstance(path, str):
            return FSMock.system_os_walk(path)
        #log(f"os_walk_mock called with path: {path}")
        if filetree is None:
            if path.startswith('left'):
                filetree = FSMock.left_filetree.rootnode()
            elif path.startswith('right'):
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
        if FSMock.is_os_fs_windows_style:
            cur_root = cur_root.replace('/','\\')
            dirs = [d.replace('/','\\') for d in dirs]
            files = [f.replace('/','\\') for f in files]
        result.insert(0, (cur_root, dirs, files))
        # (root, dirs, files)
        return result

    def _os_exists(path:str) -> bool:
        if not isinstance(path, str):
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
        if not isinstance(path, str):
            return FSMock.system_os_islink(path)
        return False
    
    def _os_getsize(path:str) -> int:
        if not isinstance(path, str):
            return FSMock.system_os_getsize(path)
        path = path.replace('\\', '/')
        if path in FSMock.file_properties:
            return FSMock.file_properties[path].st_size
        return 0
    
    def _os_remove(path):
        FSMock.removed.add(path)

    def _shutil_rmtree(path, ignore_errors=False):
        if path in FSMock.os_rmdir_failure_paths and not ignore_errors:
            FSMock._raise_permission_error('(FSMock) shutil.rmtreee simulated error', path)
        FSMock.removed_dirs.add(path)
    
    def _os_mkdir(path, mode: int = 0o777):
        if not isinstance(path, str):
            FSMock.system_os_mkdir(path,mode)
        FSMock.created_dirs.add(path)
    
    def _os_makedirs(path, exist_ok: bool = False):
        return
    
    def _shutil_copy2(src, dest):
        if src in FSMock.os_copy_failure_paths:
            FSMock._raise_permission_error('(FSMock) shutil.copy2 simulated error', src)
        if dest in FSMock.os_copy_failure_paths:
            FSMock._raise_permission_error('(FSMock) shutil.copy2 simulated error', dest)
        FSMock.copied.add((src,dest))

    def _shutil_move(src, dest):
        return
    
    def _os_stat(path, *, dir_fd: int | None = None, follow_symlinks: bool = True) -> any:
        if not isinstance(path,str):
            return FSMock.system_os_stat(path,dir_fd=dir_fd,follow_symlinks=follow_symlinks)
        res = type('TMP', (object,), {'st_size': 0})()
        return res
    
    def _os_chmod(path, mode: int, *, dir_fd: int | None = None, follow_symlinks: bool = True):
        if not isinstance(path,str):
            return FSMock.system_os_chmod(path,dir_fd=dir_fd,follow_symlinks=follow_symlinks)
        
    def _os_scandir_mock(path:str):
        if not isinstance(path, str):
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
            entries.append(FSMock._ScandirEntryMock_(file))
        return entries
        
    def _raise_permission_error(text:str, path:str):
        err = PermissionError(text)
        err.strerror = text
        err.filename = path
        raise err