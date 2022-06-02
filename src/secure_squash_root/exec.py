import subprocess
from typing import Tuple


def run_prog(cmd: [str], expect_returncode: int = 0) -> Tuple[bytes, bytes]:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    result = proc.communicate()
    if proc.returncode != expect_returncode:
        raise ChildProcessError([cmd, result])
    return result
