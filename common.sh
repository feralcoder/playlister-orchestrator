#!/bin/bash
PLAYLISTER_SETUP_SOURCE="${BASH_SOURCE[0]}"
PLAYLISTER_SETUP_DIR=$( realpath `dirname $PLAYLISTER_SETUP_SOURCE` )


#source_host_control_scripts () {
#  . ~/CODE/feralcoder/host_control/control_scripts.sh
#}

fail_exit () {
  echo; echo "FAILURE, EXITING: $1"
  python3 ~/CODE/feralcoder/twilio-pager/pager.py "KOLLA-ANSIBLE FAILURE, EXITING: $1"
  exit 1
}

test_sudo () {
  sudo -K
  if [[ $SUDO_PASS_FILE == "" ]]; then
    echo "SUDO_PASS_FILE is undefined!"
    return 1
  fi
  cat $SUDO_PASS_FILE | sudo -S ls > /dev/null 2>&1
}


use_venv () {
  local VENV=$1
  [[ $VENV != "" ]] || { echo "No VENV supllied!"; return 1; }
  source ~/CODE/venvs/$VENV/bin/activate
}

install_venv () {
  sudo apt -y install python3-pip || sudo dnf -y install python3-pip
  sudo apt -y install python3-venv || sudo dnf -y install python3-venv
}

setup_venv () {
  pip3 install --upgrade pip
  pip3 install --upgrade pep8
  pip3 install --upgrade pylint
  pip3 install --upgrade flake8
  pip3 install --upgrade pycodestyle
  pip3 install --upgrade path.py
  pip3 install --upgrade python-openstackclient
  pip3 install --upgrade python-heatclient
  pip3 install --upgrade python-magnumclient
  pip3 install --upgrade python-neutronclient
  pip3 install --upgrade python-glanceclient
  pip3 install --upgrade python-novaclient
  pip3 install --upgrade python-cinderclient
  pip3 install --upgrade python-keystoneclient
  pip3 install --upgrade python-ceilometer
  pip3 install --upgrade keystoneauth1
}

new_venv () {
  local VENV=$1
  [[ $VENV != "" ]] || { echo "No VENV supllied!"; return 1; }
  install_venv
  mkdir -p ~/CODE/venvs/$VENV &&
  python3 -m venv ~/CODE/venvs/$VENV
  use_venv $VENV
  setup_venv
}

