#!/bin/bash
PLAYLISTER_SOURCE="${BASH_SOURCE[0]}"
PLAYLISTER_DIR=$( realpath $(dirname $PLAYLISTER_SOURCE) )
TEMPLATE_DIR=$PLAYLISTER_DIR/playlister.heat/

. ~/CODE/feralcoder/host_control/control_scripts.sh
. $PLAYLISTER_DIR/common.sh
[ "${BASH_SOURCE[0]}" -ef "$0" ]  || { echo "Don't source this script!  Run it."; return 1; }

use_venv playlister               || fail_exit "use_venv kolla-ansible"
. $PLAYLISTER_SETUP_DIR/playlister-openrc.sh

ANSIBLE_CONTROLLER=dmb

STACK_NAME=$1
[[ $STACK_NAME != "" ]] || { echo "STACK_NAME undefined!"; exit 1; }

gather_stack_facts () {
  STACK_ID=$(openstack stack list | grep " $STACK_NAME " | awk '{print $2}')
  RESOURCE_LIST=$(openstack stack resource list $STACK_ID --nested-depth 10) || return 1
  FE_STACK_NAMES=$(echo "$RESOURCE_LIST" | grep " frontend " | awk '{print $12}')
  OLAP_STACK_NAMES=$(echo "$RESOURCE_LIST" | grep " olap_backend " | awk '{print $12}')
  OLTP_STACK_NAMES=$(echo "$RESOURCE_LIST" | grep " oltp_backend " | awk '{print $12}')
  STACK_LIST=$(openstack stack list --nested | grep $STACK_NAME) || return 1

  FE_STACK_IDS=$(for NAME in $FE_STACK_NAMES; do
    echo "$STACK_LIST" | grep $NAME | awk '{print $2}'
  done)

  OLAP_STACK_IDS=$(for NAME in $OLAP_STACK_NAMES; do
    echo "$STACK_LIST" | grep $NAME | awk '{print $2}'
  done)
  OLTP_STACK_IDS=$(for NAME in $OLTP_STACK_NAMES; do
    echo "$STACK_LIST" | grep $NAME | awk '{print $2}'
  done)

  FE_LB_STACK_NAME=$(echo "$RESOURCE_LIST" | grep " fe_loadbalancer " | awk '{print $12}')
  FE_LB_STACK_ID=$(echo "$STACK_LIST" | grep " $FE_LB_STACK_NAME " | awk '{print $2}')
  OLAP_LB_STACK_NAME=$(echo "$RESOURCE_LIST" | grep " olap_loadbalancer " | awk '{print $12}')
  OLAP_LB_STACK_ID=$(echo "$STACK_LIST" | grep " $OLAP_LB_STACK_NAME " | awk '{print $2}')
  OLTP_LB_STACK_NAME=$(echo "$RESOURCE_LIST" | grep " oltp_loadbalancer " | awk '{print $12}')
  OLTP_LB_STACK_ID=$(echo "$STACK_LIST" | grep " $OLTP_LB_STACK_NAME " | awk '{print $2}')
  
  FE_VIP=$(openstack stack output show $FE_LB_STACK_ID fe_vip_ip -f json | jq '.["output_value"]' | sed 's/"//g') || return 1
  OLAP_VIP=$(openstack stack output show $FE_LB_STACK_ID olap_vip_ip -f json | jq '.["output_value"]' | sed 's/"//g') || return 1
  OLTP_VIP=$(openstack stack output show $FE_LB_STACK_ID oltp_vip_ip -f json | jq '.["output_value"]' | sed 's/"//g') || return 1

  FE_IPS=$(for ID in $FE_STACK_IDS; do
    openstack stack output show $ID server_ip -f json | jq '.["output_value"]' | sed 's/"//g' || return 1
  done)

  OLAP_IPS=$(for ID in $OLAP_STACK_IDS; do
    openstack stack output show $ID server_ip -f json | jq '.["output_value"]' | sed 's/"//g' || return 1
  done)
  OLTP_IPS=$(for ID in $OLTP_STACK_IDS; do
    openstack stack output show $ID server_ip -f json | jq '.["output_value"]' | sed 's/"//g' || return 1
  done)

  SERVER_LIST=$(openstack server list | grep -v '\-\-\-\-\| Name ')
  FE_LINES=$(for IP in $FE_IPS; do
    NAME=$(echo "$SERVER_LIST" | grep "$IP[ ,]" | awk '{print $4}')
    ID=$(echo "$SERVER_LIST" | grep "$IP[ ,]" | awk '{print $2}')
    echo "$NAME:$ID:$IP"
  done)
  OLAP_LINES=$(for IP in $OLAP_IPS; do
    NAME=$(echo "$SERVER_LIST" | grep "$IP[ ,]" | awk '{print $4}')
    ID=$(echo "$SERVER_LIST" | grep "$IP[ ,]" | awk '{print $2}')
    echo "$NAME:$ID:$IP"
  done)
  OLTP_LINES=$(for IP in $OLTP_IPS; do
    NAME=$(echo "$SERVER_LIST" | grep "$IP[ ,]" | awk '{print $4}')
    ID=$(echo "$SERVER_LIST" | grep "$IP[ ,]" | awk '{print $2}')
    echo "$NAME:$ID:$IP"
  done)

}

#get_cassandra_seeds () {
#  SEEDS=$(openstack stack show $STACK_ID  -c tags | sed 's/ /\n/g' | grep SEEDS | awk -F'=' '{print $2}' | sed 's/:/,/g') || return 1
#  echo "$SEEDS"
#}

gather_stack_facts || exit 1
echo FE_VIP: $FE_VIP
echo FE_IPS: $FE_IPS
echo OLAP_VIP: $OLAP_VIP
echo OLAP_IPS: $OLAP_IPS
echo OLTP_VIP: $OLTP_VIP
echo OLTP_IPS: $OLTP_IPS

#echo FE_IPS: $FE_IPS
for LINE in $FE_STACK_IDS; do
  echo FE_STACK_ID: $LINE
done
for LINE in $FE_STACK_NAMES; do
  echo FE_STACK_NAME: $LINE
done
for LINE in $FE_LINES; do
  echo "FRONTEND: $LINE"
done

#echo OLAP_IPS: $OLAP_IPS
for LINE in $OLAP_STACK_IDS; do
  echo OLAP_STACK_ID: $LINE
done
for LINE in $OLAP_STACK_NAMES; do
  echo OLAP_STACK_NAME: $LINE
done
for LINE in $OLAP_LINES; do
  echo "OLAP_BACKEND: $LINE"
done

#echo OLTP_IPS: $OLTP_IPS
for LINE in $OLTP_STACK_IDS; do
  echo OLTP_STACK_ID: $LINE
done
for LINE in $OLTP_STACK_NAMES; do
  echo OLTP_STACK_NAME: $LINE
done
for LINE in $OLTP_LINES; do
  echo "OLTP_BACKEND: $LINE"
done

#echo BACKEND_SEEDS: $(get_cassandra_seeds)
MANILA_SHARE_PATH=`cat /etc/ceph/manila-playlister-share-path`
echo MANILA_SHARE_PATH: $MANILA_SHARE_PATH
MANILA_KEY=$(cat /etc/ceph/ceph.client.manila.keyring | grep key | awk '{print $3}')
echo MANILA_KEY: $MANILA_KEY

MON_LIST=$(for HOST in $CONTROL_HOSTS; do
  IP=$(getent ahosts $HOST | awk '{print $1}' | tail -n 1)
  echo "[v2:$IP:3300,v1:$IP:6789]"
done)

echo MON_LIST: $MON_LIST
