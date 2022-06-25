import os as _os, shutil as _shutil

def force_mkdir(path):
    if _os.path.exists(path):
        if _os.path.isfile(path):
            _os.remove(path)
        else:
            return
    _os.makedirs(path)

def force_remove(path):
    if _os.path.isfile(path):
        _os.remove(path)
    elif _os.path.isdir(path):
        _shutil.rmtree(path)

def force_copy(src, dst):
    if not _os.path.exists(src):
        return
    parent_dir = _os.path.dirname(_os.path.abspath(dst))
    force_mkdir(parent_dir)
    force_remove(dst)
    if _os.path.isfile(src):
        _shutil.copyfile(src, dst)
    else:
        _shutil.copytree(src, dst)

