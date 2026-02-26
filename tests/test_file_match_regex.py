import fnmatch
import os
import re
import pytest
from helpers import file_match_regex

def file_match_regex_(filepath:str, regex:str, isdir:bool) -> bool:
    return file_match_regex(filepath, os.path.basename(filepath), re.compile(regex), isdir)

class TestFileMatchRegex:
    def test_file_match_regex(self):
        """
            Test cases for helpers.file_match_regex() function
        """
        dataset:list = [
            # each test case is : (filepath, pattern, isdir, expected_match_result)
            # Test cases for regular files
            ('dir1/dir2/file.txt', '*.txt', False, True),
            ('dir1/dir2/file.txt', '*.tx', False, False),
            ('file.txt', '*.txt', False, True),
            ('file.tx', '*.txt', False, False),
            ('dir1/dir2/file', 'file', False, True),
            ('dir1/dir2/file', 'file/', False, False),
            ('dir1/dir2/file', '/file', False, False),
            ('dir1/dir2/file1', 'file', False, False),
            ('dir1/dir2/file1', 'file*', False, True),
            ('file', 'file', False, True),
            ('file', '/file', False, True),
            ('file', 'file/', False, False),
            ('dir1/dir2/file.py', '*/dir2/*.py', False, True),
            ('dir1/dir2/file.py', '/dir1/*.py', False, True),
            ('dir1/dir2/file.py', 'dir2', False, False),
            ('dir1/dir2/file.py', '/dir2/', False, False),
            ('dir1/dir2/file.py', '*/dir2/*', False, True),
            ('dir1/dir2/file.py', '/dir1/*', False, True),
            ('dir1/dir2/file.py', '*/dir1/*', False, True),

            # Test cases for directories
            ('dir1/dir2/toto', 'toto', True, False),
            ('dir1/dir2/toto', 'toto/', True, True),
            ('dir1/dir2/toto', '/toto/', True, False),
            ('dir1/dir2/toto', '/dir2/', True, False),
            ('dir1/dir2/toto', '*/toto/', True, True),
            ('dir1', 'dir1/', True, True),
            ('dir1', '/dir1/', True, True),
            ('dir1', 'dir1/*', True, True),
            ('dir1/dir2', '*/dir1/*', True, True),
            ('dir1/dir2_/toto', '*/dir2*/*', True, True),
        ]
        for filepath, pattern, isdir, expected in dataset:
            assert file_match_regex_(filepath, fnmatch.translate(pattern), isdir) == expected