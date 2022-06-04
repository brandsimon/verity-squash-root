import os
import shutil
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def get_test_files_path(extra: str) -> str:
    return os.path.join(os.path.dirname(__file__), "files", extra)


def wrap_tempdir(func):
    def f(*args, **kwargs):
        tempdir = tempfile.mkdtemp()
        try:
            return func(*args, **kwargs, tempdir=tempdir)
        finally:
            shutil.rmtree(tempdir)

    return f
