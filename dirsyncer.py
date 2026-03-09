from __future__ import annotations # needed for python3 older than 3.14

__author__      = "Jérôme Cuq"
__copyright__   = "Copyright 2026, Jérôme Cuq"
__license__     = "BSD-3-Clause"

import math, os, stat, shutil, filecmp
import re
from helpers import *


class CmpData(object):
    """DirSync.compare_dirs() result data class"""
    def __init__(self, left_only=set(), right_only=set(), equal=set(), different=set(), errors=set()):
        self.left_only:set = left_only
        self.right_only:set = right_only
        self.equal:set = equal
        self.different:set = different
        self.errors:set = errors

    def update(self, data:CmpData):
        self.left_only.update(data.left_only)
        self.right_only.update(data.right_only)
        self.equal.update(data.equal)
        self.different.update(data.different)
        self.errors.update(data.errors)

class SyncData(object):
    """DirSync.sync_dirs() result data class"""
    def __init__(self, errors=set()):
        self.errors:set = errors
        self.nb_copied:int = 0
        self.nb_updated:int = 0
        self.nb_deleted:int = 0
        self.size_copied:int = 0
        self.size_updated:int = 0
    
    def update(self, data:SyncData):
        self.nb_copied += data.nb_copied
        self.nb_updated += data.nb_updated
        self.nb_deleted += data.nb_deleted
        self.size_copied += data.size_copied
        self.size_updated += data.size_updated
        self.errors.update(data.errors)


