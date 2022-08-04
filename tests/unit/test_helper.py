import shutil
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def get_test_files_path(extra: str) -> Path:
    return Path(__file__).resolve().parent / "files" / extra


def wrap_tempdir(func):
    def f(*args, **kwargs):
        tempdir = Path(tempfile.mkdtemp())
        try:
            return func(*args, **kwargs, tempdir=tempdir)
        finally:
            shutil.rmtree(tempdir)

    return f
