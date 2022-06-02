import os


def get_test_files_path(extra: str):
    return os.path.join(os.path.dirname(__file__), "files", extra)
