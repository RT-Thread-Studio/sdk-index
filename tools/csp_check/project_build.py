import json
import os
import re
from gen_sdk_json import gen_sdk_para_json_file
from gen_test_case import gen_chip_test_case
from csp_check import execute_command


def csp_build_test():
    execute_command("wget -c https://github.com/RT-Thread-Studio/sdk-rt-thread-nano-source-code/archive/v3.1.3.zip")
    execute_command("unzip {0} -d /rt-thread/rt-thread-src".format("v3.1.3.zip"))
    execute_command("rm -rf v3.1.3.zip")
    execute_command("wget -c https://github.com/RT-Thread-Studio/sdk-rt-thread-source-code/archive/v4.0.2.zip")
    execute_command("unzip {0} -d /rt-thread/rt-thread-src".format("v4.0.2.zip"))
    execute_command("rm -rf v4.0.2.zip")
    # execute_command("cp eclipse.py /rt-thread/rt-thread-src/sdk-rt-thread-nano-source-code-3.1.3/tools")
    # execute_command("cp eclipse.py /rt-thread/rt-thread-src/sdk-rt-thread-source-code-4.0.2/tools")

    try:
        with open('/rt-thread/sdk-index/tools/csp_update_url.json', "r") as f:
            sdk_url = json.loads(f.read())[0]
    except Exception as e:
        print("\nError message : {0}.".format(e))
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

    gen_sdk_para_json_file(csp_path, "/rt-thread/workspace", "/rt-thread/rt-thread-src")
    gen_chip_test_case("csp_chips.json", "mcu_config")
    os.system("python csp_test_case.py")
    execute_command("rm -rf mcu_config")
    execute_command("exit")


if __name__ == "__main__":
    csp_build_test()
