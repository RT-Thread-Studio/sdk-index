import os
import json
import logging
import subprocess
from check_tools import execute_command
from check_tools import do_copy_file
from check_tools import do_copy_folder
from gen_bsp_json import gen_bsp_sdk_json
from gen_test_case import gen_sdk_test_case


def init_logger():
    log_format = "[%(filename)s %(lineno)d %(levelname)s] %(message)s "
    date_format = '%Y-%m-%d  %H:%M:%S %a '
    logging.basicConfig(level=logging.DEBUG,
                        format=log_format,
                        datefmt=date_format,
                        )


def bsp_check_test():
    init_logger()
    os.environ['SDK_CHECK_TYPE'] = 'bsp_check'
    with open('/rt-thread/sdk-index/tools/bsp_update_url.json', "r") as f:
        bsp_update_url = json.loads(f.read())[0]

    execute_command("wget -O /rt-thread/bsp.zip {0}".format(bsp_update_url))
    execute_command("unzip {0} -d /rt-thread/rt-thread-bsp".format("/rt-thread/bsp.zip"))
    execute_command("rm -rf /rt-thread/bsp.zip")
    prj_path = "/RT-ThreadStudio/plugins/gener/gener/"

    src_path = os.path.join(os.getcwd(), "templates")
    dst_path = os.path.join(prj_path, "templates")
    do_copy_folder(src_path, dst_path)
    do_copy_file("prj_gen", prj_path)

    logging.info("ls -al {0}".format(prj_path))
    os.system("ls -al {0}".format(prj_path))

    # set prj_gen_path
    os.environ['PRJ_GEN_PATH'] = prj_path

    # find bsp path
    real_bsp_path = None
    for dir in os.listdir("/rt-thread/rt-thread-bsp"):
        if dir.find("sdk-bsp") != -1:
            real_bsp_path = os.path.join("/rt-thread/rt-thread-bsp", dir)
            logging.info("bsp path : {0}".format(real_bsp_path))
            break
    if real_bsp_path is None:
        logging.error("can't find bsp path, please check it!")
    board_path = "/RT-ThreadStudio/repo/Extract/Board_Support_Packages/RealThread/board/0.1.1/"
    do_copy_folder(real_bsp_path, board_path)
    gen_bsp_sdk_json(board_path, "/rt-thread/sdk-index/", "/rt-thread/workspace/")
    # gen test case
    gen_sdk_test_case("bsp_chips.json", "mcu_config")

    os.system("python sdk_test_case.py")

    exit(0)


if __name__ == "__main__":
    bsp_check_test()
