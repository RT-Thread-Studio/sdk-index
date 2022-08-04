import os
import json
import logging
from pathlib import Path
from common_util import clear_dir, execute_command, git_clone_retry
from rt_thread_studio import bsp_parser
from rt_thread_studio import bsp_checker
from common_util import download_retry
from common_util import file_merge_unzip

class SdkIndex(object):
    """
    This is the project generator class, it contains the basic parameters and methods in all type of projects
    """

    def __init__(self,
                 sdk_index_root_path):
        self.sdk_index_root_path = Path(sdk_index_root_path)
        if os.name == "nt":
            self.is_in_linux = False
        else:
            self.is_in_linux = True

    def get_rtt_source_code_index_file_from_package(self):
        return self.sdk_index_root_path.joinpath("RT-Thread_Source_Code", "index.json")

    def get_url_from_index_file(self, index_file, package_version):
        with open(index_file, "r") as f:
            index_dict = json.loads(f.read())
            all_releases = index_dict["releases"]
            for release in all_releases:
                if release["version"] == package_version:
                    return release["url"]
            return ""

    def download_all_external_package(self, external_package_list):
        rt_studio_install_path = Path("/RT-ThreadStudio")
        rt_studio_repo_path = rt_studio_install_path.joinpath("repo/Extract")
        for package in external_package_list:
            if package["package_type"] == "RT-Thread_Source_Code":
                index_file_path = self.get_rtt_source_code_index_file_from_package()
                url = self.get_url_from_index_file(index_file_path, package["package_version"])
                if package["package_version"] == "latest":
                    if self.is_in_linux:
                        if not rt_studio_repo_path.joinpath(package["package_relative_path"]).exists():
                            os.makedirs(rt_studio_repo_path.joinpath(package["package_relative_path"]))
                        latest_folder=rt_studio_repo_path.joinpath(package["package_relative_path"])
                        if not os.path.exists(latest_folder):
                            os.makedirs(latest_folder)
                            git_clone_retry(url,latest_folder)
                else:
                    version = os.path.splitext(url.split("/")[-1])[0]
                    pack_folder = rt_studio_repo_path.joinpath(package["package_relative_path"])
                    if not os.path.exists(pack_folder):
                        download_retry(url,pack_folder,"rtt-src.zip")
                        folder=pack_folder.parent.as_posix()+"/"
                        file_merge_unzip(os.path.join(folder,"rtt-src.zip"),folder)
                        os.chdir(folder)
                        execute_command("mv {0} {1}".format("sdk-rt-thread-source-code-"+version,version))
                        execute_command("rm -f {0}".format("rtt-src.zip"))
            else:
                pass


def gen_bsp_sdk_json(bsp_path,workspace):
    parser = bsp_parser.BspParser(bsp_path)
    sdk_indexer = SdkIndex("/rt-thread/sdk-index/")
    external_package_list = parser.get_external_package_list()
    sdk_indexer.download_all_external_package(external_package_list)
    bsp_json_file = parser.generate_bsp_project_create_json_input(workspace)
    bsp_chip_json_path = os.path.join(bsp_path, "bsp_chips.json")
    try:
        with open(bsp_chip_json_path, "w", encoding="UTF8") as f:
            f.write(str(json.dumps(bsp_json_file, indent=4)))
    except Exception as e:
        logging.error("\nError message : {0}.".format(e))
        exit(1)


if __name__ == "__main__":
    # prg_gen should be @ "/RT-ThreadStudio/plugins/gener/"
    gen_bsp_sdk_json()
