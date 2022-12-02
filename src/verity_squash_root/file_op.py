import shutil
from pathlib import Path
from typing import List


def write_str_to(path: Path, content: str) -> None:
    path.write_text(content)


def read_from(path: Path) -> bytes:
    return path.read_bytes()


def read_text_from(path: Path) -> str:
    return read_from(path).decode()


def merge_files(src: List[Path], dest: Path):
    with open(dest, "wb") as dest_fd:
        for s in src:
            with open(s, "rb") as src_fd:
                shutil.copyfileobj(src_fd, dest_fd)
