import os
import time
import shutil
import logging
import subprocess


def execute_command(cmd_string, cwd=None, shell=True):
    """Execute the system command at the specified address."""

    sub = subprocess.Popen(cmd_string, cwd=cwd, stdin=subprocess.PIPE,stderr=subprocess.PIPE,
                           stdout=subprocess.PIPE, shell=shell, bufsize=4096)

    stdout_str = ''
    while sub.poll() is None:
        err= sub.stderr.read()
        if len(err)>0:
            return err
        stdout_str += str(sub.stdout.read(), encoding="UTF-8")
        time.sleep(0.1)

    return stdout_str


def do_copy_file(src, dst):
    if not os.path.exists(src):
        raise Exception("ERROR: Can’t get resource {0}, please check the resource.".format(src))

    file_dir_path = os.path.dirname(dst)
    if not os.path.exists(file_dir_path):
        os.makedirs(file_dir_path)

    try:
        shutil.copy2(src, dst)
    except Exception as e:
        logging.error("Error Message: {0}".format(e))
        raise Exception("ERROR: Can‘t copy resource {0}.".format(src))

    return True


def do_copy_folder(src_dir, dst_dir, ignore=None):
    if not os.path.exists(src_dir):
        raise Exception("ERROR: Can’t get resource {0}, please check the resource.".format(src_dir))

    try:
        shutil.copytree(src_dir, dst_dir, ignore=ignore)
    except Exception as e:
        logging.error("Error message: {0}".format(e))
        raise Exception("ERROR: Copy {0} failed.".format(src_dir))

    return True
