import atexit
import os
import shutil
import tempfile
import uuid

def read(path, strip = True):
    with open(path, 'r') as file:
        contents = file.read()

    if (strip):
        contents = contents.strip()

    return contents

def get_temp_path(prefix = '', suffix = '', rm = True):
    """
    Get a path to a valid (but not currently existing) temp dirent.
    If rm is True, then the dirent will be attempted to be deleted on exit
    (no error will occur if the path is not there).
    """

    path = None
    while ((path is None) or os.path.exists(path)):
        path = os.path.join(tempfile.gettempdir(), prefix + str(uuid.uuid4()) + suffix)

    if (rm):
        atexit.register(remove_dirent, path)

    return path

def remove_dirent(path):
    if (not os.path.exists(path)):
        return

    if (os.path.isfile(path) or os.path.islink(path)):
        os.remove(path)
    elif (os.path.isdir(path)):
        shutil.rmtree(path)
    else:
        raise ValueError("Unknown type of dirent: '%s'." % (path))

def copy_dirent(source, dest):
    """
    Copy a file or directory into dest.
    If source is a file, then dest can be a file or dir.
    If source is a dir, then dest must be a non-existent dir.
    """

    if (os.path.isfile(source)):
        shutil.copy2(source, dest)
    else:
        shutil.copytree(source, dest)
