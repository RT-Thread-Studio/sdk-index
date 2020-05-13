# -*- coding: UTF-8 -*-
import os


def main():
    os.system("apt update && apt -y upgrade && apt -y install unzip")
    os.chdir("/rt-thread/sdk-index/tools/csp_check")
    os.system("chmod 777 prj_gen")
    os.system("pip install pyyaml")
    os.system("pip install pytest-sugar")
    os.system("python project_build.py")


if __name__ == '__main__':
    main()
