# file: .profile.d/ssh-setup.sh

#!/bin/bash
echo $0: creating public and private key files

# Create the .ssh directory
mkdir -p ${HOME}/.ssh
chmod 700 ${HOME}/.ssh

# Create the public and private key files from the environment variables.
echo "${HEROKU_PUBLIC_KEY}" > ${HOME}/.ssh/heroku_id_rsa.pub
chmod 644 ${HOME}/.ssh/heroku_id_rsa.pub

# Note use of double quotes, required to preserve newlines
echo "${HEROKU_PRIVATE_KEY}" > ${HOME}/.ssh/heroku_id_rsa
chmod 600 ${HOME}/.ssh/heroku_id_rsa

# Preload the known_hosts file
echo '|1|M+8SkUnlahC3Kj+GpF94xg7EJ4Q=|Nk3fomItUU1sulP/2Qy7mcwuSZo= ssh-rsa AAAAB3NzaC1yc2EAAAABEQAAAQEAq/sURD9vq9knVcSNEEfZJQF8uxFsl0++yb6AjYzRxxYaz0PApkXQjI0QzCMjf9unV7K/W469oNUkBS5Yv5ri9/4bHRcMXgkixKV3yGahbcLRxLU7SQNsNZeoO08AysykGYa2fWsyYwUCaLTBsM4Zaad/FJGn+uvOip5J6KTy6dpksHFKdlTeKavhCx2lHY18G1UlZd/tIuUYJWhYTt8UDKfWIJUEMzxkvBguSqqbtnvQR1RYQ4tMXiJSwEZ6/iS3+HxGN3bpuG9qcAy1627o8CHizrRrd5NJUoKijn+ZKApFA+evYfuFPhEcNUpxnsFe9HVZj3grBEQBgyQ6rG4T7w==
|1|vAsGqHk24MpX8oaZboZf/wZsAoU=|RATHlyu+P8MvRIXgGNUmOjSG9Io= ssh-rsa AAAAB3NzaC1yc2EAAAABEQAAAQEAq/sURD9vq9knVcSNEEfZJQF8uxFsl0++yb6AjYzRxxYaz0PApkXQjI0QzCMjf9unV7K/W469oNUkBS5Yv5ri9/4bHRcMXgkixKV3yGahbcLRxLU7SQNsNZeoO08AysykGYa2fWsyYwUCaLTBsM4Zaad/FJGn+uvOip5J6KTy6dpksHFKdlTeKavhCx2lHY18G1UlZd/tIuUYJWhYTt8UDKfWIJUEMzxkvBguSqqbtnvQR1RYQ4tMXiJSwEZ6/iS3+HxGN3bpuG9qcAy1627o8CHizrRrd5NJUoKijn+ZKApFA+evYfuFPhEcNUpxnsFe9HVZj3grBEQBgyQ6rG4T7w==' > ${HOME}/.ssh/known_hosts


