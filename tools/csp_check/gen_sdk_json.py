# -*- coding: UTF-8 -*-
import json
import logging
import os
import yaml
from pathlib import Path
from string import Template

para_json_tmp = """
{
 "parameter": {
   "csp_path": "$csp_path",
   "rtt_nano_path": "$rtt_nano_path",
   "rtt_path": "$rtt_path",
   "tool_chain": "$toolchain",
   "project_type": "$project_type",
   "sub_series_name": "$sub_series_name",
   "chip_name": "$chip_name",
   "uart_name": "$uart_name",
   "tx_pin_name": "$tx_name",
   "rx_pin_name": "$rx_name",
   "clock_source": "hsi",
   "source_freq": "8",
   "target_freq": "$clock",
   "project_name": "$project_name",
   "output_project_path": "$output_project_path"
   }
}"""


class ParameterGenerator(object):
    """
    This is the project generator class, it contains the basic parameters and methods in all type of projects
    """

    def __init__(self,
                 csp_path,
                 toolchain_name,
                 rtt_nano_path,
                 rtt_path,
                 output_project_path,
                 parent=None):
        self.csp_path = Path(csp_path)
        self.toolchain_name = toolchain_name
        self.rtt_nano_path = rtt_nano_path
        self.rtt_path = rtt_path
        self.output_project_path = output_project_path
        self.series_dict = None
        self.pack_dict = None
        self.__dsc2dict()

    def __dsc2dict(self):
        desc_file_path = None
        pack_dict = None
        for file in os.listdir(self.csp_path):
            if ".yaml" in file:
                desc_file_path = file
                with open(self.csp_path.joinpath(desc_file_path), mode='r', encoding="UTF8") as f:
                    data = f.read()
                pack_dict = yaml.load(data, Loader=yaml.FullLoader)
                break
        if not desc_file_path:
            for file in os.listdir(self.csp_path):
                if ".json" in file:
                    desc_file_path = file
                    with open(self.csp_path.joinpath(desc_file_path), mode='r') as f:
                        data = f.read()
                    pack_dict = json.loads(data)
                    break
        if pack_dict:
            self.series_dict = pack_dict["series"]
        else:
            return False
        return True

    @staticmethod
    def __fetch_obj_in_dict(dict_obj, index_list):
        for index in index_list:
            dict_obj = dict_obj[index]
        return dict_obj

    def walk_csp_chips(self):

        chip_test_list = dict()

        for subs in self.__fetch_obj_in_dict(self.series_dict, ["sub_series"]):
            # if not Path(subs['sub_series_name']).exists():
            #     os.mkdir(subs['sub_series_name'])

            for chip in subs["chips"]:
                chip_folder_path = Path(subs['sub_series_name']).joinpath(chip["chip_name"])

                # if not chip_folder_path.exists():
                #     os.mkdir(chip_folder_path)

                for project_type in ["bare_metal", "rtt_nano", "rtt"]:
                    main_c_file_tmp = Template(para_json_tmp)
                    wstrs = main_c_file_tmp.substitute(csp_path=Path(self.csp_path).as_posix(),
                                                       rtt_nano_path=Path(self.rtt_nano_path).as_posix(),
                                                       rtt_path=Path(self.rtt_path).as_posix(),
                                                       toolchain=self.toolchain_name,
                                                       project_type=project_type,
                                                       sub_series_name=subs['sub_series_name'],
                                                       chip_name=chip["chip_name"],
                                                       uart_name="uart1",
                                                       tx_name="pa9",
                                                       rx_name="pa10",
                                                       clock=subs["cpu_info"]["max_clock"][:-6],
                                                       project_name=chip["chip_name"] + project_type,
                                                       output_project_path=Path(self.output_project_path).as_posix())

                    dict_lit = json.loads(wstrs)
                    chip_test_list[dict_lit["parameter"]["chip_name"] +
                                   dict_lit["parameter"]["project_type"]] = dict_lit

        return chip_test_list


def gen_sdk_para_json_file(csp_path, output_project_path, rt_thread_src):
    rtt_nano_path = os.path.join(rt_thread_src, "sdk-rt-thread-nano-source-code-3.1.3")
    rtt_path = os.path.join(rt_thread_src, "sdk-rt-thread-source-code-4.0.2")
    toolchain_name = "gcc"

    para_generator = ParameterGenerator(csp_path,
                                        toolchain_name,
                                        rtt_nano_path,
                                        rtt_path,
                                        output_project_path)
    test_list = para_generator.walk_csp_chips()
    with open("csp_chips.json", "w", encoding="UTF8") as f:
        f.write(str(json.dumps(test_list, indent=4)))
