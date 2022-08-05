import requests
import json
import logging
import os
import sys
from sdk_index_gen import generate_all_index
from common_util import execute_command
from ci_config import INDEX_SERVER_URL

def submit_index(prIndex):
    try:
        headers={"Content-Type":"application/json; charset=UTF-8"}
        url=INDEX_SERVER_URL+"/merge/"
        response = requests.post(url,data=json.dumps(prIndex),headers=headers,timeout=60)
        if(response.status_code==404):
            raise Exception(response.status_code)
        else:
            logging.info("update-SdkIndexGithub-Compeleted: {0}.".format(url))
    except Exception as e:
        logging.error("update-SdkIndexGithub-Failed: {0}.".format(url))
        logging.error(e)
        sys.exit(1)
def main():
    logging.getLogger().setLevel(logging.INFO)
    index=generate_all_index("../index.json")
    if 'GITEE_TOKEN' in os.environ:
        submit_index(index)
    
if __name__ == "__main__":
    main()