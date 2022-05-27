# coding=utf-8
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

import os
import json
import logging
import requests
import urllib.error
import urllib.parse
import urllib.request
from jsonschema import RefResolver, Draft7Validator, FormatChecker
from package_sync import PackagesSync
import time

def init_logger():
    log_format = "[%(filename)s %(lineno)d %(levelname)s] %(message)s "
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
        validator = Draft7Validator(index_all_schema, resolver=resolver, format_checker=FormatChecker())
        validator.validate(index_content)
        logging.info("SDK index checking successful.")

    @staticmethod
    def get_differ_from_index(last_csp_list, new_csp_list):
        last_csp_list_str = json.dumps(last_csp_list, indent=4)
        new_csp_list_str = json.dumps(new_csp_list, indent=4)

        last_csp_list = list()
        for line in last_csp_list_str.splitlines():
            if line.find(".zip") != -1:
                url = line.strip()[line.strip().find("https"): line.strip().find(".zip") + 4]
                last_csp_list.append(url)
        logging.debug(last_csp_list)

        new_csp_list = list()
        for line in new_csp_list_str.splitlines():
            if line.find(".zip") != -1:
                url = line.strip()[line.strip().find("https"): line.strip().find(".zip") + 4]
                new_csp_list.append(url)
        logging.debug(new_csp_list)

        deleted_list = list(set(last_csp_list).difference(new_csp_list))
        if len(deleted_list) != 0:
            logging.info("Please do not delete the old release: "+str(deleted_list))
            exit(1)

        incleased_list = list(set(new_csp_list).difference(set(last_csp_list)))
        return incleased_list

    @staticmethod
    def csp_to_test(csp_result):

        if len(csp_result) == 0:
            logging.info("No need to test chip support package.")
            return
        # limit commit times
        if len(csp_result) != 1:
            logging.error("You commit {0} csp packages at one time.".format(len(csp_result)))
            logging.error("But you can commit only one csp package once, so you should modify the index you commit.")
            logging.error("Please check the list following:")
            logging.error(csp_result)
            exit(1)

        logging.info("csp update : {0}".format(csp_result))
        with open("csp_update_url.json", "w") as f:
            f.write(str(json.dumps(csp_result, indent=4)))

    @staticmethod
    def bsp_to_test(bsp_result):
        if len(bsp_result) == 0:
            logging.info("No need to test board support package.")
            return
        # limit commit times
        if len(bsp_result) != 1:
            logging.error("You commit {0} csp packages at one time.".format(len(bsp_result)))
            logging.error("But you can commit only one csp package once, so you should modify the index you commit.")
            logging.error("Please check the list following:")
            logging.error(bsp_result)
            exit(1)

        logging.info("bsp update : {0}".format(bsp_result))
        with open("bsp_update_url.json", "w") as f:
            f.write(str(json.dumps(bsp_result, indent=4)))

    def get_update_list(self):
        response = requests.get("https://api.rt-thread.org/studio/sdkmanager/get/index")

        # check chip update information
        csp_last_csp_list = json.loads(response.text)["children"][1]
        csp_new_csp_list = self.index_all["children"][1]
        csp_result = self.get_differ_from_index(csp_last_csp_list, csp_new_csp_list)
        self.csp_to_test(csp_result)

        # check board update information
        bsp_last_bsp_list = json.loads(response.text)["children"][2]
        bsp_new_bsp_list = self.index_all["children"][2]
        bsp_result = self.get_differ_from_index(bsp_last_bsp_list, bsp_new_bsp_list)
        self.bsp_to_test(bsp_result)

        # sdk package need to be update and sync
        last_sdk_list = json.loads(response.text)["children"]
        new_sdk_list = self.index_all["children"]
        result = self.get_differ_from_index(last_sdk_list, new_sdk_list)
        if len(result) == 0:
            logging.info("no packages need test and update: {0}".format(result))
        else:
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

        if len(self.update_list) == 0:
            logging.info("Update list is empty, no need to sync.")
            return
        for url in self.update_list:
        #url = self.update_list[0]
            logging.info(url)

            tmp = url.split('/')
            logging.info(tmp[4])

            # get packages repository
            work_path = r'sync_local_repo/github_mirror'
            mirror_file = r'sync_local_repo/github_mirror_file'
            mirror_url = 'https://gitee.com/RT-Thread-Studio-Mirror'
            mirror_org_name = "RT-Thread-Studio-Mirror"

            if 'GITEE_TOKEN' in os.environ:
                logging.info("Find sync token")
                token = os.environ['GITEE_TOKEN']
                packages_update = PackagesSync(
                    work_path, mirror_file, mirror_url, token, mirror_org_name)

                # create new repo in mirror
                packages_update.create_repo_in_gitee(tmp[4])

                # clone repo and push
                packages_update.fetch_packages_from_git(url)
            else:
                logging.info("No sync token")

    def sync_csp_packages(self):
        logging.info("Ready to sync csp or bsp packages")
        self.do_sync_csp_packages()

    @staticmethod
    def do_update_sdk_ide_index(index):
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

            r = requests.post(os.environ["UPDATE_SDK_ABROAD_INDEX_ADDRESS"],
                              data=json.dumps(index),
                              headers=headers
                              )

            if r.status_code == requests.codes.ok:
                logging.info("Update abroad sdk index successful.")
            else:
                logging.error("Error code {0}".format(r.status_code))

        except Exception as e:
            logging.error('Error message:%s' % e)

    @staticmethod
    def packages_info_mirror_register(packages_json_file):
        with open(packages_json_file, 'rb') as f:
            json_content = f.read()

        try:
            package_json_register = json.loads(json_content.decode('utf-8'))
        except Exception as e:
            logging.error("Error message: {0}.".format(e))

        package_json_register["name"] = "RT-Thread_Studio_" + package_json_register["name"]

        for item in package_json_register['releases']:
            url = item['url']

            if url.startswith('https://github.com/'):
                if url.endswith('.git'):
                    tmp = url.split('/')
                    repo = tmp[4]
                    replace_url = "https://gitee.com/RT-Thread-Studio-Mirror" + '/' + repo
                    item['url'] = replace_url

                    if url == "https://github.com/RT-Thread/rt-thread.git":
                        item['url'] = "https://gitee.com/rtthread/rt-thread.git"
                else:
                    new_zip_url = url.replace('https://github.com', 'https://gitee.com')
                    tmp = new_zip_url.split('/')
                    tmp[3] = "RT-Thread-Studio-Mirror"
                    tmp[5] = 'repository/archive'
                    file_replace_url = '/'.join(tmp)
                    item['url'] = file_replace_url

        logging.debug(package_json_register)

        payload_register = {
            "packages": [{}
                         ]
        }

        payload_register["packages"][0] = package_json_register

        try:
            data = json.dumps(payload_register).encode("utf-8")
        except Exception as e:
            logging.error("Error message: {0}.".format(e))

        try:
            headers = {'content-type': 'application/json', 'Rt-Token':os.environ['MIRROR_REG_TOKEN']}
            request = urllib.request.Request(os.environ["MIRROR_REG_URL"], data, headers=headers)
            response = urllib.request.urlopen(request)
            resp = response.read()
        except Exception as e:
            logging.error("Error message: {0}.".format(e))
            print('======>Software package registration failed.')
        else:
            logging.info("{0} register successful.".format(package_json_register["name"]))

    def do_update_sdk_mirror_server_index(self):
        folder_walk_result = os.walk("..")
        for path, d, filelist in folder_walk_result:
            for filename in filelist:
                if filename == 'index.json':
                    index_content = StudioSdkManagerIndex.get_json_obj_from_file(os.path.join(path, filename))
                    if "releases" in index_content:
                        self.packages_info_mirror_register(os.path.join(path, filename))

    def update_sdk_index(self):
        if 'UPDATE_SDK_INDEX_ADDRESS' in os.environ:
            logging.info("Begin to update sdk IDE index")
            self.do_update_sdk_ide_index(self.new_index)

            logging.info("Begin to update sdk mirror server index")
            self.do_update_sdk_mirror_server_index()
        else:
            logging.info("No need to update sdk index")

