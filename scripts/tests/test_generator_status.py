"""Regression tests for SCons failures swallowed by the project generator.

Only load the definitions under test: importing check_sdk would install packages
and importing gen_test_case would require unrelated CI dependencies.
"""
import ast
import logging
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1]


def load_definitions(filename, names):
    source = (SCRIPTS / filename).read_text(encoding="utf-8")
    parsed = ast.parse(source, filename=filename)
    selected = ast.parse("")
    for node in parsed.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            selected.body.append(node)
        elif isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id in names
                for target in node.targets):
            selected.body.append(node)
    namespace = {
        "logging": logging, "os": os, "re": re, "shlex": shlex,
        "subprocess": subprocess, "tempfile": tempfile,
    }
    exec(compile(selected, filename, "exec"), namespace)
    return namespace


make_wrapper = load_definitions("check_sdk.py", {"_scons_wrapper"})["_scons_wrapper"]
run_generator = load_definitions("gen_test_case.py", {
    "_run_generator", "_ANSI_ESCAPE_PATTERN", "_GENERATION_ERROR_PATTERN",
})["_run_generator"]


class GeneratorTestCase(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="generator-status-test-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.log = self.root / "generate.log"

    def generate(self, script):
        return run_generator([sys.executable, "-c", script], str(self.root), str(self.log))


class GeneratorStatusTests(GeneratorTestCase):
    def test_status_fails_even_when_backend_returns_zero_without_error_text(self):
        script = (
            "import os, sys\n"
            "with open(os.environ['SDK_INDEX_SCONS_STATUS_FILE'], 'a') as f:\n"
            "    f.write('7\\n3\\n')\n"
            "print('Dependency packages missing')\n"
            "print('additional diagnostics', file=sys.stderr)\n"
        )
        with self.assertRaisesRegex(RuntimeError, r"SCons exit code\(s\) 7, 3"):
            self.generate(script)
        output = self.log.read_text(encoding="utf-8")
        self.assertIn("Dependency packages missing", output)
        self.assertIn("additional diagnostics", output)

    def test_status_is_scoped_to_one_generation_and_parent_environment_is_unchanged(self):
        script = (
            "import os\n"
            "status = os.environ['SDK_INDEX_SCONS_STATUS_FILE']\n"
            "print(status)\n"
            "with open(status, 'a') as f: f.write('1\\n')\n"
        )
        with mock.patch.dict(os.environ, {"SDK_INDEX_SCONS_STATUS_FILE": "parent-value"}):
            with self.assertRaises(RuntimeError):
                self.generate(script)
            status_path = self.log.read_text(encoding="utf-8").strip()
            self.assertNotEqual(status_path, "parent-value")
            self.assertFalse(Path(status_path).exists())
            self.assertEqual(os.environ["SDK_INDEX_SCONS_STATUS_FILE"], "parent-value")
            self.generate("print('second generation succeeded')")

    def test_generator_exit_code_and_existing_fatal_output_checks_still_work(self):
        cases = [
            ("import sys; print('stopped'); sys.exit(9)", "exit code 9"),
            ("print('\\x1b[31mRuntimeError: failed\\x1b[0m')", "fatal error in generator output"),
        ]
        for script, reason in cases:
            with self.subTest(reason=reason):
                with self.assertRaisesRegex(RuntimeError, reason):
                    self.generate(script)

    def test_success_preserves_both_output_streams(self):
        self.generate("import sys; print('stdout complete'); print('stderr complete', file=sys.stderr)")
        output = self.log.read_text(encoding="utf-8")
        self.assertIn("stdout complete", output)
        self.assertIn("stderr complete", output)


@unittest.skipUnless(shutil.which("sh"), "POSIX shell required to execute the CI wrapper")
class SConsWrapperTests(GeneratorTestCase):
    def setUp(self):
        super().setUp()
        self.shell = shutil.which("sh")
        self.wrapper = self.root / "scons"
        # A forward-slash executable path also works with Git/MSYS sh on Windows.
        self.wrapper.write_text(make_wrapper(sys.executable.replace("\\", "/")), encoding="utf-8")
        (self.root / "SCons.py").write_text(
            "import os, sys\n"
            "print('arguments=' + repr(sys.argv[2:]))\n"
            "print('library=' + repr(os.environ.get('LD_LIBRARY_PATH')))\n"
            "print('pythonhome=' + repr(os.environ.get('PYTHONHOME')))\n"
            "print('Dependency packages missing')\n"
            "sys.exit(int(sys.argv[1]))\n",
            encoding="utf-8",
        )

    def invoke_wrapper(self, exit_code, marker, *arguments):
        env = os.environ.copy()
        env["SDK_INDEX_SCONS_STATUS_FILE"] = str(marker)
        env["LD_LIBRARY_PATH_ORIG"] = "/original-library-path"
        env["LD_LIBRARY_PATH"] = "/bundled-library-path"
        env["PYTHONHOME"] = "/bundled-python-home"
        return subprocess.run(
            [self.shell, str(self.wrapper), str(exit_code)] + list(arguments),
            cwd=str(self.root), env=env, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, universal_newlines=True,
        )

    def test_wrapper_preserves_arguments_environment_and_success(self):
        marker = self.root / "failures"
        result = self.invoke_wrapper(0, marker, "argument with spaces", "*")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(marker.exists())
        self.assertIn("arguments=['argument with spaces', '*']", result.stdout)
        self.assertIn("library='/original-library-path'", result.stdout)
        self.assertIn("pythonhome=None", result.stdout)

    def test_wrapper_appends_failure_codes_and_preserves_exit_status(self):
        marker = self.root / "failures"
        for code in (7, 3):
            result = self.invoke_wrapper(code, marker)
            self.assertEqual(result.returncode, code, result.stderr)
        self.assertEqual(marker.read_text(encoding="utf-8"), "7\n3\n")
        self.assertEqual(self.invoke_wrapper(0, marker).returncode, 0)
        self.assertEqual(marker.read_text(encoding="utf-8"), "7\n3\n")

    def test_real_wrapper_detected_when_backend_discards_status_and_output(self):
        # Reproduce prj_gen's swallowed return code. Discard the child's output
        # too, proving the machine-readable status works independently of regex.
        script = (
            "import subprocess\n"
            "subprocess.call({0!r}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
            "print('Backend reported success')\n"
        ).format([self.shell, str(self.wrapper), "5"])
        with self.assertRaisesRegex(RuntimeError, r"SCons exit code\(s\) 5"):
            self.generate(script)
        self.assertEqual(self.log.read_text(encoding="utf-8").strip(), "Backend reported success")


if __name__ == "__main__":
    unittest.main()
