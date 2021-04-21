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



gather_stack_facts () {
  STACK_ID=`openstack stack list | grep " $STACK_NAME " | awk '{print $2}'`
  RESOURCE_LIST=`openstack stack resource list $STACK_ID --nested-depth 10`
  FE_STACK_NAMES=`echo "$RESOURCE_LIST" | grep " frontend " | awk '{print $12}'`
  BE_STACK_NAMES=`echo "$RESOURCE_LIST" | grep " backend " | awk '{print $12}'`
  STACK_LIST=`openstack stack list --nested | grep $STACK_NAME`

  FE_STACK_IDS=`for NAME in $FE_STACK_NAMES; do
    echo "$STACK_LIST" | grep $NAME | awk '{print $2}'
  done`

  BE_STACK_IDS=`for NAME in $BE_STACK_NAMES; do
    echo "$STACK_LIST" | grep $NAME | awk '{print $2}'
  done`

  FE_LB_STACK_NAME=`echo "$RESOURCE_LIST" | grep " fe_loadbalancer " | awk '{print $12}'`
  FE_LB_STACK_ID=`echo "$STACK_LIST" | grep " $FE_LB_STACK_NAME " | awk '{print $2}'`
  FE_VIP=`openstack stack output show $FE_LB_STACK_ID vip_ip -f json | jq '.["output_value"]' | sed 's/"//g'`

  FE_IPS=`for ID in $FE_STACK_IDS; do
    openstack stack output show $ID server_ip -f json | jq '.["output_value"]' | sed 's/"//g'
  done`

  BE_IPS=`for ID in $BE_STACK_IDS; do
    openstack stack output show $ID server_ip -f json | jq '.["output_value"]' | sed 's/"//g'
  done`
}

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
    HOSTNAME=`ssh -o "StrictHostKeyChecking no" -i ~/.ssh/keypair.cliff_admin.private -l centos $IP hostname -s`
    echo "Renaming $ID to $HOSTNAME"
    openstack server set --name $HOSTNAME $ID
  done
}

gather_stack_facts
echo FE_VIP: $FE_VIP
echo FE_IPS: $FE_IPS
echo BE_IPS: $BE_IPS


rename_servers
