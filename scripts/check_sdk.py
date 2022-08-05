
import subprocess
import time
import logging
logging.getLogger().setLevel(logging.INFO)

def execute_command(cmd_string, cwd=None, shell=True):
    sub = subprocess.Popen(cmd_string, cwd=cwd, stdin=subprocess.PIPE,stderr=subprocess.PIPE,
                           stdout=subprocess.PIPE, shell=shell, bufsize=4096)
    stdout_str = ''
    while sub.poll() is None:
        err= sub.stderr.read()
        stdout_str += str(sub.stdout.read(), encoding="UTF-8")
        if len(err)>0:
            logging.info(err)
        time.sleep(0.1)
    return stdout_str

logging.info(execute_command("apt-get update && apt-get -y upgrade"))
logging.info(execute_command("python -m pip install --upgrade pip"))
logging.info(execute_command("pip install requests wget pyyaml jsonschema pytest pytest-sugar pytest-html rt-thread-studio"))


import os
import json
import logging
import requests
import sys
from jsonschema import RefResolver, Draft7Validator, FormatChecker
import yaml
from sdk_index_gen import generate_all_index,get_json_obj_from_file
from common_util import clear_dir, do_merge_copy, rename_dir_file,execute_command,download_retry,file_merge_unzip
from ci_config import INDEX_SERVER_URL,CSP_NANO_VERSION,CSP_RTT_VERSION
from gen_csp_json import gen_sdk_para_json_file
from gen_test_case import gen_sdk_test_case
from gen_bsp_json import gen_bsp_sdk_json
def run_id():
    if 'RUN_ID' in os.environ:
        return os.environ['RUN_ID']
    else:
        raise Exception("run_id is null")

def pr_index(prIndex):
    try:
        prid = run_id()
        logging.info("pr_id:"+prid)
        headers={"Content-Type":"application/json; charset=UTF-8"}
        url=INDEX_SERVER_URL+"/pr/"+prid
        response = requests.post(url,data=json.dumps(prIndex),headers=headers,timeout=60)
        if(response.status_code==404):
            raise Exception(response.status_code)
        else:
            logging.info("request-snapshot-Compeleted: {0}.".format(url))
            return json.loads(response.text)
    except Exception as e:
        logging.error("request-snapshot-Failed.")
        logging.error(e)
        sys.exit(1)

def index_schema_check(index_content):
    def get_schema_json_obj(path):
        return get_json_obj_from_file(os.path.join("/rt-thread/sdk-index/scripts/index_schema_check", path))

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


download_dir="/rt-thread/sdk-index/scripts/sdk_check/"
tempdir_folder="/rt-thread/sdk-index/scripts/temp_sdk/"

def init_dir():
    if not os.path.exists(download_dir):
        os.mkdir(download_dir)
    if not os.path.exists(tempdir_folder):
        os.mkdir(tempdir_folder)


def prepare_pkgs(changed_pkg_urls):
    #install pytest
    execute_command("chmod 777 "+download_dir)
    os.chdir(download_dir)
    #clear_dir(download_dir)
    #get backend
    try:
        print("download--backend.zip")
        download_retry("https://realthread-download.oss-cn-hangzhou.aliyuncs.com/rt-studio/backend/rt-studio-backend.zip",download_dir,"rt-studio-backend.zip")
    except Exception as e:
        sys.exit(1)
    #download the pkgs
    for zip_url in changed_pkg_urls:
        tmp = zip_url.split('/')
        pkgname = tmp[4]
        try:
            download_retry(zip_url,download_dir,pkgname)
            file_merge_unzip(pkgname,tempdir_folder)
        except Exception as e:
            logging.error(e)
            sys.exit(1)

def check_pkgs():
    list=os.walk(tempdir_folder)
    for path,dirs,files in list:
        for filename in files:
            if os.path.splitext(filename)[1] ==".yaml":
                yaml_file=os.path.join(path,filename)
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    content=f.read()
                    map = yaml.load(content,Loader=yaml.FullLoader)
                    
                    if 'pkg_type' in map.keys and map['pkg_type']=='Board_Support_Packages':
                        temp= str(map['template_projects'])
                        if "ToolChain_Support_Packages" not in temp:
                            os.environ['SDK_CHECK_TYPE'] = 'bsp_check'
                            pkg_vendor=map['pkg_vendor']
                            pkg_name=map['board']['name']
                            pkg_version=map['pkg_version']
                            check_bsp(path,pkg_vendor,pkg_name,pkg_version)
                        else:
                            #skip this bsp
                            logging.info("\n message : {0}. has thirdparty toolchain pkgs dependency. ci skipped".format(filename))
                    elif 'type' in map.keys and map['type']=='Chip_Support_Packages':
                        os.environ['SDK_CHECK_TYPE'] = 'csp_check'
                        check_csp(path)
                    else:
                        logging.info("\n message : {0}.is not a bsp or csp pkg. ci skipped".format(filename))
                        sys.exit(0)

