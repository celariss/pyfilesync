from __future__ import annotations

from tests.fstree import FSTree # needed for python3 older than 3.14

__author__      = "Jérôme Cuq"
__copyright__   = "Copyright 2026, Jérôme Cuq"
__license__     = "BSD-3-Clause"

import os
import re

import shutil 
from dirsyncer import DirSyncer


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
    system_os_remove = os.remove
    system_shutil_rmtree = shutil.rmtree
    system_os_mkdir = os.mkdir
    system_os_makedirs = os.makedirs
    system_shutil_copy2 = shutil.copy2
    system_os_stat = os.stat
    actual_get_file_properties = DirSyncer.__get_file_properties__

    left_filetree:FSTree = FSTree()
    right_filetree:FSTree = FSTree()
    file_properties:dict[str,DirSyncer.FileProperties] = {}
    is_os_walk_mock_windows_style:bool = False
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
        os.remove = FSMock._os_remove
        shutil.rmtree = FSMock._shutil_rmtree
        os.mkdir = FSMock._os_mkdir
        os.makedirs = FSMock._os_makedirs
        shutil.copy2 = FSMock._shutil_copy2
        os.stat = FSMock._os_stat
        DirSyncer.__get_file_properties__ = FSMock._get_file_properties_mock_

    def uninstall_os_mock():
        os.walk = FSMock.system_os_walk
        os.path.isdir = FSMock.system_os_isdir
        os.path.isfile = FSMock.system_os_isfile
        os.path.join = FSMock.system_os_join
        os.path.relpath = FSMock.system_os_relpath
        os.path.dirname = FSMock.system_os_dirname
        os.path.exists = FSMock.system_os_exists
        os.path.islink = FSMock.system_os_islink
        os.remove = FSMock.system_os_remove
        shutil.rmtree = FSMock.system_shutil_rmtree
        os.mkdir = FSMock.system_os_mkdir
        os.makedirs = FSMock.system_os_makedirs
        shutil.copy2 = FSMock.system_shutil_copy2
        os.stat = FSMock.system_os_stat
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
        if FSMock.is_os_walk_mock_windows_style:
            return FSMock.system_os_join(path1, *paths2).replace('/', '\\')
        else:
            return FSMock.system_os_join(path1, *paths2).replace('\\', '/')
        
    def _os_relpath_mock_(path1:str, path2:str) -> str:
         # If path is not a string, it means that it is called from pytest, we call the real os.path.isfile on it
        if not isinstance(path1, str):
            return FSMock.system_os_relpath(path1, path2)
        if FSMock.is_os_walk_mock_windows_style:
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
        if FSMock.is_os_walk_mock_windows_style:
            return FSMock.system_os_dirname(path).replace('/', '\\')
        else:
            return FSMock.system_os_dirname(path).replace('\\', '/')
        
    def _get_file_properties_mock_(path:str, errors:list) -> DirSyncer.FileProperties:
        path = path.replace('\\', '/')
        if path in FSMock.file_properties:
            return FSMock.file_properties[path]
        return DirSyncer.FileProperties(0,0)
    
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
        if FSMock.is_os_walk_mock_windows_style:
            cur_root = cur_root.replace('/','\\')
            dirs = [d.replace('/','\\') for d in dirs]
            files = [f.replace('/','\\') for f in files]
        result.insert(0, (cur_root, dirs, files))
        # (root, dirs, files)
        return result

    def _os_exists(path:str) -> bool:
        if not isinstance(path, str):
            return FSMock.system_os_exists(path)
        return True
    
    def _os_islink(path:str) -> bool:
        if not isinstance(path, str):
            return FSMock.system_os_islink(path)
        return False
    
    def _os_remove(path):
        FSMock.removed.add(path)
        return

    def _shutil_rmtree(path):
        FSMock.removed_dirs.add(path)
        return
    
    def _os_mkdir(path, mode: int = 0o777):
        if not isinstance(path, str):
            FSMock.system_os_mkdir(path,mode)
        FSMock.created_dirs.add(path)
        return
    
    def _os_makedirs(path):
        return
    
    def _shutil_copy2(src, dest):
        FSMock.copied.add((src,dest))
        return
    
    def _os_stat(path, *, dir_fd: int | None = None, follow_symlinks: bool = True) -> any:
        if not isinstance(path,str):
            return FSMock.system_os_stat(path,dir_fd=dir_fd,follow_symlinks=follow_symlinks)
        res = type('TMP', (object,), {'st_size': 0})()
        return res