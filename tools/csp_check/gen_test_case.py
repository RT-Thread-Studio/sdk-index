# -*- coding: UTF-8 -*-
import json
import os
import random
import textwrap


def gen_chip_test_case(test_list_path, mcu_config_path):

    find_mcu_in_json_file(test_list_path)
    test_case = ''

    for chip_json in os.listdir(mcu_config_path):
        project_name = chip_json.split(".json")[0]
        json_path = os.path.join(mcu_config_path, chip_json)
        test_case_example = """ 
                def test_{0}():
                    assert csp_test("{0}", "{1}") is True
                """.format(project_name, json_path)
        test_case_format = textwrap.dedent(test_case_example)
        test_case += "\n" + test_case_format
    with open("project_test.py", "w") as f:
        f.write(file_head + test_case)


def find_mcu_in_json_file(json_path):
    with open(json_path, 'r') as f:
        data = f.read()
    parameter_dict = json.loads(data)
    os.mkdir("mcu_config")
    test_numbers = int(len(parameter_dict))
    if test_numbers > 30:
        test_numbers = 30
    mcu_dict = dict(random.sample(parameter_dict.items(), test_numbers))
    for mcu in mcu_dict:
        bare_metal_list = {"parameter": parameter_dict[mcu]["parameter"]}
        mcu_json = os.path.join("mcu_config", mcu + ".json")
        with open(mcu_json, "w") as f:
            f.write(str(json.dumps(bare_metal_list, indent=4)))
    os.remove(json_path)


file_head = """# -*- coding: UTF-8 -*-
import os
import time
import shutil
import pytest
import logging
import subprocess

 
def init_logger():
    log_format = "%(filename)s %(lineno)d %(levelname)s %(message)s "
    date_format = '%Y-%m-%d  %H:%M:%S %a '
    logging.basicConfig(level=logging.INFO,
                        format=log_format,
                        datefmt=date_format,
                        )

        
def execute_command(cmd_string, cwd=None, shell=True):
    sub = subprocess.Popen(cmd_string, cwd=cwd, stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, shell=shell, bufsize=4096)
    stdout_str = ''
    while sub.poll() is None:
        stdout_str += str(sub.stdout.read(), encoding="utf-8")
        time.sleep(0.1)
    return stdout_str


def get_generate_result(json_name):
    cmd = r"./prj_gen --csp_project=true --csp_parameter_file={0} -n xxx".format(json_name)
    result = execute_command(cmd)
    logging.info("\\ngenerate result : {0}".format(result))
    if not result:
        return False
    else:
        return True


def get_import_result(cmd_pre, project_name):
    cmd = cmd_pre + ' -import "file:/rt-thread/workspace/{0}"'.format(project_name)
    result = execute_command(cmd)
    if not result:
        return False
    else:
        return True
        
        
def get_build_result(cmd_pre, project_name):
    cmd = cmd_pre + " -cleanBuild '{0}'".format(project_name)
    result = execute_command(cmd)
    if not result:
        return False
    else:
        return True


def init_logger():
    log_format = "%(filename)s %(lineno)d %(levelname)s %(message)s "
    date_format = '%Y-%m-%d  %H:%M:%S %a '
    logging.basicConfig(level=logging.INFO,
                        format=log_format,
                        datefmt=date_format,
                        )
                        

def csp_test(project_name, json_name):

    gen_result = get_generate_result(json_name)
    if not gen_result:
        logging.info("================>Project generate fails.")
        return gen_result
        
    cmd_pre = r"/rt-thread/eclipse/eclipse -nosplash --launcher.suppressErrors " \\
              r"-application org.eclipse.cdt.managedbuilder.core.headlessbuild " \\
              r"-data '/rt-thread/eclipse/workspace/{0}'".format(project_name)
              
    import_result = get_import_result(cmd_pre, project_name)
    if not import_result:
        logging.info("================>Project import fails.")
        return import_result

    build_result = get_build_result(cmd_pre, project_name)
    
    if build_result:
        logging.info("================>Project build success.")
    else:
        logging.info("================>Project build fails.")
        
    import_project = "/rt-thread/eclipse/workspace/{0}".format(project_name)
    comp_project = "/rt-thread/workspace/{0}".format(project_name)

    shutil.rmtree(import_project)
    shutil.rmtree(comp_project)

    return result


if __name__ == "__main__":
    init_logger()
    pytest.main(["project_test.py", '-q', '--html=report.html', '--self-contained-html', '--tb=no', '--capture=sys']) 
    
"""