def main():
    init_logger()
    generate_all_index = StudioSdkManagerIndex("../index.json")
    index_content = generate_all_index.generate_all_index("index_all.json")

    # 1. sdk index schema checking
    generate_all_index.index_schema_check(index_content)

    # 2. get packages need to test and sync
    # if locked waiting until unlock or 30min later
    count=0
    while (get_merge_lock()=='true' and count<=30):
        logging.info("Merge is locked retrying in 10Secs...")
        time.sleep(10)
        count=count+1
    if(count>30):
        logging.info("Merge is locked more than 5min,skip the lock")
    
    update_list = generate_all_index.get_update_list()
    # 3. sync updated sdk package and sdk index
    sync = SdkSyncPackages(update_list, index_content)
    if sync.is_master_repo():
        set_merge_lock('true')
        logging.info("Merge Lock")
        try:
            sync.sync_csp_packages()
            sync.update_sdk_index()
            set_merge_lock('false')
            logging.info("Merge Unlock")
        except Exception as e:
            logging.error("Error message: {0}.".format(e))
            #set_merge_lock('false')
            logging.info("Merge Unlock")
            exit(1)
    else:
        logging.info("No need to sync csp or bsp packages")

def get_merge_lock():
    response = requests.get("https://api.rt-thread.org/studio/sdkmanager/mergelock")
    return response.text

def set_merge_lock(val):
    response = requests.get("https://api.rt-thread.org/studio/sdkmanager/mergelock/{0}".format(val))
    return response.text

if __name__ == "__main__":
    main()
