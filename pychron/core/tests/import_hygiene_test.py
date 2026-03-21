import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


class ImportHygieneTestCase(unittest.TestCase):
    def test_qt_editors_do_not_use_legacy_qt_imports(self):
        files = (
            ROOT / "pychron/core/ui/qt/double_spinner.py",
            ROOT / "pychron/core/ui/qt/label_editor.py",
            ROOT / "pychron/core/ui/qt/animated_png_editor.py",
            ROOT / "pychron/core/ui/qt/keyword_editor.py",
            ROOT / "pychron/core/ui/qt/keybinding_editor.py",
            ROOT / "pychron/core/ui/qt/patch_editor.py",
            ROOT / "pychron/core/ui/qt/display_editor.py",
        )
        for path in files:
            source = path.read_text()
            self.assertNotIn("from PySide import", source, path.as_posix())
            self.assertNotIn("import PySide", source, path.as_posix())
            self.assertNotIn("traitsui.qt4", source, path.as_posix())

    def test_library_modules_do_not_execute_top_level_demo_code(self):
        files = (
            ROOT / "pychron/core/stats/age_bracket.py",
            ROOT / "pychron/core/stats/peak_deconvolution.py",
        )
        for path in files:
            tree = ast.parse(path.read_text(), filename=path.as_posix())
            for node in tree.body:
                self.assertFalse(
                    self._is_top_level_call(node),
                    "{} has executable top-level code".format(path.as_posix()),
                )

    @staticmethod
    def _is_top_level_call(node):
        if isinstance(node, ast.Expr):
            return isinstance(node.value, ast.Call)
        if isinstance(node, ast.Assign):
            return isinstance(node.value, ast.Call)
        if isinstance(node, ast.AugAssign):
            return isinstance(node.value, ast.Call)
        return False


if __name__ == "__main__":
    unittest.main()
