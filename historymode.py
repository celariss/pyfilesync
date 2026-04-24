__author__      = "Jérôme Cuq"
__license__     = "BSD-3-Clause"

import os
import shutil

from helpers import *

HISTORY_DIR = '.autosave'
HISTORY_FORMAT = '_#{:0>2d}#'
HISTORY_FILE_PATTERN = '^(..*)_#([0-9]{2})#(.*)?$'

class HistoryMode:
    def save_file(basedir:str, file:str, maxnbfiles:int, maxsize:int, verbose:bool) -> str | None:
        """save a file in history (by moving the file), and remove old files in history if needed to keep only maxnbfiles and maxsize of files in history.
        param basedir: base directory of the synchronization data (not the history basedir)
        param file: file path, in the synchronization directory, to move to history (actual file, not in history directory)
        param maxnbfiles: maximum number of files to keep in history, if 0 or less, history mode is disabled, 
                          no file will be saved in history and all files in history will be removed
        param maxsize: maximum total size of files to keep in history, if 0, there is no limit on the total size of files to keep in history"""
        if maxnbfiles > 0:
            historyfilesizes:list
            historyfilepaths:list
            historyfilepaths, historyfilesizes = HistoryMode.get_file_history(basedir, file)
            filesize = os.path.getsize(file)
            nbtokeep = HistoryMode.get_nb_history_files_to_keep(filesize, historyfilesizes, maxnbfiles, maxsize)

            if nbtokeep == -1:
                # The file to save is too big to be kept in history, so we just remove all files in history
                for path in historyfilepaths:
                    os.remove(path)
                # remove directories if they are empty
                path = os.path.dirname(HistoryMode.get_history_filepath(basedir, file, 1))
                remove_empty_part_of_path(path)
                return None

            try:
                destpath = HistoryMode.get_history_filepath(basedir, file, 1)
                if verbose:
                    log('    | Saving file to history : .%s%s' % (os.path.sep, os.path.relpath(file, basedir)))
                
                # Remove files in history that should not be kept
                for i in range(nbtokeep, len(historyfilesizes)):
                    os.remove(historyfilepaths[i])

                # Move files in history to their new name, to make place for new file to save in history
                for i in range(nbtokeep, 0, -1):
                    os.rename(historyfilepaths[i-1], HistoryMode.get_history_filepath(basedir, file, i+1))

                # move file to save in history
                os.makedirs(os.path.dirname(destpath), exist_ok=True)
                shutil.move(file, destpath)
            except OSError as exc:
                log_error('Error while saving file in history : '+str(exc))
                return 'Error while saving file in history : '+str(exc)
            
            return None


    def clean_history(basedir:str, maxnbfiles:int, maxsize:int, removed_only:bool = False) -> tuple[list[str], list[str], list[str]]:
        """remove unwanted saved versions of files in history, to keep only maxnbfiles and maxsize of files in history.
        A unwanted file can be either a file that should not be kept in history because of maxnbfiles and maxsize limits, 
        or a file that should be kept in history but whose actual file does not exist anymore .
        (for example because it has been removed outside of the synchronization process).
        param basedir: base directory of the synchronization data (not the history basedir)
        param maxnbfiles: maximum number of files to keep in history, if 0 or less, history mode is disabled, 
                          no file will be saved in history and all files in history will be removed
        param maxsize: maximum total size of files to keep in history, if 0, there is no limit on the total size of files to keep in history
        param removed_only: only remove history of actual files that do not exist anymore
        return: a tuple containing 3 lists : (list of removed file paths, list of removed file sizes, list of errors that occured while removing files)"""
        errors:list = []
        removedfiles:list = []
        sizes:list = []
        historydir = os.path.join(basedir, HISTORY_DIR)
        if os.path.exists(historydir):
            for root, dirs, files in os.walk(historydir, topdown=False):
                history_files_info = HistoryMode.get_files_info_in_history_dir(root)
                for filepath, historyfilepaths, historyfilesizes in history_files_info:
                    if removed_only:
                        nbtokeep = len(historyfilesizes)
                    else:
                        nbtokeep = HistoryMode.get_nb_history_files_to_keep(-1, historyfilesizes, maxnbfiles, maxsize)
                    if not os.path.exists(filepath):
                        nbtokeep = 0
                    # Remove files in history that should not be kept
                    for i in range(nbtokeep, len(historyfilesizes)):
                        try:
                            os.remove(historyfilepaths[i])
                            remove_empty_part_of_path(os.path.dirname(historyfilepaths[i]))
                            removedfiles.append(historyfilepaths[i])
                            sizes.append(historyfilesizes[i])
                        except OSError:
                            errors.append('Error while removing file in history : '+historyfilepaths[i])
        return removedfiles, sizes, errors


    def get_files_info_in_history_dir(history_dir:str) -> list[tuple[str, list[str], list[int]]]:
        """ Returns a list of tuples containing file path, history file paths and history file sizes for each file that has at least one version in history in the given history directory
        param history_dir: path to the history directory to get files info from, this is the directory that contains history files, not the base directory of the synchronization data"""
        files_info:list[tuple[str, list[str], list[int]]] = []
        basedir = HistoryMode.remove_historydir_in_path(history_dir)
        if os.path.exists(history_dir):
            for root, dirs, files in os.walk(history_dir):
                filespath:set = set()
                root = HistoryMode.remove_historydir_in_path(root)
                for name in files:
                    match = re.match(HISTORY_FILE_PATTERN, name)
                    if match:
                        filename = match.group(1)+match.group(3)
                        filepath = os.path.join(root, filename)
                        filespath.add(filepath)
                for filepath in filespath:
                    historyfilepaths, historyfilesizes = HistoryMode.get_file_history(basedir, filepath)
                    files_info.append(tuple((filepath, historyfilepaths, historyfilesizes)))
        return files_info
    

    def get_nb_history_files_to_keep(filetosavesize:int, historyfilesizes:list[int], maxnbhistoryfiles:int, maxhistorysize:int) -> int:
        """ Returns the number of history files to keep when adding a new file in history, or -1 if the new file to save is too big to be kept in history
        param filetosavesize: size of the file to save in history (or -1 if no new file to save, for example when just cleaning history)"""
        if filetosavesize != -1 and maxhistorysize!=0 and (filetosavesize > maxhistorysize or maxnbhistoryfiles <= 0):
            return -1
        nbhistoryfiles = len(historyfilesizes)
        i = 0
        historyfilesize = 0
        while True:
            if filetosavesize == -1:
                if i == nbhistoryfiles or i >= maxnbhistoryfiles:
                    return i
            else:
                if i == nbhistoryfiles or i+1 >= maxnbhistoryfiles:
                    return i
            historyfilesize += historyfilesizes[i]
            if  maxhistorysize!=0 and (filetosavesize + historyfilesize > maxhistorysize):
                return i
            i += 1


    def get_file_history(basedir:str, file:str) -> tuple[list[str], list[int]]:
        """ Returns the list of history file paths and their sizes for a given file, sorted from the most recent to the oldest
        param basedir: base directory of the synchronization data (not the history basedir)
        param file: file path, in the synchronization directory, to get history for (actual file, not in history directory)"""
        history_name = HistoryMode.get_history_file_pattern(basedir, file, True)
        nbfiles = 0
        sizes:list = []
        paths:list = []
        while os.path.exists(history_name.format(nbfiles+1)):
            sizes.append( os.path.getsize(history_name.format(nbfiles+1)) )
            paths.append(history_name.format(nbfiles+1))
            nbfiles += 1
        return paths, sizes
    

    def get_history_filepath(basedir:str, file:str, num:int) -> str:
        history_name = HistoryMode.get_history_file_pattern(basedir, file, True)
        return history_name.format(num)
    

    def get_history_file_pattern(basedir:str, file:str, basedir_is_sync_dir:bool) -> str:
        dir, filename = os.path.split(file)
        name, ext = os.path.splitext(filename)
        if basedir_is_sync_dir:
            dir = os.path.relpath(dir, basedir)
            history_name = os.path.join(basedir, HISTORY_DIR, dir, name) + HISTORY_FORMAT + ext
        else:
            history_name = os.path.join(dir, name) + HISTORY_FORMAT + ext
        return os.path.normpath(history_name)
    
    def remove_historydir_in_path(path:str) -> str:
        sep = '\\' if '\\' in path else '/'
        parts = path.split(sep)
        if HISTORY_DIR in parts:
            parts.remove(HISTORY_DIR)
        return sep.join(parts)