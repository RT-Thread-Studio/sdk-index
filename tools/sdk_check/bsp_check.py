import os
import sys
import json
import logging
import subprocess
from check_tools import execute_command
from check_tools import do_copy_file
from check_tools import do_copy_folder
from gen_bsp_json import gen_bsp_sdk_json
from gen_test_case import gen_sdk_test_case


def exec_bsp_test_case():
    os.environ['SDK_CHECK_TYPE'] = 'bsp_check'
    with open('/rt-thread/sdk-index/tools/bsp_update_url.json', "r") as f:
        bsp_update_url = json.loads(f.read())[0]

    execute_command("wget -nv -O /rt-thread/bsp.zip {0}".format(bsp_update_url))
    execute_command("unzip {0} -d /rt-thread/rt-thread-bsp".format("/rt-thread/bsp.zip"))
    execute_command("rm -rf /rt-thread/bsp.zip")
    prj_path = "/RT-ThreadStudio/plugins/gener/gener/"

    src_path = os.path.join(os.getcwd(), "templates")
    dst_path = os.path.join(prj_path, "templates")
    do_copy_folder(src_path, dst_path)
    do_copy_file("prj_gen", prj_path)

    # set prj_gen_path
    os.environ['PRJ_GEN_PATH'] = prj_path

    # find bsp path
    real_bsp_path = None
    rt_thread_bsp_dir = os.listdir("/rt-thread/rt-thread-bsp")
    if len(rt_thread_bsp_dir) != 1:
        logging.error("Please check the zip : {0}".format(bsp_update_url))
        sys.exit(1)
    real_bsp_path = os.path.join("/rt-thread/rt-thread-bsp", rt_thread_bsp_dir[0])
    logging.info("bsp path : {0}".format(real_bsp_path))

    board_path = "/RT-ThreadStudio/repo/Extract/Board_Support_Packages/RealThread/board/0.1.1/"
    do_copy_folder(real_bsp_path, board_path)
    gen_bsp_sdk_json(board_path, "/rt-thread/sdk-index/", "/rt-thread/workspace/")
    # gen test case
    gen_sdk_test_case("bsp_chips.json", "mcu_config")
    subprocess.call("python sdk_test_case.py", shell=True)
    execute_command("rm -rf mcu_config")

    sys.exit(0)