class DirSyncer:
    def compare_dirs(leftdir:str, rightdir:str, include:list=[], exclude:list=[], compare_file_content:bool=False, ignore_right_only:bool=False) -> CmpData:
        """compare two directories and return a CmpData object containing the results
        
        :param leftdir: path to the left directory
        :param rightdir: path to the right directory
        :param include: include filters as a list of regex
        :param exclude: exclude filters as a list of regex"""

        left_files = set()
        right_files = set()
        errors = set()
        
        exclude_re = []
        for pattern in exclude:
            try:
                exclude_re.append(DirSyncer.__compile_regex__(pattern, leftdir))
            except re.error:
                errors.add((pattern, "Invalid exclude regex pattern"))
                return CmpData(set(), set(), set(), set(), errors)

        include_re = []
        for pattern in include:
            try:
                include_re.append(DirSyncer.__compile_regex__(pattern, leftdir))
            except re.error:
                errors.add((pattern, "Invalid include regex pattern"))
                return CmpData(set(), set(), set(), set(), errors)
            
        explicitly_excluded_dirs:set = set()
        explicitly_included_dirs:set = set()
        for root, dirs, files in os.walk(leftdir):
            must_clean_path:bool = False
            for f in dirs + files:
                full_path = os.path.join(root, f)
                if root in explicitly_excluded_dirs:
                    explicitly_excluded_dirs.add(full_path)
                else:
                    path = os.path.relpath(full_path, leftdir)
                    isdir = os.path.isdir(full_path)
                    match:DirSyncer.EfileMatch = DirSyncer.__file_match_all_regex__(path, f, isdir, exclude_re, include_re)
                    if isdir and (match == DirSyncer.EfileMatch.INCLUDED or (root in explicitly_included_dirs)):
                        explicitly_included_dirs.add(full_path)
                    if match == DirSyncer.EfileMatch.INCLUDED or (match == DirSyncer.EfileMatch.NO_MATCH and (root in explicitly_included_dirs)):
                        left_files.add(path)
                        must_clean_path:bool = True
                    elif isdir and match == DirSyncer.EfileMatch.EXCLUDED:
                        explicitly_excluded_dirs.add(full_path)                

            if must_clean_path:
                # we must remove parent dirs from left_files since they are already included in current path
                path_to_remove = os.path.relpath(root, leftdir)
                while path_to_remove:
                    if path_to_remove in left_files:
                        left_files.remove(path_to_remove)
                    path_to_remove = os.path.dirname(path_to_remove)

        for root, dirs, files in os.walk(rightdir):
            parent = os.path.relpath(root, rightdir)
            if  (dirs or files) and (parent in right_files):
                right_files.remove(parent)
            for f in dirs + files:
                path = os.path.relpath(os.path.join(root, f), rightdir)
                right_files.add(path)

        
        # Finding equal and different files
        common_files = left_files.intersection(right_files)
        different_files:set = set()
        equal_files:set = set()
        for f in common_files:
            file1 = os.path.join(leftdir, f)
            file2 = os.path.join(rightdir, f)
            err = False
            if os.path.isfile(file1) and os.path.isfile(file2):
                fprop1 = DirSyncer.__get_file_properties__(file1, errors)
                fprop2 = DirSyncer.__get_file_properties__(file2, errors)
                if fprop1 and fprop2:
                    # comparison criteria to detect different files are files size and modification time (or files content if asked)
                    different = fprop1.st_size != fprop2.st_size
                    if not different:
                        if compare_file_content:
                            different = (not filecmp.cmp(file1, file2, False))
                        else:
                            different = DirSyncer.__cmp_modif_times__(fprop1, fprop2)
                    if different:
                        different_files.add(f)
                    else:
                        equal_files.add(f)
            else:
                # it's a directory => equal
                equal_files.add(f)

        right_only:set = set()
        if not ignore_right_only:
            right_only = right_files.difference(common_files)
        return CmpData(left_files.difference(common_files), right_only, equal_files, different_files, errors)


    def sync_dirs(leftdir:str, rightdir:str, cmp_data: CmpData, verbose:bool=False) -> SyncData:
        """synchronize two directories according to the given CmpData results, and return sync results as SyncData"""

        syncdata:SyncData = SyncData()

        # First remove files/directories only in right directory,
        # to free space before copying files from left to right directory,
        # in case there is not enough free space to copy left files without deleting right files first
        if cmp_data.right_only:
            if verbose:
                log('  Only in %s' % rightdir)
            for rightfile in cmp_data.right_only:
                rightpath = os.path.join(rightdir, rightfile)
                if verbose:
                    log('   | Deleting %s' % rightpath)
                try:
                    if os.path.exists(rightpath):
                        try:
                            DirSyncer.__rm_file_or_dir__(rightpath)
                        except PermissionError as e:
                            if os.path.exists(rightpath):
                                os.chmod(rightpath, stat.S_IWRITE)
                            DirSyncer.__rm_file_or_dir__(rightpath)
                except Exception as e:
                    log_error('  '+str(e))
                    syncdata.errors.add((rightpath, str(e)))
                    continue
                else:
                    syncdata.nb_deleted += 1

        # Then update files that are different between left and right directories
        if cmp_data.different:
            if verbose:
                log('  Different in %s and %s' % (leftdir, rightdir))
            for f in cmp_data.different:
                leftpath = os.path.join(leftdir, f)
                rightpath = os.path.join(rightdir, f)
                try:
                    try:
                        if verbose:
                            log('   | Updating %s from %s' % (rightpath, leftpath))
                        DirSyncer.__copy_dir_or_file__(leftpath, rightpath)
                    except PermissionError as e:
                        if os.path.exists(rightpath):
                            os.chmod(rightpath, stat.S_IWRITE)
                        DirSyncer.__copy_dir_or_file__(leftpath, rightpath)
                except Exception as e:
                    log_error('  '+str(e))
                    syncdata.errors.add((f, str(e)))
                    continue
                else:
                    syncdata.nb_updated += 1
                    syncdata.size_updated += os.stat(leftpath).st_size

        # At last copy files/directories only in left directory to right directory
        if cmp_data.left_only:
            if verbose:
                log('  Only in %s' % leftdir)
            for leftfile in cmp_data.left_only:
                leftpath = os.path.join(leftdir, leftfile)
                rightpath = os.path.join(rightdir, leftfile)
                try:
                    try:
                        if verbose:
                            log('   | Copying %s to %s' % (leftpath, rightpath))
                        DirSyncer.__copy_dir_or_file__(leftpath, rightpath)
                    except PermissionError as e:
                        if os.path.exists(rightpath):
                            os.chmod(rightpath, stat.S_IWRITE)
                        DirSyncer.__copy_dir_or_file__(leftpath, rightpath)
                except Exception as e:
                    log_error('  '+str(e))
                    syncdata.errors.add((leftfile, str(e)))
                    continue
                else:
                    syncdata.nb_copied += 1
                    syncdata.size_copied += os.stat(leftpath).st_size

        return syncdata


    def __compile_regex__(pattern:str, example_path:str) -> re.Pattern:
        """compile a regex pattern and return the compiled pattern, or None if the pattern is invalid
        The compiled regex has the same case sensibility than the target filesystem 

        :param pattern: regex pattern to compile
        :param example_path: path to a file in the target filesystem
        :return: compiled regex pattern, or None if the pattern is invalid
        """
        if DirSyncer.__is_fs_case_insensitive__(example_path):
            return re.compile(pattern, re.IGNORECASE)
        return re.compile(pattern)

    class FileProperties(object):
     def __init__(self, st_size:int, st_mtime):
         self.st_size = st_size
         self.st_mtime = st_mtime

    def __get_file_properties__(path:str, errors:list = []) -> FileProperties:
        try:
            st:os.stat_result = os.stat(path)
            return DirSyncer.FileProperties(st.st_size, st.st_mtime)
        except os.error:
            errors.add((path, "Could not get file stats"))
        return None

    
    def __file_match_regex__(path:str, filename:str, regex:re.Pattern, isdir:bool) -> bool:
        """return True if the given path match the given regex, taking into account whether it is a directory or not
        (if isdir is True, the regex must have a trailing slash)

        :param path: path to match (with filename)
        :param filename: filename to match = os.path.basename(path)
        :param regex: compiled regex pattern to match against the path / filename
        :param isdir: indicates whether the path is a directory or not
        :return: True if the path match the regex, False otherwise
        """
        if isdir:
            if regex.match('/'+path+'/'):
                return True
        elif regex.match('/'+path) or regex.match(filename):
            return True
        return False

    class EfileMatch(Enum):
        NO_MATCH = 0
        EXCLUDED = 1
        INCLUDED = 2

    def __file_match_all_regex__(path:str, filename:str, isdir:bool, exclude_re:list, include_re:list) -> EfileMatch:
        result:bool = False
        path = path.replace('\\', '/')
        
        for exre in exclude_re:
            if DirSyncer.__file_match_regex__(path, filename, exre, isdir):
                return DirSyncer.EfileMatch.EXCLUDED
        # path was not in excludes, now we test if it is in includes
        else:
            if len(include_re)==0:
                return DirSyncer.EfileMatch.INCLUDED
            else:
                for incre in include_re:
                    if DirSyncer.__file_match_regex__(path, filename, incre, isdir):
                        return DirSyncer.EfileMatch.INCLUDED
        return DirSyncer.EfileMatch.NO_MATCH
    
    def __is_fs_case_insensitive__(path:str) -> bool:
        """detect whether target filesystem is case insensitive"""
        return os.path.exists(path.upper()) and os.path.exists(path.lower())

    def __cmp_modif_times__(left_ts:FileProperties, right_ts:FileProperties) -> bool:
            """Compare modification times of two files.
            return True if left_ts is more recent than right_ts"""
            return int(math.trunc(left_ts.st_mtime*100)/100 - math.trunc(right_ts.st_mtime*100)/100) != 0

    def __rm_file_or_dir__(path:str):
        if os.path.isfile(path) or os.path.islink(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)

    def __copy_dir_or_file__(src:str, dest:str):
        if os.path.isdir(src):
            #shutil.copytree(src, dest)
            if not os.path.exists(dest):
                os.mkdir(dest)
        else:
            destdir = os.path.dirname(dest)
            if not os.path.exists(destdir):
                os.makedirs(destdir)
            if os.path.islink(src):
                os.symlink(os.readlink(src), dest)
            else:
                shutil.copy2(src, dest)