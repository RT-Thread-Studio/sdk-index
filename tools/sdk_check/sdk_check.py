import os
import sys
import time
import json
import logging
import subprocess
from check_tools import execute_command
from csp_check import exec_csp_test_case
from bsp_check import exec_bsp_test_case


def init_logger():
    log_format = "[%(filename)s %(lineno)d %(levelname)s] %(message)s "
    date_format = '%Y-%m-%d  %H:%M:%S %a '
    logging.basicConfig(level=logging.INFO,
                        format=log_format,
                        datefmt=date_format,
                        )



def main():
    init_logger()

    os.chdir("/rt-thread/sdk-index/tools/sdk_check")
    
    logging.info(execute_command("apt-get update && apt-get -y upgrade"))
    logging.info(execute_command("python -m pip install --upgrade pip"))
    logging.info(execute_command("pip install pytest pytest-sugar pytest-html rt-thread-studio"))

    # get oss package
    execute_command('wget -nv https://realthread-download.oss-cn-hangzhou.aliyuncs.com/rt-studio/backend/rt-studio-backend.zip')
    execute_command("unzip rt-studio-backend.zip")
    result = execute_command("ls -al /rt-thread/sdk-index/tools/sdk_check")
    logging.info("ls -al /tools/sdk_check {0}".format(result))

    if os.path.exists("/rt-thread/sdk-index/tools/sdk_check/prj_gen"):
        execute_command("chmod 777 prj_gen")
    else:
        logging.error("can't find prj_gen!")
        sys.exit(1)

    result = execute_command("ls -al /rt-thread/sdk-index/tools/sdk_check")
    logging.debug("ls -al tools/sdk_check : {0}".format(result))

    # get update csp url
    try:
        with open('/rt-thread/sdk-index/tools/csp_update_url.json', "r") as f:
            sdk_url = json.loads(f.read())[0]
        logging.info("csp check test URL : {0}".format(sdk_url))
        exec_csp_test_case()
        sys.exit(0)
    except Exception as e:
        logging.warning("warning message : {0}.".format(e))

    # get update bsp url
    try:
        with open('/rt-thread/sdk-index/tools/bsp_update_url.json', "r") as f:
            sdk_url = json.loads(f.read())[0]
        logging.info("bsp check test URL : {0}".format(sdk_url))
        exec_bsp_test_case()
        sys.exit(0)
    except Exception as e:
        logging.error("Error message : {0}.".format(e))
        sys.exit(0)


if __name__ == "__main__":
    main()
