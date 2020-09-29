import os
import yaml
import json
import logging
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
}
"""


def init_logger():
    log_format = "[%(filename)s %(lineno)d %(levelname)s] %(message)s "
    date_format = '%Y-%m-%d  %H:%M:%S %a '
    logging.basicConfig(level=logging.INFO,
                        format=log_format,
                        datefmt=date_format,
                        )


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
        self.sub_series_dict = None
        self.chip_dict = None
        self.pack_dict = None
        self.cpu_info = None
        self.cpu_name = None
        self.__dsc2dict()

    def __dsc2dict(self):
        desc_file_path = None
        pack_dict = None
        for file in os.listdir(self.csp_path):
            if ".yaml" in file:
                desc_file_path = file
                with open(self.csp_path.joinpath(desc_file_path), mode='r', encoding="utf-8") as f:
                    data = f.read()
                pack_dict = yaml.load(data, Loader=yaml.FullLoader)
                break
        if not desc_file_path:
            for file in os.listdir(self.csp_path):
                if ".json" in file:
                    desc_file_path = file
                    with open(self.csp_path.joinpath(desc_file_path), mode='r', encoding="utf-8") as f:
                        data = f.read()
                    pack_dict = json.loads(data)
                    break
        if pack_dict:
            self.series_dict = pack_dict["series"]
        else:
            return False
        return True

    def get_cpu_name(self):

        if "cpu_info" in self.series_dict.keys():
            if isinstance(self.series_dict["cpu_info"], list):
                return self.series_dict["cpu_info"][0]["cpu_name"]

        elif "cpu_info" in self.sub_series_dict.keys():
            if isinstance(self.sub_series_dict["cpu_info"], list):
                return self.sub_series_dict["cpu_info"][0]["cpu_name"]

        elif "cpu_info" in self.chip_dict.keys():
            if isinstance(self.chip_dict["cpu_info"], list):
                return self.chip_dict["cpu_info"][0]["cpu_name"]

        return None

    def find__core_dict(self, item_in):
        if isinstance(item_in, dict):
            return item_in
        else:
            for dict_item in item_in:
                if dict_item["cpu_name"] == self.cpu_name:
                    return dict_item
            return None

    def arch_info(self):
        cpu_info = {}
        if self.cpu_name:
            if "cpu_info" in self.series_dict.keys():
                series_cpu_info = self.find__core_dict(self.series_dict["cpu_info"])
                cpu_info.update(series_cpu_info)
            if "cpu_info" in self.sub_series_dict.keys():
                sub_series_cpu_info = self.find__core_dict(self.sub_series_dict["cpu_info"])
                cpu_info.update(sub_series_cpu_info)
            if "cpu_info" in self.chip_dict.keys():
                chip_cpu_info = self.find__core_dict(self.chip_dict["cpu_info"])
                cpu_info.update(chip_cpu_info)
        else:
            if "cpu_info" in self.series_dict.keys():
                series_cpu_info = self.series_dict["cpu_info"]
                cpu_info.update(series_cpu_info)
            if "cpu_info" in self.sub_series_dict.keys():
                sub_series_cpu_info = self.sub_series_dict["cpu_info"]
                cpu_info.update(sub_series_cpu_info)
            if "cpu_info" in self.chip_dict.keys():
                chip_cpu_info = self.chip_dict["cpu_info"]
                cpu_info.update(chip_cpu_info)
        self.cpu_info = cpu_info
        return cpu_info

    @staticmethod
    def __fetch_obj_in_dict(dict_obj, index_list):
        for index in index_list:
            dict_obj = dict_obj[index]
        return dict_obj

    def walk_csp_chips(self):

        chip_test_list = dict()

        for subs in self.__fetch_obj_in_dict(self.series_dict, ["sub_series"]):
            # find sub_series
            self.sub_series_dict = subs

            for chip in subs["chips"]:
                self.chip_dict = chip
                self.cpu_name = self.get_cpu_name()
                self.arch_info()
                ui_dict = dict()
                if "ui" in self.chip_dict.keys():
                    if isinstance(self.chip_dict["ui"], list):
                        ui_dict = self.chip_dict["ui"][0]
                    else:
                        ui_dict = self.chip_dict["ui"]
                elif "ui" in self.sub_series_dict.keys():
                    if isinstance(self.sub_series_dict["ui"], list):
                        ui_dict = self.sub_series_dict["ui"][0]
                    else:
                        ui_dict = self.sub_series_dict["ui"]
                elif "ui" in self.series_dict.keys():
                    if isinstance(self.series_dict["ui"], list):
                        ui_dict = self.series_dict["ui"][0]
                    else:
                        ui_dict = self.series_dict["ui"]
                else:
                    logging.error("csp format wrong")
                uart_name = ui_dict["uart"]["default_value"]
                tx_pin = ui_dict["tx_pin"]["default_value"]
                rx_pin = ui_dict["rx_pin"]["default_value"]
                for project_type in ["bare_metal", "rtt_nano", "rtt"]:
                    main_c_file_tmp = Template(para_json_tmp)
                    wstrs = main_c_file_tmp.substitute(csp_path=Path(self.csp_path).as_posix(),
                                                       rtt_nano_path=Path(self.rtt_nano_path).as_posix(),
                                                       rtt_path=Path(self.rtt_path).as_posix(),
                                                       toolchain=self.toolchain_name,
                                                       project_type=project_type,
                                                       sub_series_name=subs['sub_series_name'],
                                                       chip_name=chip["chip_name"],
                                                       uart_name=uart_name,
                                                       tx_name=tx_pin,
                                                       rx_name=rx_pin,
                                                       clock=self.cpu_info["max_clock"][:-6],
                                                       project_name=chip["chip_name"] + project_type,
                                                       output_project_path=Path(self.output_project_path).as_posix())

                    dict_lit = json.loads(wstrs)
                    chip_test_list[
                        dict_lit["parameter"]["chip_name"] + dict_lit["parameter"]["project_type"]] = dict_lit

        return chip_test_list


def gen_sdk_para_json_file(csp_path, output_project_path, rt_thread_src):
    init_logger()
    rtt_nano_path = os.path.join(rt_thread_src, "sdk-rt-thread-nano-source-code-3.1.3")
    rtt_path = os.path.join(rt_thread_src, "sdk-rt-thread-source-code-4.0.2")
    toolchain_name = "gcc"
    try:
        para_generator = ParameterGenerator(csp_path,
                                            toolchain_name,
                                            rtt_nano_path,
                                            rtt_path,
                                            output_project_path)
        test_list = para_generator.walk_csp_chips()
        with open("csp_chips.json", "w", encoding="UTF8") as f:
            f.write(str(json.dumps(test_list, indent=4)))
    except Exception as e:
        logging.error("\nError message : {0}.".format(e))
        exit(1)
