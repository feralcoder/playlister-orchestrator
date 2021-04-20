#!/bin/bash

source_host_control_scripts () {
  . ~/CODE/feralcoder/host_control/control_scripts.sh
}

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

setup_venv () {
  pip install --upgrade pip
  pip install --upgrade pep8
  pip install --upgrade pylint
  pip install --upgrade flake8
  pip install --upgrade pycodestyle
  pip install --upgrade path.py
  pip install --upgrade python-openstackclient
  pip install --upgrade python-heatclient
  pip install --upgrade python-magnumclient
  pip install --upgrade python-neutronclient
  pip install --upgrade python-glanceclient
  pip install --upgrade python-novaclient
  pip install --upgrade python-cinderclient
  pip install --upgrade python-keystoneclient
  pip install --upgrade keystoneauth1
}

new_venv () {
  local VENV=$1
  [[ $VENV != "" ]] || { echo "No VENV supllied!"; return 1; }
  mkdir -p ~/CODE/venvs/$VENV &&
  python3 -m venv ~/CODE/venvs/$VENV
  use_venv $VENV
  setup_venv
}
