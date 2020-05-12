import logging
import os


def init_logger():
    log_format = "%(filename)s %(lineno)d %(levelname)s %(message)s "
    date_format = '%Y-%m-%d  %H:%M:%S %a '
    logging.basicConfig(level=logging.INFO,
                        format=log_format,
                        datefmt=date_format,
                        )


def main():
    env_list = os.environ
    IS_MASTER_REPO = env_list['IS_MASTER_REPO']
    print(IS_MASTER_REPO)
    IS_MASTER_REPO = env_list['HELLO']
    print(IS_MASTER_REPO)


if __name__ == "__main__":
    main()
