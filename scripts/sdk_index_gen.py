
import os
import json
import logging
import requests
import urllib.error
import urllib.parse
import urllib.request
import sys
def get_json_obj_from_file(file):
    try:
        with open(file, 'r') as f:
            content = f.read()
        return json.loads(content)
    except Exception as e:
        logging.error("json-file-err:"+file +".please fix first")
        logging.error(e)
        sys.exit(1)

def write_json_to_file(json_content, file_name):
        with open(file_name, 'w', encoding='UTF-8') as f:
            f.write(json.dumps(json_content, indent=4))


def walk_all_folder(index_entry_file):
        index_entry = get_json_obj_from_file(index_entry_file)
        if "index" in index_entry:
            index_entry["children"] = list()
            logging.debug("index has index")
            for item in index_entry["index"]:
                abs_path = os.path.abspath(index_entry_file)
                next_entry_file = os.path.join(os.path.dirname(abs_path), item, "index.json")
                sub_index = walk_all_folder(next_entry_file)
                index_entry["children"].append(sub_index)

            index_entry.pop('index')

        return index_entry

def generate_all_index(index_entry_file):
        index_entry = walk_all_folder(index_entry_file)
        #write_json_to_file(index_entry, output_file_name)
        return index_entry

def packages_info_mirror_register(packages_json_file):
    with open(packages_json_file, 'rb') as f:
        json_content = f.read()

    package_json_register = json.loads(json_content.decode('utf-8'))
    package_json_register["name"] = "RT-Thread_Studio_" + package_json_register["name"]

    for item in package_json_register['releases']:
        url = item['url']

        if url.startswith('https://github.com/'):
            if url.endswith('.git'):
                # Git 仓库地址
                replace_url = url.replace('https://github.com', 'http://git-mirror.rt-thread.com:12236')
                item['url'] = replace_url
            elif '/releases/download/' in url:
                # GitHub Releases 附件下载地址
                # 格式: https://github.com/{owner}/{repo}/releases/download/{tag}/{filename}
                parts = url.split('/')
                owner = parts[3]
                repo = parts[4]
                tag = parts[7]
                filename = parts[8]
                
                # 转换为归档下载地址（更通用）
                replace_url = f"http://git-mirror.rt-thread.com:12236/{owner}/{repo}/archive/{tag}/{filename}"
                item['url'] = replace_url
                
            elif '/archive/' in url:
                # GitHub 源码归档地址（ZIP 格式）
                # 格式: https://github.com/{owner}/{repo}/archive/{tag}.zip
                replace_url = url.replace('https://github.com', 'http://git-mirror.rt-thread.com:12236')
                item['url'] = replace_url
            else:
                # 其他类型的 GitHub URL，保持原样或记录警告
                logging.warning(f"Unhandled GitHub URL pattern: {url}")
                # 可以选择跳过或者使用默认替换
                replace_url = url.replace('https://github.com', 'http://git-mirror.rt-thread.com:12236')
                item['url'] = replace_url

    payload_register = {
        "packages": [{}]
    }

    payload_register["packages"][0] = package_json_register

    data = json.dumps(payload_register).encode("utf-8")

    headers = {'content-type': 'application/json', 'Rt-Token':os.environ['MIRROR_REG_TOKEN']}
    request = urllib.request.Request(os.environ["MIRROR_REG_URL"], data, headers=headers)
    response = urllib.request.urlopen(request)
    resp = response.read()
    logging.info("{0} register successful.".format(package_json_register["name"]))
        

#for old sync type
def do_update_sdk_mirror_server_index():
        folder_walk_result = os.walk("..")
        err=''
        for path, d, filelist in folder_walk_result:
            for filename in filelist:
                if filename == 'index.json':
                    index_content = get_json_obj_from_file(os.path.join(path, filename))
                    if "releases" in index_content:
                        try:
                            packages_info_mirror_register(os.path.join(path, filename))
                        except Exception as e:
                            if err!="Error message3: {0}.".format(e):
                                err="Error message3: {0}.".format(e)
        if err!='':
            print('======>Software package registration failed.')
                        