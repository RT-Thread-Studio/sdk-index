import os
import json
import logging
from pathlib import Path
from check_tools import execute_command
from rt_thread_studio import bsp_parser
from rt_thread_studio import bsp_checker


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

    def get_csp_index_file_from_package(self, package):
        vendor_dirs = os.listdir(self.sdk_index_root_path.joinpath("Chip_Support_Packages"))
        for vendor_dir in vendor_dirs:
            if self.sdk_index_root_path.joinpath("Chip_Support_Packages", vendor_dir).is_dir():
                package_dirs = os.listdir(self.sdk_index_root_path.joinpath("Chip_Support_Packages", vendor_dir))
                for package_dir in package_dirs:
                    if self.sdk_index_root_path.joinpath("Chip_Support_Packages", vendor_dir, package_dir).is_dir():
                        if self.sdk_index_root_path.joinpath("Chip_Support_Packages", vendor_dir, package_dir,
                                                             "index.json").exists():
                            with open(
                                    self.sdk_index_root_path.joinpath("Chip_Support_Packages", vendor_dir, package_dir,
                                                                      "index.json"), "r") as f:
                                csp_index_dict = json.loads(f.read())
                                if csp_index_dict["name"] == package["package_name"] and csp_index_dict["vendor"] == \
                                        package["package_vendor"]:
                                    logging.info(
                                        self.sdk_index_root_path.joinpath("Chip_Support_Packages", vendor_dir,
                                                                          package_dir,
                                                                          "index.json"))
                                    return self.sdk_index_root_path.joinpath("Chip_Support_Packages", vendor_dir,
                                                                             package_dir, "index.json")
                        else:
                            continue
                    else:
                        continue
            else:
                continue

    def download_all_external_package(self, external_package_list):
        rt_studio_install_path = Path("/RT-ThreadStudio")
        rt_studio_repo_path = rt_studio_install_path.joinpath("repo/Extract")
        for package in external_package_list:
            if package["package_type"] == "RT-Thread_Source_Code":
                index_file_path = self.get_rtt_source_code_index_file_from_package()
                url = self.get_url_from_index_file(index_file_path, package["package_version"])
                if package["package_version"] == "latest":
                    before = os.getcwd()
                    cmd = 'git clone ' + url
                    logging.info(rt_studio_repo_path.joinpath(package["package_relative_path"]))
                    logging.info(cmd)
                    if self.is_in_linux:
                        if not rt_studio_repo_path.joinpath(package["package_relative_path"]).exists():
                            os.makedirs(rt_studio_repo_path.joinpath(package["package_relative_path"]))
                        os.chdir(rt_studio_repo_path.joinpath(package["package_relative_path"]))
                        execute_command(cmd)
                        os.chdir(before)
                else:
                    zip_name = url.split("/")[-1]
                    pack_folder = rt_studio_repo_path.joinpath(package["package_relative_path"])
                    zip_path = pack_folder.joinpath(zip_name)

                    # create dir
                    os.makedirs(pack_folder)
                    cmd = "wget -nv -O " + str(zip_path.as_posix()) + " " + url
                    logging.info(cmd)
                    if self.is_in_linux:
                        execute_command(cmd)

                    cmd = "unzip " + str(zip_path.as_posix()) + " -d " + str(pack_folder.as_posix())
                    logging.info(cmd)
                    if self.is_in_linux:
                        execute_command(cmd)
                    for dir in os.listdir(pack_folder):
                        if dir.find("sdk") != -1:
                            sdk_path = os.path.join(pack_folder, dir)
                            logging.debug("sdk path : {0}".format(sdk_path))
                            execute_command("mv {0}/* {1}".format(sdk_path, pack_folder))
                            logging.debug("pack folder : {0}".format(pack_folder))
                            execute_command("rm -rf {0}".format(sdk_path))
                            break

                    cmd = "rm -rf " + str(zip_path.as_posix())
                    logging.info(cmd)
                    if self.is_in_linux:
                        execute_command(cmd)

            elif package["package_type"].strip() == "Chip_Support_Packages":
                index_file_path = self.get_csp_index_file_from_package(package)
                url = self.get_url_from_index_file(index_file_path, package["package_version"])
                zip_name = url.split("/")[-1]
                pack_folder = rt_studio_repo_path.joinpath(package["package_relative_path"])
                os.makedirs(pack_folder)
                zip_path = pack_folder.joinpath(zip_name)
                cmd = "wget -nv -O " + str(zip_path.as_posix()) + " " + url
                logging.info(cmd)
                if self.is_in_linux:
                    execute_command(cmd)

                cmd = "unzip " + str(zip_path.as_posix()) + " -d " + str(pack_folder.as_posix())
                logging.info(cmd)
                if self.is_in_linux:
                    execute_command(cmd)
                for dir in os.listdir(pack_folder):
                    if dir.find("sdk") != -1:
                        sdk_path = os.path.join(pack_folder, dir)
                        logging.debug("sdk path : {0}".format(sdk_path))
                        execute_command("mv {0}/* {1}".format(sdk_path, pack_folder))
                        logging.debug("pack folder : {0}".format(pack_folder))
                        execute_command("rm -rf {0}".format(sdk_path))
                        break

                cmd = "rm -rf " + str(zip_path.as_posix())
                logging.info(cmd)
                if self.is_in_linux:
                    execute_command(cmd)
            else:
                pass


def gen_bsp_sdk_json(bsp_path, index_path, output_path):
    index_root_path = index_path

    parser = bsp_parser.BspParser(bsp_path)
    sdk_indexer = SdkIndex(index_root_path)

    external_package_list = parser.get_external_package_list()
    sdk_indexer.download_all_external_package(external_package_list)
    bsp_json_file = parser.generate_bsp_project_create_json_input(output_path)
    root_path = os.getcwd()
    bsp_chip_json_path = os.path.join(root_path, "bsp_chips.json")
    try:
        with open(bsp_chip_json_path, "w", encoding="UTF8") as f:
            f.write(str(json.dumps(bsp_json_file, indent=4)))
    except Exception as e:
        logging.error("\nError message : {0}.".format(e))
        exit(1)


if __name__ == "__main__":
    # prg_gen should be @ "/RT-ThreadStudio/plugins/gener/"
    gen_bsp_sdk_json()
