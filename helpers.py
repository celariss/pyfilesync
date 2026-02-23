__author__      = "Jérôme Cuq"
__copyright__   = "Copyright 2026, Jérôme Cuq"
__license__     = "BSD-3-Clause"

import math
import os
import stat
import shutil
import sys
import filecmp
import re


def log(message: str):
    print(message)

def log_error(message: str, exitScript: bool = False):
    """print an error and stop current script

    :param message: message to print out
    :type message: str
    :param exitScript: indicates whether the function must call exit, defaults to True
    :type exitScript: bool, optional
    """
    print("ERROR: "+message, file=sys.stderr)
    if exitScript:
        exit(1)

def replace_env_variables(text: str) -> str:
    """replace env variables in a text (ex: %TEMP% or $TEMP) by their value

    :param text: text to replace env variables in
    :type text: str
    :return: text with env variables replaced
    :rtype: str
    """
    return os.path.expandvars(text)

def is_fs_case_insensitive(path:str) -> bool:
    return os.path.exists(path.upper()) and os.path.exists(path.lower())

def compile_regex(pattern:str, example_path:str) -> re.Pattern:
    """compile a regex pattern and return the compiled pattern, or None if the pattern is invalid

    :param pattern: regex pattern to compile
    :type pattern: str
    :return: compiled regex pattern, or None if the pattern is invalid
    :rtype: re.Pattern or None
    """
    if is_fs_case_insensitive(example_path):
        return re.compile(pattern, re.IGNORECASE)
    return re.compile(pattern)

def cmp_modif_times(left_ts:os.stat_result, right_ts:os.stat_result) -> bool:
        """ Compare modification times of two files.
        return True if left_ts is more recent than right_ts """
        return int(math.trunc(left_ts.st_mtime*100)/100 - math.trunc(right_ts.st_mtime*100)/100) != 0

def rm_file_or_dir(path:str):
    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)

def copy_dir_or_file(src:str, dest:str):
    if os.path.isdir(src):
        shutil.copytree(src, dest)
    else:
        destdir = os.path.dirname(dest)
        if not os.path.exists(destdir):
            os.makedirs(destdir)
        if os.path.islink(src):
            os.symlink(os.readlink(src), dest)
        else:
            shutil.copy2(src, dest)


class CmpData(object):
    """compare_dirs() result data class"""
    def __init__(self, left_only, right_only, equal, different, errors):
        self.left_only:set = left_only
        self.right_only:set = right_only
        self.equal:set = equal
        self.different:set = different
        self.errors:set = errors

class SyncData(object):
    """sync_dirs() result data class"""
    def __init__(self, errors=set()):
        self.errors:set = errors
        self.nb_copied:int = 0
        self.nb_updated:int = 0
        self.nb_deleted:int = 0
        self.size_copied:int = 0
        self.size_updated:int = 0

def compare_dirs(leftdir:str, rightdir:str, include:list=[], exclude:list=[], compare_file_content:bool=False) -> CmpData:
    """compare two directories and return a CmpData object containing the results"""

    left_files = set()
    right_files = set()
    errors = set()
    
    exclude_re = []
    for pattern in exclude:
        try:
            exclude_re.append(compile_regex(pattern, leftdir))
        except re.error:
            errors.add((pattern, "Invalid exclude regex pattern"))
            return CmpData(set(), set(), set(), set(), errors)

    include_re = []
    for pattern in include:
        try:
            include_re.append(compile_regex(pattern, leftdir))
        except re.error:
            errors.add((pattern, "Invalid include regex pattern"))
            return CmpData(set(), set(), set(), set(), errors)
        
    for cwd, dirs, files in os.walk(leftdir):
        for f in dirs + files:
            path = os.path.relpath(os.path.join(cwd, f), leftdir)
            re_path = path.replace('\\', '/')
            
            add_path = False
            for exre in exclude_re:
                if exre.match(re_path):
                    # path is in excludes, do not add it
                    break
            else:
                # path was not in excludes, test if it is in includes
                if len(include)==0:
                    # no include pattern, add path
                    add_path = True
                else:
                    for incre in include_re:
                        if incre.match(re_path):
                            add_path = True
                            break

            if add_path:
                left_files.add(path)
                anc_dirs = re_path.split('/')
                anc_dirs_path = ''
                for ad in anc_dirs:
                    anc_dirs_path = os.path.join(anc_dirs_path, ad)
                    left_files.add(anc_dirs_path)

    for cwd, dirs, files in os.walk(rightdir):
        for f in dirs + files:
            path = os.path.relpath(os.path.join(cwd, f), rightdir)
            re_path = path.replace('\\', '/')
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
            try:
                st1 = os.stat(file1)
            except os.error:
                errors.add((file1, "Could not get file stats"))
                err:True
                continue
            try:
                st2 = os.stat(file2)
            except os.error:
                errors.add((file2, "Could not get file stats"))
                err:True
                continue

            if not err:
                # comparison criteria to detect different files are files size and modification time (or files content if asked)
                different = st1.st_size != st2.st_size
                if not different:
                    different = (not filecmp.cmp(file1, file2, False)) if compare_file_content else cmp_modif_times(st1, st2)
                if different:
                    different_files.add(f)
                else:
                    equal_files.add(f)


    return CmpData(left_files.difference(common_files), right_files.difference(common_files), equal_files, different_files, errors)


def sync_dirs(leftdir:str, rightdir:str, cmp_data: CmpData, verbose:bool=False) -> SyncData:
    """synchronize two directories according to the given CmpData results, and return a set of errors encountered during synchronization"""

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
                        rm_file_or_dir(rightpath)
                    except PermissionError as e:
                        if os.path.exists(rightpath):
                            os.chmod(rightpath, stat.S_IWRITE)
                        rm_file_or_dir(rightpath)
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
                    if not os.path.isdir(leftpath):
                        if verbose:
                            log('   | Updating %s from %s' % (rightpath, leftpath))
                        copy_dir_or_file(leftpath, rightpath)
                except PermissionError as e:
                    if os.path.exists(rightpath):
                        os.chmod(rightpath, stat.S_IWRITE)
                    copy_dir_or_file(leftpath, rightpath)
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
                    if not os.path.isdir(leftpath):
                        if verbose:
                            log('   | Copying %s to %s' % (leftpath, rightpath))
                        copy_dir_or_file(leftpath, rightpath)
                except PermissionError as e:
                    if os.path.exists(rightpath):
                        os.chmod(rightpath, stat.S_IWRITE)
                    copy_dir_or_file(leftpath, rightpath)
            except Exception as e:
                log_error('  '+str(e))
                syncdata.errors.add((leftfile, str(e)))
                continue
            else:
                syncdata.nb_copied += 1
                syncdata.size_copied += os.stat(leftpath).st_size

    return syncdata