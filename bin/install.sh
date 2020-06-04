# vim: tabstop=4 shiftwidth=4 softtabstop=4
# -*- sh-basic-offset: 4 -*-

set -euo pipefail
IFS=$'\n\t'

SONAR_PATH="/home/pi/sonar"


install_base_dependencies() {
        # Rather hackish, but speeds up the runtime a lot.
        get_packages=$(dpkg -l | grep -E '^ii' | awk {'print $2'} | grep -E -e "^curl$" -e "^git$" -e "^python3-pip$"  | wc -l)
        if [ "$get_packages" -ne 3 ]; then
                apt -q update
                apt install -y git curl python3-pip
        fi
}


install_docker() {
        # Simply uses the instructions from here:
        # https://docs.docker.com/engine/install/debian/
        echo "Docker not found. Installing."
        curl -fsSL get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm get-docker.sh
        usermod -aG docker pi
}


install_docker_compose() {
        # Instructions from:
        # https://docs.docker.com/compose/install/
        pip3 install docker-compose
}


update_and_build() {
        cd "$SONAR_PATH"
        git pull
        docker-compose build
}


run_sonar() {
        # Allow access to Sonar both using the hostname and IP
        my_hostname=$(hostname -f)
        my_ip=$(ip -4 route get 8.8.8.8 | awk {'print $7'} | tr -d '\n')
        export ALLOWED_HOSTS="$my_hostname\|$my_ip"
        docker-compose up -d
        echo "You should be able to access your Sonar instance either using http://$my_hostname or http://$my_ip"
}


## Main function
if [ "$EUID" -ne 0 ]; then
        echo "Please run as root"
        exit 1
fi


install_base_dependencies

# Conditional installs
which docker > /dev/null || install_docker
which docker-compose > /dev/null || install_docker_compose

if [ ! -d "$SONAR_PATH" ]; then
        git clone https://github.com/databat-io/sonar.git "$SONAR_PATH"
        chown -R pi:pi "$SONAR_PATH"
fi

update_and_build
run_sonar
