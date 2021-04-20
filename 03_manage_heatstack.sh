#!/bin/bash
PLAYLISTER_SOURCE="${BASH_SOURCE[0]}"
PLAYLISTER_DIR=$( realpath `dirname $PLAYLISTER_SOURCE` )
TEMPLATE_DIR=$PLAYLISTER_DIR/playlister.heat/

. $PLAYLISTER_DIR/common.sh
[ "${BASH_SOURCE[0]}" -ef "$0" ]  || { echo "Don't source this script!  Run it."; return 1; }

source_host_control_scripts       || fail_exit "source_host_control_scripts"
use_venv playlister               || fail_exit "use_venv kolla-ansible"
. /etc/kolla/admin-openrc.sh

ANSIBLE_CONTROLLER=dmb

STACK_NAME=$1



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

echo FE_VIP: $FE_VIP
echo FE_IPS: $FE_IPS
echo BE_IPS: $BE_IPS
