# coding=utf-8
import sys
import os
import time
import subprocess
import urllib.request
import urllib.error
import urllib.parse
import json
import requests
import platform
import logging


class PackagesSync:

    def __init__(self, work_path_in, file_path_in, gitee_url_in, gitee_token_in, mirror_org_name):
        self.mirror_path = work_path_in
        self.mirror_file = file_path_in
        self.gitee_url = gitee_url_in
        self.gitee_token = gitee_token_in
        self.packages_index = None
        self.mirror_org_name = mirror_org_name
        print("Start synchronizing software packages.")

    @staticmethod
    def execute_command(cmdstring, cwd=None, timeout=None, shell=True):
        if shell:
            cmdstring_list = cmdstring

        sub = subprocess.Popen(cmdstring_list, cwd=cwd, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, shell=shell, bufsize=4096)

        stdout_str = ''
        while sub.poll() is None:
            # stdout_str += sub.stdout.read()
            time.sleep(0.1)

        return stdout_str

    def fetch_packages(self, package_json_path):
        """Read the git address information from the json file and download it to the local."""

        logging.info("======>Parse the %s file to get the package information." %
                     package_json_path[36:])
        package_json_file = open(package_json_path, 'rb')
        package_json_content = package_json_file.read()

        try:
            packages_json = json.loads(package_json_content.decode('utf-8'))
            json_reg = json.loads(package_json_content.decode('utf-8'))
        except Exception as e:
            logging.error("Error message: {0}.".format(e))

        # 将软件包信息注册到服务器
        self.packages_info_sync(json_reg)

        git_arr = []

        for item in packages_json['site']:
            url = item['URL']

            # 如果下载地址是一个 git 地址，那么从 git 上将软件包 clone 下来
            if url.endswith('.git'):
                if url in git_arr:  # 如果 URL 已经被下载过，那么就提示已经被更新
                    print('======>' + url[19:] +
                          ' do not need to download it again.')
                else:
                    # 如果没有被下载过，那么将下载链接加入到 git_arr 中，并克隆这个仓库
                    git_arr.append(url)
                    self.fetch_packages_from_git(url)
            else:
                # 下载地址是一个文件，不是一个以 git 为结尾的下载地址
                # self.fetch_packages_archive(URL)
                # [u'https:', u'', u'github.com', u'RT-Thread-packages', u'cJSON', u'archive', u'v1.0.1.zip']
                # [u'https:', u'', u'github.com', u'RT-Thread-packages', u'samples-1.0.0.zip']
                tmp = url.split('/')
                # 如果是一个 git 的 release 版本 zip 包
                if tmp[2] == 'github.com' and len(tmp) == 7 and tmp[5] == 'archive':
                    # print 'is github.com archive, try sync git'
                    # # 那么去同步这个 git 仓库
                    org = tmp[3]
                    repo = tmp[4]
                    repo_url = 'https://github.com/%s/%s.git'
                    repo_url = repo_url % (org, repo)
                    # print('repo_url: ' + repo_url)
                    if repo_url in git_arr:  # 如果已经被下载了，那么就提示已经被更新
                        print('======>' + repo_url +
                              ' do not need to download it again.')
                    else:
                        # 没有被下载，就克隆这个仓库
                        git_arr.append(repo_url)
                        self.fetch_packages_from_git(repo_url)

    def fetch_packages_from_git(self, packages_git_path):
        print('======>Fetch package from git repo :' + packages_git_path)
        # ['https:', '', 'github.com', 'RT-Thread-packages', 'cJSON.git']
        tmp = packages_git_path.split('/')

        # TODO
        org = tmp[3]
        repo = tmp[4]
        repo_name = repo.replace('.git', '')

        # 注册码云远程仓库
        self.create_repo_in_gitee(repo_name)

        # 从 github 上将软件包仓库 clone 到本地来
        org_path = os.path.join(self.mirror_path, org)
        if not os.path.exists(org_path):
            print('makdir -pv ' + org_path)
            os.makedirs(org_path)

        repo_path = os.path.join(org_path, repo_name)
        repo_submodule_file_path = os.path.join(repo_path, '.gitmodules')

        git_sh_path = os.path.join(os.getcwd(), 'git_get_branch.sh')
        git_repo_path = os.path.join(org_path, repo_name)
        logging.info(git_repo_path)

        # 如果仓库在本地不存在，那么重新克隆仓库并更新 submodule
        if not os.path.exists(repo_path):
            try:
                print('makdir -pv ' + repo_path)
                os.makedirs(repo_path)
                cmd = r'git clone %s %s'
                cmd = cmd % (packages_git_path, repo_name)
                print('======>Clone packages %s to local.' % repo_name)
                self.execute_command(cmd, cwd=org_path)

                print('git_repo_path : %s' % git_repo_path)

                cmd = r'cp %s .' % git_sh_path
                self.execute_command(cmd, cwd=git_repo_path)

                print('======>Start synchronizing multiple branches:')
                cmd = r'./git_get_branch.sh'
                if platform.architecture()[1] == 'WindowsPE':
                    cmd = r'.\git_get_branch.sh'
                self.execute_command(cmd, cwd=git_repo_path)
                print('======>Multi-branch synchronization is complete.')

                print('======>Start to fetch and pull Multi-branch.')
                try:
                    cmd = r'git fetch --all'
                    self.execute_command(cmd, cwd=git_repo_path)
                    cmd = r'git pull --all'
                    self.execute_command(cmd, cwd=git_repo_path)
                except Exception as e:
                    logging.error("Error message: {0}.".format(e))
                    print('error: repo : %s fetch and pull fail, wait for next update.' % repo_name)
                    return

                if os.path.isfile(repo_submodule_file_path):
                    cmd = r'git submodule init'
                    self.execute_command(cmd, cwd=repo_path)
                    cmd = r'git submodule update'
                    self.execute_command(cmd, cwd=repo_path)
            except Exception as e:
                logging.error("Error message: {0}.".format(e))
                print('error: repo : %s clone fail, wait for next update.' % repo_name)
                return
        else:
            # 如果本地已经有这个仓库,那么对仓库执行强制同步操作更新软件包，并更新子模块
            logging.info('======>Start to update local package {0} from github.'.format(repo_name))
            logging.info('git_repo_path : {0}'.format(git_repo_path))

            cmd = r'cp -a -f %s .' % git_sh_path
            self.execute_command(cmd, cwd=git_repo_path)

            print('======>Start synchronizing multiple branches:')

            cmd = r'./git_get_branch.sh'
            if platform.architecture()[1] == 'WindowsPE':
                cmd = r'.\git_get_branch.sh'
            self.execute_command(cmd, cwd=git_repo_path)

            print('======>Multi-branch synchronization is complete.')

            print('======>Start to fetch and pull Multi-branch.')

            try:
                cmd = r'git fetch --all'
                self.execute_command(cmd, cwd=git_repo_path)
                cmd = r'git pull --all'
                self.execute_command(cmd, cwd=git_repo_path)
                cmd = r'git fetch --tags'
                self.execute_command(cmd, cwd=git_repo_path)
            except Exception as e:
                logging.error("Error message: {0}.".format(e))
                print('error: repo : %s fetch and pull fail, wait for next update.' % repo_name)
                return

            logging.info('======>fetch and pull done.')

            if os.path.isfile(repo_submodule_file_path):
                cmd = r'git submodule init'
                self.execute_command(cmd, cwd=repo_path)
                cmd = r'git submodule update'
                self.execute_command(cmd, cwd=repo_path)

        # 如果已经下载好的软件包里面有 submodule,那么处理 submodule 的注册和同步
        if os.path.isfile(repo_submodule_file_path):
            self.submodule_sync(repo_submodule_file_path, git_sh_path)

        # 从本地仓库执行镜像操作到码云仓库中
        git_https_url = "%s/%s.git" % (self.gitee_url, repo_name)
        git_sslurl = self.https_url_to_ssh_url(git_https_url)

        print('======>Start to push local package %s to gitee.' % repo_name)
        cmd = r'git push --mirror --progress -v %s' % git_sslurl

        print('cmd: ' + cmd)

        self.execute_command(cmd, cwd=repo_path)
        print('======>Push done')

    @staticmethod
    def https_url_to_ssh_url(http_url):
        ssh_url = http_url.replace("https://gitee.com/", "git@gitee.com:")
        return ssh_url

    def fetch_packages_archive(self, path):
        print('fetch packages archive from ' + path)
        if not path.startswith('https://github.com/'):
            print('not github.com archive')
            return
        new_path = path.replace('https://github.com', self.mirror_file)
        # print(new_path)
        # print('dirname: ' + os.path.dirname(new_path))
        dirname = os.path.dirname(new_path)
        if not os.path.exists(dirname):
            print('makdir -pv ' + dirname)
            os.makedirs(dirname)
        cmd = r'wget -c ' + path
        print('cmd: ' + cmd)
        self.execute_command(cmd, cwd=dirname)

    def create_repo_in_gitee(self, repo_name):
        print("======>Start to create %s repo in gitee." % repo_name)
        send_data = "access_token=%s&name=%s" % (self.gitee_token, repo_name)
        send_url = "https://gitee.com/api/v5/orgs/%s/repos" % self.mirror_org_name

        try:
            request = urllib.request.Request(send_url, send_data.encode("utf-8"), {
                'content-type': 'application/x-www-form-urlencoded',
                'Connection': 'keep-alive',
                'Accept-Encoding': 'gzip, deflate',
                'Accept': '*/*',
                'User-Agent': 'curl/7.54.0'})

            response = urllib.request.urlopen(request)
            resp = response.read()
            print(resp)
        except Exception as e:
            logging.error("Error message: {0}.".format(e))


