#!/bin/bash
PLAYLISTER_SOURCE="${BASH_SOURCE[0]}"
PLAYLISTER_DIR=$( realpath `dirname $PLAYLISTER_SOURCE` )
TEMPLATE_DIR=$PLAYLISTER_DIR/playlister.heat/

. $PLAYLISTER_DIR/common.sh
[ "${BASH_SOURCE[0]}" -ef "$0" ]  || { echo "Don't source this script!  Run it."; return 1; }

source_host_control_scripts       || fail_exit "source_host_control_scripts"
new_venv playlister               || fail_exit "new_venv kolla-ansible"
use_venv playlister               || fail_exit "use_venv kolla-ansible"
. /etc/kolla/admin-openrc.sh

ANSIBLE_CONTROLLER=dmb

STACK_NAME=$1


openstack stack create -t $TEMPLATE_DIR/playlister.yaml -e $TEMPLATE_DIR/environment.yaml $STACK_NAME 
