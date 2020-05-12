import os


def is_master_repo():
    sys_environment = os.environ
    if 'IS_MASTER_REPO' in sys_environment:
        return True
    else:
        return False


