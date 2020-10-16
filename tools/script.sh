python3 main.py || travis_terminate 1

if [ -z "$IS_MASTER_REPO" ]
then
        echo "User trigger, begin to check Chip or Board Support Package."
        cd ..
        wget -nv http://gosspublic.alicdn.com/ossutil/1.6.16/ossutil64
        chmod 755 ossutil64
        ./ossutil64 config -e $OSS_ENDPOINT -i $OSS_ID -k $OSS_KEY  -L CH -c ossconfig
        ./ossutil64 -c ossconfig cp -r oss://realthread-artifacts/studio-backend/ tools/sdk_check/
        docker pull realthread/sdk_index:latest
        docker run -v "`pwd`:/rt-thread/sdk-index" -i realthread/sdk_index:latest bash -c ". /etc/profile && python /rt-thread/sdk-index/tools/sdk_check/sdk_check.py"
else
        echo "Master trigger, No need to check Chip Support Package."
fi
