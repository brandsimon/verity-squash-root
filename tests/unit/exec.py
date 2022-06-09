import unittest
from secure_squash_root.exec import exec_binary


class ExecTest(unittest.TestCase):

    def test__exec_binary__exit_code(self):
        exit_3_cmd = ["dash", "-c", "exit 3"]
        self.assertEqual(
                exec_binary(exit_3_cmd, 3),
                (b'', b''))
        with self.assertRaises(ChildProcessError) as e_ctx:
            exec_binary(exit_3_cmd)
        exception = [exit_3_cmd, (b'', b'')],
        self.assertEqual(e_ctx.exception.args, exception)

        with self.assertRaises(ChildProcessError) as e_ctx:
            exec_binary(exit_3_cmd, 1)
        self.assertEqual(e_ctx.exception.args, exception)

    def test__exec_binary__result(self):
        result = exec_binary(["dash", "-c",
                              'printf StdOutStr\\\\n123;'
                              'printf StdErrStr\\\\n456 >&2'])
        self.assertEqual(result,
                         (b'StdOutStr\n123', b'StdErrStr\n456'))
