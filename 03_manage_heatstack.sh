#!/bin/bash
PLAYLISTER_SOURCE="${BASH_SOURCE[0]}"
PLAYLISTER_DIR=$( realpath `dirname $PLAYLISTER_SOURCE` )
TEMPLATE_DIR=$PLAYLISTER_DIR/playlister.heat/

. $PLAYLISTER_DIR/common.sh
[ "${BASH_SOURCE[0]}" -ef "$0" ]  || { echo "Don't source this script!  Run it."; return 1; }

use_venv playlister               || fail_exit "use_venv kolla-ansible"
. $PLAYLISTER_SETUP_DIR/playlister-openrc.sh

ANSIBLE_CONTROLLER=dmb

STACK_NAME=$1
[[ $STACK_NAME != "" ]] || { echo "STACK_NAME undefined!"; exit; }



rename_servers () {
  SERVER_LINES=`openstack server list | grep -v '\-\-\-\| Name ' | grep " ${STACK_NAME}_"`
  FE_LINES=`echo "$SERVER_LINES" | grep " ${STACK_NAME}_fe "`
  BE_LINES=`echo "$SERVER_LINES" | grep " ${STACK_NAME}_be "`

  ID_IP_PAIRS=$(while read -r LINE; do
    ID=`echo $LINE | awk '{print $2}'`
    IP=`echo $LINE | awk '{print $8}' | awk -F'=' '{print $2}'`
    echo $ID:$IP
  done < <(printf '%s\n' "$SERVER_LINES"))

  for PAIR in $ID_IP_PAIRS; do
    ID=`echo $PAIR | awk -F':' '{print $1}'`
    IP=`echo $PAIR | awk -F':' '{print $2}'`
    HOSTNAME=`ssh -J admin1 -o "StrictHostKeyChecking no" -i ~/.ssh/keypair.cliff_admin.private -l centos $IP hostname -s`
    echo "Renaming $ID to $HOSTNAME"
    openstack server set --name $HOSTNAME $ID
  done
}

rename_servers
