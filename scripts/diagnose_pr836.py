"""Temporary reproduction of the exact BSP package used by PR 836."""
import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
import check_sdk
import gen_test_case

out = Path("/rt-thread/sdk-index/diagnostics")
out.mkdir(exist_ok=True)
original = gen_test_case._run_generator

def capture(command, cwd, log_path):
    print("GENERATOR command={!r} cwd={!r} RTT_ROOT={!r}".format(
        command, cwd, os.environ.get("RTT_ROOT")), flush=True)
    try:
        return original(command, cwd, log_path)
    finally:
        log = Path(log_path)
        if log.exists():
            shutil.copy2(str(log), str(out / "generate.log"))
            print(log.read_text(errors="replace"), flush=True)
        for cproject in Path("/rt-thread/workspace").rglob(".cproject"):
            project = cproject.parent
            destination = out / project.name
            destination.mkdir(exist_ok=True)
            for name in (".cproject", ".project", ".config", "rtconfig.h", "rtua.py", "SConstruct"):
                source = project / name
                if source.exists():
                    shutil.copy2(str(source), str(destination / name))
            tree = ET.parse(str(cproject))
            for entry in tree.findall(".//sourceEntries/entry"):
                print("GENERATED source entry: {}".format(entry.attrib), flush=True)
            for name in (".config", "rtconfig.h"):
                source = project / name
                if source.exists():
                    for line in source.read_text(errors="replace").splitlines():
                        if "UTEST" in line or "SMP" in line:
                            print("{}: {}".format(name, line), flush=True)

gen_test_case._run_generator = capture
check_sdk.init_dir()
check_sdk.prepare_pkgs([
    os.environ.get("BSP_URL", "https://github.com/hdscmcu/sdk-bsp-hc32f334-xhsc-ev/archive/refs/tags/v1.0.1.zip")
])
expect_failure = os.environ.get("EXPECT_GENERATION_FAILURE") == "true"
try:
    check_sdk.check_pkgs()
except RuntimeError as error:
    if not expect_failure or "SCons exit code(s)" not in str(error):
        raise
    print("EXPECTED GENERATION FAILURE: {}".format(error), flush=True)
else:
    if expect_failure:
        raise AssertionError("The broken package was not rejected during generation")

