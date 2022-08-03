import unittest
from verify_squash_root.exec import exec_binary, ExecBinaryError


class ExecTest(unittest.TestCase):

    def test__exec_binary__exit_code(self):
        exit_3_cmd = ["dash", "-c", "echo err str >&2 ; exit 3"]
        self.assertEqual(
                exec_binary(exit_3_cmd, 3),
                (b'', b'err str\n'))
        with self.assertRaises(ExecBinaryError) as e_ctx:
            exec_binary(exit_3_cmd)
        exception = [exit_3_cmd, (b'', b'err str\n')],
        self.assertEqual(e_ctx.exception.args, exception)

        with self.assertRaises(ExecBinaryError) as e_ctx:
            exec_binary(exit_3_cmd, 1)
        self.assertEqual(e_ctx.exception.args, exception)
        self.assertEqual(
            str(e_ctx.exception),
            "Failed to execute 'dash -c echo err str >&2 "
            "; exit 3', error: 'err str\\n'")
        self.assertEqual(e_ctx.exception.stderr(),
                         b'err str\n')

    def test__exec_binary__result(self):
        result = exec_binary(["dash", "-c",
                              'printf StdOutStr\\\\n123;'
                              'printf StdErrStr\\\\n456 >&2'])
        self.assertEqual(result,
                         (b'StdOutStr\n123', b'StdErrStr\n456'))

    def test__exec_binary__empty(self):
        with self.assertRaises(ChildProcessError) as e_ctx:
            exec_binary([])
        self.assertEqual(e_ctx.exception.args,
                         ("Cannot execute empty cmd",))

    def test__exec_binary__not_found(self):
        with self.assertRaises(ChildProcessError) as e_ctx:
            exec_binary(["notexistingbin", "-c", "param"])
        self.assertEqual(
            e_ctx.exception.args,
            ("Binary not found: notexistingbin, is it installed?",))
