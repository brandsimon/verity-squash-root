import subprocess
from typing import List, Tuple


class ExecBinaryError(ChildProcessError):

    def __init__(self, cmd: List[str], stdout: bytes, stderr: bytes):
        self.__cmd = cmd
        self.__stderr = stderr
        super().__init__([cmd, (stdout, stderr)])

    def __str__(self):
        return "Failed to execute '{}', error: {}".format(
            " ".join(self.__cmd), str(self.__stderr)[1:])


def exec_binary(cmd: List[str], expect_returncode: int = 0) \
        -> Tuple[bytes, bytes]:
    if len(cmd) == 0:
        raise ChildProcessError("Cannot execute empty cmd")
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise ChildProcessError(
            "Binary not found: {}, is it installed?".format(cmd[0]))
    result = proc.communicate()
    if proc.returncode != expect_returncode:
        raise ExecBinaryError(cmd, result[0], result[1])
    return result
