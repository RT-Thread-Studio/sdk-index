import os
import re
import sys
import json
import time
import random
import logging
import textwrap
import subprocess
import tempfile
from common_util import clear_dir, do_merge_copy

csp_json_name="csp_chips.json"
bsp_json_name="bsp_chips.json"
mcu_folder_name="mcu_config"

_ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")

# The generator can report an internal SCons failure but still exit with zero.
_GENERATION_ERROR_PATTERN = re.compile(
    r"^\s*(?:Traceback \(most recent call last\):"
    r"|(?:[\w.]*Error|Exception):"
    r"|scons:\s+\*\*\*"
    r"|(?:ERROR|FATAL|CRITICAL)(?:[:\s]|\[)"
    r"|\*\*(?:ERROR|FATAL|CRITICAL)\*\*:"
    r"|\[(?:ERROR|FATAL|CRITICAL)\])",
    re.MULTILINE,
)
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
    mcu_dict = dict(random.sample(list(parameter_dict.items()), test_numbers))

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


def _run_generator(command, cwd, log_path):
    # prj_gen can ignore SCons' return code. Give its SCons children a separate
    # status channel so a silent exit(1) cannot become a successful generation.
    with tempfile.TemporaryDirectory(prefix="sdk-index-scons-status-") as status_dir:
        status_path = os.path.join(status_dir, "failures")
        generator_env = os.environ.copy()
        generator_env["SDK_INDEX_SCONS_STATUS_FILE"] = status_path
        with open(log_path, "w", encoding="utf-8") as log_file:
            try:
                result = subprocess.run(
                    command, cwd=cwd, stdout=log_file, stderr=subprocess.STDOUT,
                    env=generator_env,
                )
            except OSError:
                logging.exception("Cannot run project generator: %s", command)
                raise

        scons_failures = []
        if os.path.exists(status_path):
            with open(status_path, "r", encoding="utf-8") as status_file:
                scons_failures = [line.strip() for line in status_file if line.strip()]

    with open(log_path, "r", encoding="utf-8", errors="replace") as log_file:
        output = log_file.read()

    normalized_output = _ANSI_ESCAPE_PATTERN.sub("", output)
    if scons_failures or result.returncode != 0 or _GENERATION_ERROR_PATTERN.search(normalized_output):
        if scons_failures:
            reason = "SCons exit code(s) {0}".format(", ".join(scons_failures))
        else:
            reason = ("exit code {0}".format(result.returncode)
                      if result.returncode else "fatal error in generator output")
        logging.error(
            "Project generation failed: %s.\nCommand: %s\nFull log (%s):\n%s",
            reason, command, log_path, output,
        )
        raise RuntimeError("Project generation failed ({0}); see {1}".format(reason, log_path))

    logging.debug("Project generation log (%s):\n%s", log_path, output)


def get_generate_result(json_path,sdk_dir):
    # judge sdk update type (csp or bsp)
    check_type = os.environ.get('SDK_CHECK_TYPE')
    json_path = os.path.abspath(json_path)
    sdk_dir = os.path.abspath(sdk_dir)

    logging.debug("project_json_info: {0}".format(check_type))
    logging.debug("json path : {0}".format(json_path))
    with open(json_path, "r", encoding="utf-8") as json_file:
        logging.debug("project parameters: %s", json_file.read())
    log_path = os.path.join(sdk_dir, "generate.log")
    # csp test case
    if check_type == 'csp_check':
        #copy default template to mcu_config path
        default_templates=os.path.join(sdk_dir,"templates")
        mcu_path=os.path.join(sdk_dir,mcu_folder_name)
        do_merge_copy(default_templates,mcu_path)
        proj_gen=os.path.join(sdk_dir,"prj_gen")
        generator_dir = sdk_dir
        cmd = [proj_gen, "--csp_project=true", "--csp_parameter_file=" + json_path, "-n", "xxx"]
    elif check_type == 'bsp_check':
        proj_gen_path = "/RT-ThreadStudio/plugins/org.rt-thread.studio.project.gener/gener"
        proj_gen=os.path.join(proj_gen_path,"prj_gen")
        generator_dir = proj_gen_path
        cmd = [proj_gen, "--bsp_project=true", "--bsp_parameter_file=" + json_path, "-n", "xxx"]
    else:
        logging.error("invalid check type")
        sys.exit(1)
    os.chmod(proj_gen, 0o777)
    _run_generator(cmd, generator_dir, log_path)
