__author__      = "Jérôme Cuq"
__copyright__   = "Copyright 2026, Jérôme Cuq"
__license__     = "BSD-3-Clause"

from enum import Enum
import re
import os
import sys


def log(message: str):
    print(message)


def log_error(message: str, prefix='ERROR: '):
    """print an error and stop current script

    :param message: message to print out
    :param exitScript: indicates whether the function must call exit, defaults to True
    """
    print(prefix+message, file=sys.stderr)


def replace_env_variables(text: str) -> str:
    """replace env variables in a text (ex: ${TEMP} or $TEMP) by their value

    :param text: text to replace env variables in
    :return: text with env variables replaced
    """
    return os.path.expandvars(text)

def is_dir_empty(path: str) -> bool:
    with os.scandir(path) as d:
        return not any(d)
    
def remove_empty_part_of_path(dirpath):
    """remove from disk parts of the given path that are empty
       (ex: 'C:/temp/emptydir/emptydir2' will be reduced to 'C:/temp' if emptydir and emptydir2 are empty)"""
    while os.path.exists(dirpath) and is_dir_empty(dirpath):
        try:
            os.rmdir(dirpath)
            dirpath = os.path.dirname(dirpath)
        except OSError:
            break

tokenizer = re.compile(r'^[ \t]*(\d+)[ \t]*([a-zA-Z]*)?[ \t]*$')

def format_size(size:int, units: list = ['byte(s)', 'Kb', 'Mb', 'Gb'], coeff: int = 1024) -> str:
    """format a size to a human readable string with given unit
    :param size: size to format
    :param units: list of units to use, in increasing order, defaults to ['byte(s)', 'Kb', 'Mb', 'Gb']
    :param coeff: coefficient to use between units, defaults to 1024"""
    for i in range(len(units)):
        if size<10*(coeff**(i+1)):
            return '%d %s' % (size/(coeff**i), units[i])
    

def value_with_unit_to_int(value: str | int, default: int, units: list = ['b|bytes|byte', 'k|kb', 'mb|m', 'g|gb'], coeff: int = 1024) -> int:
    """convert a value with unit to an int, or return default if the value is not valid
    :param value: value to convert, can be an int or a string with a number and an optional unit (ex: '100', '100B', '100 k', '1 mb')
    :param default: value to return if the value is not valid
    :param units: list of units to use, in increasing order, with possible aliases separated by '|', defaults to ['b|bytes|byte', 'k|kb', 'mb|m', 'g|gb']
    :param coeff: coefficient to use between units, defaults to 1024"""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        match = tokenizer.match(value)
        if match:
            number, unit_value = match.groups()
            try:
                number = int(number)
            except ValueError:
                return default
            if not unit_value:
                return number

            unit_level = 0
            unit_value = unit_value.lower()
            for unit in units:
                if unit_value in unit.lower().split('|'):
                    if unit_level == 0:
                        return number
                    else:
                        return number * (coeff ** unit_level)
                unit_level += 1
            
    return default