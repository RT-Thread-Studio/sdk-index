import logging
import os


def init_logger():
    log_format = "%(filename)s %(lineno)d %(levelname)s %(message)s "
    date_format = '%Y-%m-%d  %H:%M:%S %a '
    logging.basicConfig(level=logging.INFO,
                        format=log_format,
                        datefmt=date_format,
                        )


def is_master_repo():
    sys_environment = os.environ
    if 'IS_MASTER_REPO' in sys_environment:
        return True
    else:
        return False


def main():
    init_logger()

    if is_master_repo():
        print("ready to sync csp packages")


if __name__ == "__main__":
    main()
