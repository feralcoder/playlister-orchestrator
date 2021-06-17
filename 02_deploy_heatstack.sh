#!/bin/bash
PLAYLISTER_SOURCE="${BASH_SOURCE[0]}"
PLAYLISTER_DIR=$( realpath `dirname $PLAYLISTER_SOURCE` )
TEMPLATE_DIR=$PLAYLISTER_DIR/playlister.heat/

ENV_FILESERVER=http://192.168.127.220:81/files/

. $PLAYLISTER_DIR/venv.sh

[ "${BASH_SOURCE[0]}" -ef "$0" ]  || { echo "Don't source this script!  Run it."; return 1; }

use_venv playlister               || fail_exit "use_venv kolla-ansible"
. $PLAYLISTER_SETUP_DIR/playlister-openrc.sh
#. /etc/kolla/admin-openrc.sh

ANSIBLE_CONTROLLER=dmb

wait_for_stack_to_build() {
  STACK_NAME=$1
  STACK_STATE=''
  while [[ $STACK_STATE == '' ]] || [[ $STACK_STATE == 'PENDING_CREATE' ]]; do
    echo "Stack $STACK_NAME state is '$STACK_STATE'.  Sleeping 60s..."
    sleep 60
    STACK_LINE=$(openstack stack list | grep " $STACK_NAME ")
    STACK_STATE=$(echo $STACK_LINE | awk '{print $8}')
  done
  echo "Stack $STACK_NAME state is '$STACK_STATE'.  Continuing."
}

assert_stack_built_ok() {
  STACK_NAME=$1
  STACK_LINE=$(openstack stack list | grep " $STACK_NAME ")
  STACK_STATE=$(echo $STACK_LINE | awk '{print $8}')
  if [[ $STACK_STATE != 'CREATE_COMPLETE' ]]; then
    echo "Stack $STACK_NAME did not create successfully.  State is $STACK_STATE.  Exiting."
    exit 1
}

manage_stack() {
  STACK_NAME=$1
  echo "IMPLEMENT PER-NODE CORRECTNESS CHECKS BEFORE RUNNING MANAGE..."
}

STACK_NAME=playlister
#STACK_NAME=playlister2
#STACK_NAME=playlister3
#STACK_NAME=playlister4
#STACK_NAME=playlister5

python3 $TEMPLATE_DIR/../playlister-python/playlister.py FLUSH $STACK_NAME
openstack stack create -t $TEMPLATE_DIR/$STACK_NAME.yaml -e $TEMPLATE_DIR/environment-$STACK_NAME.yaml $STACK_NAME 
wait_for_stack_to_build $STACK_NAME
assert_stack_built_ok $STACK_NAME
manage_stack $STACK_NAME
