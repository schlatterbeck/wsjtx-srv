import os.path
import inspect

def called_from_pip ():
    sep  = os.path.sep
    comp = os.path.normpath (inspect.stack () [-1].filename).split (sep)
    if 'pip' in comp and '_vendor' in comp and 'pyproject_hooks' in comp:
        return True
    return False

try:
    from .wsjtx   import *
except ImportError:
    if not called_from_pip ():
        raise


try:
    from .Version import VERSION as __version__
except ImportError:
    __version__ = '0+unknown'