def check_csp(csp_dir):
    logging.info("start-check-csp--"+csp_dir)
    workspace="/rt-thread/workspace"
    clear_dir(workspace)
    try:
        with open(r"/rt-thread/sdk-index/RT-Thread_Source_Code/index.json", "r") as f:
            sourcr_releases = json.loads(f.read())["releases"]
    except Exception as e:
        logging.error("\nError message : {0}.".format(e))
        sys.exit(1)
    nano_url = None
    released_url = None
    for release in sourcr_releases:
        if release["version"].find("nano-v"+CSP_NANO_VERSION) != -1:
            nano_url = release["url"]
        if release["version"].find(CSP_RTT_VERSION) != -1:
            released_url = release["url"]
    if not nano_url:
        logging.error("Can't find nano source url, please check RT-Thread_Source_Code/index.json file.")
        sys.exit(1)
    if not released_url:
        logging.error("Can't find released source url, please check RT-Thread_Source_Code/index.json file.")
        sys.exit(1)
    #check file
    nano_dir=os.path.join(download_dir,"nano-v"+CSP_NANO_VERSION)
    if not os.path.exists(nano_dir):
        download_retry(nano_url,download_dir,"nano-v"+CSP_NANO_VERSION)
        file_merge_unzip(nano_dir, csp_dir)
    rtt_dir=os.path.join(download_dir,CSP_RTT_VERSION)
    if not os.path.exists(rtt_dir):
        download_retry(released_url,download_dir,CSP_RTT_VERSION)
        file_merge_unzip(rtt_dir, csp_dir)

    gen_sdk_para_json_file(csp_dir, workspace)
    file_merge_unzip(os.path.join(download_dir,"rt-studio-backend.zip"), csp_dir)

    gen_sdk_test_case(csp_dir)
    subprocess.call("python "+csp_dir+"/sdk_test_case.py", shell=True)
    clear_dir(workspace)

def check_bsp(temp_bsp_dir,vendor,name,version):
    logging.info("start-check-bsp--"+temp_bsp_dir)
    workspace="/rt-thread/workspace"
    clear_dir(workspace)
    studio_plugin_dir="/RT-ThreadStudio/plugins/org.rt-thread.studio.project.gener/gener"
    if vendor is None or name is None or version is None:
        logging.error("pkg_vendor,pkg_version,board/name is required "+temp_bsp_dir)
        sys.exit(1)
    studio_bsp_pkg_dir= "/RT-ThreadStudio/repo/Extract/Board_Support_Packages/{0}/{1}/".format(vendor,name)
    studio_bsp_dir=studio_bsp_pkg_dir+version
    if not os.path.exists(studio_bsp_pkg_dir):
        os.makedirs(studio_bsp_pkg_dir)
    if not os.path.exists(studio_bsp_dir):
        do_merge_copy(temp_bsp_dir,studio_bsp_pkg_dir)
        rename_dir_file(studio_bsp_pkg_dir,temp_bsp_dir.split('/')[-1],version)
    if not os.path.exists(studio_plugin_dir):
        os.makedirs(studio_plugin_dir)
        file_merge_unzip(os.path.join(download_dir,"rt-studio-backend.zip"), studio_plugin_dir)

    gen_bsp_sdk_json(studio_bsp_dir,workspace)
    gen_sdk_test_case(studio_bsp_dir)
    subprocess.call("python "+studio_bsp_dir+"/sdk_test_case.py", shell=True)
    clear_dir(workspace)

def main():
    print(sys.argv)
    os.environ['RUN_ID']=sys.argv[1]
    init_dir()
    index=generate_all_index("/rt-thread/sdk-index/index.json")
    #check schema
    index_schema_check(index)
    #pr this Index
    changed_pkgs =pr_index(index)
    removes=changed_pkgs["del"]
    adds=changed_pkgs["add"]
    if len(removes)==0:
        if len(adds)==0:
            logging.info("no pkg changed")
            sys.exit(0)
        else:
            logging.info("download changed pkgs...")
            prepare_pkgs(adds)
            logging.info("start check...")
            #check the pkg
            check_pkgs()
    else:
        logging.info("Please do not delete the old release: "+str(removes))
        sys.exit(1)
    
if __name__ == "__main__":
    main()