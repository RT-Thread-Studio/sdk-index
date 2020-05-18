# coding=utf-8
#
# Copyright (c) 2006-2020, RT-Thread Development Team
#
# SPDX-License-Identifier: Apache-2.0
#
# Change Logs:
# Date           Author       Notes
# 2020-05-12     SummerGift   first version
# 2020-05-14     SummerGift   add package sync
#

import os
import time
import subprocess
import urllib.request
import urllib.error
import urllib.parse
import json
import requests
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
            cmd_string_list = cmdstring

        sub = subprocess.Popen(cmd_string_list, cwd=cwd, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, shell=shell, bufsize=4096)

        stdout_str = ''
        while sub.poll() is None:
            time.sleep(0.1)

        return stdout_str

    def fetch_packages_from_git(self, archive_path):
        print('======>Fetch package from git repo :' + archive_path)

        url = archive_path[:archive_path.find("/archive")]
        git_path = url + ".git"
        tmp = url.split('/')
        org = tmp[3]
        repo = tmp[4]
        repo_name = repo

        org_path = os.path.join(self.mirror_path, org)
        if not os.path.exists(org_path):
            print('makdir -pv ' + org_path)
            os.makedirs(org_path)

        git_repo_path = os.path.join(org_path, repo_name)
        logging.info(git_repo_path)

        repo_path = os.path.join(org_path, repo_name)
        if not os.path.exists(repo_path):
            try:
                print('makdir -pv ' + repo_path)
                os.makedirs(repo_path)

                cmd = r'git clone %s %s'
                cmd = cmd % (git_path, repo_name)
                print('======>Clone packages %s to local.' % repo_name)
                self.execute_command(cmd, cwd=org_path)
                print('git_repo_path : %s' % git_repo_path)

                cmd = r"""git branch -r | grep -v '\->' | while read remote; do git branch --track "${remote#origin/}" 
                "$remote"; done"""
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

            except Exception as e:
                logging.error("Error message: {0}.".format(e))
                print('error: repo : %s clone fail, wait for next update.' % repo_name)
                return

        git_https_url = "%s/%s.git" % (self.gitee_url, repo_name)
        git_ssl_url = self.https_url_to_ssh_url(git_https_url)

        print('======>Start to push local package %s to gitee.' % repo_name)
        cmd = r'git push --mirror --progress -v %s' % git_ssl_url
        print('cmd: ' + cmd)
        print("repo_path: " + repo_path)

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
        dir_name = os.path.dirname(new_path)
        if not os.path.exists(dir_name):
            print('makdir -pv ' + dir_name)
            os.makedirs(dir_name)
        cmd = r'wget -c ' + path
        print('cmd: ' + cmd)
        self.execute_command(cmd, cwd=dir_name)

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

    @classmethod
    def get_access_token(cls, token_payload):
        try:
            r = requests.post(
                "https://gitee.com/oauth/token", data=token_payload)

            if r.status_code == requests.codes.ok:
                package_info = json.loads(r.text)
                return package_info['access_token']

        except Exception as e:
            logging.error("Error message: {0}.".format(e))
            print('get access token fail')



