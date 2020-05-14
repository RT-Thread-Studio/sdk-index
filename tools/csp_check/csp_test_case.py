import logging
import os
import pytest
import shutil
import subprocess
import time


def init_logger():
    log_format = "%(filename)s %(lineno)d %(levelname)s %(message)s "
    date_format = '%Y-%m-%d  %H:%M:%S %a '
    logging.basicConfig(level=logging.INFO,
                        format=log_format,
                        datefmt=date_format,
                        )


if __name__ == "__main__":
    init_logger()
    pytest.main(["project_test.py", '--html=report.html', '--self-contained-html', '-n 2'])


def csp_test(project_name, json_name):
    gen_result = get_generate_result(json_name)
    if not gen_result:
        print("================>Project generate fails.")
        return gen_result

    cmd_pre = r"/rt-thread/eclipse/eclipse -nosplash --launcher.suppressErrors "\
              r"-application org.eclipse.cdt.managedbuilder.core.headlessbuild " \
              r"-data '/rt-thread/eclipse/workspace/{0}'".format(project_name)

    import_result = get_import_result(cmd_pre, project_name)
    if not import_result:
        print("================>Project import fails.")
        return import_result

    build_result = get_build_result(cmd_pre, project_name)

    if build_result:
        print("================>Project build success.")
    else:
        print("================>Project build fails.")

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
        print("generate err : {0}".format(result))
        return False


def get_import_result(cmd_pre, project_name):
    cmd = cmd_pre + ' -import "file:/rt-thread/workspace/{0}" 2> /dev/null'.format(project_name)
    result = execute_command(cmd)
    # print("import result : {0}".format(result))
    if result.find("Create") != -1:
        return True
    else:
        print("import err : {0}".format(result))
        return False


def get_build_result(cmd_pre, project_name):
    cmd = cmd_pre + " -cleanBuild '{0}' 2> /dev/null".format(project_name)
    result = execute_command(cmd)
    # print("build result : {0}".format(result))
    if result.find("Finished building target: rtthread.elf") != -1:
        return True
    else:
        print("build err : {0}".format(result))
        return False


def execute_command(cmd_string, cwd=None, shell=True):
    sub = subprocess.Popen(cmd_string, cwd=cwd, stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, shell=shell, bufsize=4096)
    stdout_str = ''
    while sub.poll() is None:
        stdout_str += str(sub.stdout.read(), encoding="utf-8")
        time.sleep(0.1)
    return stdout_str
