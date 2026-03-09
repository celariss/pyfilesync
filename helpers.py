__author__      = "Jérôme Cuq"
__copyright__   = "Copyright 2026, Jérôme Cuq"
__license__     = "BSD-3-Clause"

from enum import Enum
import os
import sys


def log(message: str):
    print(message)

def log_error(message: str, exitScript: bool = False):
    """print an error and stop current script

    :param message: message to print out
    :param exitScript: indicates whether the function must call exit, defaults to True
    """
    print("ERROR: "+message, file=sys.stderr)
    if exitScript:
        exit(1)

def replace_env_variables(text: str) -> str:
    """replace env variables in a text (ex: ${TEMP} or $TEMP) by their value

    :param text: text to replace env variables in
    :return: text with env variables replaced
    """
    return os.path.expandvars(text)