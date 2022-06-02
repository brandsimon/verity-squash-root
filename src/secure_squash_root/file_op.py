import shutil


def write_str_to(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


def read_text_from(path: str) -> str:
    with open(path, "r") as f:
        return f.read()


def merge_files(src: [str], dest: str):
    with open(dest, "wb") as dest_fd:
        for s in src:
            with open(s, "rb") as src_fd:
                shutil.copyfileobj(src_fd, dest_fd)
