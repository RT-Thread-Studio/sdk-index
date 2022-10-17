
from pickle import FALSE, TRUE
import subprocess
import logging
import time
import os
import wget
import zipfile

def execute_command(cmd_string, cwd=None, shell=True):
    sub = subprocess.Popen(cmd_string, cwd=cwd, stdin=subprocess.PIPE,stderr=subprocess.PIPE,
                           stdout=subprocess.PIPE, shell=shell, bufsize=4096)

    stdout_str = ''
    while sub.poll() is None:
        err= sub.stderr.read()
        stdout_str += str(sub.stdout.read(), encoding="UTF-8")
        if len(err)>0:
            raise Exception(err)
        time.sleep(0.1)

    return stdout_str

def rename_dir_file(dir,old,new):
    os.chdir(dir)
    execute_command("mv {0} {1}".format(old,new))

def clear_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)
    os.chdir(dir)
    execute_command("rm -rf *")

def git_clone(url,dir):
    if os.path.exists(dir):
        clear_dir(dir)
    try:
        cmd = 'git clone ' + url
        os.chdir(dir)
        execute_command(cmd)
        logging.info(cmd+"---compeleted")
    except Exception as e:
        logging.info(e)


def download_retry(url,dir,file_name,retry=10):
    success=0
    count=0
    if not os.path.exists(dir):
        os.makedirs(dir)
    full_path=os.path.join(os.path.dirname(dir), file_name)
    while (count<=retry and success==0 ):
        count=count+1
        if os.path.exists(full_path):
            os.remove(full_path)
        try:
            logging.info(url+"---downloading")
            wget.download(url,out=full_path)
            logging.info("---downloaded")
            success=1
        except Exception as e:
            logging.error(e)
            logging.info("download failed "+ str(count)+" retry ...")
            time.sleep(10)
    if(count>retry and not success):
        raise Exception("download failed "+str(retry)+" times")

def file_merge_unzip(zip_file,target_dir):
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    logging.info("unzip:"+zip_file+"---to:"+target_dir)
    zipObj= zipfile.ZipFile(zip_file)
    zipObj.extractall(target_dir)
    zipObj.close()
    logging.info("unzip:"+zip_file+"---compeleted")

def do_merge_copy(src_dir, dst_dir):
    if not os.path.exists(src_dir):
        raise Exception("ERROR: Can’t get resource {0}, please check the resource.".format(src_dir))

    try:
        execute_command("\cp -rf {0} {1}".format(src_dir,dst_dir))
    except Exception as e:
        logging.error("Error message: {0}".format(e))
        raise Exception("ERROR: Copy {0} failed.".format(src_dir))

    return True