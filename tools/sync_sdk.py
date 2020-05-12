import os
import json
import logging
import requests


def is_master_repo():
    if 'IS_MASTER_REPO' in os.environ:
        return True
    else:
        return False


def update_sdk_index(new_index):
    if 'UPDATE_SDK_INDEX_ADDRESS' in os.environ:
        logging.info("Begin to update sdk index")
        try:
            r = requests.post(os.environ["UPDATE_SDK_INDEX_ADDRESS"], data=json.dumps(new_index))

            if r.status_code == requests.codes.ok:
                print("Update sdk index successful.")

        except Exception as e:
            print('Error message:%s' % e)
    else:
        logging.info("No need to update sdk index")


def sync_csp_packages(update_list):

    if is_master_repo():
        print("ready to sync csp packages")

    print(update_list)
