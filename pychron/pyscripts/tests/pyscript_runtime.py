import os
import tempfile
import unittest

try:
    from pychron.pyscripts.error import MainError
    from pychron.pyscripts.pyscript import PyScript
except ModuleNotFoundError:
    MainError = RuntimeError
    PyScript = None


class _Manager:
    def __init__(self):
        self.messages = []

    def info(self, message, **kw):
        self.messages.append((message, kw))


_PyScriptBase = PyScript if PyScript is not None else object


class _HarnessScript(_PyScriptBase):
    def __init__(self, *args, **kw):
        self.manager = _Manager()
        self.name = "harness.py"
        self.root = ""
        super(_HarnessScript, self).__init__(*args, **kw)

    def warning(self, msg):
        return

    def debug_exception(self):
        return ""

    def _sleep(self, *args, **kw):
        return


@unittest.skipIf(PyScript is None, "PyYAML is not installed")
class PyScriptRuntimeTestCase(unittest.TestCase):
    def test_context_cache_invalidates_when_setup_context_changes(self):
        script = _HarnessScript()
        script.setup_context(answer=1)

        ctx1 = script.get_context()
        ctx2 = script.get_context()

        self.assertEqual(ctx1["answer"], 1)
        self.assertEqual(ctx2["answer"], 1)

        script.setup_context(answer=2)
        ctx3 = script.get_context()

        self.assertEqual(ctx3["answer"], 2)

    def test_context_cache_invalidates_when_interpolation_path_changes(self):
        script = _HarnessScript()
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as w1:
            w1.write("foo: 1\n")
            p1 = w1.name

        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as w2:
            w2.write("foo: 2\n")
            p2 = w2.name

        try:
            script.interpolation_path = p1
            self.assertEqual(script.get_context()["foo"], 1)

            script.interpolation_path = p2
            self.assertEqual(script.get_context()["foo"], 2)
        finally:
            os.unlink(p1)
            os.unlink(p2)

    def test_gosub_clears_active_child_after_failure(self):
        parent = _HarnessScript()
        with tempfile.TemporaryDirectory() as root:
            parent.root = root

            child = os.path.join(parent.root, "child.py")
            with open(child, "w") as wfile:
                wfile.write("value = 1\n")

            with self.assertRaises(MainError):
                parent.gosub(name="child.py")

            self.assertIsNone(parent._gosub_script)


if __name__ == "__main__":
    unittest.main()
