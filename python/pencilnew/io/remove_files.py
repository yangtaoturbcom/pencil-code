def remove_files(path, do_it=False, do_it_really=False):
    """ This method clears path COMPLETELY.
    Meaning, if you start this method my using path on your root dir
    your whole computer is gone! So we implemented some safety mechanism.

    Args:
        path:                   path do clear
        do_it, do_it_really:    to activate pass True, True
    """

    import os, shutil
    import os
    from os.path import expanduser, isdir, realpath, relpath
    from pencilnew.io import remove_files as remove

    # safety checks
    # first get all sensible paths

    sens_paths = []
    for key in os.environ.keys():
        paths = os.environ[key].split(':')
        for p in paths:
            if isdir(p):
                sens_paths.append(realpath(p))

    sens_paths.append('/')
    sens_paths.append(expanduser('~'))

    for p in sens_paths:
        if not realpath(p) in sens_paths: sens_paths.append(realpath(p))
        while p != '/':
            p = os.path.dirname(p)
            if not realpath(p) in sens_paths: sens_paths.append(p)


    if realpath(path) in sens_paths:
        print('! ERROR: You better should not delete '+path)
        return False


    if os.path.exists(path):
        if os.path.isdir(path):
            if os.path.islink(path):
                if do_it and do_it_really:
                    os.unlink(path)
                else:
                    print('-> would unlink:\t'+relpath(path))
            else:
                for p in os.listdir(path):
                    print('-> would remove:\t'+p+'\nin '+relpath(path))
                    remove(p)
        else:
            if os.path.islink(path):
                if do_it and do_it_really:
                    os.unlink(path)
                else:
                    print('-> would unlink:\t'+relpath(path))
            else:
                if do_it and do_it_really:
                    os.remove(path)
                else:
                    print('-> would remove:\t'+relpath(path))

    return True
