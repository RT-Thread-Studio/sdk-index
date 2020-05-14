import logging
import os
import pytest
import shutil
import subprocess
import time
from csp_check import execute_command


def init_logger():
    log_format = "%(filename)s %(lineno)d %(levelname)s %(message)s "
    date_format = '%Y-%m-%d  %H:%M:%S %a '
    logging.basicConfig(level=logging.INFO,
                        format=log_format,
                        datefmt=date_format,
                        )


if __name__ == "__main__":
    init_logger()
    pytest.main(["csp_test_case.py", '--html=report.html', '--self-contained-html'])


def csp_test(project_name, json_name):
    gen_result = get_generate_result(json_name)
    if not gen_result:
        logging.error("================>Project generate fails.")
        return gen_result

    cmd_pre = r"/rt-thread/eclipse/eclipse -nosplash --launcher.suppressErrors "\
              r"-application org.eclipse.cdt.managedbuilder.core.headlessbuild " \
              r"-data '/rt-thread/eclipse/workspace/{0}'".format(project_name)

    import_result = get_import_result(cmd_pre, project_name)
    if not import_result:
        logging.error("================>Project import fails.")
        return import_result

    build_result = get_build_result(cmd_pre, project_name)

    if build_result:
        logging.info("================>Project build success.")
    else:
        logging.error("================>Project build fails.")

    import_project = "/rt-thread/eclipse/workspace/{0}".format(project_name)
    comp_project = "/rt-thread/workspace/{0}".format(project_name)

    shutil.rmtree(import_project)
    shutil.rmtree(comp_project)

    return build_result


def get_generate_result(json_name):
    cmd = r"./prj_gen --csp_project=true --csp_parameter_file={0} -n xxx 2> /dev/null".format(json_name)
    result = execute_command(cmd)
    # print("generate result : {0}".format(result))
    if result:
        return True
    else:
        logging.error("\ngenerate result : {0}".format(result))
        return False


def get_import_result(cmd_pre, project_name):
    cmd = cmd_pre + ' -import "file:/rt-thread/workspace/{0}" 2> /dev/null'.format(project_name)
    result = execute_command(cmd)
    if result.find("Create") != -1:
        return True
    else:
        logging.error("\nimport result : {0}".format(result))
        return False


def get_build_result(cmd_pre, project_name):
    cmd = cmd_pre + " -cleanBuild '{0}' 2> /dev/null".format(project_name)
    result = execute_command(cmd)
    if result.find("Finished building target: rtthread.elf") != -1:
        return True
    else:
        logging.error("\nbuild result : {0}".format(result))
        return False
