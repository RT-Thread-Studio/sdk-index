python3 main.py || travis_terminate 1

if [ -z "$IS_MASTER_REPO" ]
then
        echo "User trigger, begin to check Chip or Board Support Package."
        cd ..
        docker pull realthread/sdk_index:latest
        docker run -v "`pwd`:/rt-thread/sdk-index" -it realthread/sdk_index:latest bash -c ". /etc/profile && python /rt-thread/sdk-index/tools/sdk_check/sdk_check.py"
        cd tools/sdk_check && python3 check_report.py
else
        echo "Master trigger, No need to check Chip Support Package."
fi
