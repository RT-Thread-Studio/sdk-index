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
from common_util import clear_dir, execute_command,do_merge_copy

csp_json_name="csp_chips.json"
bsp_json_name="bsp_chips.json"
mcu_folder_name="mcu_config"
def gen_sdk_test_case(sdk_dir):
    generate_and_import_project(sdk_dir)
    mcu_config_path=os.path.join(sdk_dir,mcu_folder_name)
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
        if config_json.endswith('.json') and "smart" not in config_json:
            test_case += "\n" + test_case_format

    test_case_file=sdk_dir+"/sdk_test_case.py"
    do_merge_copy("/rt-thread/sdk-index/scripts/sdk_test_case.py",test_case_file)
    with open(test_case_file, "a") as f:
        f.write(test_case + '\n')
    main_func="""
        if __name__ == "__main__":
            exec_test_case('{0}')
    """.format(sdk_dir)
    main_func_content=textwrap.dedent(main_func)
    with open(test_case_file, "a") as f:
        f.write(main_func_content + '\n')

def find_mcu_in_json_file(sdk_dir):
    mcu_path=os.path.join(sdk_dir,mcu_folder_name)
    if os.path.exists(mcu_path):
        clear_dir(mcu_path)
    else:
        os.mkdir(mcu_path)
    json_name= bsp_json_name if os.environ['SDK_CHECK_TYPE']=="bsp_check" else csp_json_name
    with open(os.path.join(sdk_dir,json_name), 'r') as f:
        data = f.read()
    parameter_dict = json.loads(data)
    
    test_numbers = int(len(parameter_dict))
    if test_numbers > 80:
        test_numbers = 80
    mcu_dict = dict(random.sample(parameter_dict.items(), test_numbers))

    for mcu in mcu_dict:
        bare_metal_list = {"parameter": parameter_dict[mcu]["parameter"]}
        mcu_json = os.path.join(mcu_path, mcu + ".json")
        with open(mcu_json, "w") as f:
            f.write(str(json.dumps(bare_metal_list, indent=4)))
    # os.remove(json_path)


def generate_and_import_project(sdk_dir):
    find_mcu_in_json_file(sdk_dir)
    begin_time = time.time()
    logging.info("Project generate start.")
    project_number = 0
    mcu_path=os.path.join(sdk_dir,mcu_folder_name)
    for chip_json in os.listdir(mcu_path):
        if chip_json.endswith('.json') and "smart" not in chip_json:
            project_number += 1
            project_name = chip_json.split(".json")[0]
            json_path = os.path.join(sdk_dir, mcu_path, chip_json)
            logging.info("number : {1}, Project name : {0}.".format(project_name, project_number))
            get_generate_result(json_path,sdk_dir)
            logging.info("Project generate end, time consuming : {0}.".format(time.time() - begin_time))

    cmd_pre = r"/rt-thread/eclipse/eclipse -nosplash --launcher.suppressErrors "\
              r"-application org.eclipse.cdt.managedbuilder.core.headlessbuild " \
              r"-data '/rt-thread/eclipse/workspace'"
    cmd = cmd_pre + ' -importAll "file:/rt-thread/workspace" 2> /dev/null'

    logging.info("Project import start.")
    begin_time = time.time()
    subprocess.call(cmd, shell=True)
    logging.info("Project import end. time consuming : {0}.".format(time.time() - begin_time))


def get_generate_result(json_path,sdk_dir):
    # judge sdk update type (csp or bsp)
    try:
        check_type = os.environ['SDK_CHECK_TYPE']
    except Exception as e:
        logging.error(": {0}".format(e))

    logging.debug("project_json_info: {0}".format(check_type))
    logging.debug("json path : {0}".format(json_path))
    result = execute_command("cat {0}".format(json_path))
    logging.debug("cat {0} : {1}".format(json_path, result))
    log_path = os.path.join(sdk_dir, "generate.log")
    # csp test case
    if check_type == 'csp_check':
        #copy default template to mcu_config path
        default_templates=os.path.join(sdk_dir,"templates")
        mcu_path=os.path.join(sdk_dir,mcu_folder_name)
        do_merge_copy(default_templates,mcu_path)
        proj_gen=os.path.join(sdk_dir,"prj_gen")
        execute_command("chmod 777 "+sdk_dir+"/prj_gen")
        os.chdir(sdk_dir)
        cmd = r"{0} --csp_project=true --csp_parameter_file={1} -n xxx 2> {2}".format(proj_gen,json_path, log_path)
    elif check_type == 'bsp_check':
        proj_gen_path = "/RT-ThreadStudio/plugins/org.rt-thread.studio.project.gener/gener"
        proj_gen=os.path.join(proj_gen_path,"prj_gen")
        execute_command("chmod 777 "+proj_gen_path+"/prj_gen")
        os.chdir(Path(proj_gen_path))
        cmd = r"{0} --bsp_project=true --bsp_parameter_file={1} -n xxx 2> {2}".format(proj_gen,json_path, log_path)
    else:
        logging.error("invalid check type")
        sys.exit(1)
    execute_command(cmd)
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
