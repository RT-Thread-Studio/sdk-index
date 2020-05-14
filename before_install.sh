if [ -z "$IS_MASTER_REPO" ]
then
        echo "User trigger"
else
        echo "Master trigger"
        openssl aes-256-cbc -K $encrypted_3b9f0b9d36d1_key -iv $encrypted_3b9f0b9d36d1_iv -in secrets.tar.enc -out secrets.tar -d
        tar xvf secrets.tar
        eval $(ssh-agent -s)
        chmod 600 id_rsa
        ssh-add id_rsa
        cp -f known_hosts ~/.ssh
fi
