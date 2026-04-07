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

tokenizer = re.compile(r'^[ \t]*(\d+)[ \t]*([a-zA-Z]*)?[ \t]*$')

def value_with_unit_to_int(value: str | int, default: int, units: list = ['b|bytes|byte', 'k|kb', 'mb|m', 'g|gb'], coeff: int = 1024) -> int:
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