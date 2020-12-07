import os
import re
import sys
import json
import time
import random
import logging
import textwrap
import subprocess
from pathlib import Path
from check_tools import execute_command


def gen_sdk_test_case(json_path, mcu_config_path):
    generate_and_import_project(json_path, mcu_config_path)
    test_case = ''
    for config_json in os.listdir(mcu_config_path):
        project_name = config_json.split(".json")[0]
        new_project_name = re.sub(r"[\#\*\-\/\(\)\[\]\ ]", "_", project_name)
        test_case_example = """
                def test_{0}():
                    print("Build Project: {0}")
                    assert build_test("{0}") is True
                """.format(new_project_name)
        test_case_format = textwrap.dedent(test_case_example)
        test_case += "\n" + test_case_format
        config_json_path = os.path.join(mcu_config_path, config_json)

        execute_command("rm -rf {0}".format(config_json_path))
    with open("sdk_test_case.py", "a") as f:
        f.write(test_case + '\n')


def find_mcu_in_json_file(json_path, mcu_config_path):
    with open(json_path, 'r') as f:
        data = f.read()
    parameter_dict = json.loads(data)
    os.mkdir(mcu_config_path)
    test_numbers = int(len(parameter_dict))
    if test_numbers > 80:
        test_numbers = 80
    mcu_dict = dict(random.sample(parameter_dict.items(), test_numbers))

    for mcu in mcu_dict:
        bare_metal_list = {"parameter": parameter_dict[mcu]["parameter"]}
        mcu_json = os.path.join(mcu_config_path, mcu + ".json")
        with open(mcu_json, "w") as f:
            f.write(str(json.dumps(bare_metal_list, indent=4)))
    os.remove(json_path)


def generate_and_import_project(json_path, mcu_config_path):
    find_mcu_in_json_file(json_path, mcu_config_path)
    begin_time = time.time()
    logging.info("Project generate start.")
    project_number = 0
    for chip_json in os.listdir(mcu_config_path):
        project_number += 1
        project_name = chip_json.split(".json")[0]
        json_path = os.path.join(os.getcwd(), mcu_config_path, chip_json)
        logging.info("number : {1}, Project name : {0}.".format(project_name, project_number))
        get_generate_result(json_path)
    logging.info("Project generate end, time consuming : {0}.".format(time.time() - begin_time))

    cmd_pre = r"/rt-thread/eclipse/eclipse -nosplash --launcher.suppressErrors "\
              r"-application org.eclipse.cdt.managedbuilder.core.headlessbuild " \
              r"-data '/rt-thread/eclipse/workspace'"
    cmd = cmd_pre + ' -importAll "file:/rt-thread/workspace" 2> /dev/null'

    logging.info("Project import start.")
    begin_time = time.time()
    subprocess.call(cmd, shell=True)
    logging.info("Project import end. time consuming : {0}.".format(time.time() - begin_time))


def get_generate_result(csp_json_path):
    # judge sdk update type (csp or bsp)
    try:
        check_type = os.environ['SDK_CHECK_TYPE']
    except Exception as e:
        logging.error(": {0}".format(e))

    logging.debug("project_json_info: {0}".format(check_type))
    logging.debug("json path : {0}".format(csp_json_path))
    result = execute_command("cat {0}".format(csp_json_path))
    logging.debug("cat {0} : {1}".format(csp_json_path, result))

    before = os.getcwd()
    log_path = os.path.join(before, "generate.log")

    # csp test case
    if check_type == 'csp_check':
        cmd = r"./prj_gen --csp_project=true --csp_parameter_file={0} -n xxx 2> {1}".format(csp_json_path, log_path)
    elif check_type == 'bsp_check':
        try:
            prj_gen_path = os.environ['PRJ_GEN_PATH']
        except Exception as e:
            logging.error(": {0}".format(e))
        else:
            logging.debug("bsp prj_gen path : {}".format(prj_gen_path))
            os.chdir(Path(prj_gen_path))
            real_prj_gen_path = os.path.join(prj_gen_path, "prj_gen")
            cmd = r"{0} --bsp_project=true --bsp_parameter_file={1} -n xxx 2> {2}".format(real_prj_gen_path, csp_json_path, log_path)
    else:
        logging.error("Error env : {0}".format(prj_gen_path))
        sys.exit(1)

    execute_command(cmd)
    os.chdir(before)

    try:
        with open(log_path, "r") as f:
            log_info = f.readlines()
    except Exception as e:
        logging.error("Error message : {0}".format(e))
    else:
        for line in log_info:
            if line.find("Error") != -1 or line.find("error") != -1 or line.find("ERROR") != -1:
                logging.error(line)
            else:
                logging.debug(line)
