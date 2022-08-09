

import requests
import json
import logging
import os
import sys
import urllib.request
import urllib.error
import urllib.parse
from sdk_index_gen import do_update_sdk_mirror_server_index,generate_all_index
from common_util import execute_command
from ci_config import INDEX_SERVER_URL

mirror_path = r'sync_local_repo/github_mirror'
mirror_file = r'sync_local_repo/github_mirror_file'
gitee_url = 'https://gitee.com/RT-Thread-Studio-Mirror'
mirror_org_name = "RT-Thread-Studio-Mirror"

packages_index = None


def gitee_token():
    if 'GITEE_TOKEN' in os.environ:
        return os.environ['GITEE_TOKEN']
    return None



def getPkgs2Sync():
    url=INDEX_SERVER_URL+"/pkgs2sync"
    try:
        response = requests.get(url,timeout=60)
        return response.text
    except Exception as e:
        logging.error(e)
        sys.exit(1)

def onSyncCompelete(repo_name):
    url=INDEX_SERVER_URL+"/aftersync?name="
    try:
        response = requests.get(url+repo_name,timeout=60)
        logging.info("update-SdkIndexGitee-Compeleted: {0}.".format(repo_name))
    except Exception as e:
        logging.error(e)

def checkGitActionIsError(e):
    msg=str(e)
    if 'receive.denyDeleteCurrent' in msg or 'deleting the current branch is denied' in msg:
        #ignore this error
        return False
    else:
        return 'fatal:' in msg or 'disconnect:' in msg or 'error:' in msg or 'Error' in msg

def fetch_packages_from_git(zip_url):
        print('======>Fetch package from git repo :' + zip_url)

        url = zip_url[:zip_url.find("/archive")]
        git_path = url + ".git"
        tmp = url.split('/')
        org = tmp[3]
        repo_name = tmp[4]

        org_path = os.path.join(mirror_path, org)
        if not os.path.exists(org_path):
            print('makdir -pv ' + org_path)
            os.makedirs(org_path)

        git_repo_path = os.path.join(org_path, repo_name)
        logging.info(git_repo_path)

        repo_path = os.path.join(org_path, repo_name)
        if os.path.exists(repo_path):
            os.removedirs(repo_path)
        try:
            print('makdir -pv ' + repo_path)
            os.makedirs(repo_path)
            cmd = r'git clone %s %s'
            cmd = cmd % (git_path, repo_name)
            print('======>Clone packages %s to local.' % repo_name)
            execute_command(cmd, cwd=org_path)
            print('git_repo_path : %s' % git_repo_path)
            cmd = r"""git branch -r | grep -v '\->' | while read remote; do git branch --track "${remote#origin/}" 
            "$remote"; done"""
            execute_command(cmd, cwd=git_repo_path)
            print('======>Multi-branch synchronization is complete.')
            print('======>Start to fetch and pull Multi-branch.')
            cmd = r'git fetch --all'
            execute_command(cmd, cwd=git_repo_path)
            cmd = r'git pull --all'
            execute_command(cmd, cwd=git_repo_path)
            cmd = r'git fetch --tags'
            execute_command(cmd, cwd=git_repo_path)
        except Exception as e:
            if(checkGitActionIsError(e)):
                logging.error('error: %s clone failed, wait for next update.' % repo_name)
            else:
                logging.info(e)

        git_https_url = "%s/%s.git" % (gitee_url, repo_name)
        git_ssl_url = https_url_to_ssh_url(git_https_url)

        print('======>Start to push local package %s to gitee.' % repo_name)
        cmd = r'git push --mirror --progress -v %s' % git_ssl_url
        print('cmd: ' + cmd)
        print("repo_path: " + repo_path)
        try:
            execute_command(cmd, cwd=repo_path)
            print('======>Push done')
            onSyncCompelete(repo_name)
        except Exception as e:
            if(checkGitActionIsError(e)):
                logging.error("error: push failed {0}.".format(e))
            else:
                logging.info(e)
                print('======>Push done')
                onSyncCompelete(repo_name)


    
def https_url_to_ssh_url(http_url):
        ssh_url = http_url.replace("https://gitee.com/", "git@gitee.com:")
        return ssh_url

def create_repo_in_gitee(repo_name):
        print("======>Start to create %s repo in gitee." % repo_name)
        send_data = "access_token=%s&name=%s" % (gitee_token(), repo_name)
        send_url = "https://gitee.com/api/v5/orgs/%s/repos" % mirror_org_name

        try:
            request =  urllib.request.Request(send_url, send_data.encode("utf-8"), {
                'content-type': 'application/x-www-form-urlencoded',
                'Connection': 'keep-alive',
                'Accept-Encoding': 'gzip, deflate',
                'Accept': '*/*',
                'User-Agent': 'curl/7.54.0'})

            response = urllib.request.urlopen(request)
            resp = response.read()
            print(resp)
        except Exception as e:
            #continue
            logging.info(" create repo failed:  message: {0}.".format(e))


def main():
    logging.getLogger().setLevel(logging.INFO)
    logging.info("scheduler check pkgs to be async to gitee ...")
    diff=getPkgs2Sync()
    logging.info("new-pkgs:"+diff)
    arr= json.loads(diff)
    # for new gitee-index-sync
    for url in arr:
        tmp = url.split('/')
        repoName=tmp[4]
         # get packages repository
        if  gitee_token() is not None:
            try:
                # create new repo in mirror
                create_repo_in_gitee(repoName)
                # clone repo and push
                fetch_packages_from_git(url)
            except Exception as e:
                logging.error(e)
                continue
        else:
            logging.info("No sync token")

    # just for old gitee-index-sync---to be removed in future 
    new_index=generate_all_index("../index.json")
    do_update_sdk_ide_index(new_index)
    do_update_sdk_mirror_server_index()


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

if __name__ == "__main__":
    main()