import os
import shutil

from helpers import *

HISTORY_DIR = '.autosave'
HISTORY_PATTERN = '_#{:0>2d}#'

class HistoryMode:
    def save_file(basedir:str, file:str, maxnbfiles:int, maxsize:int):
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
                while os.path.exists(path) and is_dir_empty(path):
                    os.rmdir(path)
                    path = os.path.dirname(path)
                return

            # Remove files in history that should not be kept
            for i in range(nbtokeep, len(historyfilesizes)):
                os.remove(historyfilepaths[i])

            # Move files in history to their new name, to make place for new file to save in history
            for i in range(nbtokeep, 0, -1):
                os.rename(historyfilepaths[i-1], HistoryMode.get_history_filepath(basedir, file, i+1))

            # move file to save in history
            destpath = HistoryMode.get_history_filepath(basedir, file, 1)
            os.makedirs(os.path.dirname(destpath), exist_ok=True)
            shutil.move(file, destpath)


    def get_nb_history_files_to_keep(filetosavesize:int, historyfilesizes:list[int], maxnbhistoryfiles:int, maxhistorysize:int) -> int:
        """ Returns the number of history files to keep when adding a new file in history, or -1 if the new file to save is too big to be kept in history
        """
        if maxhistorysize!=0 and (filetosavesize > maxhistorysize or maxnbhistoryfiles <= 0):
            return -1
        nbhistoryfiles = len(historyfilesizes)
        i = 0
        historyfilesize = 0
        while True:
            if i == nbhistoryfiles or i+1 >= maxnbhistoryfiles:
                return i
            historyfilesize += historyfilesizes[i]
            if  maxhistorysize!=0 and (filetosavesize + historyfilesize > maxhistorysize):
                return i
            i += 1


    def get_file_history(basedir:str, file:str) -> tuple[list[str], list[int]]:
        history_name = HistoryMode.get_history_file_pattern(basedir, file)
        nbfiles = 0
        sizes:list = []
        paths:list = []
        while os.path.exists(history_name.format(nbfiles+1)):
            sizes.append( os.path.getsize(history_name.format(nbfiles+1)) )
            paths.append(history_name.format(nbfiles+1))
            nbfiles += 1
        return paths, sizes
    

    def get_history_filepath(basedir:str, file:str, num:int) -> str:
        history_name = HistoryMode.get_history_file_pattern(basedir, file)
        return history_name.format(num)
    

    def get_history_file_pattern(basedir:str, file:str) -> str:
        dir, filename = os.path.split(file)
        name, ext = os.path.splitext(filename)
        dir = os.path.relpath(dir, basedir)
        history_name = os.path.join(basedir, HISTORY_DIR, dir, name) + HISTORY_PATTERN + ext
        return os.path.normpath(history_name)