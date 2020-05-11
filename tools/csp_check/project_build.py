import json
import os
import re
import subprocess
import time
from gen_sdk_json import gen_sdk_para_json_file
from gen_test_case import gen_chip_test_case


def execute_command(cmd_string, cwd=None, shell=True):
    """Execute the system command at the specified address."""

    sub = subprocess.Popen(cmd_string, cwd=cwd, stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, shell=shell, bufsize=4096)

    stdout_str = ''
    while sub.poll() is None:
        stdout_str += str(sub.stdout.read())
        time.sleep(0.1)

    return stdout_str


def csp_build_test():
    # work path = /rt-thread/sdk-index/tools/csp_check

    # get rt-thread-src
    execute_command("wget -c https://github.com/RT-Thread-Studio/sdk-rt-thread-nano-source-code/archive/v3.1.3.zip")
    execute_command("unzip {0} -d /rt-thread/rt-thread-src".format("v3.1.3.zip"))
    execute_command("rm -rf v3.1.3.zip")
    execute_command("wget -c https://github.com/RT-Thread-Studio/sdk-rt-thread-source-code/archive/v4.0.2.zip")
    execute_command("unzip {0} -d /rt-thread/rt-thread-src".format("v4.0.2.zip"))
    execute_command("rm -rf v4.0.2.zip")
    execute_command("cp eclipse.py /rt-thread/rt-thread-src/sdk-rthread-nano-source-code-3.1.3/tools")
    execute_command("cp eclipse.py /rt-thread/rt-thread-src/sdk-rt-thread-source-code-4.0.2/tools")

    # get sdk
    try:
        with open('/rt-thread/sdk-index/sdk_url.json', "r") as f:
            sdk_url = json.loads(f.read())[0]
    except Exception as e:
        print("get update url err : {0}".format(sdk_url))
        exit(1)

    execute_command("wget -c {0}".format(sdk_url))
    zip_name = sdk_url.split("/")[-1]
    execute_command("unzip {0} -d /rt-thread".format(zip_name))
    execute_command("rm -rf {0}".format(zip_name))

    result = str(re.findall(".*/RT-Thread-Studio/(.*)/archive/.*", sdk_url)[0])
    rt_thread_dir = os.listdir("/rt-thread")
    for sdk_path in rt_thread_dir:
        if sdk_path.find(result) != -1:
            csp_path = os.path.join('/rt-thread', sdk_path)
            break

    # gen project json file
    gen_sdk_para_json_file(csp_path, "/rt-thread/workspace", "/rt-thread/rt-thread-src")

    # gen mcu_config dir
    gen_chip_test_case("csp_chips.json", "mcu_config")

    # pytest
    os.system("python project_test.py")


if __name__ == "__main__":
    csp_build_test()