def get_access_token(token_payload):
    try:
        r = requests.post(
            "https://gitee.com/oauth/token", data=token_payload)

        if r.status_code == requests.codes.ok:
            package_info = json.loads(r.text)
            return package_info['access_token']

    except Exception as e:
        logging.error("Error message: {0}.".format(e))
        print('get access token fail')


def packages_info_register(packages_json):
    with open(packages_json, 'rb') as f:
        json_content = f.read()

    try:
        package_json_register = json.loads(json_content.decode('utf-8'))
    except Exception as e:
        logging.error("Error message: {0}.".format(e))

    logging.info(package_json_register)

    package_json_register["name"] = "RT-Thread_Studio_" + package_json_register["name"]

    for item in package_json_register['releases']:
        url = item['url']

        if url.startswith('https://github.com/'):
            if url.endswith('.git'):
                tmp = url.split('/')
                repo = tmp[4]
                replace_url = "https://gitee.com/RT-Thread-Studio-Mirror" + '/' + repo
                item['url'] = replace_url
            else:
                new_zip_url = url.replace('https://github.com', 'https://gitee.com')
                tmp = new_zip_url.split('/')
                tmp[3] = "RT-Thread-Studio-Mirror"
                tmp[5] = 'repository/archive'
                file_replace_url = '/'.join(tmp)
                item['url'] = file_replace_url

    print(package_json_register)

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
        request = urllib.request.Request("http://packages.rt-thread.org/packages", data, {
            'content-type': 'application/json'})
        response = urllib.request.urlopen(request)
        resp = response.read()
    except Exception as e:
        logging.error("Error message: {0}.".format(e))
        print('======>Software package registration failed.')
    else:
        logging.info("{0} register successful.".format(package_json_register["name"]))

