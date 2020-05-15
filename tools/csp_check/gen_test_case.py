import os
import json
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
    with open("csp_test_case.py", "a") as f:
        f.write(test_case)


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
