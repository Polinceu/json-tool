"""jtool 的单元测试：helper 函数直接测，CLI  plumbing 用子进程端到端测。"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from jtool.cli import fmt_value, get_path

PKG_DIR = Path(__file__).resolve().parent.parent


class TestGetPath(unittest.TestCase):
    def setUp(self):
        self.obj = {
            "a": {"b": [{"c": 1}, {"c": 2}]},
            "name": "tom",
        }

    def test_nested_dict(self):
        self.assertEqual(get_path(self.obj, "name"), "tom")

    def test_list_index(self):
        self.assertEqual(get_path(self.obj, "a.b.0.c"), 1)
        self.assertEqual(get_path(self.obj, "a.b.1.c"), 2)

    def test_missing_key(self):
        with self.assertRaises(KeyError):
            get_path(self.obj, "a.nope")

    def test_index_out_of_range(self):
        with self.assertRaises(KeyError):
            get_path(self.obj, "a.b.9")

    def test_non_numeric_index_on_list(self):
        with self.assertRaises(KeyError):
            get_path(self.obj, "a.b.x")

    def test_drill_into_scalar(self):
        with self.assertRaises(KeyError):
            get_path(self.obj, "name.first")


class TestFmtValue(unittest.TestCase):
    def test_scalar(self):
        self.assertEqual(fmt_value(42), "42")
        self.assertEqual(fmt_value("hi"), "hi")
        self.assertEqual(fmt_value(None), "None")

    def test_compound_becomes_json(self):
        out = fmt_value({"x": 1})
        self.assertEqual(json.loads(out), {"x": 1})


class TestCLI(unittest.TestCase):
    """端到端：起子进程跑 python -m jtool，覆盖文件参数和 stdin 管道。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.sample = Path(self.tmp.name) / "sample.json"
        self.sample.write_text(
            json.dumps({"name": "tom", "tags": ["a", "b"], "meta": {"n": 3}}),
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def run_jtool(self, *args, input_text=None):
        return subprocess.run(
            [sys.executable, "-m", "jtool", *args],
            input=input_text,
            capture_output=True,
            text=True,
            cwd=PKG_DIR,
        )

    def test_fmt_file(self):
        r = self.run_jtool("fmt", str(self.sample))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout), json.loads(self.sample.read_text()))

    def test_fmt_stdin(self):
        r = self.run_jtool("fmt", input_text='{"x":1}')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('"x": 1', r.stdout)

    def test_fmt_indent_option(self):
        r = self.run_jtool("fmt", "--indent", "4", str(self.sample))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('    "name": "tom"', r.stdout)

    def test_get_scalar(self):
        r = self.run_jtool("get", "meta.n", str(self.sample))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "3")

    def test_get_list_item(self):
        r = self.run_jtool("get", "tags.1", str(self.sample))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "b")

    def test_get_object_pretty(self):
        r = self.run_jtool("get", "meta", str(self.sample))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout), {"n": 3})

    def test_get_stdin(self):
        r = self.run_jtool("get", "a", input_text='{"a": {"b": 1}}')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('"b": 1', r.stdout)

    def test_get_missing_key_fails(self):
        r = self.run_jtool("get", "nope", str(self.sample))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("找不到", r.stderr or r.stdout)

    def test_keys(self):
        r = self.run_jtool("keys", str(self.sample))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(sorted(r.stdout.split()), ["meta", "name", "tags"])

    def test_keys_on_non_object_fails(self):
        r = self.run_jtool("keys", input_text="[1, 2]")
        self.assertNotEqual(r.returncode, 0)

    def test_validate_ok(self):
        r = self.run_jtool("validate", str(self.sample))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("OK", r.stdout)

    def test_validate_bad(self):
        bad = Path(self.tmp.name) / "bad.json"
        bad.write_text('{"a": 1,}', encoding="utf-8")
        r = self.run_jtool("validate", str(bad))
        self.assertNotEqual(r.returncode, 0)

    def test_invalid_json_input_fails(self):
        r = self.run_jtool("fmt", input_text="不是 json")
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
