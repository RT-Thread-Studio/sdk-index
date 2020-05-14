# -*- coding: UTF-8 -*-
import os
import subprocess
from project_build import execute_command


def main():
    execute_command("apt update && apt -y upgrade && apt -y install unzip")
    execute_command("cd /rt-thread/sdk-index/tools/csp_check")
    execute_command("chmod 777 prj_gen")
    execute_command("pip install pyyaml")
    execute_command("pip install pytest-sugar")
    execute_command("pip install pytest-xdist")
    execute_command("python project_build.py")


if __name__ == '__main__':
    main()
