python3 main.py || travis_terminate 1

if [ -z "$IS_MASTER_REPO" ]
then
        echo "User trigger, begin to check Chip or Board Support Package."
        docker pull summergift/csp_test:v1.0
        cd ..
        docker run -v "`pwd`:/rt-thread/sdk-index" -it summergift/csp_test:v1.0 bash -c "python /rt-thread/sdk-index/tools/sdk_check/main.py"
        cd tools/sdk_check && python3 mail_send.py
else
        echo "Master trigger, No need to check Chip Support Package."
fi
