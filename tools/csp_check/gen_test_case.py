
import json
import os
import random
import textwrap


def find_mcu_in_json_file(json_path):
    with open(json_path, 'r') as f:
        data = f.read()
    parameter_dict = json.loads(data)
    os.mkdir("mcu_config")
    test_numbers = int(len(parameter_dict) * 0.1)
    print("test case numbers : {0}".format(test_numbers))
    mcu_dict = dict(random.sample(parameter_dict.items(), test_numbers))
    for mcu in mcu_dict:
        bare_metal_list = {"parameter": parameter_dict[mcu]["parameter"]}
        mcu_json = os.path.join("mcu_config", mcu + ".json")
        with open(mcu_json, "w") as f:
            f.write(str(json.dumps(bare_metal_list, indent=4)))
    os.remove(json_path)


def mcu_config_json(dir_path):
    json_path = None
    for s in os.listdir(dir_path):
        yield json_path
        json_path = os.path.join(dir_path, s)


file_head = """import os
import time
import shutil
import pytest
import subprocess


if __name__ == "__main__":
    pytest.main(["project_test.py", '-s', '--html=report.html --self-contained-html']) 
    
    
def execute_command(cmd_string, cwd=None, shell=True):
    sub = subprocess.Popen(cmd_string, cwd=cwd, stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, shell=shell, bufsize=4096)

    stdout_str = ''
    while sub.poll() is None:
        stdout_str += str(sub.stdout.read())
        time.sleep(0.1)
    return stdout_str


def get_generate_result(json_name):
    cmd = r"./prj_gen --csp_project=true --csp_parameter_file={0} -n xxx".format(json_name)
    result = execute_command(cmd)
    print("generate : {0}".format(result))
    if result.find("FileNotFoundError") != -1:
        return False
    else:
        return True


def get_import_result(cmd_pre, project_name):
    cmd = cmd_pre + ' -import "file:/rt-thread/workspace/{0}"'.format(project_name)
    result = execute_command(cmd)
    print("import : {0}".format(result))
    if result.find("can't be found!") != -1:
        return False
    else:
        return True
        
        
def get_build_result(cmd_pre, project_name):
    cmd = cmd_pre + " -cleanBuild '{0}'".format(project_name)
    result = execute_command(cmd)
    print("build : {0}".format(result))
    if result.find("Build Failed") != -1:
        return False
    else:
        return True


def csp_test(project_name, json_name):

    begin_time = time.time()
    
    result = get_generate_result(json_name)
    if not result:
        print("================>Project generate fails.")
        return result
        
    cmd_pre = r"/rt-thread/eclipse/eclipse -nosplash --launcher.suppressErrors " \\
              r"-application org.eclipse.cdt.managedbuilder.core.headlessbuild " \\
              r"-data '/rt-thread/eclipse/workspace/{0}'".format(project_name)
              
    result = get_import_result(cmd_pre, project_name)
    if not result:
        print("================>Project import fails.")
        return result

    result = get_build_result(cmd_pre, project_name)
    
    if result:
        print("================>Project build success.")
    else:
        print("================>Project build fails.")
        
    end_time = time.time()    
    print("time = {0}".format(end_time - begin_time))  
     
    import_project = "/rt-thread/eclipse/workspace/{0}".format(project_name)
    comp_project = "/rt-thread/workspace/{0}".format(project_name)

    shutil.rmtree(import_project)
    shutil.rmtree(comp_project)

    return result
"""


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
