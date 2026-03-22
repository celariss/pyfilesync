__author__      = "Jérôme Cuq"
__copyright__   = "Copyright 2026, Jérôme Cuq"
__license__     = "BSD-3-Clause"

from helpers import log
from dirsyncer import *

def check_errors_format(err:set) -> bool:
    for value in err:
        if not isinstance(value, tuple) or len(value)!=2:
            return False
    return True


def normalize_cmpdata(cmpdata:CmpData) -> CmpData:
    return CmpData(
        left_only_files = set({item.replace('\\','/') for item in cmpdata.left_only_files}),
        left_only_empty_dirs = set({item.replace('\\','/') for item in cmpdata.left_only_empty_dirs}),
        right_only_files = set({item.replace('\\','/') for item in cmpdata.right_only_files}),
        right_only_dirs = set({item.replace('\\','/') for item in cmpdata.right_only_dirs}),
        right_only_files_in_dirs = set({item.replace('\\','/') for item in cmpdata.right_only_files_in_dirs}),
        equal_files = set({item.replace('\\','/') for item in cmpdata.equal_files}),
        different_files = set({item.replace('\\','/') for item in cmpdata.different_files}),
        errors = cmpdata.errors
    )

def are_cmpdata_equal(cmpdata1:CmpData, cmpdata2:CmpData, label:str) -> bool:
        cmpdata1 = normalize_cmpdata(cmpdata1)
        cmpdata2 = normalize_cmpdata(cmpdata2)
        res:bool = True
        if cmpdata1.left_only_files != cmpdata2.left_only_files:
            log(f"left_only_files differs in {label} : (1=result of compare_dirs, 2=expected result)")
            log(f"1> {cmpdata1.left_only_files} != ")
            log(f"2> {cmpdata2.left_only_files}")
            res = False
        if cmpdata1.left_only_empty_dirs != cmpdata2.left_only_empty_dirs:
            log(f"left_only_empty_dirs differs in {label} : (1=result of compare_dirs, 2=expected result)")
            log(f"1> {cmpdata1.left_only_empty_dirs} != ")
            log(f"2> {cmpdata2.left_only_empty_dirs}")
            res = False
        if cmpdata1.right_only_files != cmpdata2.right_only_files:
            log(f"right_only_files differs in {label}: (1=result of compare_dirs, 2=expected result)")
            log(f"1> {cmpdata1.right_only_files} != ")
            log(f"2> {cmpdata2.right_only_files}")
            res = False
        if cmpdata1.right_only_files_in_dirs != cmpdata2.right_only_files_in_dirs:
            log(f"right_only_files_in_dirs differs in {label}: (1=result of compare_dirs, 2=expected result)")
            log(f"1> {cmpdata1.right_only_files_in_dirs} != ")
            log(f"2> {cmpdata2.right_only_files_in_dirs}")
            res = False
        if cmpdata1.right_only_dirs != cmpdata2.right_only_dirs:
            log(f"right_only_dirs differs in {label}: (1=result of compare_dirs, 2=expected result)")
            log(f"1> {cmpdata1.right_only_dirs} != ")
            log(f"2> {cmpdata2.right_only_dirs}")
            res = False
        if cmpdata1.equal_files != cmpdata2.equal_files:
            log(f"equal differs in {label}: (1=result of compare_dirs, 2=expected result)")
            log(f"1> {cmpdata1.equal_files} != ")
            log(f"2> {cmpdata2.equal_files}")
            res = False
        if cmpdata1.different_files != cmpdata2.different_files:
            log(f"different differs in {label}: (1=result of compare_dirs, 2=expected result)")
            log(f"1> {cmpdata1.different_files} != ")
            log(f"2> {cmpdata2.different_files}")
            res = False
        if cmpdata1.errors != cmpdata2.errors:
            log(f"errors differs in {label}: (1=result of compare_dirs, 2=expected result)")
            log(f"1> {cmpdata1.errors} != ")
            log(f"2> {cmpdata2.errors}")
            res = False
        return res