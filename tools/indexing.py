#
# Copyright (c) 2006-2020, RT-Thread Development Team
#
# SPDX-License-Identifier: Apache-2.0
#
# Change Logs:
# Date           Author       Notes
# 2020-05-08     SummerGift   first version
# 2020-05-11     SummerGift   optimize schema checking
#

import json
import logging
import os
from jsonschema import RefResolver, Draft7Validator
import requests
from .package_sync import PackagesSync, get_access_token


def init_logger():
    log_format = "%(filename)s %(lineno)d %(levelname)s %(message)s "
    date_format = '%Y-%m-%d  %H:%M:%S %a '
    logging.basicConfig(level=logging.INFO,
                        format=log_format,
                        datefmt=date_format,
                        )


class StudioSdkManagerIndex:
    def __init__(self, index):
        self.index_entry_file = index
        self.index_all = ""

    @staticmethod
    def get_json_obj_from_file(file):
        with open(file, 'r') as f:
            content = f.read()
        return json.loads(content)

    @staticmethod
    def write_json_to_file(json_content, file_name):
        with open(file_name, 'w', encoding='UTF-8') as f:
            f.write(json.dumps(json_content, indent=4))

    @staticmethod
    def walk_all_folder(self, index_entry_file):
        logging.debug("index_entry_file {0}".format(index_entry_file))
        index_entry = self.get_json_obj_from_file(index_entry_file)

        if "index" in index_entry:
            index_entry["children"] = list()
            logging.debug("index has index")
            for item in index_entry["index"]:
                abs_path = os.path.abspath(index_entry_file)
                next_entry_file = os.path.join(os.path.dirname(abs_path), item, "index.json")
                sub_index = self.walk_all_folder(self, next_entry_file)
                index_entry["children"].append(sub_index)

            index_entry.pop('index')

        return index_entry

    def generate_all_index(self, file_name):
        index_entry = self.walk_all_folder(self, self.index_entry_file)
        self.index_all = index_entry
        self.write_json_to_file(index_entry, file_name)
        return index_entry

    def index_schema_check(self, index_content):
        def get_schema_json_obj(path):
            return self.get_json_obj_from_file(os.path.join("index_schema_check", path))

        index_all_schema = get_schema_json_obj("index_all_schema.json")
        rtt_source_schema = get_schema_json_obj("rtt_source_schema.json")
        rtt_source_releases_schema = get_schema_json_obj("rtt_source_releases_schema.json")
        csp_schema = get_schema_json_obj("csp_schema.json")
        csp_dvendor_schema = get_schema_json_obj("csp_dvendor_schema.json")
        csp_dvendor_package_schema = get_schema_json_obj("csp_dvendor_package_schema.json")
        csp_dvendor_package_releases_schema = get_schema_json_obj("csp_dvendor_package_releases_schema.json")

        schema_store = {
            index_all_schema['$id']: index_all_schema,
            rtt_source_releases_schema['$id']: rtt_source_releases_schema,
            rtt_source_schema['$id']: rtt_source_schema,
            csp_schema['$id']: csp_schema,
            csp_dvendor_schema['$id']: csp_dvendor_schema,
            csp_dvendor_package_schema['$id']: csp_dvendor_package_schema,
            csp_dvendor_package_releases_schema['$id']: csp_dvendor_package_releases_schema
        }

        resolver = RefResolver.from_schema(rtt_source_releases_schema, store=schema_store)
        validator = Draft7Validator(index_all_schema, resolver=resolver)
        validator.validate(index_content)
        logging.info("SDK index checking successful.")

    def get_last_index(self):
        response = requests.get("https://www.rt-thread.org/studio/sdkmanager/get/index")
        last_csp_list = json.loads(response.text)["children"][1]
        new_csp_list = self.index_all["children"][1]
        last_csp_list_str = json.dumps(last_csp_list, indent=4)
        new_csp_list_str = json.dumps(new_csp_list, indent=4)

        last_csp_list = list()
        for line in last_csp_list_str.splitlines():
            if line.find(".zip") != -1:
                url = line.strip()[line.strip().find("https"): line.strip().find(".zip") + 4]
                last_csp_list.append(url)
        logging.info(last_csp_list)

        new_csp_list = list()
        for line in new_csp_list_str.splitlines():
            if line.find(".zip") != -1:
                url = line.strip()[line.strip().find("https"): line.strip().find(".zip") + 4]
                new_csp_list.append(url)
        logging.info(new_csp_list)

        result = list(set(new_csp_list).difference(set(last_csp_list)))
        logging.info("packages need test and update: {0}".format(result))

        return result


class SdkSyncPackages:
    def __init__(self, update_list, new_index):
        self.update_list = update_list
        self.new_index = new_index

    @staticmethod
    def is_master_repo():
        if 'IS_MASTER_REPO' in os.environ:
            return True
        else:
            return False

    def do_sync_csp_packages(self):
        logging.info("update list: {0}".format(self.update_list))

        url = self.update_list[0]
        logging.info(url)

        tmp = url.split('/')
        logging.info(tmp)

        # # 1. get packages repository
        # work_path = r'sync_local_repo/github_mirror'
        # mirror_file = r'sync_local_repo/github_mirror_file'
        # gitee_url = 'https://gitee.com/RT-Thread-Studio-Mirror'
        # mirror_org_name = "RT-Thread-Studio-Mirror"
        #
        # token = get_access_token(os.environ["TOKEN_PAYLOAD"])
        # print("access token  : %s" % token)
        #
        # packages_update = PackagesSync(
        #     work_path, mirror_file, gitee_url, token, mirror_org_name)
        #
        # # 2. create new repo in gitee
        # packages_update.create_repo_in_gitee("sdk-debuger-jlink")
        #
        # # 3. clone package repo and push to gitee
        #
        # # 4. packages info register

    def sync_csp_packages(self):
        if self.is_master_repo():
            logging.info("Ready to sync csp packages")
            self.do_sync_csp_packages()
        else:
            logging.info("No need to sync csp packages")

    @staticmethod
    def do_update_sdk_index(index):
        headers = {
            "Content-Type": "application/json"
        }

        try:
            r = requests.post(os.environ["UPDATE_SDK_INDEX_ADDRESS"],
                              data=json.dumps(index),
                              headers=headers
                              )

            if r.status_code == requests.codes.ok:
                logging.info("Update sdk index successful.")
            else:
                logging.error("Error code {0}".format(r.status_code))

        except Exception as e:
            logging.error('Error message:%s' % e)

    def update_sdk_index(self):
        if 'UPDATE_SDK_INDEX_ADDRESS' in os.environ:
            logging.info("Begin to update sdk index")
            self.do_update_sdk_index(self.new_index)
        else:
            logging.info("No need to update sdk index")


def main():
    init_logger()
    generate_all_index = StudioSdkManagerIndex("../index.json")
    index_content = generate_all_index.generate_all_index("index_all.json")

    # 1. sdk index schema checking
    generate_all_index.index_schema_check(index_content)

    # 2. get packages need to test and sync
    update_list = generate_all_index.get_last_index()

    # 3. sync updated sdk package and sdk index
    sync = SdkSyncPackages(update_list, index_content)
    sync.sync_csp_packages()
    sync.update_sdk_index()


if __name__ == "__main__":
    main()
