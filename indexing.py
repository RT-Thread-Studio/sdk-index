#
# Copyright (c) 2006-2020, RT-Thread Development Team
#
# SPDX-License-Identifier: Apache-2.0
#
# Change Logs:
# Date           Author       Notes
# 2020-05-08     SummerGift   first version
#

import json
import logging
import os
from jsonschema import validate


def init_logger():
    log_format = "%(filename)s %(lineno)d <ignore> %(levelname)s %(message)s "
    date_format = '%Y-%m-%d  %H:%M:%S %a '
    logging.basicConfig(level=logging.DEBUG,
                        format=log_format,
                        datefmt=date_format,
                        )


class StudioSdkManagerIndex:
    def __init__(self, index):
        self.index_entry_file = index

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
        self.write_json_to_file(index_entry, file_name)
        return index_entry

    def index_schema_check(self, index_content, schema_format):
        schema = self.get_json_obj_from_file(schema_format)
        validate(instance=index_content, schema=schema)


def main():
    init_logger()
    generate_all_index = StudioSdkManagerIndex("index.json")
    index_content = generate_all_index.generate_all_index("index_all.json")
    generate_all_index.index_schema_check(index_content, "index_schema.json")


if __name__ == "__main__":
    main()
