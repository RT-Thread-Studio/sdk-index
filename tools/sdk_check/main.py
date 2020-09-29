import os
import sys
import time
import json
import logging
import subprocess
from check_tools import execute_command


def init_logger():
    log_format = "[%(filename)s %(lineno)d %(levelname)s] %(message)s "
    date_format = '%Y-%m-%d  %H:%M:%S %a '
    logging.basicConfig(level=logging.INFO,
                        format=log_format,
                        datefmt=date_format,
                        )


def main():
    init_logger()
    execute_command("apt-get update && apt-get -y upgrade && apt-get -y install unzip")
    os.chdir("/rt-thread/sdk-index/tools/sdk_check")
    execute_command("python -m pip install --upgrade pip")
    result = execute_command("pip install rt-thread-studio")
    logging.info("{0}".format(result))
    execute_command("pip install pyyaml pytest-sugar pytest-parallel")
    execute_command("chmod 777 prj_gen")

    # get update csp url
    try:
        with open('/rt-thread/sdk-index/tools/csp_update_url.json', "r") as f:
            sdk_url = json.loads(f.read())[0]
        # csp ci check
        logging.info("csp check test! : {0}".format(sdk_url))
        os.system("python csp_check.py")
        sys.exit(0)
    except Exception as e:
        logging.warning("warning message : {0}.".format(e))

    # get update bsp url
    try:
        with open('/rt-thread/sdk-index/tools/bsp_update_url.json', "r") as f:
            sdk_url = json.loads(f.read())[0]
        # bsp ci chck
        logging.info("bsp check test! : {0}".format(sdk_url))
        os.system("python bsp_check.py")
        sys.exit(0)
    except Exception as e:
        logging.error("Error message : {0}.".format(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
